(function () {
  "use strict";

  const DATA = window.RADAR || {};

  const USER_QUANT_PROFILE_PROMPT =
    "我在学量化，已经学完基础课（12讲）、进阶课（12讲）和高阶专题 Part 1（7讲）：会 Python (NumPy/Pandas) 数据清洗、MAD去极值、行业市值中性化、ICIR单因子检验与分层回测、中证1000多因子指增；也会用 gplearn 遗传规划挖因子、决策树/随机森林/XGBoost 滚动训练（懂防未来函数）、HMM隐状态/RSRS/卡尔曼滤波择时、CNN K线识别，做过 Level-2 高频逐笔成交/委托/撤单订单流因子。我还没学 Part 2（另类事件驱动、行业轮动、期货CTA）、Part 3（组合优化与Barra）和 Part 4（miniqmt/ptrade实盘与TWAP/VWAP拆单）。请教我时请直接按这个工科生能听懂的实战水平来讲，别堆砌晦涩的衍生品数学天书，多给可落地的 Pandas 代码思路和踩坑点。";

  const SKILL_GROUPS = {
    all: "全部实用 Skill",
    college: "🎓 大学工科与课业",
    startup: "🚀 创业与独立开发",
    life: "☕ 日常生活便利",
    quant: "📈 你的量化课实战助手"
  };

  const CAT_LABELS = {
    all: "全部热帖",
    play: "🎮 好玩 / 可视化",
    tool: "🛠️ 提效新工具",
    bench: "⚖️ 野生实测",
    talk: "💬 极客热议"
  };

  let state = {
    demoIdx: 0,
    stageOpen: true,
    cat: "all",
    query: "",
    newsLimit: 12,
    skillZoneOpen: false,
    skillGroup: "all"
  };

  function esc(str) {
    return String(str == null ? "" : str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function fmtStars(n) {
    if (n == null) return "GitHub";
    if (n >= 1000) return "★ " + (n / 1000).toFixed(1) + "k";
    return "★ " + n;
  }

  function fmtDate(isoStr) {
    if (!isoStr) return "";
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return String(isoStr).slice(0, 10);
    const now = new Date();
    const diffH = (now - d) / 3600000;
    if (diffH >= 0 && diffH < 1) return "刚刚";
    if (diffH >= 1 && diffH < 24) return Math.floor(diffH) + "h 前";
    return String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }

  function toast(msg) {
    const el = document.getElementById("toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.remove("show"), 2000);
  }

  function copyText(text, label) {
    if (!text) return;
    const msg = label || "已复制到剪贴板";
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => toast(msg));
    } else {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
      toast(msg);
    }
  }

  // 用 Blob URL 在新标签页打开内联 HTML，100% 不会出现 not connected
  function openDemoInNewTab(demoIdx) {
    const list = DATA.classics || [];
    const c = list[demoIdx] || list[0];
    if (!c) return;
    const r = (c.runs && c.runs[0]) || {};
    if (r.inline_html) {
      const blob = new Blob([r.inline_html], { type: "text/html;charset=utf-8" });
      const blobUrl = URL.createObjectURL(blob);
      window.open(blobUrl, "_blank");
    } else if (r.file) {
      window.open(r.file, "_blank");
    }
  }

  // 打开页内 100% 全屏沉浸试玩弹窗
  function openFullscreenModal(demoIdx) {
    const list = DATA.classics || [];
    const c = list[demoIdx] || list[0];
    if (!c) return;
    const r = (c.runs && c.runs[0]) || {};
    const modal = document.getElementById("fs-modal");
    const iframe = document.getElementById("fs-iframe");
    document.getElementById("fs-title").textContent = `${c.name} · ${r.model_name || ""}`;
    modal.hidden = false;
    if (r.inline_html) {
      iframe.srcdoc = r.inline_html;
    } else if (r.file) {
      iframe.removeAttribute("srcdoc");
      iframe.src = r.file;
    }
  }

  function closeFullscreenModal() {
    const modal = document.getElementById("fs-modal");
    const iframe = document.getElementById("fs-iframe");
    modal.hidden = true;
    iframe.srcdoc = "";
  }

  // 4 张可视化项目的矢量预览图
  function demoThumbSvg(id) {
    if (id === "helicopter-kestrel") {
      return `<svg viewBox="0 0 280 128" xmlns="http://www.w3.org/2000/svg">
        <rect width="280" height="128" fill="#eef1e8"/>
        <line x1="135" y1="12" x2="135" y2="116" stroke="#ff713c" stroke-width="1.2" stroke-dasharray="3,3"/>
        <ellipse cx="135" cy="24" rx="76" ry="9" fill="none" stroke="#1e2421" stroke-width="1.6"/>
        <line x1="59" y1="24" x2="211" y2="24" stroke="#1e2421" stroke-width="2.2"/>
        <circle cx="135" cy="24" r="5" fill="#ff713c" stroke="#1e2421" stroke-width="1.5"/>
        <path d="M78 66 C78 51, 112 49, 152 54 L226 59 L234 47 L242 47 L236 64 L152 71 C115 76, 78 76, 78 66 Z" fill="#fafbf8" stroke="#1e2421" stroke-width="2"/>
        <path d="M82 64 C84 54, 106 52, 118 56 L116 68 C100 69, 84 68, 82 64 Z" fill="#cde0e6" stroke="#1e2421" stroke-width="1.4"/>
        <circle cx="238" cy="56" r="13" fill="none" stroke="#ff713c" stroke-width="1.6" stroke-dasharray="3,2"/>
        <path d="M92 102 L168 102 M106 90 L102 102 M152 90 L156 102" fill="none" stroke="#1e2421" stroke-width="2" stroke-linecap="round"/>
      </svg>`;
    }
    if (id === "chaos-attractor") {
      return `<svg viewBox="0 0 280 128" xmlns="http://www.w3.org/2000/svg">
        <rect width="280" height="128" fill="#f3f3ed"/>
        <path d="M140 66 C105 14, 42 20, 52 66 C62 110, 118 98, 140 66 C162 34, 218 18, 228 64 C238 108, 175 112, 140 66 Z" fill="none" stroke="#d9481e" stroke-width="2.3"/>
        <path d="M140 66 C112 26, 58 30, 66 66 C74 100, 120 90, 140 66 C160 42, 206 30, 214 64 C222 98, 168 102, 140 66 Z" fill="none" stroke="#1b4fa0" stroke-width="1.6"/>
        <circle cx="140" cy="66" r="3.5" fill="#181d1a"/>
      </svg>`;
    }
    if (id === "hexagon-ball") {
      return `<svg viewBox="0 0 280 128" xmlns="http://www.w3.org/2000/svg">
        <rect width="280" height="128" fill="#f4f4ee"/>
        <polygon points="140,16 186,40 186,88 140,112 94,88 94,40" fill="#fafbf8" stroke="#181d1a" stroke-width="2.6"/>
        <path d="M114 74 Q132 44 156 56 T168 80" fill="none" stroke="#d9481e" stroke-width="1.8" stroke-dasharray="3,3"/>
        <circle cx="156" cy="56" r="9.5" fill="#d9481e" stroke="#181d1a" stroke-width="1.5"/>
      </svg>`;
    }
    return `<svg viewBox="0 0 280 128" xmlns="http://www.w3.org/2000/svg">
      <rect width="280" height="128" fill="#f2f3ec"/>
      <rect x="14" y="14" width="76" height="100" fill="rgba(217,72,30,0.08)"/>
      <rect x="90" y="14" width="60" height="100" fill="rgba(194,120,14,0.06)"/>
      <rect x="150" y="14" width="116" height="100" fill="rgba(217,72,30,0.10)"/>
      <path d="M18 92 L54 74 L92 82 L134 64 L178 44 L222 30 L260 22" fill="none" stroke="#d9481e" stroke-width="2.5"/>
      <path d="M18 96 L54 84 L92 88 L134 76 L178 62 L222 54 L260 48" fill="none" stroke="#181d1a" stroke-width="1.8"/>
      <path d="M18 94 L54 80 L92 85 L134 72 L178 55 L222 44 L260 36" fill="none" stroke="#1b4fa0" stroke-width="1.6" stroke-dasharray="4,3"/>
    </svg>`;
  }

  // ---------- 顶部状态渲染 ----------
  function renderHeader() {
    if (DATA.week_label) {
      document.getElementById("week-badge").textContent = DATA.week_label + " · 每周推陈出新";
    }
    const sources = DATA.sources || [];
    const okCount = sources.filter((s) => s.ok).length;
    document.getElementById("updated-text").textContent =
      "最新同步: " +
      (DATA.generated_at ? DATA.generated_at.replace("T", " ").slice(0, 16) + " UTC" : "刚刚");
    document.getElementById("source-mini-status").textContent =
      `直连数据源 ${okCount}/${sources.length || 11} 在线 · 零二手自媒体`;
  }

  // ---------- 01 本周好玩项目渲染 ----------
  function renderPlayground() {
    const list = DATA.classics || [];
    const cardsEl = document.getElementById("playground-cards");
    const stageEl = document.getElementById("stage-container");
    const toggleBtn = document.getElementById("toggle-stage-btn");
    if (!list.length) return;

    toggleBtn.textContent = state.stageOpen ? "▼ 收起试玩画布" : "▶ 展开试玩画布";

    cardsEl.innerHTML = list
      .map((c, idx) => {
        const isAct = state.demoIdx === idx;
        return `
          <article class="play-card ${isAct ? "active" : ""}" data-select-demo="${idx}">
            <div>
              <div class="play-card-top">
                <span class="model-pill">${esc(c.badge || "LIVE")}</span>
                <span class="cat-text">${esc(c.category || "")}</span>
              </div>
              <div class="play-thumb" style="margin-top:10px">
                ${demoThumbSvg(c.id)}
                <span class="play-status-tag">${
                  isAct && state.stageOpen ? "● 正在下方画布运行" : "▶ 点击切换试玩"
                }</span>
              </div>
              <h3 class="play-title" style="margin-top:12px">${esc(c.name)}</h3>
              <p class="play-oneliner" style="margin-top:6px">${esc(
                c.one_liner || c.why
              )}</p>
            </div>
            <div class="play-card-actions">
              <button type="button" class="btn primary" data-select-demo="${idx}">
                ${isAct && state.stageOpen ? "● 正在试玩" : "▶ 在画布打开"}
              </button>
              <button type="button" class="btn" data-fs-demo="${idx}">⛶ 全屏试玩</button>
              <button type="button" class="btn" data-copy="${esc(
                c.prompt
              )}" data-copy-label="已复制 Prompt">复制提示词</button>
            </div>
          </article>
        `;
      })
      .join("");

    if (!state.stageOpen) {
      stageEl.hidden = true;
    } else {
      stageEl.hidden = false;
      const c = list[state.demoIdx] || list[0];
      const r = (c.runs && c.runs[0]) || {};
      stageEl.innerHTML = `
        <div class="stage-topbar">
          <div class="stage-topbar-left">
            <span class="stage-live-dot"></span>
            <span class="stage-title-Now">${esc(c.name)}</span>
            <span style="font-family:var(--mono);font-size:12px;color:#b8c2bc">(${esc(
              r.model_name || c.badge
            )} · 内联零断连引擎)</span>
          </div>
          <div class="stage-topbar-actions">
            <button type="button" class="stage-btn-dark accent" data-fs-demo="${
              state.demoIdx
            }">⛶ 页内全屏沉浸试玩</button>
            <button type="button" class="stage-btn-dark" data-blob-demo="${
              state.demoIdx
            }">↗ 独立新标签页打开</button>
          </div>
        </div>
        <div class="stage-body">
          <div class="stage-iframe-wrap">
            <iframe id="main-stage-iframe" title="${esc(c.name)}"></iframe>
          </div>
          <div class="stage-side-guide">
            <div style="display:flex;flex-direction:column;gap:14px">
              <div class="guide-block">
                <h4>💡 为什么好玩</h4>
                <p>${esc(c.one_liner || c.why)}</p>
              </div>
              ${
                c.look_for && c.look_for.length
                  ? `<div class="guide-block">
                       <h4>🕹️ 上手怎么玩</h4>
                       <ul>${c.look_for.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>
                     </div>`
                  : ""
              }
            </div>
            <div class="prompt-box">
              <div class="prompt-box-head">
                <span>完整生成 Prompt</span>
                <button type="button" class="btn" style="padding:2px 8px;font-size:11px" data-copy="${esc(
                  c.prompt
                )}" data-copy-label="已复制完整 Prompt">复制 Prompt</button>
              </div>
              <pre>${esc(c.prompt)}</pre>
            </div>
          </div>
        </div>
      `;

      // 使用内联 srcdoc 直接注入 HTML，彻底消除任何网络/路径引起的 not connected
      const iframe = document.getElementById("main-stage-iframe");
      if (iframe) {
        if (r.inline_html) {
          iframe.srcdoc = r.inline_html;
        } else if (r.file) {
          iframe.src = r.file;
        }
      }
    }

    // 渲染本周社区自动抓新的好玩网页/Space
    const freshGrid = document.getElementById("weekly-fresh-grid");
    const freshList = (DATA.community || [])
      .filter((it) => it.playable || it.category === "play")
      .slice(0, 4);
    freshGrid.innerHTML = freshList
      .map(
        (it) => `
        <div class="fresh-card">
          <div>
            <div class="fresh-meta">
              <span>${esc(it.source_label || "在线试玩")}</span>
              <span>${
                it.points != null
                  ? "★ " + esc(it.points)
                  : esc(fmtDate(it.published_at))
              }</span>
            </div>
            <h4 class="fresh-title" style="margin-top:6px">
              <a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(
          it.title_zh || it.title
        )}</a>
            </h4>
            <p class="fresh-one-line" style="margin-top:6px">${esc(it.why)}</p>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;padding-top:6px">
            <span style="font-family:var(--mono);font-size:11px;color:var(--muted)">${(
              it.tags || []
            )
              .map((t) => "#" + esc(t))
              .join(" ")}</span>
            <a class="btn" href="${esc(
              it.url
            )}" target="_blank" rel="noopener">去玩玩看 ↗</a>
          </div>
        </div>
      `
      )
      .join("");
  }

  // ---------- 02 社群热帖 & 企业大事记（每条一句话讲清价值） ----------
  function renderNewsSection() {
    const allComm = DATA.community || [];
    const counts = { all: allComm.length, play: 0, tool: 0, bench: 0, talk: 0 };
    allComm.forEach((it) => {
      const c = it.category || "talk";
      if (counts[c] != null) counts[c]++;
    });

    document.getElementById("cat-pills").innerHTML = Object.keys(CAT_LABELS)
      .map(
        (k) =>
          `<button type="button" class="cat-pill ${
            state.cat === k ? "on" : ""
          }" data-cat="${k}">${esc(CAT_LABELS[k])} (${counts[k] || 0})</button>`
      )
      .join("");

    const q = state.query.trim().toLowerCase();
    const filtered = allComm.filter((it) => {
      if (state.cat !== "all" && it.category !== state.cat) return false;
      if (!q) return true;
      return [it.title_zh, it.title, it.why, (it.tags || []).join(" ")]
        .join(" ")
        .toLowerCase()
        .includes(q);
    });

    const visible = filtered.slice(0, state.newsLimit);
    const moreBtn = document.getElementById("more-news-btn");
    moreBtn.hidden = filtered.length <= state.newsLimit;
    moreBtn.textContent = `展开剩余 ${filtered.length - visible.length} 条热帖`;

    const catTagMap = {
      play: "好玩项目",
      tool: "提效工具",
      bench: "野生实测",
      talk: "极客热议"
    };

    document.getElementById("community-list").innerHTML = visible
      .map((it) => {
        const cat = it.category || "talk";
        return `
          <article class="news-card">
            <div class="news-card-meta">
              <span class="cat-tag ${esc(cat)}">${esc(
          catTagMap[cat] || "热议"
        )}</span>
              <span style="font-weight:700">${esc(
                it.source_label || it.source
              )}</span>
              ${
                it.points != null
                  ? `<span>· 热度 ${esc(it.points)} ${esc(
                      it.points_label || "PTS"
                    )}</span>`
                  : ""
              }
              <span style="margin-left:auto;color:var(--muted)">${esc(
                fmtDate(it.published_at)
              )}</span>
            </div>
            <h4 class="news-title">
              <a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(
          it.title_zh || it.title
        )}</a>
            </h4>
            <div class="value-one-liner">
              <strong>💡 一句话价值：</strong>${esc(it.why)}
            </div>
            <div class="news-card-foot">
              <span>${(it.tags || []).map((t) => "#" + esc(t)).join("  ")}</span>
              <div style="display:flex;gap:8px">
                ${
                  it.discuss_url && it.discuss_url !== it.url
                    ? `<a class="btn" style="padding:3px 9px;font-size:11px" href="${esc(
                        it.discuss_url
                      )}" target="_blank" rel="noopener">原帖评论区 ↗</a>`
                    : ""
                }
                <a class="btn" style="padding:3px 9px;font-size:11px" href="${esc(
                  it.url
                )}" target="_blank" rel="noopener">直达出处 ↗</a>
              </div>
            </div>
          </article>
        `;
      })
      .join("");

    // 右栏：企业大事记
    const offList = (DATA.official || []).slice(0, 16);
    document.getElementById("official-list").innerHTML = offList
      .map(
        (it) => `
        <a class="milestone-card" href="${esc(
          it.url
        )}" target="_blank" rel="noopener">
          <div class="ms-top">
            <span class="ms-org">${esc(it.org)}</span>
            ${it.importance >= 3 ? `<span class="ms-major">重磅</span>` : ""}
            <span class="ms-date">${esc(fmtDate(it.published_at))}</span>
          </div>
          <h4 class="ms-title">${esc(it.title_zh || it.title)}</h4>
          <div class="ms-value">
            <strong>价值：</strong>${esc(it.summary_zh || "官方最新模型与技术更新。")}
          </div>
        </a>
      `
      )
      .join("");
  }

  // ---------- 03 可点开的实用 Skill 专区 ----------
  function renderSkillZone() {
    const bodyEl = document.getElementById("skill-zone-body");
    const triggerEl = document.getElementById("skill-drawer-trigger");
    const ctaEl = document.getElementById("skill-trigger-cta");
    const bannerEl = document.getElementById("quant-profile-banner");

    bodyEl.hidden = !state.skillZoneOpen;
    triggerEl.setAttribute("aria-expanded", String(state.skillZoneOpen));
    ctaEl.textContent = state.skillZoneOpen
      ? "🔼 收起 Skill 专区"
      : "📂 点击展开 Skill 专区 ▾";

    const allSkills = DATA.skills || [];
    const counts = { all: allSkills.length };
    allSkills.forEach((s) => {
      counts[s.group] = (counts[s.group] || 0) + 1;
    });

    document.getElementById("skill-tabs").innerHTML = Object.keys(SKILL_GROUPS)
      .map(
        (g) =>
          `<button type="button" class="skill-tab ${
            state.skillGroup === g ? "on" : ""
          }" data-skill-group="${g}">${esc(SKILL_GROUPS[g])} (${
            counts[g] || 0
          })</button>`
      )
      .join("");

    bannerEl.style.display =
      state.skillGroup === "all" || state.skillGroup === "quant" ? "flex" : "none";

    const filtered =
      state.skillGroup === "all"
        ? allSkills
        : allSkills.filter((s) => s.group === state.skillGroup);

    document.getElementById("skills-grid").innerHTML = filtered
      .map(
        (s) => `
        <article class="skill-card">
          <div>
            <div class="sk-top">
              <span class="sk-group-tag">${esc(s.group_label)} · ${esc(
          s.badge
        )}</span>
              <span class="sk-stars">${esc(fmtStars(s.stars))}</span>
            </div>
            <h3 class="sk-title" style="margin-top:10px">
              <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(
          s.title_zh
        )}</a>
            </h3>
            <div class="sk-one-sentence" style="margin-top:10px">
              <strong>⚡ 方便/高效在哪：</strong>${esc(s.one_sentence)}
            </div>
          </div>

          <div class="sk-foot">
            <span class="sk-cmd" data-copy="${esc(
              s.install_cmd
            )}" data-copy-label="已复制命令: ${esc(
          s.install_cmd
        )}" title="点击复制命令">$ ${esc(s.install_cmd)}</span>
            <div style="display:flex;gap:6px">
              <button type="button" class="btn" data-copy="${esc(
                s.prompt_recipe
              )}" data-copy-label="已复制配套提示词">复制配套提示词</button>
              <a class="btn" href="${esc(
                s.url
              )}" target="_blank" rel="noopener">仓库 ↗</a>
            </div>
          </div>
        </article>
      `
      )
      .join("");
  }

  function openAndScrollToSkillZone() {
    state.skillZoneOpen = true;
    renderSkillZone();
    document
      .getElementById("sec-skills")
      .scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // ---------- 全局事件绑定 ----------
  document.addEventListener("click", (e) => {
    const copyEl = e.target.closest("[data-copy]");
    if (copyEl) {
      e.stopPropagation();
      copyText(
        copyEl.getAttribute("data-copy"),
        copyEl.getAttribute("data-copy-label")
      );
      return;
    }

    const fsBtn = e.target.closest("[data-fs-demo]");
    if (fsBtn) {
      e.stopPropagation();
      openFullscreenModal(Number(fsBtn.getAttribute("data-fs-demo")) || 0);
      return;
    }

    const blobBtn = e.target.closest("[data-blob-demo]");
    if (blobBtn) {
      e.stopPropagation();
      openDemoInNewTab(Number(blobBtn.getAttribute("data-blob-demo")) || 0);
      return;
    }

    const selDemo = e.target.closest("[data-select-demo]");
    if (selDemo && !e.target.closest("a")) {
      state.demoIdx = Number(selDemo.getAttribute("data-select-demo")) || 0;
      state.stageOpen = true;
      renderPlayground();
      return;
    }

    const catBtn = e.target.closest("[data-cat]");
    if (catBtn) {
      state.cat = catBtn.getAttribute("data-cat");
      state.newsLimit = 12;
      renderNewsSection();
      return;
    }

    const skGroupBtn = e.target.closest("[data-skill-group]");
    if (skGroupBtn) {
      state.skillGroup = skGroupBtn.getAttribute("data-skill-group");
      renderSkillZone();
      return;
    }
  });

  document.getElementById("toggle-stage-btn").addEventListener("click", () => {
    state.stageOpen = !state.stageOpen;
    renderPlayground();
  });

  document.getElementById("search-input").addEventListener("input", (e) => {
    state.query = e.target.value;
    renderNewsSection();
  });

  document.getElementById("more-news-btn").addEventListener("click", () => {
    state.newsLimit += 15;
    renderNewsSection();
  });

  document
    .getElementById("skill-drawer-trigger")
    .addEventListener("click", () => {
      state.skillZoneOpen = !state.skillZoneOpen;
      renderSkillZone();
    });

  document
    .getElementById("nav-open-skills")
    .addEventListener("click", openAndScrollToSkillZone);
  document
    .getElementById("hero-open-skills")
    .addEventListener("click", openAndScrollToSkillZone);

  document.getElementById("copy-profile-btn").addEventListener("click", () => {
    copyText(
      USER_QUANT_PROFILE_PROMPT,
      "已复制你的 31 讲量化学习背景，可直接粘贴给 AI 提问！"
    );
  });

  document
    .getElementById("fs-close-btn")
    .addEventListener("click", closeFullscreenModal);
  document.getElementById("fs-newtab-btn").addEventListener("click", () => {
    openDemoInNewTab(state.demoIdx);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeFullscreenModal();
  });

  // 初始化
  renderHeader();
  renderPlayground();
  renderNewsSection();
  renderSkillZone();
})();
