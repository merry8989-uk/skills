# Routing protocol

How `scripts/route.py` turns a need into a ranked list, why the numbers are what
they are, and when to override the verdict.

## The registry

1336 entries, five types, one file each run:

| Type | Count | What an entry is |
|---|---|---|
| `skill` | 162 | A skill: 70 installed here, 92 imported as reference (see ATTRIBUTION.md). |
| `command` | 500 | A prompt lens from the `/command` library: a way of treating material. |
| `integration` | 231 | One concrete action of a connected service (Ahrefs, GitHub, Zoho, BigQuery, ...). |
| `core` | 41 | A capability the platform has without any skill loaded (file builds, web search, translation, ...). |
| `archetype` | 402 | A standard repeating task of a real profession, with no skill built yet. A blueprint, not a capability. See `professions.md`. |

Counts move as skills are added and superseded; the numbers above are the build
state, and `route.py` prints the live total.

Two status values matter at match time. `ready` is an installed skill - the agent
can load and follow it. `reference` is indexed only: the description and trigger
words are searchable, the files are not on this agent. A reference entry carries
a 0.92 multiplier so an installed skill wins a near-tie, and it can never
produce a plain `reuse` verdict.

Every entry carries `name`, `capability`, `triggers`, `source`, `group`. The
trigger list is the words the entry is *about*, generated once at build time
from the name plus the capability sentence.

## The score

For a query `q`:

1. Tokenise `q`. Lowercase, split on non-alphanumerics, drop stopwords, map
   Hinglish verbs through the alias table, singularise plurals longer than four
   characters.
2. For each entry, find the query tokens present in its text.
3. `raw = sum(idf(token))` over the matched tokens, where
   `idf = ln((N+1)/(df+1)) + 0.35`. A word that appears in two entries is worth
   about three times a word that appears in two hundred - which is why
   "instagram" alone decides nothing but "digilocker" decides everything.
4. `coverage = matched / query_tokens`, then `score = raw * (0.65 + 0.55 *
   coverage)`. An entry that accounts for the whole sentence beats one that
   catches a single word.
5. Add `1.2` per adjacent query word pair found in the entry's name or
   capability ("invoice reconciliation" as a phrase is stronger than the two
   words apart).
6. Multiply by the type weight: `skill 1.18`, `core 1.05`, `integration 1.00`,
   `command 0.90`, `archetype 0.86`. A loaded skill carries more machinery than
   a one-line lens, so it wins ties; an archetype is only a blueprint, so it
   sits below everything real.
7. `confidence = 1 - exp(-score / 8)`. Saturating: 8 raw points is a strong
   single match, 16 is a match that owns the sentence, and no score can exceed
   1.0.

## The verdict

| Confidence | Verdict | Exit | Reading |
|---|---|---|---|
| >= 0.62 | `REUSE` | 0 | Load the top entry. |
| 0.38 - 0.61 | `ADAPT` | 0 | Chain the top 2-3, or forge on top of them. |
| < 0.38 | `FORGE` | 3 | Nothing here does the job. |

Superseded entries are not in `registry.json` at all, so they cannot win a
match. That is the whole point of the supersede gate: the better skill answers.

Three overrides run before the bands:

- **An archetype matched.** If the best candidate is an archetype and its
  confidence is 0.30 or more, the verdict is `FORGE` - a real professional
  workflow exists with no skill behind it, so build one from that blueprint.
  This is how "nurse shift handover SBAR banao" goes straight to a spec instead
  of being answered with a generic writing lens.


- **The user asked for a skill.** If the need contains a build verb near "skill"
  (`naya skill`, `make a skill`, `build a skill`, `forge`), the verdict is
  `FORGE` regardless of confidence. The candidates are still listed, because
  they are what the new skill should reuse rather than reinvent.
- **Only generic words landed.** If the need has two or more distinctive words
  (each carried by <= 2% of entries) and the best entry matches none of them,
  the verdict is `FORGE` even if the confidence is in the ADAPT band. This is
  what stops "customer call recordings into SOP documents" from resolving to a
  generic planning lens because the word "plan" appeared.

## Worked examples

```
need: instagram reels ka script likhna hai hook ke saath
  REUSE  ig-reel   conf 0.93 cov 1.00
         ig-audit  conf 0.76 cov 0.67
```

`script`, `reel`, `hook`, `instagram` all land inside one skill, and coverage is
1.00 because the alias table mapped `likhna` to `write`. Load it.

```
need: gst invoice banao aur customer ko mail bhejo
  REUSE  Email drafting and sending          conf 0.70
         Zoho Invoice: Create and send invoices conf 0.68
```

The verdict says reuse because one capability is above the band, but the need
has two verbs - create the invoice, then mail it. Read the list, not just the
verdict: this is a two-step workflow over the top two entries.

```
need: weekly sales report from shopify data in excel
  ADAPT  dashboard-design  conf 0.50
         excel-automation  conf 0.48
```

`shopify` is in no entry, so it eats a large share of the query's information
mass and depresses every score. The matches that remain are real: build the
sheet, then decide what the weekly view should say. Adapt, or forge a
`shopify-weekly-report` skill that names both as dependencies.

```
need: turn customer call recordings into SOP documents
  FORGE  (distinctive-word override)
```

`recordings` and `sop` are distinctive and match nothing that does this job end
to end. Forge.

## When to override the script

The score is lexical. It does not know that "deck" and "slides" are the same
artefact, or that "reconcile" implies matching two records. So:

- **Downgrade** `REUSE` to `ADAPT` when the top capability covers only part of
  the sentence. Read the capability line every time; it takes one second and it
  is the difference between reusing a skill and misusing one.
- **Upgrade** `ADAPT` to `REUSE` when two candidates turn out to be the same
  underlying capability described twice.
- **Ignore** candidates that share a keyword but not the job. "board deck" pulls
  `dashboard-design` because of "product health board"; the deck skills are
  further down the same list and are the right answer.
- **Trust the grep** over the score when the domain vocabulary is unfamiliar:
  `rg -i "sop|transcript|recording" registry/registry.md`.

## Using the result

For `REUSE` on a `skill`: `skill_view("<name>")` and follow it. On an
`integration`: call the tool. On a `core`: just do the work. On a `command`:
apply the lens to the user's material.

For `ADAPT`: write the chained workflow down before starting - which capability
handles which step, in what order, and where the handoff artefact lives. A chain
that is not written down becomes two half-done jobs.

For `FORGE`: go to `references/forge-blueprint.md`.
