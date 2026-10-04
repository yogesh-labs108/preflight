import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
WEB_DIR = ROOT / "web"
REPORTS_DIR = ROOT / "reports"
EXAMPLE_CHAPTERS = ROOT / "examples" / "the-ninth-furnace" / "chapters"
RUBRIC_FILE = ROOT / "rubric.md"

# The key is looked for here, in order. The last entry is the sibling
# utility-bill-qa checkout, so one key serves both tools on this machine.
ENV_FILES = [
    ROOT / ".env",
    Path.home() / "Desktop" / "utility-bill-qa" / ".env",
]


def _load_env():
    for env_file in ENV_FILES:
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_env()

MODEL = os.environ.get("PREFLIGHT_MODEL", os.environ.get("BILLQA_MODEL", "claude-sonnet-5"))
EFFORT = os.environ.get("PREFLIGHT_EFFORT", "medium")
DEFAULT_TARGET_MINUTES = 12
DEFAULT_WPM = 150


def api_key():
    value = os.environ.get("ANTHROPIC_API_KEY")
    if not value:
        raise SystemExit(
            "Missing ANTHROPIC_API_KEY. Put it in "
            + " or ".join(str(p) for p in ENV_FILES)
        )
    return value
