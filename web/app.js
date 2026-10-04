(function () {
  const $ = (id) => document.getElementById(id);
  const form = $("runForm");
  const folderInput = $("folderInput");
  const minutesInput = $("minutesInput");
  const runBtn = $("runBtn");
  const exampleBtn = $("exampleBtn");
  const status = $("status");
  const board = $("board");

  let report = null;
  let activeChapter = 1;
  let activeIssue = null;

  function esc(text) {
    return String(text == null ? "" : text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function showStatus(text, isError) {
    status.hidden = false;
    status.textContent = text;
    status.classList.toggle("is-error", !!isError);
  }

  function riskWord(score) {
    return score >= 67 ? "high" : score >= 34 ? "medium" : "low";
  }

  // --- normalise text so model quotes can be found in the chapter body
  function norm(text) {
    return String(text).replace(/[“”]/g, '"').replace(/[‘’]/g, "'").replace(/[—–]/g, "-").replace(/\s+/g, " ").trim().toLowerCase();
  }

  // Find `quote` inside `body` tolerating quote/dash/whitespace differences;
  // returns [start, end] in body coordinates or null.
  function locate(body, quote) {
    const q = norm(quote);
    if (!q) return null;
    const map = [];
    let n = "";
    let lastSpace = false;
    for (let i = 0; i < body.length; i++) {
      let ch = body[i];
      if (/[“”]/.test(ch)) ch = '"';
      else if (/[‘’]/.test(ch)) ch = "'";
      else if (/[—–]/.test(ch)) ch = "-";
      if (/\s/.test(ch)) {
        if (lastSpace || n === "") continue;
        ch = " ";
        lastSpace = true;
      } else {
        lastSpace = false;
      }
      n += ch.toLowerCase();
      map.push(i);
    }
    const at = n.indexOf(q);
    if (at === -1) return null;
    return [map[at], map[at + q.length - 1] + 1];
  }

  // --- render pieces
  function renderNovel() {
    const meta = report.meta;
    $("novelTitle").textContent = report.title;
    $("cover").textContent = report.title;
    const verdict = (report.verdict || "").toUpperCase();
    const v = $("verdict");
    v.textContent = verdict;
    v.className = "verdict verdict--" + verdict.toLowerCase();
    $("novelMeta").textContent = report.verdict_reason || "";
    $("novelCounts").textContent =
      meta.chapters_analyzed + " chapters analyzed • " + meta.proposed_episodes + " proposed audio episodes";
    $("promise").innerHTML = "<b>Promise from chapter 1:</b> " + esc(report.promise);
  }

  function renderChart() {
    const chart = $("chart");
    chart.innerHTML = "";
    (report.episodes || []).forEach((ep) => {
      const score = Math.max(0, Math.min(100, Number(ep.risk) || 0));
      const bar = document.createElement("div");
      bar.className = "bar" + (score >= 67 ? " bar--high" : "");
      bar.title = "Episode " + ep.number + " — " + riskWord(score) + " risk (" + score + "). " + (ep.risk_reason || "");
      bar.innerHTML =
        '<span class="bar__value">' + score + "</span>" +
        '<div class="bar__fill" style="height:' + Math.max(4, score * 0.8) + '%"></div>' +
        '<span class="bar__label">E' + esc(ep.number) + "</span>";
      chart.appendChild(bar);
    });
  }

  function renderChapterTabs() {
    const tabs = $("chapterTabs");
    tabs.innerHTML = "";
    report.chapters.forEach((ch) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chapter-tab" + (ch.number === activeChapter ? " is-active" : "");
      b.textContent = "Ch " + ch.number;
      b.title = ch.title + " — " + ch.words + " words, " + ch.minutes + " min";
      b.onclick = () => { activeChapter = ch.number; activeIssue = null; renderManuscript(); renderChapterTabs(); renderIssues(); renderEvidence(); };
      tabs.appendChild(b);
    });
  }

  function renderManuscript() {
    const chapter = report.chapters.find((c) => c.number === activeChapter) || report.chapters[0];
    const body = chapter.body;
    const spans = [];
    (report.issues || []).forEach((issue) => {
      if (issue.chapter !== chapter.number) return;
      const pos = locate(body, issue.quote);
      if (pos) spans.push({ start: pos[0], end: pos[1], id: issue.id });
    });
    spans.sort((a, b) => a.start - b.start);

    let html = "";
    let cursor = 0;
    spans.forEach((s) => {
      if (s.start < cursor) return; // overlapping, skip
      html += esc(body.slice(cursor, s.start));
      html += '<mark data-issue="' + s.id + '"' + (s.id === activeIssue ? ' class="is-active"' : "") + ">" +
        esc(body.slice(s.start, s.end)) + "</mark>";
      cursor = s.end;
    });
    html += esc(body.slice(cursor));

    const paragraphs = html.split(/\n\s*\n/).map((p) => "<p>" + p.replace(/\n/g, "<br>") + "</p>").join("");
    $("manuscript").innerHTML =
      '<div class="manuscript__chapter">Chapter ' + chapter.number + " — " + esc(chapter.title) +
      " · " + chapter.words + " words · " + chapter.minutes + " min</div>" + paragraphs;

    const active = $("manuscript").querySelector("mark.is-active");
    if (active) active.scrollIntoView({ block: "center", behavior: "smooth" });
  }

  function selectIssue(issue) {
    activeIssue = issue.id;
    activeChapter = issue.chapter || activeChapter;
    renderChapterTabs();
    renderManuscript();
    renderIssues();
    renderEvidence();
  }

  function renderIssues() {
    const list = $("issues");
    list.innerHTML = "";
    if (!(report.issues || []).length) {
      list.innerHTML = '<li class="empty">No causes proven with a quoted line.</li>';
      return;
    }
    report.issues.forEach((issue) => {
      const li = document.createElement("li");
      li.className = "issue issue--" + (issue.severity || "medium") + (issue.id === activeIssue ? " is-active" : "");
      li.innerHTML =
        '<span class="issue__dot"></span>' +
        '<span class="issue__label">' + esc(issue.label || issue.cause) + "</span>" +
        '<span class="issue__where">ch ' + esc(issue.chapter) + (issue.episode ? " · ep " + esc(issue.episode) : "") + "</span>" +
        '<span class="issue__id">Issue #' + esc(issue.id) + "</span>";
      li.onclick = () => selectIssue(issue);
      list.appendChild(li);
    });
  }

  function renderRecs() {
    const list = $("recs");
    list.innerHTML = "";
    (report.issues || []).forEach((issue) => {
      const li = document.createElement("li");
      li.className = "rec";
      li.innerHTML = '<span class="rec__id">' + esc(issue.id) + '</span><span class="rec__text">' + esc(issue.recommendation) + "</span>";
      li.onclick = () => selectIssue(issue);
      list.appendChild(li);
    });
  }

  function renderPlan() {
    const list = $("plan");
    list.innerHTML = "";
    (report.episodes || []).forEach((ep) => {
      const li = document.createElement("li");
      const chapters = String(ep.chapters || "").replace(/^ch\.?\s*/i, "");
      const ending = String(ep.ends_on || "").trim().replace(/^["“](.*)["”]$/s, "$1");
      const change = ep.change && !/^none\b/i.test(ep.change) ? '<span class="plan__change">Change: ' + esc(ep.change) + "</span>" : "";
      li.innerHTML =
        "<b>Episode " + esc(ep.number) + ":</b> Chapters " + esc(chapters) +
        ' (Ending: <i>"' + esc(ending) + '"</i>' + (ep.ends_on_verified === false ? " · rewritten line" : "") + ")" +
        '<span class="plan__risk">' + riskWord(Number(ep.risk) || 0) + " risk</span>" + change;
      list.appendChild(li);
    });
  }

  function renderEvidence() {
    const box = $("evidence");
    box.innerHTML = "";
    (report.issues || []).forEach((issue) => {
      const div = document.createElement("div");
      div.className = "evidence__item" + (issue.id === activeIssue ? " is-active" : "");
      div.innerHTML =
        '<div class="evidence__head">Source Evidence for ' + esc(issue.id) + " · chapter " + esc(issue.chapter) + "</div>" +
        '<div class="evidence__quote">"' + esc(String(issue.quote || "").trim().replace(/^["“](.*)["”]$/s, "$1")) + '"</div>' +
        '<div class="evidence__why">' + esc(issue.why) + "</div>" +
        (issue.verified ? "" : '<div class="evidence__warn">This quote was not found word for word in the source text. Check it before acting on it.</div>');
      div.onclick = () => selectIssue(issue);
      box.appendChild(div);
    });
    const active = box.querySelector(".is-active");
    if (active) active.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function renderRewrites() {
    const box = $("rewrites");
    box.innerHTML = "";
    if (!(report.rewrites || []).length) {
      box.innerHTML = '<p class="empty">The plan keeps the novel\'s own openings and endings.</p>';
    }
    (report.rewrites || []).forEach((rw) => {
      const div = document.createElement("div");
      div.className = "rewrite";
      div.innerHTML = '<div class="rewrite__head">Episode ' + esc(rw.episode) + " · " + esc(rw.part) + "</div>" +
        '<div class="rewrite__text">' + esc(rw.text) + "</div>";
      box.appendChild(div);
    });

    const after = $("after");
    after.innerHTML = "";
    (report.after_launch || []).forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      after.appendChild(li);
    });
    const m = report.meta;
    $("runMeta").textContent =
      m.model + " (effort " + m.effort + ") · " + m.seconds + "s · " +
      m.input_tokens.toLocaleString() + " tokens in / " + m.output_tokens.toLocaleString() + " out" +
      (m.saved_to ? " · saved to " + m.saved_to : "");
  }

  function render() {
    activeChapter = (report.issues && report.issues[0] && report.issues[0].chapter) || 1;
    activeIssue = report.issues && report.issues[0] ? report.issues[0].id : null;
    renderNovel();
    renderChart();
    renderChapterTabs();
    renderManuscript();
    renderIssues();
    renderRecs();
    renderPlan();
    renderEvidence();
    renderRewrites();
    board.hidden = false;
  }

  // --- actions
  async function run() {
    runBtn.disabled = true;
    exampleBtn.disabled = true;
    board.hidden = true;
    showStatus("Measuring chapters and reading the novel. This usually takes 30–90 seconds…");
    try {
      const res = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder: folderInput.value, target_minutes: Number(minutesInput.value) || 12 }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || res.statusText);
      report = data;
      status.hidden = true;
      render();
    } catch (err) {
      showStatus(err.message || String(err), true);
    } finally {
      runBtn.disabled = false;
      exampleBtn.disabled = false;
    }
  }

  async function loadSaved(slug) {
    const res = await fetch("/reports/" + encodeURIComponent(slug));
    if (!res.ok) { showStatus("Could not open that saved report.", true); return; }
    report = await res.json();
    folderInput.value = report.meta.folder || "";
    minutesInput.value = report.meta.target_minutes || 12;
    status.hidden = true;
    render();
  }

  async function listSaved() {
    try {
      const res = await fetch("/reports");
      const items = await res.json();
      if (!items.length) return;
      const select = $("savedSelect");
      items.forEach((item) => {
        const opt = document.createElement("option");
        opt.value = item.slug;
        opt.textContent = item.title + (item.verdict ? " — " + item.verdict : "") + (item.chapters ? " (" + item.chapters + " ch)" : "");
        select.appendChild(opt);
      });
      $("savedField").hidden = false;
      select.addEventListener("change", () => { if (select.value) loadSaved(select.value); });
      const wanted = new URLSearchParams(location.search).get("report");
      if (wanted && items.some((i) => i.slug === wanted)) { select.value = wanted; loadSaved(wanted); }
    } catch (_) { /* no saved reports */ }
  }

  form.addEventListener("submit", (e) => { e.preventDefault(); run(); });
  if (new URLSearchParams(location.search).get("shot")) document.body.classList.add("is-shot");
  listSaved();
  exampleBtn.addEventListener("click", async () => {
    const res = await fetch("/example");
    const data = await res.json();
    folderInput.value = data.folder;
    minutesInput.value = data.target_minutes;
    run();
  });
})();
