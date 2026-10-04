---
name: preflight
description: >-
  Reads a web novel before it is turned into an audio series, predicts which
  episodes will lose listeners and why, and plans how chapters become episodes.
  Use when the user says "run @preflight" on a folder of novel chapters.
disable-model-invocation: true
---

# Preflight

Retention numbers only arrive after a show is recorded and launched. Preflight reads the source novel first and says where the audio version will lose listeners, so the fix happens in the adaptation plan instead of in a rework.

## Input

A folder of chapters, one `.md` or `.txt` file each, named so they sort in order (`ch001.md`, `ch002.md`, ...). The first 30 chapters are enough.

## Steps

1. Measure the chapters and draft a split:
   ```bash
   python3 /Users/yogesh.thambidurai/Downloads/preflight/scripts/chapter_stats.py <chapters folder>
   ```
   Default episode length is 12 minutes at 150 words per minute. Use `--target-minutes` if the user gives another length.
2. Read chapter 1 and write the promise it makes to the listener in one sentence.
3. Read the opening run: episode 1, then the next episodes up to the first real payoff. That is the stretch where a new listener decides whether to stay.
4. Diagnose each draft episode against [rubric.md](rubric.md). The script's flags (many new names or terms, recap openings, the last line of each chapter) are leads to check, not verdicts. Keep only causes you can prove with a quoted line.
5. Fix the plan. Move episode boundaries so each episode ends on a line that opens a question, cut or compress what the rubric flags, and merge or reorder chapters where the promise waits too long.
6. Write the report below and save it as `preflight-report.md` next to the chapters folder.

## Report

```markdown
# Preflight: <novel>

**Verdict:** GO / ADAPT / HOLD, and one sentence on why
**The promise from chapter 1:** <one sentence>

## Predicted drop-off
| Stretch | What to check after launch | Risk | Cause |
|---|---|---|---|
| The hook (episode 1) | listeners who finish it and start the next | low / medium / high | <cause, or none> |
| The promise (the episodes right after) | listeners still there once the opening bet should have paid off | ... | ... |
| The habit (once the show should have them) | listeners who keep coming back on their own | ... | ... |

## Why
1. **<Cause>**, chapter <n>. "<quoted line>" <why this loses a listener>
(two to five causes, worst first)

## Episode plan
| Episode | Source | Ends on | Change |
|---|---|---|---|
| 1 | ch 1 | "<last line>" | <none, or what changed> |

## Rewrites
The rewritten opening or ending for each episode the plan changes the most. Write it in full, in the novel's own voice and names.

## After launch
Which listener behaviour confirms or disproves each prediction, and what result would mean the plan was wrong.
```

Rules:
- ADAPT means the plan fixes the risks. HOLD means the risk is in the story itself, such as a promise the novel never pays off, and an adaptation cannot fix it.
- Risk levels are predictions. Say so, and never present them as measured retention.
- Do not invent characters, events, or numbers. Rewrites rearrange and compress what the novel already contains.
