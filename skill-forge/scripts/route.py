#!/usr/bin/env python3
"""Route a plain-language need to the best capability in the registry.

Usage:
    python route.py "instagram reels ka script likhna hai"
    python route.py "nurse shift handover SBAR banao" --top 5
    python route.py "<need>" --json

Exit 0 = reusable capability found (verdict reuse/adapt),
exit 3 = forge a new skill (nothing close, or only an archetype matched).

Also importable: `from route import load, rank` for the other scripts.
"""
import argparse, json, math, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve()
DEFAULT_ROOT = next((p for p in (HERE.parent.parent, pathlib.Path.cwd())
                     if (p / "registry" / "registry.json").exists()), None)

STOP = set("""a an the of for and or to in on with by from into over under as at is are be been
your you their its it this that these those how what when where which who why do does did make
made using use used best top all any more most other some such no not only own same so than too
very can will just should now need want like help please give get got have has had my me we our
skill skills new naya nayi ek koi bhi hai hain ho kar ka ki ke ko se me mein par aur ya kuch
chahiye chaiye karna karo karke banao bana banai banaye likho likhe likhna dikhao dikha
batao bata dena do dubara wala wali wale jaisa jaise liye kaam
turn turns into onto about across based thing things stuff also then there here
want wants need needs raha rahe rahi hota hoti hoga kuchh sab sabhi apna apni apne
mera meri mere tum aap hum""".split())

# Hinglish / casual verbs -> the English token the registry uses.
ALIAS = {
    "banao": "create", "bana": "create", "banai": "create", "banaye": "create", "banana": "create",
    "likho": "write", "likhe": "write", "likhna": "write", "likh": "write",
    "dikhao": "show", "dikha": "show", "batao": "explain", "samjhao": "explain",
    "sudharo": "improve", "theek": "fix", "sahi": "fix", "galti": "debug", "error": "debug",
    "tasveer": "image", "photo": "image", "chitra": "image",
    "awaaz": "voice", "aawaz": "voice",
    "patra": "letter", "paisa": "payment", "paisaa": "payment",
    "grahak": "customer", "bekri": "sales", "bikri": "sales", "hisab": "account",
    "soochi": "list", "suchi": "list", "jaanch": "audit", "roz": "daily",
    "hafte": "weekly", "hafta": "weekly", "mahine": "monthly",
    "kholo": "open", "bhejo": "send", "bhej": "send",
    "padho": "read", "padhna": "read", "suno": "listen", "dhoondo": "search", "khojo": "search",
}


# two-character tokens that carry real meaning in this registry; without this
# "check PR karo" loses the word that identifies the skill entirely
SHORT_OK = {"pr", "ai", "ml", "ui", "ux", "qa", "hr", "ci", "cd", "db", "vr", "ar", "3d", "2d", "5s"}


def tokens(text):
    out = []
    for raw in re.split(r"[^a-z0-9]+", str(text).lower()):
        if (len(raw) < 3 and raw not in SHORT_OK) or raw in STOP:
            continue
        t = ALIAS.get(raw, raw)
        # crude singular form, applied identically to queries and entries so
        # "reels" matches "reel" and "documents" matches "document"
        if len(t) > 4 and t.endswith("s"):
            t = t[:-1]
        out.append(t)
    return out


def entry_text(e):
    return " ".join([e.get("name", ""), e.get("title", ""), e.get("capability", ""),
                     " ".join(e.get("triggers", [])), e.get("group", "")]).lower()


def load(root=None):
    r = pathlib.Path(root).resolve() if root else DEFAULT_ROOT
    if r is None:
        sys.exit("registry/registry.json not found - run scripts/build_registry.py first")
    return json.loads((r / "registry" / "registry.json").read_text(encoding="utf-8")), r


