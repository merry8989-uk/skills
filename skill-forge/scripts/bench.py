#!/usr/bin/env python3
"""Auto-build, step 2: score a skill and decide whether it may replace one.

Usage:
    python scripts/bench.py score /scratch/work/forged/gst-checker
    python scripts/bench.py score <dir> --judgement /scratch/work/j.json
    python scripts/bench.py compare <new-dir> <old-dir> --new-judgement a.json \
        --old-judgement b.json --out /scratch/work/proof.json

Scoring is 45 points of measured structure plus 55 points of judged quality.
The structure half is computed from the files, so it cannot be talked up. The
judgement half is five questions scored 0-5 in a JSON file:

    {"coverage": 4, "precision": 5, "triggers": 4, "boundaries": 3, "gates": 5,
     "notes": "why these numbers"}

    coverage     does it do the whole job end to end, or a slice of it
    precision    is the output contract literal enough to reproduce
    triggers     will it fire for the phrasings a real user types
    boundaries   does it refuse what it cannot do, and name its neighbours
    gates        are the quality gates checkable yes/no against the deliverable

Nothing is replaced on a hunch. REPLACE needs a margin of 10 points, a
judgement file for BOTH skills, and no regression on coverage or precision.
Otherwise the old skill stays and the new one either sits beside it or is
rejected outright.
"""
import argparse, datetime, json, pathlib, re, sys

JUDGE_KEYS = ["coverage", "precision", "triggers", "boundaries", "gates"]
WEIGHT = 2.2  # 5 keys x 5 points x 2.2 = 55


def sections(text):
    body = text.split("\n---", 1)[-1] if text.startswith("---") else text
    out, cur = {}, "_head"
    for line in body.splitlines():
        m = re.match(r"^##+\s+(.*)$", line)
        if m:
            cur = m.group(1).strip().lower()
            out.setdefault(cur, [])
        else:
            out.setdefault(cur, []).append(line)
    return out


def count_items(lines):
    n = 0
    for line in lines:
        if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+\S", line):
            n += 1
    return n


def pick(sec, *keys):
    for k in sec:
        if any(w in k for w in keys):
            return sec[k]
    return []


def structure(d):
    d = pathlib.Path(d)
    if not (d / "SKILL.md").exists():
        sys.exit("bench: no SKILL.md in %s" % d)
    md = (d / "SKILL.md").read_text(encoding="utf-8")
    sec = sections(md)
    desc = ""
    m = re.search(r"^description:\s*(.*)$", md.split("\n---")[0], re.M)
    if m:
        desc = m.group(1).strip().strip('"')

    steps = count_items(pick(sec, "workflow", "step", "process"))
    outs = count_items(pick(sec, "output", "deliverable", "format"))
    gates = count_items(pick(sec, "quality", "gate", "checklist", "before you deliver"))
    scripts = 1 if any((d / "scripts").glob("*.py")) else 0
    refs = 1 if any(p for p in (d / "references").glob("*") if p.is_file()) else 0
    trig = bool(re.search(r"\b(use this|use whenever|whenever the user|when the user|use when)\b", desc.lower()))
    desc_pts = (3 if trig else 0) + (2 if 300 <= len(desc) <= 1024 else 0)

    parts = {
        "workflow_steps": (min(steps, 5) * 2, 10, steps),
        "output_contract": (min(outs, 5) * 2, 10, outs),
        "quality_gates": (min(gates, 5) * 2, 10, gates),
        "has_scripts": (scripts * 5, 5, scripts),
        "has_references": (refs * 5, 5, refs),
        "description": (desc_pts, 5, len(desc)),
    }
    return parts, sum(v[0] for v in parts.values())


def judge(path):
    if not path:
        return None
    j = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    for k in JUDGE_KEYS:
        if k not in j:
            sys.exit("judgement file is missing '%s'" % k)
        if not isinstance(j[k], (int, float)) or not 0 <= j[k] <= 5:
            sys.exit("judgement '%s' must be a number 0-5" % k)
    return j


def total(parts_sum, j):
    return round(parts_sum + (sum(j[k] for k in JUDGE_KEYS) * WEIGHT if j else 0))


