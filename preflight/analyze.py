"""Measure the chapters with the script, then have the model read them.

The script decides lengths, the draft split, new-name counts, recap openings
and last lines. The model decides the promise, the causes, the risk per
episode, the plan and the rewrites. Every cause must quote a line that is
actually in the chapters; quotes that are not found are marked, not hidden.
"""

import json
import re
import sys
import time
from pathlib import Path

from anthropic import Anthropic

from . import config

sys.path.insert(0, str(config.SCRIPTS_DIR))
import chapter_stats  # noqa: E402

_client = None

REPORT_SHAPE = """
{
  "title": "the novel's title (use the NOVEL line given, not a chapter title)",
  "verdict": "GO | ADAPT | HOLD",
  "verdict_reason": "one sentence",
  "promise": "the promise chapter 1 makes to the listener, one sentence",
  "issues": [
    {
      "id": "EA001",
      "cause": "one of the rubric headings, e.g. Closed ending",
      "label": "editorial category in 2-4 words, e.g. Slow Opening, Pacing Concern, Weak Episode Ending, Exposition Dump, Name Flood, Hero Missing",
      "chapter": 2,
      "episode": 2,
      "severity": "low | medium | high",
      "quote": "a line copied exactly from the chapter text",
      "why": "one or two sentences on why this loses a listener",
      "recommendation": "one or two sentences on the fix"
    }
  ],
  "episodes": [
    {
      "number": 1,
      "chapters": "1",
      "ends_on": "the line this episode should end on, copied exactly from the chapters (from a rewrite only if no existing line works)",
      "change": "none, or what changed from the draft split",
      "risk": 20,
      "risk_reason": "one sentence"
    }
  ],
  "rewrites": [
    {"episode": 2, "part": "opening | ending", "text": "the rewritten passage in full"}
  ],
  "after_launch": ["one sentence per prediction on what listener behaviour confirms or disproves it"]
}
""".strip()


def _get_client():
    global _client
    if _client is None:
        _client = Anthropic(api_key=config.api_key())
    return _client


def measure(folder, target_minutes, wpm):
    files = chapter_stats.chapter_files(folder)
    chapters = chapter_stats.measure(files, wpm)
    for chapter, path in zip(chapters, files):
        chapter["body"] = chapter_stats.body_of(path.read_text())
    episodes = chapter_stats.draft_episodes(chapters, target_minutes)
    stats_text = chapter_stats.report(chapters, episodes, target_minutes, wpm)
    return chapters, episodes, stats_text


def _system_prompt(rubric):
    return (
        "You are Preflight, a pre-production story editor for serialized audio. "
        "You read a web novel before it is recorded and predict where the audio "
        "version will lose listeners.\n\n"
        "Read the chapters as a listener will hear them. Use the rubric below. "
        "The script's measurements are leads to check, not verdicts. Keep only "
        "causes you can prove with a line quoted exactly from the chapter text. "
        "Risk numbers are predictions from the text, never measured retention. "
        "Do not invent characters, events or numbers. Rewrites rearrange and "
        "compress what the novel already contains, in its own voice and names.\n\n"
        "GO means the draft split can be recorded as is. ADAPT means the plan "
        "fixes the risks. HOLD means the risk is in the story itself and an "
        "adaptation cannot fix it.\n\n"
        "Return one JSON object and nothing else, in exactly this shape:\n\n"
        f"{REPORT_SHAPE}\n\n"
        "Issue ids run EA001, EA002, ... worst first. Give every episode in your "
        "plan a risk from 0 to 100, where 0 means no listener is expected to "
        "leave because of the text and 100 means most will.\n\n"
        f"RUBRIC\n------\n{rubric}"
    )


def _novel_title(folder):
    name = folder.parent.name if folder.name.lower() == "chapters" else folder.name
    return re.sub(r"[-_]+", " ", name).strip().title()