def rank(reg, need, top=5):
    entries = reg["entries"]
    df = {}
    for e in entries:
        for t in set(tokens(entry_text(e))):
            df[t] = df.get(t, 0) + 1
    N = len(entries)

    def idf(t):
        return math.log((N + 1) / (df.get(t, 0) + 1)) + 0.35

    qt = tokens(need)
    if not qt:
        sys.exit("the need has no usable keywords - describe the task in a few words")
    qset = list(dict.fromkeys(qt))
    total_idf = sum(idf(t) for t in qset) or 1.0
    rare = {t for t in qset if df.get(t, 0) <= max(2, int(0.02 * N))}
    wants_new = bool(re.search(
        r"\b(new|naya|nayi|create|banao|build|make|forge)\b.*\bskill\b|\bskill\b.*\b(new|naya|banao|build|make|forge)\b",
        need.lower()))

    scored = []
    for e in entries:
        et = set(tokens(entry_text(e)))
        hits = [t for t in qset if t in et]
        if not hits:
            continue
        raw = sum(idf(t) for t in hits)
        coverage = len(hits) / len(qset)
        s = raw * (0.65 + 0.55 * coverage)
        name_l = e.get("name", "").lower()
        for i in range(len(qt) - 1):
            bg = qt[i] + " " + qt[i + 1]
            if bg in name_l or bg in e.get("capability", "").lower():
                s += 1.2
        s *= {"skill": 1.18, "core": 1.05, "integration": 1.0, "command": 0.9,
              "archetype": 0.86}.get(e["type"], 1.0)
        # an entry whose files are not installed is worth less than one you can
        # actually load, so an installed skill wins a near-tie
        if e.get("status") == "reference":
            s *= 0.92
        conf = round(1.0 - math.exp(-s / 8.0), 3)
        scored.append((round(s, 3), conf, e, round(coverage, 2), len([t for t in hits if t in rare])))

    scored.sort(key=lambda x: (-x[0], x[2]["name"].lower()))
    top_rows = scored[:top]
    best = top_rows[0] if top_rows else (0.0, 0.0, None, 0.0, 0)

    if best[2] is not None and best[2]["type"] == "archetype" and best[1] >= 0.30:
        verdict = "forge"
        why = ("the need maps to a known professional workflow with no skill built for it - "
               "forge it, using that archetype as the blueprint")
    elif wants_new:
        verdict = "forge"
        why = "the user asked for a new skill; the candidates below are for reuse or inspiration"
    elif len(rare) >= 2 and best[4] == 0:
        verdict = "forge"
        why = "the distinctive words in the need match nothing - only generic words landed"
    elif best[1] >= 0.62:
        verdict = "reuse"
        why = "one capability matches the need closely"
    elif best[1] >= 0.38:
        verdict = "adapt"
        why = "partial matches only - combine them, or forge a focused skill on top of the best one"
    else:
        verdict = "forge"
        why = "no capability in the registry is close enough"

    # an entry whose files are not installed can inform a build but cannot be
    # "loaded and followed", so it never produces a plain REUSE
    if verdict == "reuse" and best[2] is not None and best[2].get("status") == "reference":
        verdict = "adapt"
        why = ("the closest match is a reference implementation - indexed but not installed. "
               "Adapt from it, or import its files before relying on it")

    return {
        "need": need,
        "registry_size": reg["total"],
        "verdict": verdict,
        "why": why,
        "candidates": [{"id": e["id"], "type": e["type"], "name": e["name"],
                        "capability": e["capability"], "source": e.get("source", ""),
                        "status": e.get("status", ""),
                        "score": s, "confidence": c, "coverage": cov,
                        "distinctive_hits": rh} for s, c, e, cov, rh in top_rows],
        "next": ("load the top candidate and work from it"
                 if verdict == "reuse" else
                 "combine the top candidates into one workflow, or forge a focused skill"
                 if verdict == "adapt" else
                 "run scripts/scaffold_spec.py, fill the judgement gaps, then scripts/forge_skill.py"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("need", nargs="+")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root")
    a = ap.parse_args()

    reg, _ = load(a.root)
    result = rank(reg, " ".join(a.need), a.top)

    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        print("need      : " + result["need"])
        print("registry  : %d entries" % result["registry_size"])
        print("verdict   : %s (%s)" % (result["verdict"].upper(), result["why"]))
        print("next      : " + result["next"])
        for i, c in enumerate(result["candidates"], 1):
            print("  %d. [%s] %s  conf=%.2f cov=%.2f  (%s)"
                  % (i, c["type"], c["name"], c["confidence"], c["coverage"], c["id"]))
    sys.exit(3 if result["verdict"] == "forge" else 0)


if __name__ == "__main__":
    main()