def report(d, j, as_json=False):
    parts, ssum = structure(d)
    tot = total(ssum, j)
    if as_json:
        return {"skill": pathlib.Path(d).name, "structure": ssum, "judgement": round(sum(j[k] for k in JUDGE_KEYS) * WEIGHT) if j else 0,
                "total": tot, "parts": {k: {"points": v[0], "max": v[1], "raw": v[2]} for k, v in parts.items()}}
    print("skill     : %s" % pathlib.Path(d).name)
    for k, (p, mx, raw) in parts.items():
        print("  %-16s %2d/%-2d  (measured: %s)" % (k, p, mx, raw))
    print("  %-16s %2d/45" % ("structure", ssum))
    if j:
        for k in JUDGE_KEYS:
            print("  %-16s %4.1f/11  (judged %d/5)" % (k, j[k] * WEIGHT, j[k]))
    else:
        print("  judgement      0/55  (no judgement file - structure only)")
    print("  %-16s %3d/100" % ("TOTAL", tot))
    return {"skill": pathlib.Path(d).name, "structure": ssum, "total": tot}


def compare(new_dir, old_dir, nj, oj, out):
    nparts, nsum = structure(new_dir)
    oparts, osum = structure(old_dir)
    nt, ot = total(nsum, nj), total(osum, oj)
    margin = nt - ot

    if nj is None or oj is None:
        verdict = "KEEP_BOTH"
        why = ("no judgement file for %s - superiority cannot be proven, so nothing is replaced"
               % ("the new skill" if nj is None else "the incumbent"))
    elif nt < 60:
        verdict = "REJECT_NEW"
        why = "the new skill scores %d/100 - below the 60 admission floor" % nt
    elif margin >= 10 and nj["coverage"] >= oj["coverage"] and nj["precision"] >= oj["precision"]:
        verdict = "REPLACE"
        why = ("+%d points and no regression on coverage or precision - the new skill is "
               "demonstrably better at the same job" % margin)
    elif margin > 0:
        verdict = "KEEP_BOTH"
        why = ("only +%d points - better in places, not better overall. Register the new skill as a "
               "scoped variant and let routing decide per request" % margin)
    else:
        verdict = "REJECT_NEW"
        why = "the new skill scores %d against the incumbent's %d - do not add it" % (nt, ot)

    proof = {
        "verdict": verdict,
        "why": why,
        "winner": pathlib.Path(new_dir).name,
        "loser": pathlib.Path(old_dir).name,
        "margin": margin,
        "scores": {
            "new": {"structure": nsum, "total": nt, "judgement": nj},
            "old": {"structure": osum, "total": ot, "judgement": oj},
        },
        "date": datetime.date.today().isoformat(),
    }
    if out:
        pathlib.Path(out).write_text(json.dumps(proof, ensure_ascii=False, indent=1), encoding="utf-8")
    return proof


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score")
    s.add_argument("dir")
    s.add_argument("--judgement")
    s.add_argument("--json", action="store_true")
    c = sub.add_parser("compare")
    c.add_argument("new")
    c.add_argument("old")
    c.add_argument("--new-judgement")
    c.add_argument("--old-judgement")
    c.add_argument("--out")
    c.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.cmd == "score":
        rep = report(a.dir, judge(a.judgement), a.json)
        if a.json:
            print(json.dumps(rep, indent=1))
        return

    nj, oj = judge(a.new_judgement), judge(a.old_judgement)
    print("--- new ---")
    report(a.new, nj)
    print("--- incumbent ---")
    report(a.old, oj)
    proof = compare(a.new, a.old, nj, oj, a.out)
    if a.json:
        print(json.dumps(proof, ensure_ascii=False, indent=1))
    else:
        print("\nverdict : %s" % proof["verdict"])
        print("why     : %s" % proof["why"])
        print("margin  : %+d points (%d vs %d)" % (proof["margin"], proof["scores"]["new"]["total"],
                                                   proof["scores"]["old"]["total"]))
        if a.out:
            print("proof   : %s" % a.out)
        if proof["verdict"] == "REPLACE":
            print("\nnext    : python scripts/update_registry.py --supersede %s --proof %s"
                  % (proof["loser"], a.out or "<proof.json>"))
    sys.exit(0 if proof["verdict"] != "REJECT_NEW" else 4)


if __name__ == "__main__":
    main()
