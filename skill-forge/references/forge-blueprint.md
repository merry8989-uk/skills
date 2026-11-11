# Forge blueprint

The spec is the only part a model has to author. `scripts/forge_skill.py` turns
it into a complete, uniformly structured skill folder.

## Spec schema

| Key | Required | Type | What it is |
|---|---|---|---|
| `name` | yes | string | kebab-case, 1-64 chars, the job not the domain |
| `description` | yes | string | <= 1024 chars. What it does **and** when to trigger. Must contain a clause like "Use this skill whenever ..." |
| `title` | no | string | H1 of SKILL.md; defaults to the name title-cased |
| `capability` | yes | string | 1-3 sentences: the job, the boundary, what it refuses |
| `outputs` | no | string | The deliverable in one line |
| `use_when` | no | string[] | The phrasings and situations that should load it |
| `dont_use_when` | no | string[] | Name the skills this must not steal work from |
| `inputs` | no | object[] | `{name, needed, how}` - how to obtain each input |
| `workflow` | yes | object[] | 3-7 steps: `{do, why, tool?, detail?}`. A bare string is allowed but loses the "why" |
| `output_contract` | yes | string[] | The literal shape of the deliverable |
| `quality_gates` | yes | string[] | >= 3 checkable statements |
| `anti_patterns` | no | string[] | The specific wrong turns this skill tends to invite |
| `notes` | no | string[] | Constraints, house rules, edge cases |
| `references` | no | object[] | `{path, purpose}` - must match a file in `files` |
| `scripts` | no | object[] | `{path, purpose}` - same rule |
| `files` | no | object[] | `{path, content}` for every bundled file |
| `allowed_tools` | no | string | space-delimited tool names |
| `metadata` | no | object | extra frontmatter |

The renderer refuses a spec that is missing a required key, has a
non-kebab-case name, a description under 80 chars or over 1024, no triggering
clause, fewer than 3 workflow steps, fewer than 2 output-contract lines, fewer
than 3 quality gates, or any placeholder marker (`TODO`, `TBD`, `{{ }}`).

## Filled example

Need: *"call recordings se SOP documents banao"* - routed to `FORGE` because
nothing in the registry does transcription to procedure end to end.

