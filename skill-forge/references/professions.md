# The profession layer

402 of the registry's 1244 entries are **archetypes**: the repeating, standard
tasks of a real profession, with no skill built for them yet. They exist so the
answer to "is there a skill for this?" is never a shrug - for any line of work
on earth, the router can at least name the job and hand the forge a blueprint.

An archetype is not a skill. It has no workflow, no output contract, no gates.
It says: *this is a real, repeating professional task; build it properly when
someone needs it.*

## What is covered

Thirty sectors, roughly six professions each, two core workflows per profession.
The list is deliberately broad rather than deep - breadth is what makes the
router useful on the first sentence from a stranger.

| Sector | Example professions |
|---|---|
| Healthcare and medicine | physician, nurse, surgeon, radiologist, pharmacist, physiotherapist, hospital administrator, public health officer |
| Mental health and counselling | clinical psychologist, counsellor, psychiatrist, school counsellor |
| Law and justice | litigation lawyer, corporate lawyer, compliance officer, paralegal, IP attorney |
| Civil and construction engineering | civil engineer, site engineer, quantity surveyor, structural designer, surveyor |
| Mechanical, electrical, industrial | design engineer, maintenance engineer, electrical engineer, instrumentation, HVAC |
| Software and IT | backend, frontend, data engineer, analyst, SRE, QA, security, PM, architect |
| Data, AI and research engineering | ML engineer, research scientist, statistician, BI developer, prompt designer |
| Finance and accounting | accountant, CA, financial analyst, treasury, credit, internal audit, payroll |
| Banking, insurance and markets | relationship manager, loan officer, underwriter, claims adjuster, actuary, equity research |
| Sales, marketing and growth | sales exec, KAM, marketing manager, content, SEO, performance, brand, CSM, research |
| Education and training | teacher, lecturer, curriculum designer, corporate trainer, exam coordinator |
| Research and academia | PhD researcher, postdoc, lab manager, peer reviewer, research administrator |
| Agriculture and food production | farmer, agronomist, livestock manager, food technologist, cold chain |
| Manufacturing and quality | production supervisor, quality engineer, Lean/Six Sigma lead, process engineer, EHS |
| Logistics and supply chain | planner, procurement, warehouse, fleet, customs broker, last-mile |
| Hospitality, travel and food service | hotel manager, front office, chef, restaurant manager, travel agent, event manager |
| Retail and e-commerce | store manager, category manager, marketplace operator, merchandiser, buyer |
| Media, arts and design | journalist, editor, copywriter, graphic designer, UX, photographer, video editor, author |
| Sports, fitness and performance | strength coach, sports physio, team analyst, PE teacher, yoga instructor |
| Government and public service | civil servant, municipal officer, urban planner, welfare officer, regulator |
| Defence, safety and emergency | police, fire officer, emergency responder, industrial safety, forensic analyst |
| Environment, energy and utilities | environmental engineer, sustainability, solar/wind developer, energy auditor, water utility |
| Science and laboratory | chemist, biologist, microbiologist, metrologist, lab safety |
| Pharmaceutical and regulatory | regulatory affairs, CRA, pharmacovigilance, QA, medical writer |
| People, HR and recruiting | HRBP, recruiter, sourcer, L&D, compensation, employee relations, HR ops |
| Real estate and property | agent, property manager, valuer, facilities manager, land acquisition |
| Textiles, fashion and crafts | designer, merchandiser, textile technologist, pattern maker, artisan |
| Automotive, aviation and maritime | service advisor, design engineer, EV charging, airline ops, pilot, port officer |
| Telecom and infrastructure ops | network planner, NOC engineer, field technician, regulatory analyst |
| Mining, metals and heavy industry | mine planning, mine safety, metallurgist, heavy equipment planner |
| Nonprofit, development and impact | programme manager, grant writer, M&E officer, field coordinator, volunteer manager |
| Personal, family and life admin | individual, student, job seeker, parent, home owner, caregiver, freelancer, small business |

## What happens when an archetype matches

`route.py` returns `FORGE` with the archetype named as the blueprint. That is
the signal to build a real skill, not to improvise an answer:

```
need:  nurse shift handover SBAR banao
FORGE  archetype  Nurse: shift handover in SBAR format   conf 0.97
```

The archetype tells you three things the user's one line did not: who does this
job, what the artefact is called in that field, and which neighbouring workflows
exist (so the new skill can name its boundaries).

## Forging for a profession

Professional skills are judged by different things than content skills, and the
spec has to show it:

- **Name the artefact the profession actually uses.** SBAR, BOQ, 8D, CAPA, tech
  pack, logframe, valuation report, run sheet, line sheet, method statement. A
  generic "report" is a red flag that the skill has not understood the job.
- **Encode the profession's own order.** 8D is D1-D8 in order; SBAR is
  S-B-A-R; a valuation report has a fixed section sequence. Reordering it makes
  the output unusable to a practitioner.
- **Use the field's units, codes and thresholds.** HSN codes, ICD-10, IS codes,
  GS1, acuity scores, grade control cut-offs, tolerance classes.
- **State the professional limit.** Clinical, legal and financial skills must
  say what they document versus what they advise. `dont_use_when` and `notes`
  carry this; the refusal is part of the quality, not a disclaimer bolted on.
- **Cite the standard where one exists**, so a reader can check the skill
  against it. Where no standard exists, say the sequence is a convention.

Two of the blueprint examples are professional skills - a call-recording to SOP
build and a GST invoice checker - and `references/forge-blueprint.md` shows the
full spec for both.

## Extending the layer

Adding a profession is a seed edit, not a code change. In
`registry/seed.json`, append entries with `"type": "archetype"`,
`"status": "not-built"`, a `capability` sentence and `triggers`, then run
`scripts/build_registry.py`. Keep one entry per repeating workflow, phrased the
way the profession phrases it - that phrase is what makes the router find it.

Do not add an archetype for a workflow a real skill already covers. Run
`route.py` on the phrase first; if an installed skill scores above 0.62, the
archetype would only add noise.

## Honesty rules

- An archetype is a **map entry**, not a capability. Never answer a user as if a
  skill exists because an archetype matched.
- Do not invent a profession's workflow to fill a gap. If the field's actual
  artefact is unknown, say so and ask the user - a wrong artefact name is worse
  than a question.
- The count is what the script prints, never a number remembered from a
  previous run.
