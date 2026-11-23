(function () {
  "use strict";

  const DATA = window.RADAR || {};

  const DISC_META = {
    all: { label: "全部学科" },
    quant_fin: { label: "量化金融" },
    market: { label: "金融市场" },
    fin_math: { label: "金融数学" },
    econometrics: { label: "计量经济学" },
    stat: { label: "统计学" },
    macro: { label: "宏观经济学" }
  };

  const CAT_META = {
    all: { label: "全部", stamp: "ALL" },
    tool: { label: "效率工具", stamp: "工具·TOOL" },
    play: { label: "好玩/可视化", stamp: "神作·PLAY" },
    bench: { label: "野生实测", stamp: "实测·BENCH" },
    talk: { label: "深度讨论", stamp: "讨论·TALK" }
  };

  let state = {
    discipline: "all",
    wireTab: "official", // "official" | "flash"
    region: "ALL",
    classicIdx: 0,
    theaterOpen: true,
    cat: "all",
    sort: "pick",
    query: "",
    limit: 20
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
    toast._t = setTimeout(() => el.classList.remove("show"), 1900);
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

  // ---------- 为每个量化 Skill 生成专属的数学/金融可视化微图 SVG ----------
  function quantSparkSvg(kind) {
    switch (kind) {
      case "alpha_ic_curve":
        return `<svg viewBox="0 0 110 42"><path d="M4 36 L22 28 L40 22 L58 18 L76 11 L94 7 L106 4" fill="none" stroke="#196b48" stroke-width="2"/><path d="M4 36 L22 35 L40 37 L58 38 L76 39 L106 40" fill="none" stroke="#8c948d" stroke-width="1.2" stroke-dasharray="2,2"/><rect x="10" y="24" width="6" height="12" fill="#d9481e" opacity="0.7"/><rect x="28" y="18" width="6" height="18" fill="#196b48" opacity="0.7"/><rect x="46" y="21" width="6" height="15" fill="#196b48" opacity="0.7"/><rect x="64" y="13" width="6" height="23" fill="#196b48" opacity="0.85"/></svg>`;
      case "iv_term_structure":
        return `<svg viewBox="0 0 110 42"><path d="M6 10 Q36 36 58 26 T104 14" fill="none" stroke="#d9481e" stroke-width="2.1"/><path d="M6 20 Q36 38 58 31 T104 24" fill="none" stroke="#1b4fa0" stroke-width="1.6"/><circle cx="58" cy="26" r="2.5" fill="#181d1a"/></svg>`;
      case "did_event_study":
        return `<svg viewBox="0 0 110 42"><line x1="52" y1="3" x2="52" y2="39" stroke="#d9481e" stroke-width="1.2" stroke-dasharray="2,2"/><line x1="4" y1="28" x2="106" y2="28" stroke="#8c948d" stroke-width="1"/><path d="M10 28 L30 27 L52 28 L72 17 L90 11 L104 9" fill="none" stroke="#1b4fa0" stroke-width="2"/><path d="M72 11 L72 23 M90 5 L90 17" stroke="#1b4fa0" stroke-width="1.3"/></svg>`;
      case "garch_vol_cone":
        return `<svg viewBox="0 0 110 42"><path d="M4 22 L14 21 L22 8 L30 34 L38 14 L48 25 L60 20 L72 9 L82 31 L94 19 L106 21" fill="none" stroke="#1b4fa0" stroke-width="1.5"/><path d="M4 16 L22 5 L38 11 L60 17 L72 6 L106 16" fill="none" stroke="#d9481e" stroke-width="1.6"/></svg>`;
      case "conformal_fan":
        return `<svg viewBox="0 0 110 42"><polygon points="56,22 104,6 104,36" fill="rgba(158,97,8,0.18)"/><path d="M6 28 L24 23 L40 26 L56 22 L80 18 L104 19" fill="none" stroke="#9e6108" stroke-width="2"/></svg>`;
      case "cvar_frontier":
        return `<svg viewBox="0 0 110 42"><path d="M14 36 Q32 10 98 7" fill="none" stroke="#5b2c91" stroke-width="2.2"/><circle cx="46" cy="17" r="3" fill="#d9481e"/><circle cx="32" cy="26" r="2" fill="#181d1a"/><circle cx="68" cy="12" r="2" fill="#196b48"/></svg>`;
      case "sabr_smile":
        return `<svg viewBox="0 0 110 42"><path d="M8 8 C28 36, 72 38, 102 12" fill="none" stroke="#5b2c91" stroke-width="2.2"/><path d="M12 16 L98 28" fill="none" stroke="#8c948d" stroke-width="1" stroke-dasharray="2,2"/></svg>`;
      case "lob_imbalance":
        return `<svg viewBox="0 0 110 42"><polygon points="6,38 6,12 24,12 24,20 48,20 48,38" fill="rgba(25,107,72,0.28)" stroke="#196b48" stroke-width="1.5"/><polygon points="60,38 60,24 82,24 82,9 104,9 104,38" fill="rgba(217,72,30,0.25)" stroke="#d9481e" stroke-width="1.5"/></svg>`;
      case "yield_curve_erp":
        return `<svg viewBox="0 0 110 42"><path d="M8 34 Q36 16 102 10" fill="none" stroke="#196b48" stroke-width="2"/><path d="M8 14 Q42 28 102 32" fill="none" stroke="#d9481e" stroke-width="1.6" stroke-dasharray="3,2"/></svg>`;
      default:
        return `<svg viewBox="0 0 110 42"><path d="M6 21 C24 4, 44 38, 66 15 S92 30, 104 12" fill="none" stroke="#185a7a" stroke-width="2"/></svg>`;
    }
  }

  // ---------- 为 4 个可视化标本卡片生成精细矢量缩略图 ----------
  function specimenPreviewSvg(id) {
    if (id === "helicopter-kestrel") {
      return `<svg viewBox="0 0 280 118" xmlns="http://www.w3.org/2000/svg">
        <rect width="280" height="118" fill="#eef1e8"/>
        <g stroke="#d5dcd0" stroke-width="0.8">
          <line x1="0" y1="30" x2="280" y2="30"/><line x1="0" y1="60" x2="280" y2="60"/><line x1="0" y1="90" x2="280" y2="90"/>
          <line x1="70" y1="0" x2="70" y2="118"/><line x1="140" y1="0" x2="140" y2="118"/><line x1="210" y1="0" x2="210" y2="118"/>
        </g>
        <!-- 爆炸拆解轴线 -->
        <line x1="135" y1="12" x2="135" y2="106" stroke="#ff713c" stroke-width="1.2" stroke-dasharray="3,3"/>
        <!-- 顶层：主旋翼五桨叶总成 (Exploded Up) -->
        <ellipse cx="135" cy="22" rx="76" ry="9" fill="none" stroke="#1e2421" stroke-width="1.6"/>
        <line x1="59" y1="22" x2="211" y2="22" stroke="#1e2421" stroke-width="2.2"/>
        <line x1="95" y1="14" x2="175" y2="30" stroke="#1e2421" stroke-width="1.8"/>
        <circle cx="135" cy="22" r="5" fill="#ff713c" stroke="#1e2421" stroke-width="1.5"/>
        <!-- 中层：H-07 机身 + 座舱 + 尾梁 + 尾桨 -->
        <path d="M78 62 C78 47, 112 45, 152 50 L226 55 L234 43 L242 43 L236 60 L152 67 C115 72, 78 72, 78 62 Z" fill="#fafbf8" stroke="#1e2421" stroke-width="2"/>
        <path d="M82 60 C84 50, 106 48, 118 52 L116 64 C100 65, 84 64, 82 60 Z" fill="#cde0e6" stroke="#1e2421" stroke-width="1.4"/>
        <circle cx="238" cy="52" r="13" fill="none" stroke="#ff713c" stroke-width="1.6" stroke-dasharray="3,2"/>
        <line x1="227" y1="52" x2="249" y2="52" stroke="#1e2421" stroke-width="1.8"/>
        <!-- 底层：起落滑橇 (Exploded Down) -->
        <path d="M92 96 L168 96 M106 84 L102 96 M152 84 L156 96 M84 92 L92 96" fill="none" stroke="#1e2421" stroke-width="2" stroke-linecap="round"/>
        <text x="10" y="18" font-family="monospace" font-size="9.5" font-weight="bold" fill="#42775c">01 ROTOR HUB</text>
        <text x="10" y="108" font-family="monospace" font-size="9.5" font-weight="bold" fill="#ff713c">8-PART EXPLODED VIEW</text>
      </svg>`;
    }
    if (id === "quant-vol-lob") {
      return `<svg viewBox="0 0 280 118" xmlns="http://www.w3.org/2000/svg">
        <rect width="280" height="118" fill="#f2f3ec"/>
        <!-- 3D Volatility Surface Mesh -->
        <path d="M18 82 Q65 24 115 54 T172 26" fill="none" stroke="#d9481e" stroke-width="2.4"/>
        <path d="M26 94 Q73 38 123 66 T180 40" fill="none" stroke="#196b48" stroke-width="1.8"/>
        <path d="M34 104 Q81 52 131 78 T188 54" fill="none" stroke="#1b4fa0" stroke-width="1.5"/>
        <line x1="18" y1="82" x2="34" y2="104" stroke="#181d1a" stroke-width="1"/>
        <line x1="115" y1="54" x2="131" y2="78" stroke="#181d1a" stroke-width="1"/>
        <line x1="172" y1="26" x2="188" y2="54" stroke="#181d1a" stroke-width="1"/>
        <!-- Right mini LOB depth -->
        <rect x="198" y="14" width="72" height="90" fill="#fafbf8" stroke="#181d1a" stroke-width="1.2"/>
        <polygon points="202,98 202,48 218,48 218,68 231,68 231,98" fill="rgba(25,107,72,0.3)" stroke="#196b48" stroke-width="1.4"/>
        <polygon points="237,98 237,72 252,72 252,34 266,34 266,98" fill="rgba(217,72,30,0.28)" stroke="#d9481e" stroke-width="1.4"/>
        <text x="12" y="18" font-family="monospace" font-size="9.5" font-weight="bold" fill="#181d1a">σ_IV(K,τ) + L2 LOB</text>
      </svg>`;
    }
    if (id === "chaos-attractor") {
      return `<svg viewBox="0 0 280 118" xmlns="http://www.w3.org/2000/svg">
        <rect width="280" height="118" fill="#f3f3ed"/>
        <path d="M140 62 C105 12, 42 18, 52 62 C62 104, 118 92, 140 62 C162 32, 218 16, 228 60 C238 102, 175 106, 140 62 Z" fill="none" stroke="#d9481e" stroke-width="2.2"/>
        <path d="M140 62 C112 24, 58 28, 66 62 C74 94, 120 84, 140 62 C160 40, 206 28, 214 60 C222 92, 168 96, 140 62 Z" fill="none" stroke="#1b4fa0" stroke-width="1.5"/>
        <path d="M140 62 C120 36, 74 38, 80 62 C86 84, 124 76, 140 62 C156 48, 192 40, 198 60 C204 82, 160 84, 140 62 Z" fill="none" stroke="#196b48" stroke-width="1.3"/>
        <circle cx="140" cy="62" r="3.5" fill="#181d1a"/>
        <text x="12" y="18" font-family="monospace" font-size="9.5" font-weight="bold" fill="#181d1a">RK4 STRANGE ATTRACTOR</text>
      </svg>`;
    }
    return `<svg viewBox="0 0 280 118" xmlns="http://www.w3.org/2000/svg">
      <rect width="280" height="118" fill="#f4f4ee"/>
      <polygon points="140,14 184,38 184,82 140,106 96,82 96,38" fill="#fafbf8" stroke="#181d1a" stroke-width="2.5"/>
      <path d="M114 70 Q132 42 156 54 T168 76" fill="none" stroke="#d9481e" stroke-width="1.8" stroke-dasharray="3,3"/>
      <circle cx="156" cy="54" r="9" fill="#d9481e" stroke="#181d1a" stroke-width="1.5"/>
      <text x="12" y="18" font-family="monospace" font-size="9.5" font-weight="bold" fill="#181d1a">V4-PRO TANGENTIAL PHYSICS</text>
    </svg>`;
  }

  // ---------- 顶部直连数据源监测表 ----------
  function renderTelemetry() {
    const updatedEl = document.getElementById("updated-text");
    const sumEl = document.getElementById("telemetry-summary");
    const gridEl = document.getElementById("telemetry-grid");

    const sources = DATA.sources || [];
    const okCount = sources.filter((s) => s.ok).length;
    updatedEl.textContent =
      "最新采集: " +
      (DATA.generated_at ? DATA.generated_at.replace("T", " ").slice(0, 16) + " UTC" : "刚刚") +
      (DATA.model ? ` · 提纯: ${DATA.model}` : "");

    sumEl.textContent = `${okCount}/${sources.length} 源在线`;

    const cells = sources.map(
      (s) =>
        `<div class="tel-cell" title="${esc(s.error || s.name)}">
           <span class="tel-name">${esc(s.name)}</span>
           <span class="tel-val">${s.ok ? s.count + "条" : "ERR"}</span>
         </div>`
    );
    gridEl.innerHTML = cells.join("");
  }

  // ---------- 00 24h 实时焦点简报横条 ----------
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
      .slice(0, 4)
      .map((p) => {
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
            <div class="brief-text">${esc(p.text)}</div>
            ${refs ? `<div class="brief-refs">${refs}</div>` : ""}
          </div>
        `;
      })
      .join("");

    sec.innerHTML = `
      <div class="briefing-lead">
        <span class="briefing-kicker">24H PULSE // 今日一手技术脉络</span>
        <h2 class="briefing-headline">${esc(b.headline)}</h2>
      </div>
      <div class="briefing-points">${cells}</div>
    `;
  }

  // ---------- 01 权重 #1：量化与数理研究效率 Skills 矩阵 ----------
  function renderQuantSkills() {
    const all = DATA.quant_skills || [];
    const barEl = document.getElementById("discipline-bar");
    const gridEl = document.getElementById("quant-grid");

    const counts = { all: all.length };
    all.forEach((it) => {
      counts[it.discipline] = (counts[it.discipline] || 0) + 1;
    });

    barEl.innerHTML = Object.keys(DISC_META)
      .map(
        (k) =>
          `<button type="button" class="disc-btn ${
            state.discipline === k ? "on" : ""
          }" data-disc="${k}">${esc(DISC_META[k].label)}<span class="cnt">(${
            counts[k] || 0
          })</span></button>`
      )
      .join("");

    const filtered =
      state.discipline === "all"
        ? all
        : all.filter((it) => it.discipline === state.discipline);

    gridEl.innerHTML = filtered
      .map(
        (it) => `
        <article class="quant-card">
          <div>
            <div class="q-card-top">
              <span class="q-disc-tag ${esc(it.discipline)}">${esc(
          it.discipline_label
        )} · ${esc(it.kind)}</span>
              <div class="q-repo-meta">
                <span class="q-stars">${esc(fmtStars(it.stars))}</span>
                <span>${esc(it.language || "Python")}</span>
                <span>更新 ${esc(fmtDate(it.pushed_at))}</span>
              </div>
            </div>

            <div class="q-title-row" style="margin-top:8px">
              <div>
                <h3 class="q-title"><a href="${esc(
                  it.url
                )}" target="_blank" rel="noopener">${esc(it.title_zh)}</a></h3>
                <div class="q-kind-sub">${esc(it.repo)}</div>
              </div>
              <div class="q-spark-box" title="量化/数理机制示意图">
                ${quantSparkSvg(it.visual_preview)}
                <div class="q-spark-caption">${esc(it.metrics_badge || it.discipline_label)}</div>
              </div>
            </div>

            <p class="q-gain" style="margin-top:8px">${esc(it.efficiency_gain)}</p>
          </div>

          <div>
            <div class="q-recipe-box">
              <div class="q-recipe-head">
                <span>⚡ AGENT SKILL / 投研提示词模板</span>
                <button type="button" class="act-btn" data-copy="${esc(
                  it.skill_recipe
                )}" data-copy-label="已复制量化 Skill 提示词">复制 Skill 提示词</button>
              </div>
              <div class="q-recipe-text">${esc(it.skill_recipe)}</div>
            </div>

            <div class="q-foot" style="margin-top:8px">
              <span class="q-cmd" data-copy="${esc(
                it.install_cmd
              )}" data-copy-label="已复制安装命令: ${esc(it.install_cmd)}" title="点击复制安装命令">$ ${esc(
          it.install_cmd
        )}</span>
              <div class="q-actions">
                <a class="act-btn" href="${esc(
                  it.url
                )}" target="_blank" rel="noopener">GitHub 仓库 ↗</a>
              </div>
            </div>
          </div>
        </article>
      `
      )
      .join("");
  }

  // ---------- 02 首屏右栏：24h 实时大事记 & 极客快讯电报 ----------
  function renderLiveWire() {
    const container = document.getElementById("wire-list-container");
    const subbar = document.getElementById("wire-subbar");

    document.querySelectorAll(".wire-tab-btn").forEach((b) => {
      b.classList.toggle("on", b.getAttribute("data-wire-tab") === state.wireTab);
    });

    if (state.wireTab === "official") {
      subbar.style.display = "flex";
      const list = (DATA.official || []).filter(
        (it) => state.region === "ALL" || it.region === state.region
      );
      if (!list.length) {
        container.innerHTML = `<div style="padding:24px;text-align:center;color:var(--muted)">暂无符合条件的大厂通告</div>`;
        return;
      }
      const byDay = {};
      list.forEach((it) => {
        const k = dayKey(it.published_at);
        (byDay[k] = byDay[k] || []).push(it);
      });
      container.innerHTML = Object.keys(byDay)
        .sort()
        .reverse()
        .map((day) => {
          const rows = byDay[day]
            .map(
              (it) => `
              <a class="wire-entry" href="${esc(it.url)}" target="_blank" rel="noopener">
                <div class="wire-meta">
                  <span class="wire-org">${esc(it.org)}</span>
                  <span class="wire-region">${esc(it.region)}</span>
                  ${it.importance >= 3 ? `<span class="wire-major">重磅</span>` : ""}
                  <span style="margin-left:auto;color:var(--muted)">${esc(
                    fmtDate(it.published_at)
                  )}</span>
                </div>
                <div class="wire-entry-title">${esc(it.title_zh || it.title)}</div>
                ${
                  it.summary_zh
                    ? `<div class="wire-entry-sum">${esc(it.summary_zh)}</div>`
                    : ""
                }
              </a>
            `
            )
            .join("");
          return `<div class="wire-date-header">${esc(day)}</div>${rows}`;
        })
        .join("");
    } else {
      subbar.style.display = "none";
      const list = (DATA.community || [])
        .slice()
        .sort((a, b) =>
          String(b.published_at || "").localeCompare(String(a.published_at || ""))
        )
        .slice(0, 18);
      container.innerHTML = list
        .map(
          (it) => `
          <a class="wire-entry" href="${esc(it.url)}" target="_blank" rel="noopener">
            <div class="wire-meta">
              <span class="wire-org">${esc(it.source_label || it.source)}</span>
              ${
                it.points != null
                  ? `<span class="wire-region">${esc(it.points)} ${esc(
                      it.points_label || "PTS"
                    )}</span>`
                  : ""
              }
              <span style="margin-left:auto;color:var(--muted)">${esc(
                fmtDate(it.published_at)
              )}</span>
            </div>
            <div class="wire-entry-title">${esc(it.title_zh || it.title)}</div>
            ${it.why ? `<div class="wire-entry-sum">${esc(it.why)}</div>` : ""}
          </a>
        `
        )
        .join("");
    }
  }

  // ---------- 03 权重 #2：好玩的可视化项目与提示词标本舱 ----------
  function renderVisualSpecimens() {
    const list = DATA.classics || [];
    const stripEl = document.getElementById("specimen-filmstrip");
    const dockEl = document.getElementById("theater-dock");
    const toggleBtn = document.getElementById("toggle-theater-btn");
    if (!list.length) return;

    toggleBtn.classList.toggle("active", state.theaterOpen);
    toggleBtn.textContent = state.theaterOpen
      ? "▼ 收起实盘交互剧场（仅看标本卡片）"
      : "▶ 展开 580px 实盘交互剧场";

    stripEl.innerHTML = list
      .map((c, idx) => {
        const r = (c.runs && c.runs[0]) || {};
        const isSel = state.classicIdx === idx;
        return `
          <article class="specimen-card ${
            isSel ? "selected" : ""
          }" data-spec-idx="${idx}">
            <div>
              <div class="spec-top">
                <span class="spec-model-badge">${esc(
                  c.badge || r.model_name || "LIVE DEMO"
                )}</span>
                <span class="spec-cat">${esc(c.category || "交互实盘")}</span>
              </div>
              <div class="spec-preview-art" style="margin-top:8px">
                ${specimenPreviewSvg(c.id)}
                <span class="spec-live-pill">${
                  isSel && state.theaterOpen ? "● 正在下方剧场运行" : "▶ 点击启动实盘"
                }</span>
              </div>
              <h3 class="spec-title" style="margin-top:9px">${esc(c.name)}</h3>
              <p class="spec-why" style="margin-top:5px">${esc(c.why)}</p>
            </div>
            <div class="spec-actions">
              <button type="button" class="act-btn primary" data-launch-spec="${idx}">
                ${isSel && state.theaterOpen ? "● 剧场运行中" : "▶ 展开实盘画布"}
              </button>
              <button type="button" class="act-btn" data-copy="${esc(
                c.prompt
              )}" data-copy-label="已复制「${esc(c.name)}」Prompt">复制 Prompt</button>
              ${
                r.file
                  ? `<a class="act-btn" href="${esc(
                      r.file
                    )}" target="_blank" rel="noopener" title="新窗口全屏打开">全屏 ↗</a>`
                  : ""
              }
            </div>
          </article>
        `;
      })
      .join("");

    if (!state.theaterOpen) {
      dockEl.hidden = true;
    } else {
      dockEl.hidden = false;
      const c = list[state.classicIdx] || list[0];
      const r = (c.runs && c.runs[0]) || {};
      dockEl.innerHTML = `
        <div class="theater-grid">
          <div class="theater-dossier">
            <div>
              <div class="dossier-kicker">SPECIMEN #${pad2(
                state.classicIdx + 1
              )} // ${esc(c.name_en || "")}</div>
              <h3 class="dossier-title">${esc(c.name)}</h3>
            </div>
            <div class="dossier-block">
              <h4>项目背景与工程亮点</h4>
              <p>${esc(c.origin)} ${esc(c.why)}</p>
            </div>
            ${
              c.look_for && c.look_for.length
                ? `<div class="dossier-block">
                     <h4>实盘交互指南（上手操作）</h4>
                     <ul>${c.look_for.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>
                   </div>`
                : ""
            }
            <div class="prompt-stamp">
              <div class="prompt-stamp-head">
                <span>完整生成 Prompt</span>
                <button type="button" class="act-btn" data-copy="${esc(
                  c.prompt
                )}" data-copy-label="已复制完整 Prompt">复制 Prompt</button>
              </div>
              <pre>${esc(c.prompt)}</pre>
            </div>
          </div>

          <div class="theater-stage-col">
            <div class="stage-col-head">
              <div>
                <span class="stage-model-tag">${esc(r.model_name || r.model)}</span>
                <span> · 单文件零外部依赖实盘 · 耗时 ${esc(r.seconds)}s · ${esc(
        r.completion_tokens || "-"
      )} tokens</span>
              </div>
              <a class="stage-open" href="${esc(
                r.file
              )}" target="_blank" rel="noopener">新标签页全屏运行 ↗</a>
            </div>
            <div class="stage-viewport">
              <iframe src="${esc(r.file)}" title="${esc(c.name)}" loading="lazy"></iframe>
            </div>
          </div>
        </div>
      `;
    }

    // 渲染社区今日最新可玩/可视化项目
    const playRow = document.getElementById("live-playables-row");
    const playables = (DATA.community || [])
      .filter((it) => it.playable || it.category === "play")
      .slice(0, 4);
    playRow.innerHTML = playables
      .map(
        (it) => `
        <div class="mini-play-card">
          <div>
            <div class="mini-play-top">
              <span>${esc(it.source_label || "可在线体验")}</span>
              <span>${
                it.points != null
                  ? "★ " + esc(it.points) + " " + esc(it.points_label || "likes")
                  : esc(fmtDate(it.published_at))
              }</span>
            </div>
            <h4 class="mini-play-title" style="margin-top:4px">
              <a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(
          it.title_zh || it.title
        )}</a>
            </h4>
            <p class="mini-play-why" style="margin-top:4px">${esc(it.why)}</p>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px">
            <span style="font-family:var(--mono);font-size:10.5px;color:var(--muted)">${(
              it.tags || []
            )
              .map((t) => "#" + esc(t))
              .join(" ")}</span>
            <a class="act-btn" href="${esc(
              it.url
            )}" target="_blank" rel="noopener">${
          it.playable ? "在线试玩 ↗" : "查看项目 ↗"
        }</a>
          </div>
        </div>
      `
      )
      .join("");
  }

  // ---------- 04 权重 #3：去同质化社区深度总表 & HF 飙升榜 ----------
  function renderChips() {
    const items = DATA.community || [];
    const counts = { all: items.length, tool: 0, play: 0, bench: 0, talk: 0 };
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
        (it.tags || []).join(" ")
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
      container.innerHTML = `<div style="padding:32px;text-align:center;color:var(--muted)">当前筛选条件下无匹配条目。</div>`;
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

        const actions = [];
        if (it.playable) {
          actions.push(
            `<a class="act-btn primary" href="${esc(
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
            )}" target="_blank" rel="noopener">评论区 ↗</a>`
          );
        }

        return `
          <article class="ledger-item" id="item-${esc(it.id)}">
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

  function renderHfTrending() {
    const ol = document.getElementById("hf-trending");
    const list = (DATA.hf_trending || []).slice(0, 10);
    ol.innerHTML = list
      .map(
        (m, i) => `
        <li>
          <span class="hf-rank">${pad2(i + 1)}</span>
          <a class="hf-name" href="${esc(m.url)}" target="_blank" rel="noopener">${esc(
          m.id
        )}</a>
          <span class="hf-likes">♥ ${esc(m.likes || 0)}</span>
        </li>
      `
      )
      .join("");
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

    const discBtn = e.target.closest("[data-disc]");
    if (discBtn) {
      state.discipline = discBtn.getAttribute("data-disc");
      renderQuantSkills();
      return;
    }

    const wireTabBtn = e.target.closest("[data-wire-tab]");
    if (wireTabBtn) {
      state.wireTab = wireTabBtn.getAttribute("data-wire-tab");
      renderLiveWire();
      return;
    }

    const regBtn = e.target.closest("#region-seg button");
    if (regBtn) {
      state.region = regBtn.getAttribute("data-region");
      document.querySelectorAll("#region-seg button").forEach((b) => {
        b.classList.toggle("on", b === regBtn);
      });
      renderLiveWire();
      return;
    }

    const launchBtn = e.target.closest("[data-launch-spec]");
    if (launchBtn) {
      e.stopPropagation();
      state.classicIdx = Number(launchBtn.getAttribute("data-launch-spec")) || 0;
      state.theaterOpen = true;
      renderVisualSpecimens();
      document.getElementById("theater-dock").scrollIntoView({ behavior: "smooth", block: "nearest" });
      return;
    }

    const specCard = e.target.closest("[data-spec-idx]");
    if (specCard && !e.target.closest("a, button")) {
      state.classicIdx = Number(specCard.getAttribute("data-spec-idx")) || 0;
      state.theaterOpen = true;
      renderVisualSpecimens();
      return;
    }

    const chip = e.target.closest("[data-cat]");
    if (chip) {
      state.cat = chip.getAttribute("data-cat");
      state.limit = 20;
      renderChips();
      renderFeed();
      return;
    }

    const jumpBtn = e.target.closest("[data-jump]");
    if (jumpBtn) {
      const id = jumpBtn.getAttribute("data-jump");
      state.cat = "all";
      state.query = "";
      state.limit = 80;
      renderChips();
      renderFeed();
      const target = document.getElementById("item-" + id);
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      return;
    }
  });

  document.getElementById("toggle-theater-btn").addEventListener("click", () => {
    state.theaterOpen = !state.theaterOpen;
    renderVisualSpecimens();
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
    state.limit += 25;
    renderFeed();
  });

  // 初始化渲染
  renderTelemetry();
  renderBriefing();
  renderQuantSkills();
  renderLiveWire();
  renderVisualSpecimens();
  renderChips();
  renderFeed();
  renderHfTrending();
})();