```json
{
  "name": "call-recording-to-sop",
  "title": "Call recording to SOP",
  "description": "Use this skill whenever the user wants a repeatable procedure extracted from recorded calls, demos, support conversations or training sessions - 'call recording se SOP banao', 'turn these transcripts into a process doc', 'document how our team actually does this'. It reads the transcripts, finds the steps that repeat across calls, separates the intended process from the improvised one, and produces a numbered SOP with owners, decision points and failure modes, delivered as a .docx.",
  "capability": "Turn a set of call recordings or transcripts into one SOP that describes what the team actually does. The output is a procedure someone new can follow on their first day, not a summary of the calls. It refuses when fewer than three calls are supplied, because a procedure cannot be inferred from one instance.",
  "outputs": "A .docx SOP: purpose, scope, prerequisites, numbered steps with owner and system, decision points, known failure modes, and an appendix mapping each step to the call timestamps that evidenced it.",
  "use_when": [
    "the user supplies recordings or transcripts and asks for a process document",
    "a team wants its tribal knowledge written down before someone leaves",
    "an onboarding doc is needed for a role that only exists in people's heads"
  ],
  "dont_use_when": [
    "one call needs summarising - use /minutes or /meetingsummary instead",
    "the user wants a sales script, not a procedure - use scriptwriting",
    "the deliverable is a slide deck walkthrough - use sarvam-slides"
  ],
  "inputs": [
    {"name": "recordings or transcripts", "needed": "yes", "how": "the files the user attached; transcribe audio first if only audio was given"},
    {"name": "role and team", "needed": "yes", "how": "ask in the same message as any other gap"},
    {"name": "systems named in the calls", "needed": "no", "how": "infer from the transcripts, confirm in the appendix"}
  ],
  "workflow": [
    {
      "do": "Transcribe and segment every recording",
      "why": "Steps are only visible at the sentence level; a whole-call summary flattens exactly the detail an SOP needs.",
      "tool": "bash",
      "detail": "One file per call, speaker-labelled, with timestamps preserved. Keep them - the appendix cites them."
    },
    {
      "do": "Tag every action sentence across all calls",
      "why": "The SOP describes what repeats. A step that appears once is either a mistake or an edge case, and the two are treated differently.",
      "detail": "Columns: verb, object, system, actor, condition. Write it to a working CSV, not to prose."
    },
    {
      "do": "Cluster the tags into steps and rank by frequency",
      "why": "Frequency is the only evidence that a step is the process rather than one person's habit.",
      "tool": "bash",
      "detail": "A step seen in >= 60% of calls is core; 20-60% is conditional; below 20% goes to failure modes, not the main flow."
    },
    {
      "do": "Resolve contradictions between calls explicitly",
      "why": "Two people doing the same step differently is the single most valuable finding, and silently picking one destroys it.",
      "detail": "List each conflict with both versions and a recommended standard, and mark it for the user to confirm."
    },
    {
      "do": "Write the SOP in the output contract's order",
      "why": "A reader who follows the document top to bottom should never have to jump back.",
      "tool": "sarvam-docx"
    },
    {
      "do": "Run the quality gates, then deliver with the conflict list on top",
      "why": "The conflicts are what the user has to decide; burying them in an appendix means they get ignored."
    }
  ],
  "output_contract": [
    "Purpose - two sentences, who this is for and what it makes possible",
    "Scope - what this SOP covers and explicitly what it does not",
    "Prerequisites - access, tools, prior knowledge, in a table",
    "Numbered steps - each with: action, owner, system, expected result, and the call timestamps that evidenced it",
    "Decision points - each with the condition, both branches and who decides",
    "Known failure modes - what goes wrong, how it is spotted, what to do",
    "Open conflicts - the disagreements found between calls, with a recommendation each",
    "Appendix - a table mapping every step to its evidence timestamps"
  ],
  "quality_gates": [
    "Every numbered step cites at least one call timestamp in the appendix",
    "No step appears that was observed in only one call unless it is labelled 'observed once'",
    "Every system or tool named in a step is spelled as the team spells it, not as the transcript guessed",
    "The open-conflicts section is present even when empty, and says so",
    "The document names no person as the owner of a step unless the calls show them doing it",
    "Reading only the numbered steps is enough to perform the procedure"
  ],
  "anti_patterns": [
    "Summarising each call and stitching the summaries - that produces a meeting-notes pile, not a procedure",
    "Inventing a clean step order the calls never showed, because it reads better",
    "Softening a contradiction into 'may vary by case' - name both versions and ask",
    "Putting the conflicts in an appendix where they will be missed"
  ],
  "notes": [
    "Fewer than three calls: stop and say why, do not forge ahead",
    "Audio-only input: transcribe with the platform's speech tool before segmenting",
    "If the user's calls are in Hindi or Hinglish, keep the SOP in the language they asked for and quote the original phrasing in the appendix"
  ],
  "allowed_tools": "execute_code terminal",
  "files": [
    {
      "path": "references/tagging-schema.md",
      "purpose": "the exact tagging columns and sentence-splitting rules used in step 2",
      "content": "# Tagging schema\n\nOne row per action sentence, columns:\n\n| column | meaning | example |\n|---|---|---|\n| call | source file id | call-03 |\n| ts | timestamp | 00:12:44 |\n| actor | who acts | support agent |\n| verb | the action | verify |\n| object | what is acted on | GST number |\n| system | where | Zoho Books |\n| condition | when it applies | if amount > 50k |\n\nRules: one verb per row; split \"and then\" sentences; keep the speaker's wording\nin a `quote` column so the SOP can cite it verbatim.\n"
    },
    {
      "path": "scripts/cluster_steps.py",
      "purpose": "clusters tagged rows into core / conditional / edge steps by call frequency",
      "content": "#!/usr/bin/env python3\n\"\"\"Cluster tagged action rows into candidate SOP steps by frequency.\n\nUsage: python cluster_steps.py tags.csv --min-share 0.2\n\"\"\"\nimport argparse, collections, csv, sys\n\n\ndef main():\n    ap = argparse.ArgumentParser()\n    ap.add_argument(\"tags\")\n    ap.add_argument(\"--min-share\", type=float, default=0.2)\n    a = ap.parse_args()\n    rows = list(csv.DictReader(open(a.tags, encoding=\"utf-8\")))\n    if not rows:\n        sys.exit(\"no rows in \" + a.tags)\n    calls = {r[\"call\"] for r in rows}\n    counts = collections.Counter((r[\"verb\"].strip().lower(), r[\"object\"].strip().lower()) for r in rows)\n    share = {k: v / len(calls) for k, v in counts.items()}\n    core = [(k, round(s, 2)) for k, s in share.items() if s >= 0.6]\n    cond = [(k, round(s, 2)) for k, s in share.items() if a.min_share <= s < 0.6]\n    edge = [(k, round(s, 2)) for k, s in share.items() if s < a.min_share]\n    for label, group in ((\"core\", core), (\"conditional\", cond), (\"edge\", edge)):\n        print(\"-- \" + label)\n        for (v, o), s in sorted(group, key=lambda x: -x[1]):\n            print(\"  %-22s %-28s %.2f\" % (v, o, s))\n\n\nif __name__ == \"__main__\":\n    main()\n"
    }
  ]
}
```

