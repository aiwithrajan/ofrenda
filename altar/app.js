// ==========================================================================
// OFRENDA — THE GHOST IN THE MACHINE
// Forensic Interview & Altar Interactive Runtime (UI/UX Pro Max Edition)
// ==========================================================================

// Pre-registered client-side archive knowledge base (Instant fallback)
const ARCHIVE_KNOWLEDGE = [
  {
    triggers: ["why", "deprecated", "deprecate", "die", "death", "reason", "rewritten"],
    answer: "On March 22, 2019, issue #3142 ('Request’s Past, Present and Future') declared maintenance mode. With over 41,000 dependent packages and 14M weekly downloads, rewriting request for modern async/await patterns, streams, or HTTP/2 would break the foundational plumbing of the JavaScript ecosystem.",
    citation: "Issue #3142 • Commit aded7e4f (2020-02-11)"
  },
  {
    triggers: ["final", "commit", "last commit", "message", "aded7e4f", "3c0cddc7"],
    answer: "The final deprecation commit aded7e4f ('doc: note full deprecation (#3267)') was authored by Mikeal Rogers on February 11, 2020. A subsequent typo fix commit 3c0cddc7 ('README: typo in deprecation message (#3268)') by Gregor Martynus sealed the repository archive.",
    citation: "Commit aded7e4f • Commit 3c0cddc7 (git log)"
  },
  {
    triggers: ["http/2", "http2", "support", "native"],
    answer: "No native HTTP/2 support was ever officially implemented. Maintainers determined that HTTP/2 streaming architecture required a complete ground-up rewrite that was incompatible with request's Node 0.4 callback foundations.",
    citation: "Issue #3142 • Issue #2311 (comment by @mikeal)"
  },
  {
    triggers: ["downloads", "weekly", "traffic", "scale"],
    answer: "At the time of deprecation declaration in Issue #3142, request was downloaded 14 million times a week and served as a direct or transitive dependency for over 41,000 packages in the npm registry.",
    citation: "Issue #3142 • Repository Metadata (npm registry)"
  },
  {
    triggers: ["license", "software license", "apache", "mit"],
    answer: "request operated under the Apache License 2.0 (SPDX identifier: Apache-2.0), preserved across all versions.",
    citation: "Repository Metadata • LICENSE file"
  },
  {
    triggers: ["ghosting", "divergence", "strangers", "latency", "gap"],
    answer: "The Ghosting Band emerged in 2017: maintainer response latency to stranger inquiries rose from 4.2 days to over 180 days, alerting to abandonment a full 35 months prior to the final git deprecation commit.",
    citation: "TabPFN Feature f4_latency_trend & LORO Model Fit"
  },
  {
    triggers: ["born", "created", "created_at", "genesis", "who built"],
    answer: "The repository was created on January 23, 2011 by Mikeal Rogers with the goal of being the 'simplest possible way to make http calls' in Node.js.",
    citation: "Repository Metadata (id: 1283503) • git log"
  }
];

const DEFAULT_ABSTENTION = {
  answer: "The archive is silent on that.",
  citation: "Strict Abstention Gate (PRD v2.0 §12)"
};

// --------------------------------------------------------------------------
// Web Audio API Synthetic Chime (Zero External Asset Dependency)
// --------------------------------------------------------------------------
class MemorialChime {
  constructor() {
    this.ctx = null;
  }

  init() {
    if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
    }
  }

  playFlame() {
    try {
      this.init();
      if (!this.ctx || this.ctx.state === "suspended") {
        this.ctx?.resume();
      }
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(440, this.ctx.currentTime); // A4
      osc.frequency.exponentialRampToValueAtTime(880, this.ctx.currentTime + 0.3); // A5

      gain.gain.setValueAtTime(0.04, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.6);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.6);
    } catch (e) {
      // Audio autoplay policy catch
    }
  }
}

const chime = new MemorialChime();