def _user_prompt(chapters, stats_text, target_minutes, title):
    parts = [
        f"NOVEL: {title}",
        f"TARGET EPISODE LENGTH: {target_minutes:g} minutes\n",
        "SCRIPT MEASUREMENTS\n-------------------\n" + stats_text,
        "\nCHAPTERS\n--------",
    ]
    for chapter in chapters:
        parts.append(f"\n### Chapter {chapter['number']} — {chapter['title']}\n\n{chapter['body']}")
    parts.append("\nWrite the Preflight report as the JSON object described.")
    return "\n".join(parts)


def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The model did not return a JSON object.")
    return json.loads(text[start:end + 1])


def _normalise(text):
    text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    text = text.replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", text).strip().lower()


def _verify_quotes(report, chapters):
    """Mark whether each quoted line is really in the chapter it cites."""
    bodies = {c["number"]: _normalise(c["body"]) for c in chapters}
    everything = " ".join(bodies.values())
    for issue in report.get("issues", []):
        quote = _normalise(issue.get("quote", ""))
        chapter = issue.get("chapter")
        in_cited = bool(quote) and quote in bodies.get(chapter, "")
        issue["verified"] = in_cited or (bool(quote) and quote in everything)
        if issue["verified"] and not in_cited:
            for number, body in bodies.items():
                if quote in body:
                    issue["chapter"] = number
                    break
    for episode in report.get("episodes", []):
        ends = _normalise(episode.get("ends_on", ""))
        episode["ends_on_verified"] = bool(ends) and ends in everything
    return report


def run(folder, target_minutes=None, wpm=None):
    target_minutes = target_minutes or config.DEFAULT_TARGET_MINUTES
    wpm = wpm or config.DEFAULT_WPM
    folder = Path(folder)
    chapters, draft, stats_text = measure(folder, target_minutes, wpm)
    rubric = config.RUBRIC_FILE.read_text(encoding="utf-8")

    started = time.monotonic()
    kwargs = dict(
        model=config.MODEL,
        max_tokens=16000,
        system=[{"type": "text", "text": _system_prompt(rubric),
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": _user_prompt(chapters, stats_text, target_minutes, _novel_title(folder))}],
    )
    client = _get_client()
    try:
        with client.messages.stream(output_config={"effort": config.EFFORT}, **kwargs) as stream:
            message = stream.get_final_message()
    except TypeError:
        with client.messages.stream(**kwargs) as stream:
            message = stream.get_final_message()

    text = "".join(block.text for block in message.content if block.type == "text")
    report = _verify_quotes(_extract_json(text), chapters)

    usage = message.usage
    report["meta"] = {
        "folder": str(folder),
        "title": report.get("title") or _novel_title(folder),
        "chapters_analyzed": len(chapters),
        "draft_episodes": len(draft),
        "proposed_episodes": len(report.get("episodes", [])),
        "target_minutes": target_minutes,
        "wpm": wpm,
        "model": config.MODEL,
        "effort": config.EFFORT,
        "seconds": round(time.monotonic() - started, 1),
        "input_tokens": (usage.input_tokens or 0)
                        + (getattr(usage, "cache_read_input_tokens", 0) or 0)
                        + (getattr(usage, "cache_creation_input_tokens", 0) or 0),
        "output_tokens": usage.output_tokens or 0,
    }
    report["title"] = report["meta"]["title"]
    report["chapters"] = [
        {"number": c["number"], "title": c["title"], "words": c["words"],
         "minutes": round(c["minutes"], 1), "new_names": c["new_names"],
         "recap": c["recap"], "last_line": c["last_line"], "body": c["body"]}
        for c in chapters
    ]
    report["draft"] = [
        {"number": n, "chapters": [c["number"] for c in group],
         "minutes": round(sum(c["minutes"] for c in group), 1)}
        for n, group in enumerate(draft, start=1)
    ]
    report["stats_text"] = stats_text
    return report
