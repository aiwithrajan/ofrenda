// ==========================================================================
// OFRENDA — THE DIGITAL MEMORIAL
// Runtime Controller: Audio Synthesis, Dynamic Terminal, & Altar Interaction
// ==========================================================================

// Pre-registered client-side archive knowledge base (Instant grounded fallback)
const ARCHIVE_KNOWLEDGE = [
  {
    triggers: ["why", "deprecated", "deprecate", "die", "death", "reason", "rewritten"],
    answer: "On March 22, 2019, issue #3142 ('Request’s Past, Present and Future') declared maintenance mode. With over 41,000 dependent packages and 14M weekly downloads, rewriting request for modern async/await patterns, streams, or HTTP/2 would break the foundational plumbing of the JavaScript ecosystem.",
    citation: "Issue #3142 • Commit aded7e4f (2020-02-11)"
  },
  {
    triggers: ["when", "date", "february", "2020", "deprecated"],
    answer: "request/request was fully deprecated on February 11, 2020 via commit aded7e4f authored by original creator Mikeal Rogers.",
    citation: "Commit aded7e4f (2020-02-11)"
  },
  {
    triggers: ["final", "commit", "last commit", "message", "aded7e4f", "3c0cddc7"],
    answer: "The final deprecation commit aded7e4f ('doc: note full deprecation (#3267)') was authored by Mikeal Rogers on February 11, 2020. A subsequent typo fix commit 3c0cddc7 by Gregor Martynus sealed the archive.",
    citation: "Commit aded7e4f • Commit 3c0cddc7 (git log)"
  },
  {
    triggers: ["http/2", "http2", "support", "native"],
    answer: "No native HTTP/2 support was ever officially implemented. Maintainers determined that HTTP/2 streaming architecture required a complete ground-up rewrite that was incompatible with request's Node 0.4 callback foundations.",
    citation: "Issue #3142 • Issue #2311"
  },
  {
    triggers: ["downloads", "weekly", "traffic", "scale"],
    answer: "At the time of deprecation declaration in Issue #3142, request was downloaded 14 million times a week and served as a direct or transitive dependency for over 41,000 packages.",
    citation: "Issue #3142 • npm registry"
  },
  {
    triggers: ["license", "software license", "apache", "mit"],
    answer: "request operated under the Apache License 2.0 (SPDX identifier: Apache-2.0), preserved across all versions.",
    citation: "Repository Metadata • LICENSE file"
  },
  {
    triggers: ["author", "creator", "who made", "who built", "mikeal"],
    answer: "Mikeal Rogers was the original author and primary maintainer who conceived request in January 2011.",
    citation: "Repository Metadata • package.json"
  },
  {
    triggers: ["alternatives", "substitute", "got", "axios", "undici", "fetch"],
    answer: "Recommended modern alternatives include got, axios, node-fetch, undici, or native global fetch in modern Node.js.",
    citation: "Issue #3142 Deprecation Roadmap"
  }
];

const DEFAULT_ABSTENTION = {
  answer: "The archive is silent on that.",
  citation: "Strict Abstention Gate (PRD v2.0 §12)"
};

// --------------------------------------------------------------------------
// 1. Synthetic Web Audio Bell / Chime Generator
// --------------------------------------------------------------------------
class SacredChime {
  constructor() {
    this.ctx = null;
  }

  init() {
    if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
    }
  }

  ring() {
    try {
      this.init();
      if (!this.ctx) return;
      if (this.ctx.state === "suspended") {
        this.ctx.resume();
      }

      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(528, now); // 528 Hz Solfeggio frequency
      osc.frequency.exponentialRampToValueAtTime(1056, now + 0.35);

      gain.gain.setValueAtTime(0.04, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.85);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.85);
    } catch (e) {
      // Audio autoplay policy catch
    }
  }
}

const chime = new SacredChime();