// --------------------------------------------------------------------------
// Embers Canvas Animation
// --------------------------------------------------------------------------
function initEmbersCanvas() {
  const canvas = document.getElementById("embersCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const isReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (isReducedMotion) return;

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener("resize", () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const numParticles = Math.min(35, Math.floor(width / 35));
  const particles = [];

  for (let i = 0; i < numParticles; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      size: Math.random() * 2 + 0.8,
      speedY: Math.random() * 0.45 + 0.15,
      speedX: (Math.random() - 0.5) * 0.25,
      opacity: Math.random() * 0.6 + 0.2,
      pulse: Math.random() * Math.PI,
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.y -= p.speedY;
      p.x += p.speedX;
      p.pulse += 0.02;

      if (p.y < -10) {
        p.y = height + 10;
        p.x = Math.random() * width;
      }

      const currentOpacity = p.opacity * (0.6 + 0.4 * Math.sin(p.pulse));

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(245, 158, 11, ${currentOpacity})`;
      ctx.shadowColor = "#f59e0b";
      ctx.shadowBlur = 4;
      ctx.fill();
    }

    requestAnimationFrame(render);
  }

  requestAnimationFrame(render);
}

// --------------------------------------------------------------------------
// Interactive Candle Altar Component
// --------------------------------------------------------------------------
const CANDLE_CONFIGS = [
  { height: 44, width: 20 },
  { height: 58, width: 22 },
  { height: 72, width: 24 },
  { height: 85, width: 26 }, // Center tall candle
  { height: 72, width: 24 },
  { height: 58, width: 22 },
  { height: 44, width: 20 },
];

function createCandleSvg(cfg, idx) {
  const div = document.createElement("div");
  div.className = "svg-candle";
  div.setAttribute("role", "button");
  div.setAttribute("tabindex", "0");
  div.setAttribute("aria-label", `Memorial candle ${idx + 1}. Click to toggle flame.`);
  div.setAttribute("data-lit", "true");

  div.innerHTML = `
    <div class="candle-flame-wrap" aria-hidden="true">
      <svg width="22" height="36" viewBox="0 0 22 36" fill="none">
        <defs>
          <radialGradient id="flameGrad${idx}" cx="50%" cy="65%" r="50%">
            <stop offset="0%" stop-color="#ffffff"/>
            <stop offset="35%" stop-color="#fef08a"/>
            <stop offset="70%" stop-color="#f59e0b"/>
            <stop offset="100%" stop-color="#ea580c"/>
          </radialGradient>
        </defs>
        <path d="M11 2 C8 9 3 15 3 23 C3 28 6.5 33 11 33 C15.5 33 19 28 19 23 C19 15 14 9 11 2 Z" fill="url(#flameGrad${idx})"/>
        <ellipse cx="11" cy="24" rx="3.5" ry="5.5" fill="#ffffff" opacity="0.85"/>
      </svg>
    </div>
    <div class="candle-body" style="height: ${cfg.height}px; width: ${cfg.width}px;" aria-hidden="true"></div>
  `;

  function toggleCandle() {
    const isLit = div.getAttribute("data-lit") === "true";
    if (isLit) {
      div.setAttribute("data-lit", "false");
      div.classList.add("extinguished");
      div.setAttribute("aria-label", `Memorial candle ${idx + 1} (extinguished). Click to rekindle.`);
    } else {
      div.setAttribute("data-lit", "true");
      div.classList.remove("extinguished");
      div.setAttribute("aria-label", `Memorial candle ${idx + 1} (burning). Click to extinguish.`);
      chime.playFlame();
    }
  }

  div.addEventListener("click", toggleCandle);
  div.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggleCandle();
    }
  });

  return div;
}

function initCandleAltar() {
  const row = document.getElementById("candlesRow");
  const lightBtn = document.getElementById("lightOfferingBtn");
  const counter = document.getElementById("offeringCounter");
  if (!row) return;

  row.innerHTML = "";
  const candleElements = CANDLE_CONFIGS.map((cfg, i) => {
    const el = createCandleSvg(cfg, i);
    row.appendChild(el);
    return el;
  });

  let offeringTally = 14208;

  if (lightBtn) {
    lightBtn.addEventListener("click", () => {
      chime.playFlame();
      offeringTally++;
      if (counter) {
        counter.textContent = `${offeringTally.toLocaleString()} candles lit across 150 repositories`;
      }

      // Ensure all candles are glowing
      candleElements.forEach((el) => {
        el.setAttribute("data-lit", "true");
        el.classList.remove("extinguished");
      });

      // Quick visual burst on button
      lightBtn.style.transform = "scale(0.96)";
      setTimeout(() => (lightBtn.style.transform = ""), 150);
    });
  }
}

// --------------------------------------------------------------------------
// Forensic Interview Terminal Runtime
// --------------------------------------------------------------------------
function initForensicTerminal() {
  const chatViewport = document.getElementById("chatViewport");
  const chatForm = document.getElementById("chatForm");
  const userInput = document.getElementById("userInput");
  const chips = document.querySelectorAll(".chip");

  if (!chatViewport || !chatForm || !userInput) return;

  function appendMessage(text, isUser, citation = null) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${isUser ? "user" : "assistant"}`;

    const avatar = document.createElement("div");
    avatar.className = `avatar ${isUser ? "user-avatar" : "ghost-avatar"}`;
    avatar.setAttribute("aria-hidden", "true");

    if (isUser) {
      avatar.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
      `;
    } else {
      avatar.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 10h.01M15 10h.01M12 2a8 8 0 0 0-8 8v12l3-3 2.5 2.5L12 19l2.5 2.5L17 19l3 3V10a8 8 0 0 0-8-8z"/>
        </svg>
      `;
    }

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    const p = document.createElement("p");
    p.textContent = text;
    bubble.appendChild(p);

    if (!isUser) {
      const actions = document.createElement("div");
      actions.className = "bubble-actions";

      if (citation) {
        const citePill = document.createElement("span");
        citePill.className = "citation-pill";
        citePill.innerHTML = `
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
          </svg>
          Source: ${citation}
        `;
        actions.appendChild(citePill);
      }

      const copyBtn = document.createElement("button");
      copyBtn.type = "button";
      copyBtn.className = "message-copy-btn";
      copyBtn.setAttribute("aria-label", "Copy archive statement to clipboard");
      copyBtn.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
        </svg>
        <span>Copy</span>
      `;

      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(text);
        copyBtn.querySelector("span").textContent = "Copied!";
        setTimeout(() => {
          copyBtn.querySelector("span").textContent = "Copy";
        }, 1800);
      });

      actions.appendChild(copyBtn);
      bubble.appendChild(actions);
    }

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    chatViewport.appendChild(msgDiv);
    chatViewport.scrollTop = chatViewport.scrollHeight;
  }

  async function handleQuery(query) {
    const qTrimmed = query.trim();
    if (!qTrimmed) return;

    appendMessage(qTrimmed, true);

    // Typing indicator
    const typingMsg = document.createElement("div");
    typingMsg.className = "message assistant";
    typingMsg.innerHTML = `
      <div class="avatar ghost-avatar" aria-hidden="true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 10h.01M15 10h.01M12 2a8 8 0 0 0-8 8v12l3-3 2.5 2.5L12 19l2.5 2.5L17 19l3 3V10a8 8 0 0 0-8-8z"/>
        </svg>
      </div>
      <div class="bubble">
        <span class="typing-dots">
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
        </span>
        <em style="margin-left: 8px; font-size: 0.85rem; color: #94a3b8;">Searching 11,748 corpus records...</em>
      </div>
    `;
    chatViewport.appendChild(typingMsg);
    chatViewport.scrollTop = chatViewport.scrollHeight;

    // 1. Attempt live Ollama / Python server backend
    try {
      const resp = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: qTrimmed }),
      });

      if (resp.ok) {
        const data = await resp.json();
        typingMsg.remove();
        const citStr = data.citations && data.citations.length > 0 ? data.citations.join(" • ") : null;
        appendMessage(data.answer, false, citStr);
        return;
      }
    } catch (e) {
      // Backend not running -> fall back smoothly
    }

    // 2. Client-side grounded lookup fallback
    setTimeout(() => {
      typingMsg.remove();
      const qLower = qTrimmed.toLowerCase();
      let matched = null;

      for (const item of ARCHIVE_KNOWLEDGE) {
        if (item.triggers.some((t) => qLower.includes(t))) {
          matched = item;
          break;
        }
      }

      if (!matched) {
        matched = DEFAULT_ABSTENTION;
      }

      appendMessage(matched.answer, false, matched.citation);
    }, 450);
  }

  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = userInput.value;
    userInput.value = "";
    handleQuery(q);
  });

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-q");
      if (q) {
        userInput.value = "";
        handleQuery(q);
      }
    });
  });
}

// --------------------------------------------------------------------------
// Figure Lightbox Modal
// --------------------------------------------------------------------------
function initFigureLightbox() {
  const modal = document.getElementById("lightboxModal");
  const backdrop = document.getElementById("lightboxBackdrop");
  const closeBtn = document.getElementById("lightboxCloseBtn");
  const imgEl = document.getElementById("lightboxImg");
  const titleEl = document.getElementById("lightboxTitle");
  const captionEl = document.getElementById("lightboxCaption");

  if (!modal || !backdrop || !closeBtn || !imgEl) return;

  let lastActiveElement = null;

  function openLightbox(src, title, caption, triggerEl) {
    lastActiveElement = triggerEl;
    imgEl.src = src;
    imgEl.alt = title;
    if (titleEl) titleEl.textContent = title;
    if (captionEl) captionEl.textContent = caption;
    modal.removeAttribute("hidden");
    document.body.style.overflow = "hidden";
    closeBtn.focus();
  }

  function closeLightbox() {
    modal.setAttribute("hidden", "");
    document.body.style.overflow = "";
    imgEl.src = "";
    if (lastActiveElement && typeof lastActiveElement.focus === "function") {
      lastActiveElement.focus();
    }
  }

  document.querySelectorAll(".figure-card").forEach((card) => {
    const triggerOpen = () => {
      const figSrc = card.getAttribute("data-fig");
      const title = card.getAttribute("data-title") || "Statistical Visualization";
      const caption = card.getAttribute("data-caption") || "";
      if (figSrc) {
        openLightbox(figSrc, title, caption, card);
      }
    };

    card.addEventListener("click", triggerOpen);
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        triggerOpen();
      }
    });
  });

  closeBtn.addEventListener("click", closeLightbox);
  backdrop.addEventListener("click", closeLightbox);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.hasAttribute("hidden")) {
      closeLightbox();
    }
  });
}

// --------------------------------------------------------------------------
// Interactive 19-Category Honest Ledger Filter
// --------------------------------------------------------------------------
function initLedgerFilter() {
  const searchInput = document.getElementById("ledgerSearchInput");
  const filterPills = document.querySelectorAll(".f-pill");
  const table = document.getElementById("ledgerTable");
  const countLabel = document.getElementById("ledgerCountLabel");

  if (!table) return;

  const rows = table.querySelectorAll("tbody tr");
  let activeFilter = "all";
  let searchTerm = "";

  function applyFilters() {
    let visibleCount = 0;

    rows.forEach((row) => {
      const cat = row.getAttribute("data-cat") || "";
      const text = row.textContent.toLowerCase();

      const matchesCat = activeFilter === "all" || cat === activeFilter;
      const matchesSearch = !searchTerm || text.includes(searchTerm);

      if (matchesCat && matchesSearch) {
        row.style.display = "";
        visibleCount++;
      } else {
        row.style.display = "none";
      }
    });

    if (countLabel) {
      countLabel.textContent = `Showing ${visibleCount} of ${rows.length} verified integrations`;
    }
  }

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchTerm = e.target.value.toLowerCase().trim();
      applyFilters();
    });
  }

  filterPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      filterPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      activeFilter = pill.getAttribute("data-filter") || "all";
      applyFilters();
    });
  });
}

// --------------------------------------------------------------------------
// Code Block Copy Buttons
// --------------------------------------------------------------------------
function initCopyButtons() {
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const text = btn.getAttribute("data-copy");
      if (!text) return;

      navigator.clipboard.writeText(text);
      const span = btn.querySelector("span");
      if (span) {
        const orig = span.textContent;
        span.textContent = "Copied!";
        setTimeout(() => (span.textContent = orig), 1800);
      }
    });
  });
}

// --------------------------------------------------------------------------
// Initialize All Components on DOM Ready
// --------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initEmbersCanvas();
  initCandleAltar();
  initForensicTerminal();
  initFigureLightbox();
  initLedgerFilter();
  initCopyButtons();
});
