# Skill Forge

Part of the [skills](https://github.com/merry8989-uk/skills) collection. The repo
root hosts the [project page](https://merry8989-uk.github.io/skills/); every
skill lives in its own folder with its `SKILL.md`, references, scripts and data.

A self-updating skill factory for AI agents. It routes any request against a
1,262-entry capability registry, reuses what already exists, forges a new skill
when nothing does, validates it, benchmarks it — and only retires an existing
skill when the replacement measurably beats it.

Built to work for any line of work: a nurse writing an SBAR handover, a chartered
accountant closing the month, a quantity surveyor checking a BOQ, a farmer
planning a season, or a founder building a board deck.

**Project page:** <https://merry8989-uk.github.io/skills/> — full
documentation, the direct SKILL.md download, and contact.
**Contact:** [@osintgram_io](https://instagram.com/osintgram_io) on Instagram.

## The three rules

1. **Route before you answer.** Never say "there's no skill for that" from
   memory. Every request goes through the registry first.
2. **Build from the registry, not from memory.** A new skill names what it
   reuses and what it must not steal work from.
3. **Nothing leaves until something better is proven.** A skill is replaced only
   when a bench run shows the new one is at least 10 points better on the same
   job. A registry full of competitors for the same trigger word triggers for
   none of them.

## The registry

1,262 entries, five types. Counts are the build state — the scripts print the
live total.

| Type | Count | What an entry is |
|---|---|---|
| `skill` | 88 | A full skill: 70 installed here, 18 imported as reference |
| `command` | 500 | A prompt lens from a slash-command library (`/swot`, `/eli5`, `/hook10`) |
| `integration` | 231 | One concrete action of a connected service (GitHub, BigQuery, Zoho, Ahrefs, Notion, Supabase, WordPress, …) |
| `core` | 41 | A capability the platform has without any skill loaded (file builds, web search, translation) |
| `archetype` | 402 | A standard repeating task of a real profession, with no skill built yet — a blueprint, not a capability |

402 archetypes span 32 sectors, from healthcare and law to mining, maritime
operations and personal life admin. An archetype hit means: *this is a real
professional job, build it properly* — it hands the forge the profession's own
artefact name (SBAR, BOQ, 8D, tech pack, logframe) instead of a generic "report".

## Quick start

```bash
git clone https://github.com/merry8989-uk/skills
cp -r skill-forge <your-agent-skills-dir>/
```


```bash
# drop the skill folder into a skills directory, then:
cd skill-forge

python scripts/route.py "nurse shift handover SBAR banao"     # what already exists?
python scripts/scaffold_spec.py "nurse shift handover SBAR banao" --out spec.json
python scripts/forge_skill.py spec.json --out /scratch/work/forged
python scripts/validate_skill.py /scratch/work/forged/<name>
python scripts/bench.py score /scratch/work/forged/<name> --judgement j.json
python scripts/package_skill.py /scratch/work/forged/<name>
```

Requirements: Python 3.9+, standard library only. No network, no dependencies.

## Commands

| Script | Does |
|---|---|
| `route.py` | Need → ranked candidates + verdict (`reuse` / `adapt` / `forge`), exit 3 on forge |
| `scaffold_spec.py` | Need → pre-filled spec skeleton; leaves the judgement fields empty on purpose |
| `forge_skill.py` | Spec → complete skill folder (frontmatter, workflow, contract, gates, bundled files) |
| `validate_skill.py` | Form gate: frontmatter, name, description limits, sections, placeholders, broken paths, script compile |
| `bench.py` | Rubric score (45 measured + 55 judged) and the `REPLACE` / `KEEP_BOTH` / `REJECT_NEW` decision |
| `package_skill.py` | Validated folder → zip, refusing to package a skill that fails validation |
| `update_registry.py` | Ingest zips/folders, supersede with proof, restore, rebuild |
| `build_registry.py` | Rebuild `registry.json` / `registry.md` from `seed.json` + `extra.json` |

## How a build runs

**Route.** A lexical scorer with IDF weighting, Hinglish verb mapping, plural
folding and three overrides (archetype hit, "user asked for a skill", and a
guard that fires when only generic words land). Verdict bands: `reuse` at 0.62,
`adapt` at 0.38, else `forge`. Details in `references/routing-protocol.md`.

**Scaffold + forge.** The scaffold fills everything the registry already knows.
The three judgement fields — workflow, output contract, quality gates — are left
empty, and the renderer refuses an unfilled skeleton, so the thinking cannot be
skipped.

**Validate.** Form only: a thin one-paragraph skill can pass at 100/100 and still
be worth nothing. That is why the next step exists.

**Bench.** 45 points measured from the files (steps, contract lines, gates,
scripts, references, description) plus 55 judged 0–5 across coverage, precision,
triggers, boundaries and gates. `REPLACE` needs a 10-point margin, judgement
files for both skills, and no regression on coverage or precision.

**Supersede.** The losing entry is not deleted. It moves to
`registry/superseded.json` with the winner, date, margin and proof path, stops
routing, and stays listed in `registry.md`. `--unsupersede` restores it. Seed
entries can never be deleted — only superseded.

## Layout

```
skill-forge/
├── SKILL.md                     the protocol an agent follows
├── references/                  routing, professions, forge blueprint, gates, supersede, updates
├── scripts/                     the eight scripts above
└── registry/
    ├── seed.json                curated base (skills, lenses, integrations, capabilities, archetypes)
    ├── extra.json               skills imported from what the user supplied
    ├── superseded.json          retired entries with their replacement proof
    ├── registry.json            built, machine-readable, used by the scripts
    ├── registry.md              built, greppable one line per entry
    └── ATTRIBUTION.md           origin and licence of every imported entry
```

## Limits, stated plainly

- Routing is lexical, not semantic. It can be confidently wrong on a paraphrase;
  the protocol therefore requires reading the top candidate's capability line
  before trusting a `reuse` verdict.
- The validator checks form, not quality. The bench is what judges quality, and
  its judgement half is a human-or-model score, not a measurement.
- `reference` entries are indexed but not installed: their descriptions and
  trigger words are searchable, the files are not present. The router never
  returns `reuse` for one.
- Archetypes are map entries, not capabilities. A match means "build this",
  never "this exists".

## Attribution

Imported skills and their licences are recorded in
[`registry/ATTRIBUTION.md`](skill-forge/registry/ATTRIBUTION.md). The current
registry indexes 18 skills from
[anthropics/skills](https://github.com/anthropics/skills) (Apache 2.0, commit
`2c5958e`) as reference entries.

## Licence

No licence file has been added to this repository yet. Until one is, the default
is all rights reserved.
