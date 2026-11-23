/* 野生 AI 雷达 · 前端交互逻辑 (Guided by antialgorithm, 零外部框架，全字段转义) */
(function () {
  "use strict";

  const DATA = window.RADAR || {};
  const CAT_META = {
    all: { label: "全部", stamp: "ALL" },
    play: { label: "整活 / 好玩", stamp: "整活·PLAY" },
    bench: { label: "野生评测", stamp: "野测·BENCH" },
    tool: { label: "开源工具", stamp: "工具·TOOL" },
    talk: { label: "社区论战", stamp: "论战·TALK" },
  };

  let state = {
    cat: "all",
    region: "ALL",
    sort: "pick",
    query: "",
    limit: 24,
    classicIdx: 0,
    compareMode: "split", // "split" | "flash" | "pro"
  };

  function esc(str) {
    return String(str == null ? "" : str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function pad2(n) {
    return String(n).padStart(2, "0");
  }

  function fmtDate(isoStr) {
    if (!isoStr) return "";
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return String(isoStr).slice(0, 10);
    const now = new Date();
    const diffH = (now - d) / 3600000;
    if (diffH >= 0 && diffH < 1) return "刚刚";
    if (diffH >= 1 && diffH < 24) return Math.floor(diffH) + "h 前";
    return pad2(d.getMonth() + 1) + "-" + pad2(d.getDate());
  }

  function dayKey(isoStr) {
    if (!isoStr) return "近期";
    return String(isoStr).slice(0, 10);
  }

  function toast(msg) {
    const el = document.getElementById("toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.remove("show"), 1800);
  }

  function copyText(text) {
    if (!text) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => toast("已复制 Prompt 到剪贴板"));
    } else {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
      toast("已复制 Prompt 到剪贴板");
    }
  }

  // ---------- 报头右侧：直连数据源监测表 ----------
  function renderTelemetry() {
    const updatedEl = document.getElementById("updated-text");
    const sumEl = document.getElementById("telemetry-summary");
    const gridEl = document.getElementById("telemetry-grid");

    const sources = DATA.sources || [];
    const okCount = sources.filter((s) => s.ok).length;
    updatedEl.textContent =
      "最新采集: " +
      (DATA.generated_at ? DATA.generated_at.replace("T", " ").slice(0, 16) + " UTC" : "刚刚") +
      (DATA.model ? ` · 提纯引擎: ${DATA.model}` : "");

    sumEl.textContent = `${okCount}/${sources.length} 源正常`;

    const cells = sources.map(
      (s) =>
        `<div class="tel-cell" title="${esc(s.error || s.name)}">
           <span class="tel-name">${esc(s.name)}</span>
           <span class="tel-val">${s.ok ? s.count + "条" : "ERR"}</span>
         </div>`
    );
    (DATA.unavailable || []).forEach((u) => {
      cells.push(
        `<div class="tel-cell na" title="${esc(u.reason)}">
           <span class="tel-name">${esc(u.name)}</span>
           <span class="tel-val">403反爬</span>
         </div>`
      );
    });
    gridEl.innerHTML = cells.join("");
  }

  // ---------- 01 头版简报 Poster-Scale Briefing ----------
  function renderBriefing() {
    const sec = document.getElementById("sec-briefing");
    const b = DATA.briefing;
    if (!b || !b.headline) {
      sec.hidden = true;
      return;
    }
    sec.hidden = false;

    const idToRank = {};
    (DATA.community || []).forEach((it, idx) => {
      idToRank[it.id] = pad2(idx + 1);
    });

    const cells = (b.points || [])
      .slice(0, 5)
      .map((p, i) => {
        const refs = (p.ids || [])
          .filter((id) => idToRank[id])
          .map(
            (id) =>
              `<button type="button" class="ref-jump" data-jump="${esc(id)}">#${esc(
                idToRank[id]
              )}</button>`
          )
          .join("");
        return `
          <div class="brief-cell">
            <div class="brief-idx">${pad2(i + 1)}</div>
            <div class="brief-text">${esc(p.text)}</div>
            ${refs ? `<div class="brief-refs">${refs}</div>` : ""}
          </div>
        `;
      })
      .join("");

    sec.innerHTML = `
      <div class="briefing-banner">
        <span class="sec-num">01</span>
        <span class="briefing-kicker">HEADLINE DISPATCH // 今日一手社区焦点脉络（点击 #编号 直接定位至下方原帖）</span>
        <h2 class="briefing-headline">${esc(b.headline)}</h2>
      </div>
      <div class="briefing-strip">${cells}</div>
    `;
  }

  // ---------- 02 民间必考题 · 双模型同台对决台 ----------
  function renderArena() {
    const list = DATA.classics || [];
    const tabsEl = document.getElementById("classic-tabs");
    const bodyEl = document.getElementById("arena-body");
    if (!list.length) return;

    tabsEl.innerHTML = list
      .map(
        (c, idx) =>
          `<button type="button" class="${
            state.classicIdx === idx ? "on" : ""
          }" data-classic-tab="${idx}">考题 ${pad2(idx + 1)} · ${esc(c.name.split("（")[0])}</button>`
      )
      .join("");

    document.querySelectorAll("#compare-mode button").forEach((b) => {
      b.classList.toggle("on", b.getAttribute("data-mode") === state.compareMode);
    });

    const c = list[state.classicIdx] || list[0];
    const runs = c.runs || [];
    let visibleRuns = runs;
    if (state.compareMode === "flash") {
      visibleRuns = runs.filter((r) => r.model.includes("flash"));
    } else if (state.compareMode === "pro") {
      visibleRuns = runs.filter((r) => r.model.includes("pro"));
    }
    if (!visibleRuns.length) visibleRuns = runs;

    const stagesHtml = visibleRuns
      .map(
        (r) => `
        <div class="stage-col">
          <div class="stage-col-head">
            <div>
              <span class="stage-model-tag">${esc(r.model_name || r.model)}</span>
              <span class="stage-stats"> · 实测耗时 ${esc(r.seconds)}s · ${esc(
          r.completion_tokens || "-"
        )} tokens</span>
            </div>
            <a class="stage-open" href="${esc(r.file)}" target="_blank" rel="noopener">全屏运行 ↗</a>
          </div>
          <div class="stage-viewport">
            <iframe src="${esc(r.file)}" title="${esc(c.name)} - ${esc(
          r.model_name
        )}" loading="lazy"></iframe>
          </div>
        </div>
      `
      )
      .join("");

    bodyEl.innerHTML = `
      <div class="arena-grid">
        <div class="arena-dossier">
          <div>
            <div class="dossier-en">TESTBENCH #${pad2(state.classicIdx + 1)} // ${esc(
      c.name_en || ""
    )}</div>
            <h3 class="dossier-title">${esc(c.name)}</h3>
          </div>
          <div class="dossier-block">
            <h4>考题来历</h4>
            <p>${esc(c.origin)}</p>
            ${
              c.origin_url
                ? `<a class="dossier-origin-link" href="${esc(
                    c.origin_url
                  )}" target="_blank" rel="noopener">${esc(
                    c.origin_label || c.origin_url
                  )} ↗</a>`
                : ""
            }
          </div>
          <div class="dossier-block">
            <h4>为什么极客认这道题</h4>
            <p>${esc(c.why)}</p>
          </div>
          ${
            c.look_for && c.look_for.length
              ? `<div class="dossier-block">
                   <h4>一眼判高下（观察要点）</h4>
                   <ul>${c.look_for.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>
                 </div>`
              : ""
          }
          <div class="prompt-stamp">
            <div class="prompt-stamp-head">
              <span>实测 Prompt ${c.prompt_note ? `· ${esc(c.prompt_note)}` : ""}</span>
              <button type="button" class="act-btn" data-copy="${esc(
                c.prompt
              )}">复制 Prompt</button>
            </div>
            <pre>${esc(c.prompt)}</pre>
          </div>
        </div>
        <div class="arena-stages ${visibleRuns.length === 1 ? "single" : ""}">
          ${stagesHtml}
        </div>
      </div>
    `;
  }

  // ---------- 03 一手社区情报总表 ----------
  function renderChips() {
    const items = DATA.community || [];
    const counts = { all: items.length, play: 0, bench: 0, tool: 0, talk: 0 };
    items.forEach((it) => {
      const c = it.category || "talk";
      if (counts[c] != null) counts[c]++;
    });

    const wrap = document.getElementById("cat-chips");
    wrap.innerHTML = Object.keys(CAT_META)
      .map(
        (k) =>
          `<button type="button" class="chip ${
            state.cat === k ? "on" : ""
          }" data-cat="${k}">${esc(CAT_META[k].label)}<span class="n">${
            counts[k] || 0
          }</span></button>`
      )
      .join("");
  }

  function renderFeed() {
    const container = document.getElementById("feed");
    const moreBtn = document.getElementById("more-btn");
    const q = state.query.trim().toLowerCase();

    const allItems = DATA.community || [];
    const maxPts = Math.max(
      100,
      ...allItems.map((it) => Number(it.points || it.comments || 0))
    );

    let list = allItems.filter((it) => {
      if (state.cat !== "all" && it.category !== state.cat) return false;
      if (!q) return true;
      const hay = [
        it.title_zh,
        it.title,
        it.why,
        it.source_label,
        (it.tags || []).join(" "),
      ]
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });

    if (state.sort === "new") {
      list = list
        .slice()
        .sort((a, b) =>
          String(b.published_at || "").localeCompare(String(a.published_at || ""))
        );
    } else if (state.sort === "hot") {
      list = list
        .slice()
        .sort(
          (a, b) =>
            (b.points || b.comments || 0) - (a.points || a.comments || 0)
        );
    }

    if (!list.length) {
      container.innerHTML = `<div class="empty">当前筛选条件下无匹配条目。</div>`;
      moreBtn.hidden = true;
      return;
    }

    const visible = list.slice(0, state.limit);
    moreBtn.hidden = list.length <= state.limit;
    moreBtn.textContent = `展开剩余 ${list.length - visible.length} 条一手情报`;

    container.innerHTML = visible
      .map((it, idx) => {
        const cat = it.category || "talk";
        const catInfo = CAT_META[cat] || CAT_META.talk;
        const titleMain = it.title_zh || it.title;
        const showOrig = it.title_zh && it.title && it.title_zh !== it.title;
        const isLead = idx < 3 && state.cat === "all" && !q && state.sort === "pick";

        const rawScore = Number(it.points || it.comments || 0);
        const pct = Math.min(100, Math.max(8, Math.round((rawScore / maxPts) * 100)));

        const metrics = [];
        if (it.points != null) {
          metrics.push(
            `<span class="heat-meter"><span class="heat-bar"><span class="heat-fill" style="width:${pct}%"></span></span>${esc(
              it.points
            )} ${esc(it.points_label || "PTS")}</span>`
          );
        }
        if (it.comments != null) {
          metrics.push(`<span>${esc(it.comments)} 评</span>`);
        }
        if (it.published_at) {
          metrics.push(`<span>${esc(fmtDate(it.published_at))}</span>`);
        }

        const promptHtml = it.prompt
          ? `<div class="prompt-stamp" style="margin:4px 0;">
               <div class="prompt-stamp-head">
                 <span>原帖附带 Prompt</span>
                 <button type="button" class="act-btn" data-copy="${esc(
                   it.prompt
                 )}">复制 Prompt</button>
               </div>
               <pre>${esc(it.prompt)}</pre>
             </div>`
          : "";

        const actions = [];
        if (it.playable) {
          actions.push(
            `<a class="act-btn playable" href="${esc(
              it.url
            )}" target="_blank" rel="noopener">在线试玩 Space ↗</a>`
          );
        } else {
          actions.push(
            `<a class="act-btn" href="${esc(
              it.url
            )}" target="_blank" rel="noopener">直达原文 ↗</a>`
          );
        }
        if (it.discuss_url && it.discuss_url !== it.url) {
          actions.push(
            `<a class="act-btn" href="${esc(
              it.discuss_url
            )}" target="_blank" rel="noopener">原帖评论区 ↗</a>`
          );
        }

        return `
          <article class="ledger-item cat-${esc(cat)} ${
          isLead ? "lead" : ""
        }" id="item-${esc(it.id)}">
            <div class="item-index-col">
              <span class="rank-num">${pad2(idx + 1)}</span>
              <span class="cat-stamp ${esc(cat)}">${esc(catInfo.stamp)}</span>
            </div>
            <div class="item-main-col">
              <div class="item-top-bar">
                <span class="item-source">${esc(it.source_label || it.source)}</span>
                <div class="item-metrics">${metrics.join(" · ")}</div>
              </div>
              <h3 class="item-title"><a href="${esc(
                it.url
              )}" target="_blank" rel="noopener">${esc(titleMain)}</a></h3>
              ${showOrig ? `<div class="item-orig">${esc(it.title)}</div>` : ""}
              ${it.why ? `<p class="item-why">${esc(it.why)}</p>` : ""}
              ${promptHtml}
              <div class="item-foot">
                <div class="tag-row">${(it.tags || [])
                  .map((t) => `<span>#${esc(t)}</span>`)
                  .join("")}</div>
                <div class="action-row">${actions.join("")}</div>
              </div>
            </div>
          </article>
        `;
      })
      .join("");
  }

  // ---------- 04 右侧：大厂官方发布电报 ----------
  function renderOfficial() {
    const box = document.getElementById("official");
    const list = (DATA.official || []).filter(
      (it) => state.region === "ALL" || it.region === state.region
    );
    if (!list.length) {
      box.innerHTML = `<div class="empty">暂无符合条件的大厂发布</div>`;
      return;
    }
    let lastDay = "";
    let html = "";
    for (const it of list.slice(0, 22)) {
      const day = dayKey(it.published_at);
      if (day !== lastDay) {
        html += `<div class="wire-date-header">${esc(day)}</div>`;
        lastDay = day;
      }
      html += `
        <a class="wire-entry" href="${esc(it.url)}" target="_blank" rel="noopener">
          <div class="wire-meta">
            <span class="wire-org">${esc(it.org)}</span>
            <span class="wire-region">${it.region === "CN" ? "国内" : "海外"}</span>
            ${it.importance >= 3 ? `<span class="wire-major">★ 重要发布</span>` : ""}
          </div>
          <div class="wire-entry-title">${esc(it.title_zh || it.title)}</div>
          ${
            it.summary_zh
              ? `<div class="wire-entry-sum">${esc(it.summary_zh)}</div>`
              : ""
          }
        </a>
      `;
    }
    box.innerHTML = html;
  }

  // ---------- 04 右侧：Hugging Face 飙升榜 ----------
  function renderHfTrending() {
    const box = document.getElementById("hf-trending");
    const list = DATA.hf_trending || [];
    box.innerHTML = list
      .slice(0, 10)
      .map(
        (m, i) =>
          `<li>
             <span class="hf-rank">${pad2(i + 1)}</span>
             <a class="hf-name" href="${esc(m.url)}" target="_blank" rel="noopener">${esc(
            m.id
          )}</a>
             <span class="hf-likes">♥ ${esc(m.likes || 0)}</span>
           </li>`
      )
      .join("");
  }

  // ---------- 事件绑定 ----------
  function bindEvents() {
    document.addEventListener("click", (e) => {
      const copyBtn = e.target.closest("[data-copy]");
      if (copyBtn) {
        copyText(copyBtn.getAttribute("data-copy"));
        return;
      }

      const classicTab = e.target.closest("[data-classic-tab]");
      if (classicTab) {
        state.classicIdx = Number(classicTab.getAttribute("data-classic-tab"));
        renderArena();
        return;
      }

      const modeBtn = e.target.closest("[data-mode]");
      if (modeBtn) {
        state.compareMode = modeBtn.getAttribute("data-mode");
        renderArena();
        return;
      }

      const catBtn = e.target.closest("[data-cat]");
      if (catBtn) {
        state.cat = catBtn.getAttribute("data-cat");
        state.limit = 24;
        renderChips();
        renderFeed();
        return;
      }

      const regBtn = e.target.closest("[data-region]");
      if (regBtn) {
        state.region = regBtn.getAttribute("data-region");
        document
          .querySelectorAll("#region-seg button")
          .forEach((b) =>
            b.classList.toggle("on", b.getAttribute("data-region") === state.region)
          );
        renderOfficial();
        return;
      }

      const jumpBtn = e.target.closest("[data-jump]");
      if (jumpBtn) {
        const id = jumpBtn.getAttribute("data-jump");
        state.cat = "all";
        state.query = "";
        state.limit = 90;
        renderChips();
        renderFeed();
        const row = document.getElementById("item-" + id);
        if (row) {
          row.scrollIntoView({ behavior: "smooth", block: "center" });
          row.classList.remove("flash");
          void row.offsetWidth;
          row.classList.add("flash");
        }
      }
    });

    document.getElementById("search").addEventListener("input", (e) => {
      state.query = e.target.value;
      renderFeed();
    });

    document.getElementById("sort").addEventListener("change", (e) => {
      state.sort = e.target.value;
      renderFeed();
    });

    document.getElementById("more-btn").addEventListener("click", () => {
      state.limit += 24;
      renderFeed();
    });
  }

  function init() {
    renderTelemetry();
    renderBriefing();
    renderArena();
    renderChips();
    renderFeed();
    renderOfficial();
    renderHfTrending();
    bindEvents();
  }

  init();
})();
