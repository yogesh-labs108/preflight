"""Render the structured report as the Markdown laid out in SKILL.md."""


def _risk_word(score):
    if score >= 67:
        return "high"
    if score >= 34:
        return "medium"
    return "low"


def markdown(report):
    meta = report["meta"]
    issues = report.get("issues", [])
    episodes = report.get("episodes", [])

    lines = [
        f"# Preflight: {report['title']}",
        "",
        f"**Verdict:** {report.get('verdict', '')}. {report.get('verdict_reason', '')}".rstrip(),
        f"**The promise from chapter 1:** {report.get('promise', '')}",
        "",
        "## Predicted drop-off",
        "",
        "These are predictions from the text, not measured retention.",
        "",
        "| Episode | Source | Risk | Why |",
        "|---|---|---|---|",
    ]
    for ep in episodes:
        lines.append(
            f"| {ep.get('number')} | ch {ep.get('chapters')} | "
            f"{_risk_word(ep.get('risk', 0))} ({ep.get('risk', 0)}) | {ep.get('risk_reason', '')} |"
        )

    lines += ["", "## Why", ""]
    for n, issue in enumerate(issues, start=1):
        flag = "" if issue.get("verified") else " _(quote not found in the source text)_"
        lines.append(
            f"{n}. **{issue.get('cause', issue.get('label', ''))}**, chapter {issue.get('chapter')}. "
            f"\"{issue.get('quote', '')}\" {issue.get('why', '')}{flag}"
        )
        lines.append(f"   Fix: {issue.get('recommendation', '')}")
        lines.append("")

    lines += ["## Episode plan", "", "| Episode | Source | Ends on | Change |", "|---|---|---|---|"]
    for ep in episodes:
        lines.append(
            f"| {ep.get('number')} | ch {ep.get('chapters')} | \"{ep.get('ends_on', '')}\" | {ep.get('change', 'none')} |"
        )

    rewrites = report.get("rewrites", [])
    if rewrites:
        lines += ["", "## Rewrites", ""]
        for rewrite in rewrites:
            lines += [f"### Episode {rewrite.get('episode')}, {rewrite.get('part')}", "", rewrite.get("text", ""), ""]

    after = report.get("after_launch", [])
    if after:
        lines += ["## After launch", ""]
        lines += [f"- {item}" for item in after]

    lines += [
        "",
        "---",
        f"{meta['chapters_analyzed']} chapters analysed, {meta['proposed_episodes']} episodes proposed. "
        f"{meta['model']} (effort {meta['effort']}), {meta['seconds']}s, "
        f"{meta['input_tokens']:,} in / {meta['output_tokens']:,} out.",
    ]
    return "\n".join(lines) + "\n"
