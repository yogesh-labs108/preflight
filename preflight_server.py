#!/usr/bin/env python3
"""Preflight web app. Give it a folder of chapters, get the review board.

    python3 preflight_server.py            -> http://127.0.0.1:8789
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / ".venv" / "bin" / "python"
if VENV_PY.exists() and Path(sys.executable).resolve() != VENV_PY.resolve():
    os.execv(str(VENV_PY), [str(VENV_PY), *sys.argv])

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402
import uvicorn  # noqa: E402

from preflight import analyze, config, report as report_md  # noqa: E402

app = FastAPI(title="Preflight")


class AnalyzeRequest(BaseModel):
    folder: str = ""
    target_minutes: float = config.DEFAULT_TARGET_MINUTES
    wpm: int = config.DEFAULT_WPM


def _slug(path):
    name = path.parent.name if path.name.lower() == "chapters" else path.name
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "novel"


def _save(report, folder):
    out_dir = config.REPORTS_DIR / _slug(folder)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "preflight-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "preflight-report.md").write_text(report_md.markdown(report), encoding="utf-8")
    return out_dir


@app.get("/")
def index():
    return FileResponse(config.WEB_DIR / "index.html")


@app.get("/example")
def example():
    return {"folder": str(config.EXAMPLE_CHAPTERS), "target_minutes": 1.5}


@app.get("/reports")
def list_reports():
    items = []
    if config.REPORTS_DIR.exists():
        for path in sorted(config.REPORTS_DIR.glob("*/preflight-report.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                continue
            items.append({"slug": path.parent.name, "title": data.get("title", path.parent.name),
                          "verdict": data.get("verdict", ""), "chapters": data.get("meta", {}).get("chapters_analyzed")})
    return items


@app.get("/reports/{slug}")
def get_report(slug: str):
    if not re.fullmatch(r"[a-z0-9-]+", slug):
        raise HTTPException(status_code=404)
    path = config.REPORTS_DIR / slug / "preflight-report.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No saved report with that name.")
    return FileResponse(path, media_type="application/json")


@app.post("/analyze")
def analyze_folder(request: AnalyzeRequest):
    folder = Path(request.folder.strip()).expanduser() if request.folder.strip() else config.EXAMPLE_CHAPTERS
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"No such folder: {folder}")
    try:
        report = analyze.run(folder, request.target_minutes, request.wpm)
    except SystemExit as exc:  # chapter_stats and config raise SystemExit on bad input
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    out_dir = _save(report, folder)
    report["meta"]["saved_to"] = str(out_dir)
    return JSONResponse(report)


app.mount("/static", StaticFiles(directory=str(config.WEB_DIR)), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PREFLIGHT_PORT", "8789")))
