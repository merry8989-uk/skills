---
name: skill-forge
description: "Use this skill whenever the user wants a skill built for any profession or task, asks which skill or command to use, or hands over skills to be absorbed. It routes the need against a 1240+ entry registry covering every installed skill, the 500-lens prompt library, the actions of every connected integration, the platform's own capabilities, and 402 profession archetypes across 32 sectors - so the answer works for a nurse, a CA, a surveyor, a farmer or a founder alike. It then either loads the right capability or forges a new skill from a blueprint, validates it, benchmarks it against the incumbent, and only replaces an existing skill when the new one scores at least 10 points better on a fixed rubric. Triggers on 'skill banao', 'naya skill', 'make a skill for X', 'is there a skill for this', 'which skill should I use', 'skill for a CA / nurse / lawyer / farmer / teacher', 'update my skills', 'replace this skill', '1200 skills' - and on any repeatable workflow the agent should own."
allowed-tools: "bash"
metadata:
  version: "2.0"
  registry_floor: "800"
---

# Skill Forge

A dynamic, universal skill factory. It knows what the agent can already do
(1262 registry entries: 88 skills, 500 prompt lenses, 231 integration actions,
41 platform capabilities, 402 profession archetypes - the scripts print the live
count), builds new skills from that knowledge, absorbs new ones the user
supplies, and refuses to lose a good skill to a worse one.

## The three rules

1. **Route before you answer.** Never say "there's no skill for that" from
   memory. Every request goes through the registry first.
2. **Build from the registry, not from memory.** A new skill names what it
   reuses and what it must not steal work from.
3. **Nothing leaves until something better is proven.** A skill is replaced only
   when a bench run shows the new one is at least 10 points better on the same
   job. "Newer" is not "better", and a registry full of competitors for the same
   trigger word is worse than a short one.

## Step 1 - One task sentence

`<verb> <object> for <context>, delivered as <artefact>`.

> "nurse shift handover SBAR banao" -> "Write a per-patient SBAR shift handover
> for a ward nurse, delivered as a printable .docx."

Hinglish, typos and half-sentences are fine - `route.py` maps common Hinglish
verbs (`banao`, `likho`, `bhejo`, `dikhao`, `jaanch`) onto the English words the
registry uses. If the sentence cannot be written, ask exactly one question:
who is it for, and what artefact comes out.

## Step 2 - Route

Run from the skill folder, or prefix with `/scratch/skills/skill-forge/`.

```bash
python scripts/route.py "<task sentence>" --top 5
```

| Verdict | Meaning | What you do |
|---|---|---|
| `REUSE` (>= 0.62) | One capability covers the need | Load it and work from it. Do not rebuild it. |
| `ADAPT` (0.38 - 0.62) | Partial matches only | Chain 2-3 candidates, or forge one focused skill on top of them. |
| `FORGE` (exit 3) | Nothing close, an archetype matched, or the user asked for a new skill | Steps 3-7. |

An **archetype** hit is the important one: it means the need is a real,
repeating professional task with no skill behind it. The archetype gives the new
skill its name, its artefact and its boundaries - see `references/professions.md`.

A `reference` entry is indexed but **not installed** - its descriptions and
trigger words are searchable, the files are not on this agent. The router never
returns `reuse` for one; it returns `adapt` and says the files must be imported
first (`--status ready`). Never tell a user a reference skill will run.

Read the top candidate's capability line before trusting any verdict. The score
is lexical; it can be confidently wrong on a paraphrase. If the candidate does
not cover the job end to end, treat `REUSE` as `ADAPT`.

When the user's domain words are spelled differently from the registry's:

```bash
rg -i "reconcil|ledger|gst|sbar|boq|8d" registry/registry.md
```

## Step 3 - Scaffold the spec

Auto-build starts here. The scaffold fills everything the registry already knows
so only the judgement is left to write:

```bash
python scripts/scaffold_spec.py "<task sentence>" --out /scratch/work/<name>-spec.json
```

It fills: name, a description draft, the capability line, `use_when`, and
`dont_use_when` taken from the runners-up so the new skill cannot steal their
work. It leaves `workflow`, `output_contract` and `quality_gates` empty on
purpose - and `forge_skill.py` refuses to render an unfilled skeleton, so the
judgement step cannot be skipped.

## Step 4 - Fill the judgement, then forge

Read `references/forge-blueprint.md` for the schema and two complete examples.
Then fill, honestly:

- **Name the artefact the profession uses.** SBAR, BOQ, 8D, CAPA, tech pack,
  logframe, run sheet, method statement. A generic "report" means the skill has
  not understood the job.
- **Workflow: 3-7 steps, each with a why.** A step whose reason is unstated gets
  skipped the first time it is inconvenient.
- **Output contract: literal.** "Six rows: item, qty, rate, taxable value, CGST,
  SGST" beats "a clear summary".
- **Quality gates: checkable yes/no** against the finished deliverable.
- **`dont_use_when`: name the neighbouring skills.** This is what keeps the
  registry from growing duplicates.
- **Deterministic work goes in `scripts/`.** Parsing, building, computing,
  converting: a script runs without loading into context, which is how a skill
  stays short.

