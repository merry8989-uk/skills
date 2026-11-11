#!/usr/bin/env python3
"""Zip a finished skill folder for handover, after the validator passes.

Usage:
    python package_skill.py /path/to/skill-folder
    python package_skill.py /path/to/skill-folder --dest /scratch/output
    python package_skill.py /path/to/skill-folder --skip-validate   # only when you know why

The zip contains the skill folder itself (SKILL.md, references/, scripts/,
registry/ ...) so the receiver can drop it straight into their skills directory.
"""
import argparse, pathlib, shutil, subprocess, sys, zipfile

SKIP_DIRS = {"__pycache__", ".git", ".ipynb_checkpoints", "node_modules"}
SKIP_FILES = {".DS_Store"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--dest", default="/scratch/output")
    ap.add_argument("--name")
    ap.add_argument("--skip-validate", action="store_true")
    a = ap.parse_args()

    src = pathlib.Path(a.path).resolve()
    if not (src / "SKILL.md").exists():
        sys.exit("package: %s has no SKILL.md - not a skill folder" % src)

    if not a.skip_validate:
        v = subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / "validate_skill.py"),
                            str(src)], capture_output=True, text=True)
        if v.returncode != 0:
            sys.stderr.write(v.stdout + v.stderr)
            sys.exit("package: validation failed - fix the FAILs above and run again")

    dest = pathlib.Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    zpath = dest / (a.name or (src.name + ".zip"))

    count = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob("*")):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.name in SKIP_FILES or p.suffix == ".pyc":
                continue
            if p.is_dir():
                continue
            z.write(p, arcname=str(pathlib.Path(src.name) / p.relative_to(src)))
            count += 1

    print("wrote %s (%d files, %.1f KB)" % (zpath, count, zpath.stat().st_size / 1024))


if __name__ == "__main__":
    main()
