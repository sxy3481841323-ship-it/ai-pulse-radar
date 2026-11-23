/* AI 雷达 · 前端交互逻辑 (零外部框架，全部 DOM 安全转义，无 XSS 风险) */
(function () {
  "use strict";

  const DATA = window.RADAR || {};
  const CAT_LABELS = {
    all: "全部",
    play: "整活 / 好玩",
    bench: "野生评测",
    tool: "开源工具 / Demo",
    talk: "社区热议",
  };

  let state = {
    view: "radar",
    cat: "all",
    region: "ALL",
    sort: "pick",
    query: "",
    limit: 24,
  };

  function esc(str) {
    return String(str == null ? "" : str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function fmtDate(isoStr) {
    if (!isoStr) return "";
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return String(isoStr).slice(0, 10);
    const now = new Date();
    const diffH = (now - d) / 3600000;
    if (diffH >= 0 && diffH < 1) return "刚刚";
    if (diffH >= 1 && diffH < 24) return Math.floor(diffH) + " 小时前";
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return (y === now.getFullYear() ? "" : y + "-") + m + "-" + day;
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
      navigator.clipboard.writeText(text).then(() => toast("已复制到剪贴板"));
    } else {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
      toast("已复制到剪贴板");
    }
  }

  // ---------- 顶部状态栏 ----------
  function renderStatus() {
    const btnText = document.getElementById("updated-text");
    const dot = document.getElementById("status-dot");
    const panel = document.getElementById("status-panel");
    const sources = DATA.sources || [];
    const okCount = sources.filter((s) => s.ok).length;
    const total = sources.length;

    btnText.textContent =
      (DATA.generated_at ? "更新于 " + fmtDate(DATA.generated_at) : "已加载") +
      (total ? ` · ${okCount}/${total} 源正常` : "");

    if (okCount < total) dot.classList.add("warn");

    const rows = sources
      .map(
        (s) =>
          `<li><span>${esc(s.name)}</span><span class="${s.ok ? "" : "bad"}">${
            s.ok ? s.count + " 条" : "失败: " + esc(s.error || "未知")
          }</span></li>`
      )
      .join("");

    const unavail = (DATA.unavailable || [])
      .map(
        (u) =>
          `<li><span>${esc(u.name)}</span><span class="na">${esc(
            u.reason
          )}</span></li>`
      )
      .join("");

    panel.innerHTML = `
      <h4>实时抓取源状态</h4>
      <ul>${rows}</ul>
      ${unavail ? `<h4>暂未收录说明</h4><ul>${unavail}</ul>` : ""}
      <div class="meta">生成时间：${esc(DATA.generated_at || "-")} · 提纯模型：${esc(
      DATA.model || "规则排序"
    )}</div>
    `;

    const aboutSources = document.getElementById("about-sources");
    if (aboutSources) {
      aboutSources.innerHTML = `<table class="src-table"><tbody>${sources
        .map(
          (s) =>
            `<tr><td>${esc(s.name)}</td><td>${
              s.ok ? `已抓取 ${s.count} 条最新内容` : esc(s.error)
            }</td></tr>`
        )
        .join("")}${(DATA.unavailable || [])
        .map(
          (u) =>
            `<tr><td>${esc(u.name)}</td><td>${esc(u.reason)}</td></tr>`
        )
        .join("")}</tbody></table>`;
    }
  }

  // ---------- 今日简报 ----------
  function renderBriefing() {
    const box = document.getElementById("briefing");
    const b = DATA.briefing;
    if (!b || !b.headline) {
      box.hidden = true;
      return;
    }
    box.hidden = false;
    const pts = (b.points || [])
      .map((p) => {
        const refs = (p.ids || [])
          .map(
            (id, idx) =>
              `<button type="button" data-jump="${esc(id)}">[${idx + 1}]</button>`
          )
          .join("");
        return `<li><span>${esc(p.text)} ${
          refs ? `<span class="refs">${refs}</span>` : ""
        }</span></li>`;
      })
      .join("");

    box.innerHTML = `
      <div class="briefing-label">今日一手社区简报</div>
      <h1>${esc(b.headline)}</h1>
      ${pts ? `<ol>${pts}</ol>` : ""}
    `;
  }

  // ---------- 分类按钮 ----------
  function renderChips() {
    const items = DATA.community || [];
    const counts = { all: items.length, play: 0, bench: 0, tool: 0, talk: 0 };
    items.forEach((it) => {
      const c = it.category || "talk";
      if (counts[c] != null) counts[c]++;
    });

    const wrap = document.getElementById("cat-chips");
    wrap.innerHTML = Object.keys(CAT_LABELS)
      .map(
        (k) =>
          `<button type="button" class="chip ${
            state.cat === k ? "on" : ""
          }" data-cat="${k}">${esc(CAT_LABELS[k])}<span class="n">${
            counts[k] || 0
          }</span></button>`
      )
      .join("");
  }

  // ---------- 主信息流 ----------
  function renderFeed() {
    const container = document.getElementById("feed");
    const moreBtn = document.getElementById("more-btn");
    const q = state.query.trim().toLowerCase();

    let list = (DATA.community || []).filter((it) => {
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
      container.innerHTML = `<div class="empty">没有匹配的条目，试试切换分类或清空搜索词。</div>`;
      moreBtn.hidden = true;
      return;
    }

    const visible = list.slice(0, state.limit);
    moreBtn.hidden = list.length <= state.limit;
    moreBtn.textContent = `显示更多（还有 ${list.length - visible.length} 条）`;

    let html = "";
    for (const it of visible) {
      const cat = it.category || "talk";
      const catName = CAT_LABELS[cat] || "社区";
      const titleMain = it.title_zh || it.title;
      const showOrig = it.title_zh && it.title && it.title_zh !== it.title;
      const stats = [];
      if (it.points != null) {
        stats.push(`${it.points} ${it.points_label || "points"}`);
      }
      if (it.comments != null) {
        stats.push(`${it.comments} 评论`);
      }
      if (it.published_at) {
        stats.push(fmtDate(it.published_at));
      }

      const tagsHtml = (it.tags || [])
        .map((t) => `<span class="tag">${esc(t)}</span>`)
        .join("");

      const promptHtml = it.prompt
        ? `<div class="prompt-box">
             <div class="prompt-head">
               <span>原帖 Prompt</span>
               <button type="button" class="btn small" data-copy="${esc(
                 it.prompt
               )}">复制 Prompt</button>
             </div>
             <pre>${esc(it.prompt)}</pre>
           </div>`
        : "";

      const actions = [];
      if (it.playable) {
        actions.push(
          `<a class="btn play" href="${esc(
            it.url
          )}" target="_blank" rel="noopener">在线试玩 ↗</a>`
        );
      } else {
        actions.push(
          `<a class="btn" href="${esc(
            it.url
          )}" target="_blank" rel="noopener">查看原文 ↗</a>`
        );
      }
      if (it.discuss_url && it.discuss_url !== it.url) {
        actions.push(
          `<a class="btn" href="${esc(
            it.discuss_url
          )}" target="_blank" rel="noopener">社区讨论 ↗</a>`
        );
      }

      html += `
        <article class="card" id="item-${esc(it.id)}">
          <div class="card-meta">
            <span class="cat ${esc(cat)}">${esc(catName)}</span>
            <span class="src">${esc(it.source_label || it.source)}</span>
            ${stats.map((s) => `<span class="stat">· ${esc(s)}</span>`).join("")}
          </div>
          <h3><a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(
        titleMain
      )}</a></h3>
          ${showOrig ? `<div class="orig">${esc(it.title)}</div>` : ""}
          ${it.why ? `<p class="why">${esc(it.why)}</p>` : ""}
          ${promptHtml}
          <div class="card-foot">
            <div class="tags">${tagsHtml}</div>
            <div class="actions">${actions.join("")}</div>
          </div>
        </article>
      `;
    }
    container.innerHTML = html;
  }

  // ---------- 右侧：官方动态 ----------
  function renderOfficial() {
    const box = document.getElementById("official");
    const list = (DATA.official || []).filter(
      (it) => state.region === "ALL" || it.region === state.region
    );
    if (!list.length) {
      box.innerHTML = `<div class="empty">暂无符合筛选的官方动态</div>`;
      return;
    }
    let lastDay = "";
    let html = "";
    for (const it of list.slice(0, 22)) {
      const day = dayKey(it.published_at);
      if (day !== lastDay) {
        html += `<div class="tl-date">${esc(day)}</div>`;
        lastDay = day;
      }
      const title = it.title_zh || it.title;
      html += `
        <a class="tl-item" href="${esc(it.url)}" target="_blank" rel="noopener">
          <div class="tl-top">
            <span class="org">${esc(it.org)}</span>
            <span class="flag">${it.region === "CN" ? "国内" : "海外"}</span>
            ${it.importance >= 3 ? `<span class="imp">重要发布</span>` : ""}
          </div>
          <div class="tl-title">${esc(title)}</div>
          ${it.summary_zh ? `<div class="tl-sum">${esc(it.summary_zh)}</div>` : ""}
        </a>
      `;
    }
    box.innerHTML = html;
  }

  // ---------- 右侧：Hugging Face 热门模型 ----------
  function renderHfTrending() {
    const box = document.getElementById("hf-trending");
    const list = DATA.hf_trending || [];
    box.innerHTML = list
      .slice(0, 10)
      .map(
        (m) =>
          `<li><a href="${esc(m.url)}" target="_blank" rel="noopener">${esc(
            m.id
          )}</a><span>♥ ${esc(m.likes || 0)}</span></li>`
      )
      .join("");
  }

  // ---------- 经典测试实验室（真实可玩 Demo） ----------
  function renderClassics() {
    const box = document.getElementById("classics");
    const list = DATA.classics || [];
    if (!list.length) {
      box.innerHTML = `<div class="empty">暂无实验室数据</div>`;
      return;
    }

    box.innerHTML = list
      .map((c, idx) => {
        const runs = c.runs || [];
        const firstRun = runs[0] || null;
        const btns = runs
          .map(
            (r, i) =>
              `<button type="button" class="${
                i === 0 ? "on" : ""
              }" data-classic-idx="${idx}" data-run-idx="${i}">${esc(
                r.model_name || r.model
              )}</button>`
          )
          .join("");

        const metaText = firstRun
          ? `DeepSeek 实测生成 · 耗时 ${firstRun.seconds}s · ${
              firstRun.completion_tokens || "-"
            } tokens`
          : "等待生成";

        return `
          <article class="classic" data-classic="${idx}">
            <div class="classic-info">
              <div>
                <h2>${esc(c.name)}</h2>
                <div class="en">${esc(c.name_en || "")}</div>
              </div>
              <div>
                <h4>出处</h4>
                <p>${esc(c.origin)}</p>
                ${
                  c.origin_url
                    ? `<a class="origin-link" href="${esc(
                        c.origin_url
                      )}" target="_blank" rel="noopener">${esc(
                        c.origin_label || c.origin_url
                      )} ↗</a>`
                    : ""
                }
              </div>
              <div>
                <h4>为什么大家爱拿它考模型</h4>
                <p>${esc(c.why)}</p>
              </div>
              ${
                c.look_for && c.look_for.length
                  ? `<div><h4>看哪里判断高下</h4><ul>${c.look_for
                      .map((l) => `<li>${esc(l)}</li>`)
                      .join("")}</ul></div>`
                  : ""
              }
              <div class="prompt-box" style="margin-top:auto">
                <div class="prompt-head">
                  <span>测试 Prompt ${
                    c.prompt_note ? `（${esc(c.prompt_note)}）` : ""
                  }</span>
                  <button type="button" class="btn small" data-copy="${esc(
                    c.prompt
                  )}">复制 Prompt</button>
                </div>
                <pre>${esc(c.prompt)}</pre>
              </div>
            </div>
            <div class="classic-stage">
              <div class="stage-bar">
                <div class="seg">${btns}</div>
                <div style="display:flex;align-items:center;gap:8px;">
                  <span class="stage-meta" id="stage-meta-${idx}">${esc(
          metaText
        )}</span>
                  ${
                    firstRun
                      ? `<a class="btn small" id="stage-open-${idx}" href="${esc(
                          firstRun.file
                        )}" target="_blank" rel="noopener">新窗口全屏打开 ↗</a>`
                      : ""
                  }
                </div>
              </div>
              <div class="stage-frame" id="stage-frame-${idx}">
                ${
                  firstRun
                    ? `<iframe src="${esc(
                        firstRun.file
                      )}" title="${esc(c.name)}" loading="lazy"></iframe>`
                    : `<div class="stage-empty">正在生成真实模型输出…</div>`
                }
              </div>
              <div class="stage-hint">上面展示的是用左侧 Prompt 直接调用 DeepSeek API 一次生成的原始结果，未经人工修图或改代码。点击顶部按钮可切换不同模型对比。</div>
            </div>
          </article>
        `;
      })
      .join("");
  }

  // ---------- 视图切换 ----------
  function setView(view) {
    if (!["radar", "lab", "about"].includes(view)) view = "radar";
    state.view = view;
    document.getElementById("view-radar").hidden = view !== "radar";
    document.getElementById("view-lab").hidden = view !== "lab";
    document.getElementById("view-about").hidden = view !== "about";
    document.querySelectorAll("[data-view-link]").forEach((a) => {
      a.classList.toggle(
        "on",
        a.getAttribute("data-view-link") === view &&
          a.closest(".view-tabs") != null
      );
    });
  }

  // ---------- 事件绑定 ----------
  function bindEvents() {
    window.addEventListener("hashchange", () => {
      const h = (location.hash || "#radar").replace("#", "");
      setView(h);
    });

    document.addEventListener("click", (e) => {
      const copyBtn = e.target.closest("[data-copy]");
      if (copyBtn) {
        copyText(copyBtn.getAttribute("data-copy"));
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
        const card = document.getElementById("item-" + id);
        if (card) {
          card.scrollIntoView({ behavior: "smooth", block: "center" });
          card.classList.remove("flash");
          void card.offsetWidth;
          card.classList.add("flash");
        }
        return;
      }

      const runBtn = e.target.closest("[data-classic-idx]");
      if (runBtn) {
        const cIdx = Number(runBtn.getAttribute("data-classic-idx"));
        const rIdx = Number(runBtn.getAttribute("data-run-idx"));
        const classic = (DATA.classics || [])[cIdx];
        const run = classic && (classic.runs || [])[rIdx];
        if (!run) return;
        runBtn
          .parentElement
          .querySelectorAll("button")
          .forEach((b, i) => b.classList.toggle("on", i === rIdx));
        const frameWrap = document.getElementById("stage-frame-" + cIdx);
        const metaEl = document.getElementById("stage-meta-" + cIdx);
        const openEl = document.getElementById("stage-open-" + cIdx);
        if (frameWrap) {
          frameWrap.innerHTML = `<iframe src="${esc(run.file)}" title="${esc(
            classic.name
          )}"></iframe>`;
        }
        if (metaEl) {
          metaEl.textContent = `DeepSeek 实测生成 · 耗时 ${run.seconds}s · ${
            run.completion_tokens || "-"
          } tokens`;
        }
        if (openEl) {
          openEl.setAttribute("href", run.file);
        }
        return;
      }

      const statusBtn = e.target.closest("#status-btn");
      const statusPanel = document.getElementById("status-panel");
      if (statusBtn) {
        const open = statusPanel.hidden;
        statusPanel.hidden = !open;
        statusBtn.setAttribute("aria-expanded", String(open));
        return;
      }
      if (statusPanel && !statusPanel.hidden && !e.target.closest("#status-panel")) {
        statusPanel.hidden = true;
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
    renderStatus();
    renderBriefing();
    renderChips();
    renderFeed();
    renderOfficial();
    renderHfTrending();
    renderClassics();
    bindEvents();
    const initialView = (location.hash || "#radar").replace("#", "");
    setView(initialView);
  }

  init();
})();
