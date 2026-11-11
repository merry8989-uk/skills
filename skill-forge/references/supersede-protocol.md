# Supersede protocol

The rule: **nothing leaves the registry until something measurably better at the
same job exists.** A skill that is merely new is not better. A skill that is
better on one axis and worse on another is a variant, not a replacement.

This is enforced in code, not in prose. `update_registry.py --supersede` refuses
to act without a bench proof whose verdict is `REPLACE`, and `--remove` refuses
to touch a seed entry at all.

## Why it is a rule and not a preference

A registry is a ranking. Every entry competes for the same trigger words, so a
mediocre skill added next to a good one does not sit quietly - it splits the
match and both fire less reliably. Removing the good one to make room is how an
agent ends up with a shelf of skills that never trigger. So the bar for
replacement has to be higher than the bar for addition.

## The rubric

`bench.py` scores out of 100 in two halves.

**Structure, 45 points, measured from the files** - cannot be argued upward:

| Component | Points | Measured as |
|---|---|---|
| workflow_steps | 10 | 2 per step, capped at 5 steps |
| output_contract | 10 | 2 per line, capped at 5 lines |
| quality_gates | 10 | 2 per gate, capped at 5 gates |
| has_scripts | 5 | any `.py` under `scripts/` |
| has_references | 5 | any file under `references/` |
| description | 5 | 3 for an explicit trigger clause, 2 for 300-1024 chars |

**Judgement, 55 points, scored 0-5 per criterion** (11 points each) in a JSON
file the model writes honestly:

| Criterion | The question |
|---|---|
| coverage | does it do the whole job end to end, or a slice |
| precision | is the output contract literal enough to reproduce the result |
| triggers | will it fire for the phrasings a real user types |
| boundaries | does it refuse what it cannot do and name its neighbours |
| gates | are the gates checkable yes/no against the deliverable |

```json
{"coverage": 5, "precision": 5, "triggers": 4, "boundaries": 4, "gates": 5,
 "notes": "per-patient SBAR, explicit coverage statement, time-bound asks"}
```

Write the notes honestly: they are what a later reader uses to re-check the
score when the skill changes.

## The decision

| Condition | Verdict | What happens |
|---|---|---|
| new < 60 | `REJECT_NEW` | not admitted at all - a weak skill makes the registry worse |
| margin >= 10 **and** no regression on coverage or precision | `REPLACE` | the old entry is superseded and stops routing |
| margin > 0 but under 10, or a regression on coverage/precision | `KEEP_BOTH` | new skill registers as a scoped variant; routing picks per request |
| margin <= 0 | `REJECT_NEW` | the incumbent wins |
| either judgement file missing | `KEEP_BOTH` | superiority cannot be proven, so nothing is replaced |

The 10-point bar is roughly one full criterion's worth of improvement. Below
that, the two scores are inside each other's noise - the difference is taste,
not quality.

## The full sequence

```bash
# 1. score the new skill on its own
python scripts/bench.py score /scratch/work/forged/nurse-handover \
    --judgement /scratch/work/j-new.json

# 2. compare against the incumbent, writing a proof file
python scripts/bench.py compare /scratch/work/forged/nurse-handover \
    /scratch/work/forged/nurse-handover-v1 \
    --new-judgement /scratch/work/j-new.json \
    --old-judgement /scratch/work/j-old.json \
    --out /scratch/work/proof.json

# 3. only if the verdict is REPLACE
python scripts/update_registry.py --supersede skill-nurse-handover-v1 \
    --proof /scratch/work/proof.json
```

Worked example from a real run:

```
TOTAL new 86/100 (structure 35 + judgement 51)
TOTAL old 31/100 (structure 15 + judgement 16)
verdict : REPLACE
why     : +55 points and no regression on coverage or precision
margin  : +55 points (86 vs 31)
```

And the reverse, which must be refused:

```
verdict : REJECT_NEW
why     : the new skill scores 31/100 - below the 60 admission floor
```

## What superseding actually does

The losing entry is **not deleted**. It moves to `registry/superseded.json` with
the winner's id, the date, the margin and the proof path. `build_registry.py`
then keeps it out of `registry.json` (so it never routes) and lists it in
`registry.md` under `## superseded`.

That gives three things deletion cannot: the history of why a skill was retired,
the ability to restore it (`--unsupersede`) if the replacement disappoints, and
proof that a replacement was earned rather than assumed.

## What is never allowed

- Deleting a seed entry (`--remove` refuses; seed entries are curated knowledge
  and the record of what replaced them has to survive).
- Superseding on the strength of a structure score alone - structure measures
  form, and a beautifully formatted skill that does half the job is still half
  the job.
- Editing the proof file to change the verdict. The proof records a measurement;
  if the measurement changes, rerun the bench.
- Superseding to "clean up" a skill nobody uses. Unused is not the same as
  worse; leave it and let routing decide.
