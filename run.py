#!/usr/bin/env python3
"""Run Preflight from the terminal and print the Markdown report.

    python3 run.py examples/the-ninth-furnace/chapters --target-minutes 1.5
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / ".venv" / "bin" / "python"
if VENV_PY.exists() and Path(sys.executable).resolve() != VENV_PY.resolve():
    os.execv(str(VENV_PY), [str(VENV_PY), *sys.argv])

from preflight import analyze, config, report as report_md  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--target-minutes", type=float, default=config.DEFAULT_TARGET_MINUTES)
    parser.add_argument("--wpm", type=int, default=config.DEFAULT_WPM)
    parser.add_argument("--json", action="store_true", help="print the structured report instead")
    args = parser.parse_args()

    report = analyze.run(args.folder, args.target_minutes, args.wpm)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        sys.stdout.write(report_md.markdown(report))


if __name__ == "__main__":
    main()