Save that as `/scratch/work/call-recording-to-sop-spec.json`, then:

```bash
python scripts/forge_skill.py /scratch/work/call-recording-to-sop-spec.json --out /scratch/work/forged
python scripts/validate_skill.py /scratch/work/forged/call-recording-to-sop
python scripts/package_skill.py /scratch/work/forged/call-recording-to-sop
```

## A thinner example

Not every skill needs references and scripts. A lens-style skill is mostly
workflow and output contract:

```json
{
  "name": "gst-invoice-checker",
  "description": "Use this skill whenever the user wants an Indian GST invoice checked before it is sent or paid - 'invoice check karo', 'is this GST invoice correct', 'GST number validate karo'. It verifies the GSTIN format and state code, the HSN/SAC code, the CGST-SGST vs IGST split against the place of supply, the tax arithmetic, and the mandatory fields, then returns a pass/fail table with the fix for each failure.",
  "capability": "Check one or more GST invoices for the errors that get them rejected or held up in input credit. Educational and documentary only - it reports what is wrong with the document, it does not advise on tax treatment.",
  "workflow": [
    {"do": "Extract the invoice fields", "why": "Arithmetic checks are worthless on a misread amount."},
    {"do": "Validate the GSTIN and state code pair", "why": "The first two digits of a GSTIN are the state code, and the tax split must agree with it."},
    {"do": "Recompute every tax line", "why": "The printed total hides rounding errors that show up later in the ledger."},
    {"do": "Check the mandatory field set", "why": "A missing field is the most common rejection reason and the cheapest to fix."},
    {"do": "Report pass/fail per check with the fix", "why": "A list of failures without fixes just moves the work back to the user."}
  ],
  "output_contract": [
    "A pass/fail table: check, expected, found, verdict",
    "The corrected tax arithmetic when any line was wrong",
    "A one-line verdict at the top: usable as-is, fixable, or regenerate"
  ],
  "quality_gates": [
    "Every failed check names the exact field and the corrected value",
    "No tax advice beyond what the document shows",
    "Amounts are shown in the invoice's own rounding"
  ]
}
```

## Writing the description

The description is the only thing an agent sees before deciding to load the
skill, and agents under-trigger. So:

- open with `Use this skill whenever the user ...`;
- include the user's own words - Hinglish included - because that is what they
  will type;
- name the artefact (`a .docx`, `a pass/fail table`) so the agent knows it will
  not have to improvise the format;
- stay under 1024 characters, and comfortably under: aim for 400-700.

Bad: `Helps with invoices.`
Good: the `gst-invoice-checker` description above - job, triggers, artefact.
