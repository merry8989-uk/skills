#!/usr/bin/env python3
"""Auto-build, step 1: turn a need into a pre-filled spec skeleton.

Usage:
    python scripts/scaffold_spec.py "nurse shift handover SBAR banao"
    python scripts/scaffold_spec.py "<need>" --out /scratch/work/my-spec.json
    python scripts/scaffold_spec.py "<need>" --print      # JSON to stdout, no file

What it fills for you, from the registry: the name, a description draft, the
capability line, the trigger list, and the `dont_use_when` boundaries taken from
the runners-up so the new skill cannot steal their work.

What it deliberately leaves empty: workflow, output_contract, quality_gates.
Those are the judgement calls - if a script could invent them, the skill would be
worthless. `forge_skill.py` refuses a spec with them missing, so an unfilled
skeleton can never become a delivered skill.
"""
import argparse, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
from route import load, rank  # noqa: E402


def slug(x, n=40):
    return re.sub(r"[^a-z0-9]+", "-", x.lower()).strip("-")[:n].strip("-")


def build(need, top=6, root=None):
    reg, _ = load(root)
    r = rank(reg, need, top)
    cands = r["candidates"]
    best = cands[0] if cands else None
    arche = next((c for c in cands if c["type"] == "archetype"), None)
    anchor = arche or best

    if anchor and anchor["type"] == "archetype":
        prof, _, flow = anchor["name"].partition(": ")
        name = slug(prof, 24) + "-" + slug(flow, 34)
        title = flow.strip()[:1].upper() + flow.strip()[1:] + " (" + prof + ")"
        capability = (flow.strip()[:1].upper() + flow.strip()[1:] + " for a " + prof.lower()
                      + ". The user's own phrasing of this job: \"" + need.strip().rstrip(".") + "\".")
    else:
        name = slug(need, 56)
        title = need.strip()[:1].upper() + need.strip()[1:].rstrip(".")
        capability = need.strip().rstrip(".") + "."

    description = ("Use this skill whenever the user needs " +
                   (anchor["capability"].split(" - ")[0].lower() if anchor else need.lower()) +
                   " - for example \"" + need.strip() + "\". It runs the same workflow every time, "
                   "so two runs on comparable input produce comparable output, and it says what it "
                   "cannot do instead of guessing.")

    dont = []
    for c in cands[1:5]:
        if c["type"] == "archetype":
            continue
        dont.append("%s is better handled by '%s' (%s)" % (c["name"], c["id"], c["type"]))

    spec = {
        "name": name,
        "title": title,
        "description": description,
        "capability": capability,
        "outputs": "",
        "use_when": [need.strip()] + ([anchor["name"]] if anchor else []),
        "dont_use_when": dont,
        "inputs": [],
        "workflow": [],
        "output_contract": [],
        "quality_gates": [],
        "anti_patterns": [],
        "notes": [],
        "allowed_tools": "bash",
        "_routing": {
            "verdict": r["verdict"],
            "why": r["why"],
            "registry_size": r["registry_size"],
            "candidates": [{"id": c["id"], "type": c["type"], "name": c["name"],
                            "confidence": c["confidence"]} for c in cands],
        },
        "_gaps": [
            "description: replace the drafted wording with the user's own phrases - that is what makes it trigger",
            "outputs: one line naming the artefact (a .docx, a table, a PDF)",
            "inputs: each input, whether it is needed, and how to obtain it",
            "workflow: 3-7 steps, each with 'do' and 'why'; name a tool when a script or skill does the step",
            "output_contract: the literal shape of the deliverable, line by line",
            "quality_gates: at least 3 statements a reader can check yes/no against the output",
            "anti_patterns: the specific wrong turns this job invites",
        ],
    }
    return spec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("need", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--print", dest="to_stdout", action="store_true")
    ap.add_argument("--root")
    a = ap.parse_args()

    need = " ".join(a.need)
    spec = build(need, root=a.root)
    body = json.dumps(spec, ensure_ascii=False, indent=1)

    if a.to_stdout:
        print(body)
        return
    out = pathlib.Path(a.out or ("/scratch/work/%s-spec.json" % spec["name"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    print(json.dumps({
        "spec": str(out),
        "name": spec["name"],
        "routed_as": spec["_routing"]["verdict"],
        "gaps_to_fill": len(spec["_gaps"]),
        "next": "fill workflow / output_contract / quality_gates in %s, then run forge_skill.py" % out,
    }, indent=1))


if __name__ == "__main__":
    main()
