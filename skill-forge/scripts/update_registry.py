#!/usr/bin/env python3
"""Keep the registry current, and never lose a good skill to a worse one.

Usage:
    python update_registry.py --zip /scratch/work/incoming.zip     # add skills
    python update_registry.py --dir /scratch/input/new-skills
    python update_registry.py --list                               # what came from user imports
    python update_registry.py --rebuild

    # the only way to take a skill out of routing:
    python update_registry.py --supersede skill-old-name --proof /scratch/work/proof.json
    python update_registry.py --unsupersede skill-old-name

    # escape hatch, deliberately awkward:
    python update_registry.py --remove skill-x --force

Rules this file enforces:
  - a seed entry (an installed skill or a curated capability) is never deleted,
    only superseded, so the knowledge stays auditable;
  - --supersede refuses to run without a bench proof whose verdict is REPLACE;
  - nothing is removed on a hunch, because a registry that loses good skills
    silently is worse than no registry at all.
"""
import argparse, datetime, json, pathlib, re, subprocess, sys, tempfile, zipfile

HERE = pathlib.Path(__file__).resolve()
ROOT = next((p for p in (HERE.parent.parent, pathlib.Path.cwd())
             if (p / "registry" / "seed.json").exists()), None)
STOP = set("""a an the of for and or to in on with by from into over under as at is are be been
your you their its it this that these those how what when where which who why do does make
use used this skill whenever user wants""".split())


def triggers(*texts):
    out, seen = [], set()
    for t in texts:
        for tok in re.split(r"[^a-z0-9]+", str(t).lower()):
            if len(tok) < 3 or tok in STOP or tok in seen:
                continue
            seen.add(tok)
            out.append(tok)
    return out[:12]


