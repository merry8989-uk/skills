#!/usr/bin/env python3
"""Hard gate for any skill folder before it is packaged or handed over.

Usage:
    python validate_skill.py /path/to/skill-folder
    python validate_skill.py /path/to/skill-folder --json
    python validate_skill.py /path/to/skill-folder --min 95

Exit 0 = pass, exit 1 = fail. Failures block packaging; warnings only cost score.
Nothing below --min (default 90) should ever be delivered.
"""
import argparse, json, pathlib, py_compile, re, sys

BANNED = ["TODO", "TBD", "FIXME", "lorem ipsum", "{{", "}}", "<placeholder", "XXX", "your-skill-here"]
REQUIRED_HINTS = {
    "workflow": r"^##+ .*(workflow|step|process|procedure|how it works|protocol|route)",
    "output": r"^##+ .*(output|deliverable|format|report structure|what you produce|what you deliver|hand over|handover)",
    "quality": r"^##+ .*(quality|checklist|gate|before you deliver|qa|validate)",
}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def parse_front(text):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, text
    body = "\n".join(lines[end + 1:])
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
    return meta, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min", type=int, default=90)
    a = ap.parse_args()

    d = pathlib.Path(a.path).resolve()
    fails, warns, passes = [], [], []

    skill_md = d / "SKILL.md"
    if not skill_md.exists():
        print(json.dumps({"ok": False, "fails": ["SKILL.md is missing"], "score": 0}, indent=1))
        sys.exit(1)
    text = skill_md.read_text(encoding="utf-8")
    meta, body = parse_front(text)

    if meta is None:
        fails.append("SKILL.md has no parseable YAML frontmatter")
        meta = {}
    else:
        passes.append("frontmatter parses")

    name = meta.get("name", "")
    if not name:
        fails.append("frontmatter has no name")
    elif not NAME_RE.match(name) or len(name) > 64:
        fails.append("name is not kebab-case, lowercase, 1-64 chars: %r" % name)
    else:
        passes.append("name is valid kebab-case")
        if name != d.name:
            warns.append("folder name (%s) differs from frontmatter name (%s)" % (d.name, name))

    desc = meta.get("description", "")
    if not desc:
        fails.append("frontmatter has no description")
    elif len(desc) > 1024:
        fails.append("description is %d chars, over the 1024 limit" % len(desc))
    else:
        passes.append("description within length limit (%d chars)" % len(desc))
        if len(desc) < 80:
            warns.append("description is short (%d chars) - it may not trigger reliably" % len(desc))
        if not re.search(r"\b(use this|use whenever|whenever the user|when the user|use when)\b", desc.lower()):
            warns.append("description has no explicit triggering clause ('Use this skill whenever ...')")
        else:
            passes.append("description states when to trigger")

    n_lines = text.count("\n") + 1
    if n_lines > 500:
        warns.append("SKILL.md is %d lines - move detail into references/" % n_lines)
    else:
        passes.append("SKILL.md is %d lines" % n_lines)

    low = body.lower()
    for label, pat in REQUIRED_HINTS.items():
        if re.search(pat, low, re.M):
            passes.append("has a %s section" % label)
        else:
            warns.append("no obvious %s section" % label)

    for b in BANNED:
        if b.lower() in text.lower():
            fails.append("SKILL.md still contains the placeholder marker %r" % b)

    if "[cite:" in text:
        fails.append("SKILL.md contains a [cite:...] marker - files cannot render those")

    # every bundled file named in the body must exist
    named = set(re.findall(r"(?:references|scripts|assets|registry)/[A-Za-z0-9_.\-/]+", body))
    for rel in sorted(named):
        rel_clean = rel.rstrip(".,);:`")
        if not (d / rel_clean).exists():
            fails.append("SKILL.md points at a file that does not exist: " + rel_clean)
    if named and not fails:
        passes.append("all %d referenced files exist" % len(named))

    # bundled files that nothing points at are dead weight
    for folder in ("references", "scripts", "assets", "registry"):
        d2 = d / folder
        if not d2.is_dir():
            continue
        for f in sorted(d2.rglob("*")):
            if f.is_dir() or f.name == "SKILL.md":
                continue
            if "__pycache__" in f.parts or f.suffix == ".pyc":
                continue
            rel = str(f.relative_to(d))
            if rel not in body:
                warns.append("bundled file is never mentioned in SKILL.md: " + rel)

    # python scripts must at least compile
    for py in sorted(d.rglob("*.py")):
        try:
            py_compile.compile(str(py), doraise=True, cfile=str(py) + ".pyc.tmp")
        except py_compile.PyCompileError as e:
            fails.append("%s does not compile: %s" % (py.relative_to(d), str(e).splitlines()[-1]))
        finally:
            tmp = pathlib.Path(str(py) + ".pyc.tmp")
            if tmp.exists():
                tmp.unlink()
    if any(d.rglob("*.py")) and not any("does not compile" in f for f in fails):
        passes.append("python scripts compile")

    for junk in d.rglob("__pycache__"):
        warns.append("remove %s before packaging" % junk.relative_to(d))
    for junk in list(d.rglob("*.pyc")) + list(d.rglob(".DS_Store")):
        warns.append("remove %s before packaging" % junk.relative_to(d))

    score = max(0, 100 - 25 * len(fails) - 4 * len(warns))
    ok = not fails and score >= a.min
    out = {"ok": ok, "skill": d.name, "score": score, "min": a.min,
           "fails": fails, "warnings": warns, "passes": passes}
    if a.json:
        print(json.dumps(out, indent=1))
    else:
        print("skill   : %s" % d.name)
        print("score   : %d/100 (need %d)" % (score, a.min))
        print("verdict : %s" % ("PASS" if ok else "FAIL"))
        for p in passes:
            print("  ok   - " + p)
        for w in warns:
            print("  warn - " + w)
        for f in fails:
            print("  FAIL - " + f)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