// --------------------------------------------------------------------------
// 2. Ambient Floating Embers Canvas
// --------------------------------------------------------------------------
function initEmbersCanvas() {
  const canvas = document.getElementById("embersCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  const particles = [];
  const COUNT = 32;

  for (let i = 0; i < COUNT; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      radius: Math.random() * 1.5 + 0.5,
      speedY: Math.random() * 0.45 + 0.15,
      speedX: (Math.random() - 0.5) * 0.25,
      opacity: Math.random() * 0.5 + 0.15,
      flickerSpeed: Math.random() * 0.02 + 0.01,
      flickerOffset: Math.random() * Math.PI * 2
    });
  }

  let time = 0;
  function animate() {
    time += 0.02;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (let p of particles) {
      p.y -= p.speedY;
      p.x += p.speedX;

      if (p.y < -10) {
        p.y = canvas.height + 10;
        p.x = Math.random() * canvas.width;
      }
      if (p.x < 0) p.x = canvas.width;
      if (p.x > canvas.width) p.x = 0;

      const alpha = p.opacity * (0.6 + 0.4 * Math.sin(time * 3 + p.flickerOffset));
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(245, 158, 11, ${alpha})`;
      ctx.shadowColor = "#f59e0b";
      ctx.shadowBlur = 4;
      ctx.fill();
    }
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);
}

// --------------------------------------------------------------------------
// 3. Interactive Offering & Candles
// --------------------------------------------------------------------------
let candlesLitCount = 14210;

function handleLightCandle() {
  candlesLitCount++;
  chime.ring();

  const countDisplay = document.getElementById("candlesCountDisplay");
  if (countDisplay) {
    countDisplay.textContent = candlesLitCount.toLocaleString();
    countDisplay.style.color = "#fbbf24";
    setTimeout(() => (countDisplay.style.color = "#ffffff"), 350);
  }

  // Ignite from 3 outline candles into full glowing candle cluster
  const shrine = document.getElementById("candleShrineWrapper");
  if (shrine) {
    if (shrine.classList.contains("state-unlit")) {
      shrine.classList.remove("state-unlit");
      shrine.classList.add("state-lit");
      shrine.setAttribute("title", "Altar fully kindled in memoriam. Click to offer another candle.");
    }
    shrine.style.transform = "scale(1.08)";
    setTimeout(() => (shrine.style.transform = ""), 250);
  }
}

// --------------------------------------------------------------------------
// 4. Modal Dialog Controller
// --------------------------------------------------------------------------
function initModal() {
  const modal = document.getElementById("archiveModal");
  const closeBtn = document.getElementById("modalCloseBtn");
  const exploreBtn = document.getElementById("btnExploreArchive");
  const viewAllBtn = document.getElementById("btnViewAllRepos");
  const navTabs = document.querySelectorAll(".nav-tab");

  function openModal() {
    if (modal) {
      modal.classList.add("open");
      modal.setAttribute("aria-hidden", "false");
    }
  }

  function closeModal() {
    if (modal) {
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
    }
  }

  if (exploreBtn) exploreBtn.addEventListener("click", openModal);
  if (viewAllBtn) viewAllBtn.addEventListener("click", openModal);
  if (closeBtn) closeBtn.addEventListener("click", closeModal);

  const specimenCards = document.querySelectorAll(".specimen-card");
  specimenCards.forEach((card) => {
    card.addEventListener("click", () => {
      const repo = card.getAttribute("data-repo");
      chime.ring();
      openModal();
      const searchInput = document.getElementById("ledgerSearchInput");
      if (searchInput && repo) {
        searchInput.value = repo;
        searchInput.dispatchEvent(new Event("input"));
      }
    });
  });

  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal();
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal && modal.classList.contains("open")) {
      closeModal();
    }
  });

  navTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      navTabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const tabName = tab.getAttribute("data-tab");
      if (tabName === "ghosting" || tabName === "methodology") {
        openModal();
      }
    });
  });
}

// --------------------------------------------------------------------------
// 5. Forensic Interview Terminal
// --------------------------------------------------------------------------
function initTerminal() {
  const form = document.getElementById("terminalForm");
  const input = document.getElementById("terminalInput");
  const chatLog = document.getElementById("terminalChatLog");
  const chips = document.querySelectorAll(".quick-chip");

  if (!form || !input || !chatLog) return;

  function appendChat(text, type) {
    const msg = document.createElement("div");
    msg.className = `chat-msg ${type}`;
    msg.textContent = text;
    chatLog.appendChild(msg);
    chatLog.scrollTop = chatLog.scrollHeight;
    return msg;
  }

  async function queryGhost(question) {
    appendChat(question, "user");
    input.value = "";
    const pendingMsg = appendChat("...", "bot");

    try {
      // Live backend POST /api/ask call
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
      });

      if (res.ok) {
        const data = await res.json();
        pendingMsg.textContent = data.answer || "The archive is silent on that.";
        return;
      }
    } catch (e) {
      // Fallback to client-side grounded knowledge
    }

    // Client-side fallback matching
    const qLower = question.toLowerCase();
    const matched = ARCHIVE_KNOWLEDGE.find((item) =>
      item.triggers.some((trig) => qLower.includes(trig))
    );

    if (matched) {
      pendingMsg.textContent = `${matched.answer} (${matched.citation})`;
    } else {
      pendingMsg.textContent = DEFAULT_ABSTENTION.answer;
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (q) queryGhost(q);
  });

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-q");
      if (q) queryGhost(q);
    });
  });
}

// --------------------------------------------------------------------------
// 6. Specimen Ledger Data & Filtering
// --------------------------------------------------------------------------
const SAMPLE_SPECIMENS = [
  { name: "request/request", status: "DEPRECATED", dls: "14,000,000", bus: 1, conceived: "2011", silence: "2020-02" },
  { name: "pallets/flask", status: "ACTIVE", dls: "12,000,000", bus: 4, conceived: "2010", silence: "None" },
  { name: "django/django", status: "ACTIVE", dls: "8,500,000", bus: 8, conceived: "2005", silence: "None" },
  { name: "twilio/twilio-python", status: "MAINTAINED", dls: "4,100,000", bus: 3, conceived: "2011", silence: "None" },
  { name: "left-pad", status: "UNPUBLISHED", dls: "2,500,000", bus: 1, conceived: "2016", silence: "2016-03" },
  { name: "event-stream", status: "ABANDONED", dls: "1,800,000", bus: 1, conceived: "2011", silence: "2018-11" },
  { name: "colors.js", status: "SABOTAGED", dls: "20,000,000", bus: 1, conceived: "2011", silence: "2022-01" },
  { name: "faker.js", status: "SABOTAGED", dls: "2,800,000", bus: 1, conceived: "2011", silence: "2022-01" },
  { name: "moment/moment", status: "MAINTENANCE", dls: "18,000,000", bus: 2, conceived: "2011", silence: "2020-09" },
  { name: "lodash/lodash", status: "MAINTENANCE", dls: "45,000,000", bus: 1, conceived: "2012", silence: "2021-04" },
  { name: "axios/axios", status: "ACTIVE", dls: "38,000,000", bus: 4, conceived: "2014", silence: "None" },
  { name: "sindresorhus/got", status: "ACTIVE", dls: "16,000,000", bus: 2, conceived: "2014", silence: "None" },
  { name: "node-fetch/node-fetch", status: "ACTIVE", dls: "30,000,000", bus: 3, conceived: "2015", silence: "None" },
  { name: "nodejs/undici", status: "ACTIVE", dls: "11,000,000", bus: 5, conceived: "2018", silence: "None" },
];

function initLedger() {
  const tbody = document.getElementById("ledgerTableBody");
  const searchInput = document.getElementById("ledgerSearchInput");
  if (!tbody) return;

  function renderTable(filterText = "") {
    const q = filterText.toLowerCase();
    const rows = SAMPLE_SPECIMENS.filter((s) => s.name.toLowerCase().includes(q));

    tbody.innerHTML = rows
      .map(
        (s) => `
        <tr>
          <td><strong>${s.name}</strong></td>
          <td><span style="color: ${s.status === "ACTIVE" ? "#22c55e" : s.status === "DEPRECATED" ? "#ef4444" : "#f59e0b"}">${s.status}</span></td>
          <td>${s.dls}</td>
          <td>${s.bus}</td>
          <td>${s.conceived}</td>
          <td>${s.silence}</td>
        </tr>
      `
      )
      .join("");
  }

  renderTable();

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      renderTable(e.target.value);
    });
  }
}

// --------------------------------------------------------------------------
// 7. Evidence Tag Pills & Terminal Button Quick Interaction
// --------------------------------------------------------------------------
function initEvidencePills() {
  const pills = document.querySelectorAll(".ev-btn, .evidence-pill");
  pills.forEach((pill) => {
    pill.addEventListener("click", () => {
      const type = pill.getAttribute("data-evidence") || "records";
      chime.ring();
      pill.style.borderColor = "#f59e0b";
      setTimeout(() => (pill.style.borderColor = ""), 400);

      // Open modal with specific query
      const modal = document.getElementById("archiveModal");
      const input = document.getElementById("terminalInput");
      if (modal && input) {
        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
        input.value = `Tell me about ${type} for request/request`;
        input.focus();
      }
    });
  });

  const termBtn = document.getElementById("dossierTerminalBtn");
  if (termBtn) {
    termBtn.addEventListener("click", () => {
      chime.ring();
      const modal = document.getElementById("archiveModal");
      const input = document.getElementById("terminalInput");
      if (modal) {
        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
        if (input) input.focus();
      }
    });
  }
}

// --------------------------------------------------------------------------
// Bootstrap on DOM Ready
// --------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initEmbersCanvas();
  initModal();
  initTerminal();
  initLedger();
  initEvidencePills();

  // Wire buttons
  const lightBtn = document.getElementById("btnLightOffering");
  if (lightBtn) lightBtn.addEventListener("click", handleLightCandle);

  const shrineWrap = document.getElementById("candleShrineWrapper");
  if (shrineWrap) shrineWrap.addEventListener("click", handleLightCandle);
});