def frontmatter(text):
    """YAML-lite: flat keys plus block scalars (| and >), which real skill
    frontmatters use for long descriptions."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}
    meta, i = {}, 1
    while i < end:
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", lines[i])
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in ("|", "|-", "|+", ">", ">-", ">+"):
            i += 1
            buf = []
            while i < end and (lines[i][:1] in (" ", "\t") or lines[i].strip() == ""):
                buf.append(lines[i].strip())
                i += 1
            meta[key] = (" ".join(x for x in buf if x) if val.startswith(">")
                         else "\n".join(buf).strip())
            continue
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        meta[key] = val
        i += 1
    return meta


def entry_from_skill(skill_dir, origin, status="reference"):
    md = skill_dir / "SKILL.md"
    meta = frontmatter(md.read_text(encoding="utf-8", errors="replace"))
    name = meta.get("name") or skill_dir.name
    desc = meta.get("description", "").strip()
    if not desc:
        return None
    return {
        "id": "skill-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
        "type": "skill", "name": name, "title": desc.split(".")[0][:90],
        "capability": desc, "triggers": triggers(name, desc),
        "output": "loaded skill workflow", "source": origin, "status": status,
        "group": "skills",
    }


def collect(path, origin, status="reference"):
    """Find skills in a folder. Returns (found, skipped) where skipped explains
    every SKILL.md that was deliberately not indexed."""
    path = pathlib.Path(path)
    found, skipped = [], []
    if not path.is_dir():
        return found, skipped
    for md in sorted(path.rglob("SKILL.md")):
        d = md.parent
        name = frontmatter(md.read_text(encoding="utf-8", errors="replace")).get("name", d.name)
        # a SKILL.md that contains other skills (anywhere below it) is a bundle
        # wrapper, not a skill - indexing it would make it compete with its own
        # children for the same trigger words
        if any(other != md for other in d.rglob("SKILL.md")):
            skipped.append({"path": str(d), "why": "bundle wrapper: contains other skills"})
            continue
        if "template" in d.name.lower() or "template" in str(name).lower():
            skipped.append({"path": str(d), "why": "template, not a usable skill"})
            continue
        e = entry_from_skill(d, origin, status)
        if e is None:
            skipped.append({"path": str(d), "why": "no description in frontmatter"})
            continue
        found.append(e)
    return found, skipped


def jread(f, default):
    f = pathlib.Path(f)
    if not f.exists():
        return default
    return json.loads(f.read_text(encoding="utf-8"))


def rebuild(root):
    subprocess.run([sys.executable, str(HERE.parent / "build_registry.py"), "--root", str(root)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip")
    ap.add_argument("--dir")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--remove")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--supersede")
    ap.add_argument("--proof")
    ap.add_argument("--unsupersede")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--status", default="reference",
                    choices=["reference", "ready"],
                    help="reference = indexed only, files not installed; ready = installed")
    ap.add_argument("--on-collision", default="skip", choices=["skip", "update"],
                    help="what to do when an imported id already exists")
    ap.add_argument("--root")
    a = ap.parse_args()

    root = pathlib.Path(a.root).resolve() if a.root else ROOT
    if root is None:
        sys.exit("could not find registry/seed.json - run this from the skill folder")
    reg = root / "registry"
    extra = jread(reg / "extra.json", {"entries": []})
    sup = jread(reg / "superseded.json", {})

    if a.list:
        for e in extra["entries"]:
            print("%-42s %s" % (e["id"], e["capability"][:66]))
        if sup:
            print("\nsuperseded:")
            for k, v in sup.items():
                print("  %-40s -> %s (%s)" % (k, v.get("by"), v.get("date")))
        print("\n%d added entries, %d superseded" % (len(extra["entries"]), len(sup)))
        return

    if a.rebuild:
        rebuild(root)
        return

    # ---------- supersede: the only sanctioned removal path ----------
    if a.supersede:
        target = a.supersede
        if not a.proof:
            sys.exit("supersede needs --proof <bench.json>. Run bench.py compare first; "
                     "nothing is replaced on a hunch.")
        proof = jread(a.proof, None)
        if proof is None:
            sys.exit("no such proof file: %s" % a.proof)
        if proof.get("verdict") != "REPLACE":
            sys.exit("proof verdict is %r, not REPLACE - the new skill is not demonstrably better, "
                     "so %s stays in routing." % (proof.get("verdict"), target))
        if proof.get("loser") != target:
            sys.exit("proof is about %r, not %r - refusing to act on the wrong file"
                     % (proof.get("loser"), target))
        winner = proof.get("winner")
        known = {e["id"] for e in extra["entries"]} | {e["id"] for e in jread(reg / "seed.json", {"entries": []})["entries"]}
        # a bench proof names the skill by its folder; the registry keys it by id
        if winner not in known and ("skill-" + str(winner)) in known:
            winner = "skill-" + winner
        if target not in known and ("skill-" + target) in known:
            target = "skill-" + target
        if winner not in known:
            sys.exit("the winning skill %r is not in the registry - import it with --zip or --dir first" % winner)
        if proof.get("margin", 0) < 10:
            sys.exit("proof margin is %s, below the 10-point bar" % proof.get("margin"))
        sup[target] = {"by": winner, "date": datetime.date.today().isoformat(),
                       "margin": proof.get("margin"), "proof": str(a.proof),
                       "why": proof.get("why", "")}
        (reg / "superseded.json").write_text(json.dumps(sup, ensure_ascii=False, indent=1), encoding="utf-8")
        rebuild(root)
        print(json.dumps({"superseded": target, "by": winner, "margin": proof.get("margin"),
                          "note": "kept in the registry as superseded; it no longer routes"}, indent=1))
        return

    if a.unsupersede:
        if a.unsupersede in sup:
            sup.pop(a.unsupersede)
            (reg / "superseded.json").write_text(json.dumps(sup, ensure_ascii=False, indent=1), encoding="utf-8")
            rebuild(root)
            print("restored %s to routing" % a.unsupersede)
        else:
            print("%s was not superseded" % a.unsupersede)
        return

    # ---------- remove: escape hatch only ----------
    if a.remove:
        seed_ids = {e["id"] for e in jread(reg / "seed.json", {"entries": []})["entries"]}
        if a.remove in seed_ids:
            sys.exit("%s is a seed entry - it cannot be deleted. Use --supersede with a REPLACE "
                     "proof so the record of what replaced it survives." % a.remove)
        if not a.force:
            sys.exit("--remove needs --force. If a better skill exists, use --supersede instead.")
        before = len(extra["entries"])
        extra["entries"] = [e for e in extra["entries"] if e["id"] != a.remove]
        (reg / "extra.json").write_text(json.dumps(extra, ensure_ascii=False, indent=1), encoding="utf-8")
        rebuild(root)
        print("removed %d entry" % (before - len(extra["entries"])))
        return

    # ---------- ingest ----------
    found, skipped = [], []
    if a.zip:
        z = pathlib.Path(a.zip).expanduser()
        if not z.exists():
            sys.exit("no such zip: %s" % z)
        tmp = pathlib.Path(tempfile.mkdtemp())
        with zipfile.ZipFile(z) as zf:
            zf.extractall(tmp)
        f, sk = collect(tmp, "user zip: " + z.name, a.status)
        found += f
        skipped += sk
    if a.dir:
        f, sk = collect(pathlib.Path(a.dir).expanduser(),
                        "user folder: " + pathlib.Path(a.dir).name, a.status)
        found += f
        skipped += sk

    if not found and not skipped:
        sys.exit("nothing ingested - no SKILL.md found in the supplied zip or folder")

    seed_ids = {e["id"] for e in jread(reg / "seed.json", {"entries": []})["entries"]}
    by_id = {e["id"]: e for e in extra["entries"]}
    added = updated = 0
    collisions = []
    for e in found:
        if e["id"] in by_id or e["id"] in seed_ids:
            if a.on_collision == "update" and e["id"] in by_id:
                by_id[e["id"]].update({k: e[k] for k in ("capability", "title", "triggers", "source", "status")})
                updated += 1
                continue
            # never overwrite curated knowledge with an import
            collisions.append({"id": e["id"], "name": e["name"],
                               "kept": "existing entry", "incoming_source": e["source"]})
            continue
        by_id[e["id"]] = e
        added += 1

    extra["entries"] = list(by_id.values())
    (reg / "extra.json").write_text(json.dumps(extra, ensure_ascii=False, indent=1), encoding="utf-8")
    rebuild(root)
    print(json.dumps({"added": added, "updated": updated,
                      "collisions_skipped": collisions, "skipped": skipped,
                      "extra_total": len(extra["entries"]),
                      "status": a.status}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
