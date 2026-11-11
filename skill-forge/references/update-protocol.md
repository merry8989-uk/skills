# Update protocol

The user will keep handing over skills: a zip they downloaded, a folder they
exported, a link to a repository. The registry is only useful if it stays true,
so absorb them rather than reading them once and forgetting.

## Ingest

```bash
# a zip
python scripts/update_registry.py --zip /scratch/work/incoming.zip

# a folder (one skill or many, nested is fine)
python scripts/update_registry.py --dir /scratch/input/new-skills

# a link - download first, then treat it as a zip
curl -L "<url>" -o /scratch/work/incoming.zip
python scripts/update_registry.py --zip /scratch/work/incoming.zip
```

Each `SKILL.md` found becomes one entry: `name` and `description` from the
frontmatter, triggers derived from both. Entries land in `registry/extra.json`,
then `build_registry.py` runs and rewrites `registry.json` and `registry.md`.

Report the before and after total to the user. If the total falls below 800,
say so plainly - the floor is part of what this skill promises, and a silent
drop means something was removed by accident.

## Inspect and remove

```bash
python scripts/update_registry.py --list                  # what came from user imports
python scripts/update_registry.py --remove skill-old-name
python scripts/update_registry.py --rebuild                # after editing extra.json by hand
```

## What the ingester will not do

- **It will not fetch a link itself.** Downloads go through `curl` so the
  sandbox's egress rules apply and you can see what actually arrived.
- **It will not read a non-skill zip.** If no `SKILL.md` turns up it exits with
  a message. That is the signal to look inside the archive before assuming it
  was the wrong file - a repo often nests skills two or three directories deep,
  which the scan handles, but a plain document collection will not have any.
- **It will not overwrite the curated seed.** `seed.json` is the base set built
  from the installed skills, the 500-command library, the integration actions
  and the platform capabilities. User imports live only in `extra.json`, so a
  rebuild can never lose them and never has to re-read the seed.

## Collisions

Re-importing the same skill updates its capability text and triggers, keyed by
id, so there is never a second copy. A genuine collision is two different
skills that do the same job. When that happens:

1. `route.py "<description of the job>"` - see which one wins.
2. Read both capability lines. If one is a strict subset, keep the broader one
   and remove the narrower from `extra.json`.
3. If they are both legitimate but scoped differently, sharpen both
   descriptions so the boundary is obvious: the narrower one should name the
   context it exists for, and the broader one should list it in
   `dont_use_when`.
4. Rebuild and confirm the count.

## Keeping the seed honest

The seed is generated data, not magic. If the agent gains a new installed skill
or loses one, `registry/seed.json` is the file to edit - add an entry under
`entries` with `type: "skill"`, a `capability` sentence and `triggers` - then
run `build_registry.py`. Do not hand-edit `registry.json`; it is overwritten on
every rebuild.
