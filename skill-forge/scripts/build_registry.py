#!/usr/bin/env python3
"""Rebuild registry/registry.json and registry/registry.md from the curated seed
plus anything the user has added later (registry/extra.json).

Usage:
    python build_registry.py                # rebuild in place
    python build_registry.py --root <dir>   # build for a skill folder elsewhere

The seed is the curated base: every installed skill, the 500-command prompt
library, the concrete actions of every connected integration, and the platform's
own capabilities. extra.json holds entries added from skills the user supplies
later (see update_registry.py), so a rebuild never loses them.
"""
import argparse, json, pathlib, re, sys


def find_root(explicit=None):
    if explicit:
        return pathlib.Path(explicit).resolve()
    here = pathlib.Path(__file__).resolve()
    for cand in (here.parent.parent, pathlib.Path.cwd()):
        if (cand / "registry" / "seed.json").exists():
            return cand
    sys.exit("could not locate the skill root (no registry/seed.json found)")


def dedupe(entries):
    seen, out = set(), []
    for e in entries:
        key = e.get("id") or (e.get("type", "") + "::" + e.get("name", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root")
    a = ap.parse_args()

    root = find_root(a.root)
    reg = root / "registry"
    seed = json.loads((reg / "seed.json").read_text(encoding="utf-8"))
    extra = []
    xf = reg / "extra.json"
    if xf.exists():
        try:
            extra = json.loads(xf.read_text(encoding="utf-8")).get("entries", [])
        except json.JSONDecodeError:
            sys.exit("registry/extra.json is not valid JSON - fix it before rebuilding")

    superseded = {}
    sf = reg / "superseded.json"
    if sf.exists():
        try:
            superseded = json.loads(sf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            sys.exit("registry/superseded.json is not valid JSON - fix it before rebuilding")

    all_entries = dedupe(seed.get("entries", []) + extra)
    # a superseded entry stays on record but stops routing: the skill that beat it
    # in the bench has to be the one that answers, or the replacement was pointless
    entries = [e for e in all_entries if e["id"] not in superseded]
    counts = {}
    for e in entries:
        counts[e["type"]] = counts.get(e["type"], 0) + 1

    out = {
        "version": seed.get("version", 1),
        "total": len(entries),
        "counts": counts,
        "superseded": superseded,
        "note": "Built by scripts/build_registry.py. Do not hand-edit; edit seed.json or extra.json.",
        "entries": entries,
    }
    (reg / "registry.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # human/grep friendly index
    lines = ["# Skill Forge registry", "",
             "%d routing entries: %s" % (len(entries), ", ".join("%d %s" % (v, k) for k, v in sorted(counts.items()))),
             ""]
    if superseded:
        lines.append("%d superseded (on record, no longer routing): %s"
                     % (len(superseded), ", ".join(sorted(superseded))))
        lines.append("")
    lines += ["Grep this file (`rg -i '<need>' registry/registry.md`) or run `scripts/route.py`.",
              "One entry per line: `id | type | name - capability`.", ""]
    by_group = {}
    for e in entries:
        by_group.setdefault(e.get("group", e["type"]), []).append(e)
    for group in sorted(by_group):
        lines.append("## " + group)
        lines.append("")
        for e in sorted(by_group[group], key=lambda x: x["name"].lower()):
            lines.append("- `%s` | %s | %s - %s" % (e["id"], e["type"], e["name"], e["capability"]))
        lines.append("")
    if superseded:
        lines.append("## superseded")
        lines.append("")
        for k in sorted(superseded):
            v = superseded[k]
            lines.append("- `%s` -> replaced by `%s` on %s (margin %s)"
                         % (k, v.get("by"), v.get("date"), v.get("margin")))
        lines.append("")
    (reg / "registry.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"total": len(entries), "counts": counts,
                      "written": [str(reg / "registry.json"), str(reg / "registry.md")]}, indent=1))
    if len(entries) < 800:
        print("WARNING: registry is below the 800-entry floor - add seed or extra entries.", file=sys.stderr)


if __name__ == "__main__":
    main()
