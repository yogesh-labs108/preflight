# Preflight

An AI skill for Cursor and Claude that reads a web novel before it is made into an audio series. It predicts which episodes will lose listeners and why, then plans how the chapters become episodes.

Retention numbers like %H1, %H5, and %H10 only exist after a show has been recorded, voiced, and launched. By then the listeners who left are gone, and fixing the show means a rework. How popular a novel is with readers does not predict how it holds listeners. Preflight moves the check before production. It reads the chapters the way a listener will hear them, finds the passages that work on a page but lose people in audio, and writes an episode plan with each boundary on a cliffhanger.

## Use it

```
run @preflight on examples/the-ninth-furnace/chapters
```

It writes `preflight-report.md`. [The sample report](examples/the-ninth-furnace/preflight-report.md) is the output for a six-chapter example novel. It predicts that episodes 1 to 5 as drafted would lose most listeners between episodes 2 and 5. The revenge promised in chapter 1 is summarised in one sentence four chapters later, chapter 2 is a list of 22 cultivation terms, and chapter 4 leaves out the hero entirely. It reorders the chapters, moves every episode ending onto an open question, and writes the new openings and endings.

## How it works

1. `scripts/chapter_stats.py` measures every chapter: length, minutes of audio, new names and terms, recap openings, and the last line. It drafts a split of whole chapters into episodes of the target length.
2. The model reads chapter 1 and states the promise it makes to the listener.
3. It reads the chapters behind episodes 1 to 10 and diagnoses them against [rubric.md](rubric.md), ten reasons a novel loses listeners in audio. Each cause it keeps has to be backed by a quoted line.
4. It fixes the plan by moving boundaries, cutting, and reordering, then writes the rewritten lines and says which %H number will show whether the prediction was right.

The measuring is plain code, so the same novel always produces the same draft. The model does the reading, the judgement, and the rewriting.

## Install

```bash
mkdir -p ~/.cursor/skills/preflight
cp SKILL.md rubric.md ~/.cursor/skills/preflight/
```

The example novel is fictional, and its chapters are cut to a few hundred words. Its draft uses `--target-minutes 1.5`; real chapters use the default of 12.

```bash
cd scripts && python3 -m unittest
```
