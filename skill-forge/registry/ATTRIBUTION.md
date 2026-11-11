# Registry attribution

Entries imported from outside this agent are listed here with their origin and
licence, because a registry that cannot say where a capability came from cannot
be audited.

## anthropic-skills (18 reference entries)

- **Source:** `github.com/anthropics/skills`, commit `2c5958ecac7cee2b583967a2c4981d0f4a75c579`
- **Supplied as:** `anthropic-skills.zip`, extracted 2026-11-11
- **Licence:** Apache 2.0 (per-skill `LICENSE.txt` and `THIRD_PARTY_NOTICES.md` inside the bundle)
- **Indexed:** 18 of the 19 skills. `skill-creator` was skipped because an
  identical id already exists in the curated seed and an import must never
  overwrite curated knowledge.
- **Not indexed:** the bundle's own wrapper `SKILL.md` (it would compete with its
  own children) and `reference/skill-template` (a template, not a usable skill).
- **Status:** `reference` - the descriptions and trigger words are indexed so the
  router can find them, but the skill files are **not installed on this agent**.
  A `reference` entry never produces a plain `reuse` verdict; the router returns
  `adapt` and says the files have to be imported first.

To install them for real, extract the bundle into a skills directory and import
with `--status ready`:

```bash
python scripts/update_registry.py --dir <extracted>/skills --status ready --on-collision skip
```

## paperclipai/paperclip (74 reference entries)

- **Source:** `github.com/paperclipai/paperclip`, branch `master`, commit `80b2369f26983be3bb8459f00f9cc6f7d271d7f3`
- **Supplied as:** the public repository URL, cloned 2026-11-12
- **Licence:** MIT (Copyright (c) 2025 Paperclip AI), see `LICENSE` in that repo
- **Scanned:** 83 `SKILL.md` files across the whole tree — `.agents/skills` (37),
  `packages/skills-catalog` (16), `integrations/assistant-plugins` (9),
  `packages/plugins` (6), `skills/` (8), `skills-releases` (2),
  `packages/teams-catalog`, `server/src/onboarding-assets`, `.claude/skills`
- **Indexed:** 74 entries (76 unique skill names; the remainder are duplicate
  copies that collapsed to one entry each):
  - `delegate-work`, `follow-up-results`, `review-my-team` — three copies each
    (claude, openai and shared plugin folders)
  - `doc-maintenance` — twice (`.agents/skills` and the skills catalogue)
  - `paperclip` — three times (`skills/`, `skills-releases/v0`, `skills-releases/v7-roster`)
- **Status:** `reference` — descriptions and trigger words are indexed so the
  router can find them, but the files are **not installed on this agent**. A
  `reference` entry never produces a plain `reuse` verdict.

The skills are Paperclip's own operational tooling (agent creation, eval
runners, PR gardening, release changelogs, LLM-wiki maintenance, task planning).
They are indexed as they are; none of them was rewritten.
