# Quality gates

Two gates, two different questions. Do not confuse them.

| Gate | Question it answers | Script |
|---|---|---|
| Validator | Is this skill well formed and safe to hand over? | `validate_skill.py` |
| Bench | Is this skill *better* than what we already have? | `bench.py` |

A skill can pass the validator at 100/100 and still be worth nothing - a thin
one-paragraph handover passed cleanly in testing and scored 31/100 on the bench.
The validator checks hygiene; the bench checks quality. Both, in that order.

`scripts/validate_skill.py` is the gate between a draft and a delivered skill.
Pass means exit 0 with score >= 90. A `FAIL` is never negotiable; a warning is
worth 4 points and four warnings at 88 is a skill that is not finished.

## What it checks

| Gate | Fails when | Fix |
|---|---|---|
| Frontmatter parses | No `---` block, or a line that is not `key: value` | Keep it to `name`, `description`, `allowed-tools`, `metadata` |
| Name is valid | Uppercase, underscores, spaces, > 64 chars | kebab-case, lowercase, and make it the job |
| Name matches folder | Warning only | Rename the folder to the frontmatter name before packaging |
| Description length | Over 1024 chars | Cut the second paragraph; keep job + triggers + artefact |
| Description length | Under 80 chars (warning) | It will not trigger - write the triggering clause |
| Description triggers | No "Use this skill whenever ..." style clause (warning) | Add it as the first sentence |
| SKILL.md length | Over 500 lines (warning) | Move detail into `references/` and point at it from the step that needs it |
| Section: workflow | No `## Workflow` / `## Steps` / `## Process` heading | Rename the section; the validator looks for the pattern |
| Section: output | No `## Output contract` / `## Deliverable` / `## Format` | State the literal shape of the deliverable |
| Section: quality | No `## Quality gates` / `## Checklist` / `## Before you deliver` | Add checkable statements |
| Placeholders | `TODO`, `TBD`, `FIXME`, `{{ }}`, `<placeholder`, `XXX`, `lorem ipsum` | Fill it or delete the line - a placeholder ships as broken output |
| Citation markers | `[cite:` anywhere in SKILL.md | Files cannot render citation pills; write a plain source line instead |
| Broken references | A `references/...` or `scripts/...` path in the body that is not on disk | Create the file or remove the mention |
| Scripts compile | A `.py` file under the folder raises `PyCompileError` | Fix the syntax; a skill that ships a broken script fails at the worst moment |
| Packaging junk | `__pycache__`, `.pyc`, `.DS_Store` present (warning) | `package_skill.py` skips them, but clean the folder |

## The gates the script cannot check

These are the ones that decide whether the skill is any good. Check them by
reading the rendered SKILL.md once, end to end.

1. **One job.** If the capability sentence needs "and" between two verbs, split
   it. A skill that does two jobs triggers for neither reliably.
2. **The steps have reasons.** Every step whose "why" is unstated gets skipped
   the first time it is inconvenient. If you cannot write the why, the step is
   probably not needed.
3. **The output contract is literal.** "A clear summary" is not a contract. "Six
   rows: item, qty, rate, taxable value, CGST, SGST" is.
4. **The gates are checkable.** Each one should be answerable yes or no by
   looking at the deliverable. "Accurate" is not checkable; "no number appears
   without a source cell" is.
5. **No duplicates in the registry.** Run `route.py` on the new skill's own
   description. If an existing entry comes back above 0.62, you are about to
   create a competitor for it - extend that skill instead, or make the new one
   narrow enough that the boundary is obvious.
6. **Scripts were actually run.** A bundled script that has never been executed
   is a liability. Run it once with real input before packaging.
7. **The description uses the user's words.** Grep the conversation for how they
   phrased the need and put those phrases in the description.
8. **The skill refuses what it cannot do.** A `dont_use_when` section and an
   explicit "stop and say why" condition prevent the most expensive failure
   mode: a skill confidently producing the wrong artefact.

## Reading the output

```
skill   : gst-invoice-checker
score   : 100/100 (need 90)
verdict : PASS
  ok   - frontmatter parses
  ok   - name is valid kebab-case
  ok   - description within length limit (486 chars)
  ...
```

A `FAIL` line tells you the exact problem; fix and rerun. Do not hand-edit the
validator to make a skill pass, and do not package with `--skip-validate` unless
you can say out loud why the failure is harmless.
