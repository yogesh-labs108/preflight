# Preflight

An AI check that reads a web novel before it is made into an audio series. It predicts which episodes will lose listeners and why, quotes the passage that causes it, plans how the chapters become episodes, and rewrites the weak openings and endings.

A show's listener numbers only exist after it has been recorded, voiced, and released. By then the people who left are gone, and fixing it means a rework. How popular a novel is with readers does not predict how it holds listeners. Preflight moves the check before production. It reads the chapters the way a listener will hear them, finds the passages that work on a page but lose people in audio, and writes an episode plan with each boundary on a cliffhanger.

It comes in two forms that share the same rubric and the same measuring script:

- a **Cursor skill** (`SKILL.md`), run as `run @preflight on <chapters folder>`, which writes `preflight-report.md`
- a **web app** (`preflight_server.py`), which shows the same findings as a review board

## The web app

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env            # add your ANTHROPIC_API_KEY
python3 preflight_server.py     # http://127.0.0.1:8789
```

Paste the path to a folder of chapters, set the episode length, and run. The board shows:

- the novel, a GO / ADAPT / HOLD verdict, and the promise chapter 1 makes to the listener
- **Predicted Engagement Risks**, one bar per proposed episode (model estimates, not listener data)
- **Source Manuscript**, with every quoted passage highlighted in the chapter it came from
- **Engagement Analysis**, the causes found, numbered EA001, EA002, ... worst first
- **Editorial Recommendations**, the fix for each cause
- **Episode Planner**, which chapters go into each episode and the line each one ends on
- **Source Evidence**, the exact line behind each cause and why it loses a listener
- **Rewrites** of the openings and endings the plan changes, and what to check **After Launch**

Every report is saved under `reports/<novel>/` as JSON and Markdown, and can be reopened from the "Saved reports" menu without running the model again. "Use example novel" runs the bundled six-chapter sample.

From the terminal:

```bash
python3 run.py examples/the-ninth-furnace/chapters --target-minutes 1.5
```

## How it works

1. `scripts/chapter_stats.py` measures every chapter: length, minutes of audio, new names and terms, recap openings, and the last line. It drafts a split of whole chapters into episodes of the target length. This is plain code, so the same novel always produces the same draft.
2. `preflight/analyze.py` sends the measurements, the chapters, and [rubric.md](rubric.md) (ten reasons a novel loses listeners in audio) to Claude, and asks for a structured report: the promise, the causes, a risk per episode, the plan, the rewrites.
3. Every quoted line is checked against the chapter text. A quote that is not found word for word is shown with a warning instead of being hidden. Episode endings that come from a rewrite rather than the novel are marked.
4. `preflight/report.py` renders the Markdown report in the layout from `SKILL.md`; `web/` renders the board.

The model does the reading, the judgement, and the rewriting. The script does the counting, and the checker keeps the model honest.

## Install the skill

```bash
mkdir -p ~/.cursor/skills/preflight
cp SKILL.md rubric.md ~/.cursor/skills/preflight/
```

The example novel is fictional, and its chapters are cut to a few hundred words. Its draft uses `--target-minutes 1.5`; real chapters use the default of 12.

```bash
cd scripts && python3 -m unittest
```
