#!/usr/bin/env python3
"""Measure a novel's chapters for audio and draft a chapter-to-episode split.

Usage: chapter_stats.py <chapters folder> [--target-minutes 12] [--wpm 150]
"""

import argparse
import re
import sys
from pathlib import Path

RECAP_PHRASES = ("as we know", "previously", "as mentioned", "to recap", "as you may recall")
TITLE_WORDS = {
    "Elder", "Senior", "Junior", "Brother", "Sister", "Steward", "Disciple", "Master",
    "Sect", "Grand", "Lord", "Lady", "Young", "Patriarch", "Hall", "Peak", "Mr", "Mrs",
}
SENTENCE_END = re.compile(r"[.!?\"'”’]\s*$")
WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")


def chapter_files(folder):
    files = sorted(
        path for path in Path(folder).iterdir()
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}
    )
    if not files:
        raise SystemExit("no .md or .txt chapters in %s" % folder)
    return files


def body_of(text):
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    return "\n".join(lines).strip()


def title_of(text, fallback):
    for line in text.splitlines():
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            return re.sub(r"^chapter\s+\d+\s*[—:-]\s*", "", title, flags=re.IGNORECASE)
    return fallback


def capitalised_mid_sentence(body):
    """Capitalised words that are not at the start of a sentence or line."""
    found = []
    for paragraph in body.splitlines():
        previous = ""
        for match in WORD.finditer(paragraph):
            word = re.sub(r"['’]s$", "", match.group(0).strip("'’"))
            before = paragraph[:match.start()]
            starts_sentence = previous == "" or bool(SENTENCE_END.search(before))
            is_pronoun = word == "I" or word.startswith(("I'", "I’"))
            if (word[:1].isupper() and not starts_sentence and not is_pronoun
                    and word not in TITLE_WORDS and len(word) > 1):
                found.append(word)
            previous = word
    return found


def measure(files, wpm):
    seen = set()
    chapters = []
    for number, path in enumerate(files, start=1):
        text = path.read_text()
        body = body_of(text)
        words = len(WORD.findall(body))
        names = []
        for name in capitalised_mid_sentence(body):
            if name not in seen:
                seen.add(name)
                names.append(name)
        paragraphs = [part.strip() for part in body.split("\n\n") if part.strip()]
        opening = paragraphs[0].lower() if paragraphs else ""
        chapters.append({
            "number": number,
            "file": path.name,
            "title": title_of(text, path.stem),
            "words": words,
            "minutes": words / wpm,
            "new_names": names,
            "recap": any(phrase in opening for phrase in RECAP_PHRASES),
            "last_line": paragraphs[-1] if paragraphs else "",
        })
    return chapters


def draft_episodes(chapters, target_minutes):
    """Group whole chapters into episodes near the target length."""
    episodes = []
    current = []
    minutes = 0.0
    for chapter in chapters:
        would_be = minutes + chapter["minutes"]
        if current and would_be > target_minutes * 1.5:
            episodes.append(current)
            current, minutes = [], 0.0
        current.append(chapter)
        minutes += chapter["minutes"]
        if minutes >= target_minutes * 0.85:
            episodes.append(current)
            current, minutes = [], 0.0
    if current:
        episodes.append(current)
    return episodes


def report(chapters, episodes, target_minutes, wpm):
    out = ["CHAPTERS (%d, at %d words per minute)" % (len(chapters), wpm), ""]
    for chapter in chapters:
        flags = []
        if len(chapter["new_names"]) >= 4:
            flags.append("%d new names or terms" % len(chapter["new_names"]))
        if chapter["recap"]:
            flags.append("opens with a recap")
        out.append("ch %-3d %-30s %5d words  %4.1f min  %s"
                   % (chapter["number"], chapter["title"][:30], chapter["words"],
                      chapter["minutes"], "; ".join(flags)))
        if chapter["new_names"]:
            out.append("       new names or terms: %s" % ", ".join(chapter["new_names"]))
        out.append("       ends: %s" % chapter["last_line"].replace("\n", " ")[:140])
    out += ["", "DRAFT EPISODES (target %g min, whole chapters only)" % target_minutes, ""]
    for number, group in enumerate(episodes, start=1):
        minutes = sum(chapter["minutes"] for chapter in group)
        span = ", ".join(str(chapter["number"]) for chapter in group)
        out.append("ep %-3d chapters %-12s %4.1f min  ends on ch %d" % (number, span, minutes, group[-1]["number"]))
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--target-minutes", type=float, default=12)
    parser.add_argument("--wpm", type=int, default=150)
    args = parser.parse_args()
    if not Path(args.folder).is_dir():
        raise SystemExit("no such folder: %s" % args.folder)
    chapters = measure(chapter_files(args.folder), args.wpm)
    episodes = draft_episodes(chapters, args.target_minutes)
    sys.stdout.write(report(chapters, episodes, args.target_minutes, args.wpm))


if __name__ == "__main__":
    main()
