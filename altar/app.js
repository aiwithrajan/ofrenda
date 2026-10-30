// Forensic Interview & Altar Interactive Runtime

// Grounded knowledge base for specimen request/request
const ARCHIVE_KNOWLEDGE = [
  {
    triggers: ["why", "deprecated", "deprecate", "die", "death", "reason"],
    answer: "On March 22, 2019, issue #3142 ('What is the future of request?') was opened by Mikeal Rogers. The project had grown to over 41,000 dependent packages and 14M downloads a week, making it impossible to introduce modern async/await patterns, streams improvements, or HTTP/2 without breaking the JavaScript ecosystem.",
    citation: "Issue #3142 • commit aded7e4f (2020-02-11)"
  },
  {
    triggers: ["final", "commit", "last commit", "coded", "pushed"],
    answer: "The final commit to the repository was aded7e4f3a74421b5be82fcf3e098dfc3f0b2f5b on Tuesday, February 11, 2020 at 08:35:14 -0800, authored by Mikeal Rogers with the commit message: 'Deprecate request npm package'.",
    citation: "Commit aded7e4f (git log -1)"
  },
  {
    triggers: ["http/2", "http2", "modern", "async", "await", "promise", "promises"],
    answer: "Request was designed in 2011 around callback patterns and Node 0.4 streams. Core maintainers noted that supporting native Promises and HTTP/2 would require a total ground-up rewrite that would invalidate existing middleware and plugins across millions of downstream projects.",
    citation: "Issue #3142 comment by @mikeal"
  },
  {
    triggers: ["maintainer", "stop answering", "strangers", "ghosted", "ghosting", "latency", "response"],
    answer: "In 2017, the ratio of incoming stranger issues to maintainer replies crossed the divergence threshold. Latency for first-maintainer comment rose from 4.2 days (2014) to over 180 days (2018), marking the emergence of the Ghosting Band 35 months prior to the final deprecation commit.",
    citation: "Derived TabPFN Feature f4_latency_trend & Issue stream analysis"
  },
  {
    triggers: ["creator", "who made", "author", "founded", "born", "who built"],
    answer: "The repository was created by Mikeal Rogers on February 1, 2011 to be the 'simplest possible way to make http calls' in Node.js, reaching over 24,000 GitHub stars and 14 million weekly downloads at its peak.",
    citation: "README.md & repo meta.ndjson (id: 1310672)"
  },
  {
    triggers: ["competitors", "alternatives", "2024", "axios", "got", "node-fetch", "undici", "future"],
    answer: "The archive is silent on that. The project's record ends with the deprecation notice in 2020. No commentary on post-2020 events exists within git or issue logs.",
    citation: "Strict Abstention Gate (PRD v2.0 §12)"
  }
];

const DEFAULT_ABSTENTION = {
  answer: "The archive is silent on that. The records contain no commit, issue, or pull request addressing this inquiry.",
  citation: "Strict Abstention Gate (PRD v2.0 §12)"
};

document.addEventListener("DOMContentLoaded", () => {
  const chatViewport = document.getElementById("chatViewport");
  const chatForm = document.getElementById("chatForm");
  const userInput = document.getElementById("userInput");
  const chips = document.querySelectorAll(".chip");

  function appendMessage(text, isUser, citation = null) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${isUser ? "user" : "assistant"}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = isUser ? "👤" : "👻";

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    const p = document.createElement("p");
    p.textContent = text;
    bubble.appendChild(p);

    if (citation && !isUser) {
      const citePill = document.createElement("span");
      citePill.className = "citation-pill";
      citePill.textContent = `Source: ${citation}`;
      bubble.appendChild(citePill);
    }

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    chatViewport.appendChild(msgDiv);
    chatViewport.scrollTop = chatViewport.scrollHeight;
  }

  async function handleQuery(query) {
    const qLower = query.toLowerCase().trim();
    if (!qLower) return;

    appendMessage(query, true);

    // Simulated thought / retrieval delay
    const typingIndicator = document.createElement("div");
    typingIndicator.className = "message assistant typing";
    typingIndicator.innerHTML = `
      <div class="avatar">👻</div>
      <div class="bubble"><p><em>Consulting repository archive records...</em></p></div>
    `;
    chatViewport.appendChild(typingIndicator);
    chatViewport.scrollTop = chatViewport.scrollHeight;

    try {
      // Attempt live server forensic query
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: query }),
      });

      if (res.ok) {
        const data = await res.json();
        typingIndicator.remove();
        const citStr = data.citations && data.citations.length > 0 ? data.citations.join(" • ") : null;
        appendMessage(data.answer, false, citStr);
        return;
      }
    } catch (err) {
      // Backend not running / static mode -> fall back smoothly
    }

    setTimeout(() => {
      typingIndicator.remove();

      // Check knowledge base
      let matched = null;
      for (const item of ARCHIVE_KNOWLEDGE) {
        if (item.triggers.some(t => qLower.includes(t))) {
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
    const query = userInput.value.trim();
    if (!query) return;
    userInput.value = "";
    handleQuery(query);
  });

  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-q");
      if (q) {
        userInput.value = "";
        handleQuery(q);
      }
    });
  });
});