```bash
python scripts/forge_skill.py /scratch/work/<name>-spec.json --out /scratch/work/forged
```

## Step 5 - Validate (form gate)

```bash
python scripts/validate_skill.py /scratch/work/forged/<name>
```

Pass means exit 0, `PASS`, score >= 90. Every `FAIL` is mandatory. This checks
form: frontmatter, name, description length and trigger clause, 500-line budget,
required sections, no placeholders, every referenced file on disk, scripts
compile, no citation markers.

The validator says a skill is *well formed*, not that it is *good*. A thin
one-paragraph handover passed at 100/100 in testing and scored 31/100 on the
bench. Step 6 is where quality is decided.

## Step 6 - Bench, then promote

Score both skills on the same rubric - 45 points measured from the files, 55
points judged - and let the comparison decide. Full rubric and worked numbers in
`references/supersede-protocol.md`.

```bash
# write a judgement file per skill (0-5 on five criteria, plus notes)
python scripts/bench.py score /scratch/work/forged/<new> --judgement j-new.json

python scripts/bench.py compare /scratch/work/forged/<new> <old-skill-dir> \
    --new-judgement j-new.json --old-judgement j-old.json \
    --out /scratch/work/proof.json
```

| Verdict | Meaning |
|---|---|
| `REPLACE` | +10 points or more, no regression on coverage or precision - the old entry is superseded |
| `KEEP_BOTH` | better in places, not overall - registers as a scoped variant, routing decides per request |
| `REJECT_NEW` | weaker, or under the 60/100 admission floor - do not add it |

Only on `REPLACE`:

```bash
python scripts/update_registry.py --supersede <old-id> --proof /scratch/work/proof.json
```

The losing entry is not deleted. It moves to `registry/superseded.json` with the
winner, date, margin and proof path, stops routing, and is listed under
`## superseded` in `registry.md`. `--unsupersede` brings it back. That is the
rule made mechanical: nothing leaves the registry until something better has
earned the place, and the receipt survives.

## Step 7 - Package and hand over

```bash
python scripts/package_skill.py /scratch/work/forged/<name>
```

The validator runs again inside packaging, so a failing skill cannot be zipped.
The zip lands in `/scratch/output/` containing the skill folder itself
(SKILL.md, references/, scripts/) - droppable straight into a skills directory.

Then tell the user, five lines or fewer: the skill name and its one job; when it
fires (their own phrases); the zip filename; two or three test prompts; and the
live registry count if it changed. Never paste the SKILL.md into chat.

## Step 8 - Keep the registry current

```bash
python scripts/update_registry.py --zip /scratch/work/incoming.zip
python scripts/update_registry.py --dir /scratch/input/new-skills
python scripts/update_registry.py --list
```

For a link, download it first (`curl -L <url> -o /scratch/work/incoming.zip`)
and pass the local file. Re-importing the same skill updates its text instead of
duplicating it. Report the before and after total; if it drops, say so - the
800-entry floor is part of what this skill promises.

`--remove` requires `--force`, and refuses seed entries outright: curated
knowledge is superseded, never deleted. Details in
`references/update-protocol.md`.

## Precision rules

- One skill, one job. If the spec needs "and" between two verbs, it is two
  skills or a workflow over two.
- Reuse beats forge; a forged duplicate is worse than no skill, because it
  splits trigger matching.
- A profession skill must carry the profession's own artefact name, order, units
  and codes. Generic output is a failed build even when it validates.
- Clinical, legal and financial skills state what they document versus what they
  advise. The refusal is part of the quality.
- Never claim a bundled script works without running it once.
- Never quote a registry count you have not just printed.
- If a need genuinely cannot be served (missing integration, no data source),
  say so plainly and stop - do not forge a skill that fails at step one.

## Bundled files

- `references/routing-protocol.md` - how the score is computed, the thresholds,
  the archetype override, worked boundary cases.
- `references/professions.md` - the 32-sector profession layer and how to forge
  a professional skill properly.
- `references/forge-blueprint.md` - spec schema plus two complete filled specs.
- `references/quality-gates.md` - every validator gate and its fix.
- `references/supersede-protocol.md` - the rubric, the decision table, the
  promote/restore commands.
- `references/update-protocol.md` - ingesting new skills, dedupe, collisions.
- `registry/registry.md` - greppable index of every routing entry.
- `registry/registry.json` - machine-readable registry used by the scripts.
- `registry/seed.json` - the curated base (skills, lenses, integrations,
  platform capabilities, profession archetypes).
- `registry/extra.json` - skills added from what the user supplied.
- `registry/superseded.json` - retired entries with their replacement proof.
- `registry/ATTRIBUTION.md` - origin and licence of every imported entry.
- `scripts/route.py` - need -> ranked candidates + verdict.
- `scripts/scaffold_spec.py` - need -> pre-filled spec skeleton.
- `scripts/forge_skill.py` - spec -> complete skill folder.
- `scripts/validate_skill.py` - form gate.
- `scripts/bench.py` - rubric score, comparison, replace decision.
- `scripts/package_skill.py` - validated folder -> zip in /scratch/output.
- `scripts/update_registry.py` - ingest, supersede, restore, rebuild.
- `scripts/build_registry.py` - rebuild registry.json / registry.md from seed + extra.
