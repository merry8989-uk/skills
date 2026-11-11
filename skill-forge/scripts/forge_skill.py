#!/usr/bin/env python3
"""Forge a new skill from a filled spec. Deterministic scaffolding, no guessing.

Usage:
    python forge_skill.py spec.json --out /scratch/work/new-skills
    python forge_skill.py spec.json --out . --force      # overwrite an existing folder

The spec is the part only a human-or-model judgement can supply (what the skill
does, the steps, the output shape). Everything structural - frontmatter order,
section order, file layout, length checks - is done here so every forged skill
looks and behaves the same way. See references/forge-blueprint.md for a filled
example.

Required spec keys: name, description, capability, workflow, output_contract,
quality_gates. Everything else is optional and simply omitted when absent.
"""
import argparse, json, pathlib, re, sys

REQUIRED = ["name", "description", "capability", "workflow", "output_contract", "quality_gates"]
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BANNED = ["TODO", "TBD", "FIXME", "lorem ipsum", "{{", "}}", "<placeholder", "XXX"]


def die(msg):
    print("forge: " + msg, file=sys.stderr)
    sys.exit(2)


def check_spec(spec):
    missing = [k for k in REQUIRED if not spec.get(k)]
    if missing:
        die("spec is missing required keys: " + ", ".join(missing))
    name = spec["name"]
    if not NAME_RE.match(name) or len(name) > 64:
        die("name must be kebab-case, lowercase, 1-64 chars: " + name)
    d = spec["description"]
    if len(d) > 1024:
        die("description is %d chars; the hard limit is 1024" % len(d))
    if len(d) < 80:
        die("description is too thin (%d chars). Say what the skill does AND the user phrasings that should trigger it." % len(d))
    if not re.search(r"\b(use this|use whenever|whenever the user|when the user)\b", d.lower()):
        die("description has no triggering clause. Add one, e.g. 'Use this skill whenever the user ...'")
    if len(spec["workflow"]) < 3:
        die("workflow needs at least 3 steps - a one-step skill is just a prompt")
    if len(spec["output_contract"]) < 2:
        die("output_contract needs at least 2 entries")
    if len(spec["quality_gates"]) < 3:
        die("quality_gates needs at least 3 checks")
    # check the values, not the serialised JSON - json.dumps puts braces next to
    # each other and would trip the placeholder check on any nested object
    def strings(o):
        if isinstance(o, str):
            yield o
        elif isinstance(o, dict):
            for v in o.values():
                yield from strings(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                yield from strings(v)

    for val in strings(spec):
        for b in BANNED:
            if b.lower() in val.lower():
                die("spec still contains a placeholder marker %r in: %s"
                    % (b, val[:70].replace("\n", " ")))


def render(spec):
    L = []
    L.append("---")
    L.append("name: " + spec["name"])
    L.append("description: " + json.dumps(spec["description"], ensure_ascii=False))
    if spec.get("allowed_tools"):
        L.append("allowed-tools: " + spec["allowed_tools"])
    if spec.get("metadata"):
        L.append("metadata:")
        for k, v in spec["metadata"].items():
            L.append("  %s: %s" % (k, json.dumps(v, ensure_ascii=False)))
    L.append("---")
    L.append("")
    L.append("# " + spec.get("title", spec["name"].replace("-", " ").title()))
    L.append("")
    L.append("## What this does")
    L.append("")
    L.append(spec["capability"].strip())
    L.append("")
    if spec.get("outputs"):
        L.append("**Deliverable:** " + spec["outputs"].strip())
        L.append("")

    if spec.get("use_when"):
        L.append("## When this applies")
        L.append("")
        for u in spec["use_when"]:
            L.append("- " + u)
        L.append("")
    if spec.get("dont_use_when"):
        L.append("## When this is the wrong skill")
        L.append("")
        L.append("Hand these back to the named skill or to plain tools instead - using this one "
                 "for them produces worse output than not loading it at all.")
        L.append("")
        for u in spec["dont_use_when"]:
            L.append("- " + u)
        L.append("")

    if spec.get("inputs"):
        L.append("## Inputs")
        L.append("")
        L.append("| Input | Needed | How to get it |")
        L.append("|---|---|---|")
        for i in spec["inputs"]:
            if isinstance(i, str):
                L.append("| %s | ask if missing | ask one question |" % i)
            else:
                L.append("| %s | %s | %s |" % (i.get("name", ""), i.get("needed", "yes"),
                                               i.get("how", "ask one question")))
        L.append("")
        L.append("Ask for every missing *needed* input in one message, then start. Do not "
                 "invent a value to avoid asking - a wrong input is discovered late and costs "
                 "the whole run.")
        L.append("")

    L.append("## Workflow")
    L.append("")
    L.append("Follow the steps in order. Each one names why it exists, because the reason "
             "is what lets you adapt when the input is unusual.")
    L.append("")
    for n, w in enumerate(spec["workflow"], 1):
        if isinstance(w, str):
            L.append("%d. %s" % (n, w))
            continue
        head = "**%s**" % w.get("do", "").strip()
        if w.get("tool"):
            head += " (`%s`)" % w["tool"]
        L.append("%d. %s" % (n, head))
        if w.get("why"):
            L.append("   Why: " + w["why"].strip())
        if w.get("detail"):
            for line in str(w["detail"]).strip().splitlines():
                L.append("   " + line.strip())
    L.append("")

    L.append("## Output contract")
    L.append("")
    L.append("Produce exactly this shape. A reader should be able to act on it without asking a follow-up question.")
    L.append("")
    for o in spec["output_contract"]:
        L.append("- " + o)
    L.append("")

    L.append("## Quality gates")
    L.append("")
    L.append("Check every line before delivering. If one fails, fix it and re-check; do not ship with a known miss.")
    L.append("")
    for g in spec["quality_gates"]:
        L.append("- [ ] " + g)
    L.append("")

    if spec.get("anti_patterns"):
        L.append("## Anti-patterns")
        L.append("")
        for x in spec["anti_patterns"]:
            L.append("- " + x)
        L.append("")

    if spec.get("notes"):
        L.append("## Notes")
        L.append("")
        for x in spec["notes"]:
            L.append("- " + x)
        L.append("")

    refs = list(spec.get("references") or [])
    scr = list(spec.get("scripts") or [])
    # any bundled file that is not listed yet still has to be named in the body,
    # otherwise it ships as an orphan nobody knows to read
    listed = {r.get("path") for r in refs} | {x.get("path") for x in scr}
    for f in spec.get("files", []):
        rel = f["path"].lstrip("/")
        if rel in listed:
            continue
        item = {"path": rel, "purpose": f.get("purpose") or "bundled with this skill"}
        (scr if rel.startswith("scripts/") else refs).append(item)
        listed.add(rel)
    if refs or scr:
        L.append("## Bundled files")
        L.append("")
        L.append("Read a reference only when the workflow step that needs it comes up - "
                 "loading everything up front wastes context on the parts this run never touches.")
        L.append("")
        for r in refs:
            L.append("- `%s` - %s" % (r.get("path", ""), r.get("purpose", "")))
        for s in scr:
            L.append("- `%s` - %s (run it, do not read it)" % (s.get("path", ""), s.get("purpose", "")))
        L.append("")

    return "\n".join(L).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", default="/scratch/work")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    spec = json.loads(pathlib.Path(a.spec).read_text(encoding="utf-8"))
    check_spec(spec)

    body = render(spec)
    lines = body.count("\n")
    if lines > 500:
        print("forge: warning - SKILL.md is %d lines; move detail into references/" % lines, file=sys.stderr)

    dest = pathlib.Path(a.out).resolve() / spec["name"]
    if dest.exists() and not a.force:
        die("%s already exists - pass --force to overwrite" % dest)
    (dest / "references").mkdir(parents=True, exist_ok=True)
    (dest / "scripts").mkdir(parents=True, exist_ok=True)
    (dest / "SKILL.md").write_text(body, encoding="utf-8")

    written = ["SKILL.md"]
    for f in spec.get("files", []):
        rel = f["path"].lstrip("/")
        if not rel.startswith(("references/", "scripts/", "assets/", "registry/")):
            die("bundled file must live under references/, scripts/, assets/ or registry/: " + rel)
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f["content"], encoding="utf-8")
        written.append(rel)

    # drop the empty dirs we made if nothing landed in them
    for d in ("references", "scripts"):
        try:
            (dest / d).rmdir()
        except OSError:
            pass

    print(json.dumps({"skill": str(dest), "lines": lines, "files": written,
                      "next": "python scripts/validate_skill.py %s" % dest}, indent=1))


if __name__ == "__main__":
    main()
