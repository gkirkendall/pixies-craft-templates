#!/usr/bin/env python3
"""Test the version-folder choice of tools/render.py and tools/verify.py (PLAN.md, VER1). Free: no app needed.

  python3 tools/tests/test_versions.py

A stand-in effectcraft-cli reports a chosen version. Checks, on the real Fill the Frame template (tested with 0.13.0): 0.13.0 uses
effectcraft-0.13 without a warning, 0.14.0 uses it with the warning, and 0.12.0 is refused. Then a rehearsal in a scratch copy:
effectcraft-0.13 frozen beside a new effectcraft-0.14, where each version must get the right folder, and verify --list must run
only the right ones.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "effectcraft" / "utility" / "fill_frame"


def stand_in(tmp, version):
    cli = pathlib.Path(tmp) / f"effectcraft-cli-{version}"
    cli.write_text(f"#!/bin/sh\necho 'effectcraft-cli {version}'\n")
    cli.chmod(0o755)
    return cli


def run(tool, *args):
    r = subprocess.run([sys.executable, ROOT / "tools" / tool, *map(str, args)], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def main():
    results = []

    def check(name, ok, detail):
        results.append(ok)
        print(("PASS " if ok else "FAIL ") + name + ": " + detail.strip().replace("\n", " | "))

    with tempfile.TemporaryDirectory() as tmp:
        for version, folder, warns in (("0.13.0", "effectcraft-0.13", False), ("0.14.0", "effectcraft-0.13", True)):
            code, out, err = run("render.py", TEMPLATE, "--which", "--effectcraft-cli", stand_in(tmp, version))
            ok = code == 0 and out.split()[0].endswith(folder) and ("warning" in err) == warns
            check(f"render on {version}", ok, f"{out}{err}")
        code, out, err = run("render.py", TEMPLATE, "--which", "--effectcraft-cli", stand_in(tmp, "0.12.0"))
        check("render on 0.12.0 refused", code != 0 and "no folder of Fill the Frame opens in EffectCraft 0.12.0" in err, err)

        # Rehearsal: the 0.13 folder frozen, a 0.14 folder beside it (manifests only; nothing is rendered).
        copy = pathlib.Path(tmp) / "fill_frame"
        for name, built, tested, frozen in (("effectcraft-0.13", "0.13.0", ["0.13.0", "0.13.4"], True),
                                            ("effectcraft-0.14", "0.14.0", ["0.14.0"], False)):
            m = json.loads((TEMPLATE / "effectcraft-0.13" / "template.json").read_text())
            m.update(built_with=built, app_min_version=tested[0], frozen=frozen,
                     tested=[{"version": v, "date": "2026-10-21", "result": "pass", "checks": "1/1"} for v in tested])
            (copy / name).mkdir(parents=True)
            (copy / name / "template.json").write_text(json.dumps(m))
        for version, folder, warns in (("0.13.2", "effectcraft-0.13", False), ("0.14.0", "effectcraft-0.14", False),
                                       ("0.15.0", "effectcraft-0.14", True)):
            code, out, err = run("render.py", copy, "--which", "--effectcraft-cli", stand_in(tmp, version))
            ok = code == 0 and out.split()[0].endswith(folder) and ("warning" in err) == warns
            check(f"rehearsal: render on {version}", ok, f"{out}{err}")
        code, out, err = run("render.py", copy, "--which", "--folder", "effectcraft-0.13", "--effectcraft-cli", stand_in(tmp, "0.14.0"))
        check("rehearsal: --folder picks the frozen folder", code == 0 and out.split()[0].endswith("effectcraft-0.13") and "warning" in err,
              f"{out}{err}")
        for version, runs in (("0.13.2", {"effectcraft-0.13": "run", "effectcraft-0.14": "skip"}),
                              ("0.14.0", {"effectcraft-0.13": "skip", "effectcraft-0.14": "run"})):
            code, out, err = run("verify.py", copy, "--list", "--effectcraft-cli", stand_in(tmp, version))
            got = {line.split()[1]: line.split()[2] for line in out.splitlines() if "effectcraft-0.1" in line and len(line.split()) > 2}
            check(f"rehearsal: verify --list on {version}", code == 0 and got == runs, f"{got}")
    print(f"\n{sum(results)} of {len(results)} checks pass")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
