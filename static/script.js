/* Consolidated front-end logic for chat UI, sidebar, and interactions.
   Drop this file into static/script.js (replace existing script.js).
*/

(() => {
  // State
  let currentChat = null;
  let currentMode = "online";
  let searchActive = false;

  // DOM refs (populated on DOMContentLoaded)
  let chatBox, inputEl, sendBtn, emptyState, modeBtn;
  let sidebar, toggleBtn, overlay, mainContent;
  let thinkingIndicator, loadingIndicator, chatList;

  /* =====================
     UTIL
  ====================== */
  function safeUUID() {
    return (crypto && crypto.randomUUID) ? crypto.randomUUID() : `chat-${Date.now()}-${Math.floor(Math.random()*1000)}`;
  }

  function isMobile() {
    return window.innerWidth <= 768;
  }

  /* =====================
     Markdown -> HTML
  ====================== */
  function markdownToHtml(text) {
    if (!text) return "";
    let html = text;

    // Escape HTML
    html = html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

    // Code blocks
    html = html.replace(/```(\w+)?\n([\s\S]*?)\n```/g, (match, lang, code) => {
      const trimmed = code.trim();
      const escaped = trimmed.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      return `<pre><code class="language-${lang || 'plain'}">${escaped}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, (m, code) => {
      const escaped = code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      return `<code>${escaped}</code>`;
    });

    // Headings
    html = html.replace(/^###### (.+)$/gm, "<h6>$1</h6>");
    html = html.replace(/^##### (.+)$/gm, "<h5>$1</h5>");
    html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

    // Bold/italic
    html = html.replace(/\*\*([^\*]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/__([^_]+)__/g, "<strong>$1</strong>");
    html = html.replace(/\*([^\*]+)\*/g, "<em>$1</em>");
    html = html.replace(/_([^_]+)_/g, "<em>$1</em>");

    // Lists - simple conversion
    html = html.replace(/^\d+\.\s+(.+)$/gm, "<li>$1</li>");
    html = html.replace(/(<li>[\s\S]*<\/li>)/s, (m) => m.includes("<ol>") || m.includes("<ul>") ? m : `<ol>${m}</ol>`);

    html = html.replace(/^[\-\*]\s+(.+)$/gm, "<li>$1</li>");
    html = html.replace(/(<li>[\s\S]*?<\/li>)/s, (m) => m.includes("<ol>") || m.includes("<ul>") ? m : `<ul>${m}</ul>`);

    // Blockquotes (work with escaped &gt;)
    html = html.replace(/^&gt;\s(.+)$/gm, "<blockquote>$1</blockquote>");

    // Wrap remaining lines in paragraphs (skip if already tags)
    html = html.split("\n").map(line => {
      const trimmed = line.trim();
      if (!trimmed) return "";
      if (trimmed.match(/^<(h\d|p|pre|blockquote|ul|ol|li|table|tr|td|th)/)) return line;
      return `<p>${line}</p>`;
    }).filter(Boolean).join("\n");

    return html;
  }

  /* =====================
     UI: Add message
  ====================== */
  function addMessage(role, text, stream = false) {
    if (!chatBox) return null;
    const msg = document.createElement("div");
    msg.className = `message ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    if (role === "assistant") {
      bubble.innerHTML = markdownToHtml(text);
    } else {
      bubble.innerText = text;
    }

    if (stream) bubble.id = "streaming";

    msg.appendChild(bubble);
    chatBox.appendChild(msg);

    chatBox.classList.add("active");
    if (emptyState) emptyState.style.display = "none";
    chatBox.scrollTop = chatBox.scrollHeight;

    return bubble;
  }

  /* =====================
     Welcome card for empty state
  ====================== */
  function showWelcomeCard() {
    if (!emptyState || !chatBox) return;
    emptyState.innerHTML = `
      <div class="empty-card">
        <h1>What can I help with?</h1>
        <p class="subtitle">Try: "Summarize my notes", "Write an email", or "Generate a plan"</p>
      </div>
    `;
    emptyState.style.display = "flex";
    chatBox.innerHTML = "";
    chatBox.classList.remove("active");
  }

  /* =====================
     Chats list
  ====================== */
  async function loadChats() {
    try {
      const res = await fetch("/chats");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const chats = await res.json();

      if (!chatList) return;
      chatList.innerHTML = "";

      if (!chats || chats.length === 0) {
        chatList.innerHTML = '<div class="empty-history">No chats yet</div>';
        showWelcomeCard();
        return;
      }

      chats.forEach(([id, title]) => {
        const item = document.createElement("div");
        item.className = "chat-item";

        const displayTitle = title.length > 40 ? title.substring(0, 40) + "..." : title;

        const textSpan = document.createElement("span");
        textSpan.className = "chat-item-text";
        textSpan.innerText = displayTitle;
        textSpan.title = title;
        textSpan.addEventListener("click", () => loadChat(id));

        const deleteBtn = document.createElement("button");
        deleteBtn.className = "chat-item-delete";
        deleteBtn.innerText = "✕";
        deleteBtn.title = "Delete chat";
        deleteBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          deleteChat(id, title);
        });

        item.appendChild(textSpan);
        item.appendChild(deleteBtn);
        chatList.appendChild(item);
      });

      if (emptyState) {
        emptyState.style.display = "none";
        emptyState.innerHTML = "";
      }
    } catch (err) {
      console.error("Failed to load chats:", err);
    }
  }

  /* =====================
     Delete chat
  ====================== */
  async function deleteChat(id, title) {
    if (!confirm(`Delete chat "${title}"?`)) return;
    try {
      const res = await fetch(`/delete/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await loadChats();
      if (currentChat === id) createNewChat();
    } catch (err) {
      console.error("Error deleting chat:", err);
    }
  }

  /* =====================
     Load specific chat
  ====================== */
  async function loadChat(id) {
    try {
      if (searchActive) {
        searchActive = false;
        if (inputEl) {
          inputEl.placeholder = "+ Ask anything";
          inputEl.value = "";
        }
      }

      currentChat = id;
      if (chatBox) chatBox.innerHTML = "";

      const res = await fetch(`/history/${id}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const messages = await res.json();
      messages.forEach(([role, text]) => addMessage(role, text));
    } catch (err) {
      console.error("Failed to load chat:", err);
    }
  }

  /* =====================
     Navigation / actions
  ====================== */
  function handleNavAction(action) {
    switch (action) {
      case "new-chat": createNewChat(); break;
      case "search": toggleSearchChats(); break;
      case "images": showFeature("Images"); break;
      case "apps": showFeature("Apps"); break;
      case "projects": showFeature("Projects"); break;
      default: console.log("Unknown action:", action);
    }
  }

  function setupNavigationButtons() {
    const navItems = document.querySelectorAll(".nav-item[data-action]");
    navItems.forEach(item => {
      item.addEventListener("click", () => {
        handleNavAction(item.getAttribute("data-action"));
        if (isMobile() && sidebar && sidebar.classList.contains("open")) {
          closeSidebar();
        }
      });
      item.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          item.click();
        }
      });
    });
  }

  function showFeature(feature) {
    if (!chatBox || !emptyState) return;
    const featureMsg = `<strong>${feature} feature</strong> is coming soon! 🚀`;
    emptyState.style.display = "none";
    chatBox.innerHTML = "";
    const msg = document.createElement("div");
    msg.className = "message assistant";
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.innerHTML = featureMsg;
    msg.appendChild(bubble);
    chatBox.appendChild(msg);
    chatBox.classList.add("active");
  }

  /* =====================
     New chat / search
  ====================== */
  function createNewChat() {
    currentChat = safeUUID();
    if (chatBox) chatBox.innerHTML = "";
    if (inputEl) inputEl.value = "";
    if (emptyState) emptyState.style.display = "flex";
    chatBox.classList.remove("active");
    searchActive = false;
    inputEl?.focus();
  }

  function toggleSearchChats() {
    searchActive = !searchActive;
    if (!inputEl) return;
    if (searchActive) {
      inputEl.placeholder = "🔍 Search chats...";
      inputEl.focus();
    } else {
      inputEl.placeholder = "+ Ask anything";
      inputEl.value = "";
      loadChats();
    }
  }

  /* =====================
     Quick actions & input icons
  ====================== */
  function handleQuickAction(action) {
    const prompts = {
      "code": "Generate a simple Python script that prints a greeting",
      "explain": "Explain the concept of machine learning in simple terms",
      "creative": "Write a short creative story about an AI discovering consciousness",
      "analyze": "Analyze the pros and cons of remote work"
    };
    if (prompts[action] && inputEl) {
      inputEl.value = prompts[action];
      inputEl.focus();
      inputEl.dispatchEvent(new Event("input"));
    }
  }

  function setupQuickButtons() {
    const quickBtns = document.querySelectorAll(".quick-btn");
    quickBtns.forEach(btn => {
      btn.addEventListener("click", () => handleQuickAction(btn.getAttribute("data-action")));
    });
  }

  function setupInputIcons() {
    const icons = document.querySelectorAll(".input-icons .icon-btn[data-action]");
    icons.forEach(btn => {
      btn.addEventListener("click", () => {
        const action = btn.getAttribute("data-action");
        if (action === "voice") {
          console.log("Voice input - coming soon");
        } else if (action === "attach") {
          console.log("File attachment - coming soon");
        }
      });
    });
  }

  /* =====================
     Mode toggle
  ====================== */
  function setupModeToggle() {
    if (!modeBtn) return;
    modeBtn.addEventListener("click", toggleMode);
  }

  async function loadMode() {
    if (!modeBtn) return;
    try {
      const res = await fetch("/mode");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data?.mode) currentMode = data.mode;
      updateModeButton();
    } catch (err) {
      console.error("Failed to load mode:", err);
    }
  }

  async function toggleMode() {
    if (!modeBtn) return;
    currentMode = (currentMode === "online") ? "offline" : "online";
    try {
      const res = await fetch("/mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: currentMode })
      });
      if (res.ok) updateModeButton();
    } catch (err) {
      console.error("Failed to toggle mode:", err);
    }
  }

  function updateModeButton() {
    if (!modeBtn) return;
    if (currentMode === "online") {
      modeBtn.textContent = "🔵 Online";
      modeBtn.classList.remove("offline");
      modeBtn.classList.add("online");
      modeBtn.setAttribute("aria-pressed", "false");
    } else {
      modeBtn.textContent = "🔴 Offline";
      modeBtn.classList.remove("online");
      modeBtn.classList.add("offline");
      modeBtn.setAttribute("aria-pressed", "true");
    }
  }

  /* =====================
     Clear history
  ====================== */
  function setupClearHistoryButton() {
    const clearBtn = document.getElementById("clearHistoryBtn");
    if (!clearBtn) return;
    clearBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm("Are you sure you want to delete all chats? This cannot be undone.")) return;
      try {
        const res = await fetch("/chats");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const chats = await res.json();
        for (const [id] of chats) {
          await fetch(`/delete/${id}`, { method: "DELETE" });
        }
        await loadChats();
        createNewChat();
      } catch (err) {
        console.error("Error clearing history:", err);
      }
    });
  }

  /* =====================
     Send message (and search)
  ====================== */
  async function sendMessage() {
    if (!inputEl) return;
    const text = inputEl.value.trim();

    // Search mode
    if (searchActive) {
      try {
        const res = await fetch("/chats");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const chats = await res.json();
        if (!chatList) return;
        chatList.innerHTML = "";
        const filtered = chats.filter(([_, title]) => title.toLowerCase().includes(text.toLowerCase()));
        if (filtered.length === 0) {
          chatList.innerHTML = '<div class="empty-history">No matching chats</div>';
          return;
        }
        filtered.forEach(([id, title]) => {
          const item = document.createElement("div");
          item.className = "chat-item";
          const displayTitle = title.length > 40 ? title.substring(0, 40) + "..." : title;
          const textSpan = document.createElement("span");
          textSpan.className = "chat-item-text";
          textSpan.innerText = displayTitle;
          textSpan.title = title;
          textSpan.addEventListener("click", () => loadChat(id));
          const deleteBtn = document.createElement("button");
          deleteBtn.className = "chat-item-delete";
          deleteBtn.innerText = "✕";
          deleteBtn.title = "Delete chat";
          deleteBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            deleteChat(id, title);
          });
          item.appendChild(textSpan);
          item.appendChild(deleteBtn);
          chatList.appendChild(item);
        });
      } catch (err) {
        console.error("Search failed:", err);
      }
      return;
    }

    if (!text) return;
    if (!currentChat) currentChat = safeUUID();
    inputEl.value = "";
    if (emptyState) emptyState.style.display = "none";

    addMessage("user", text);
    const assistantBubble = addMessage("assistant", "", true);

    if (thinkingIndicator) thinkingIndicator.classList.add("show");

    try {
      const response = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, chat_id: currentChat })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i].trim();
          if (!line) continue;
          if (line.startsWith("data: ")) {
            const data = line.substring(6);
            try {
              const event = JSON.parse(data);
              if (event.type === "text") {
                fullText += event.text;
                assistantBubble.innerHTML = markdownToHtml(fullText);
                // syntax highlight if available
                try {
                  if (window.hljs) {
                    assistantBubble.querySelectorAll("pre code").forEach(block => {
                      hljs.highlightElement(block);
                    });
                  }
                } catch (_) {}
                chatBox.scrollTop = chatBox.scrollHeight;
              } else if (event.type === "status") {
                console.log("Status:", event.text);
              } else if (event.type === "done") {
                // optionally handle done
              }
            } catch (err) {
              console.error("Stream parse error:", err);
            }
          }
        }
        buffer = lines[lines.length - 1];
      }

      if (thinkingIndicator) thinkingIndicator.classList.remove("show");
      assistantBubble.removeAttribute("id");
      await loadChats();
    } catch (err) {
      console.error("Error sending message:", err);
      assistantBubble.innerHTML = "<strong>Sorry, an error occurred. Please try again.</strong>";
      if (thinkingIndicator) thinkingIndicator.classList.remove("show");
    }
  }

  /* =====================
     Sidebar behavior
  ====================== */
  function openSidebar() {
    if (!sidebar || !overlay || !toggleBtn) return;
    sidebar.classList.add("open");
    sidebar.setAttribute("aria-hidden", "false");
    toggleBtn.setAttribute("aria-expanded", "true");
    overlay.classList.add("visible");
    overlay.removeAttribute("hidden");
    mainContent?.classList.add("sidebar-open");
    const firstNavItem = sidebar.querySelector('.nav-item');
    if (firstNavItem) firstNavItem.focus();
  }

  function closeSidebar() {
    if (!sidebar || !overlay || !toggleBtn) return;
    sidebar.classList.remove("open");
    sidebar.setAttribute("aria-hidden", "true");
    toggleBtn.setAttribute("aria-expanded", "false");
    overlay.classList.remove("visible");
    overlay.setAttribute("hidden", "");
    mainContent?.classList.remove("sidebar-open");
    toggleBtn.focus();
  }

  function toggleSidebar() {
    if (!sidebar) return;
    const open = sidebar.classList.contains("open");
    if (open) closeSidebar(); else openSidebar();
  }

  function setupSidebarToggle() {
    if (!toggleBtn || !overlay || !sidebar) return;

    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleSidebar();
    });

    overlay.addEventListener('click', () => closeSidebar());

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && isMobile() && sidebar.classList.contains('open')) {
        closeSidebar();
      }
    });

    window.addEventListener('resize', () => {
      if (!isMobile()) {
        sidebar.classList.remove('open');
        sidebar.setAttribute('aria-hidden', 'false');
        toggleBtn.setAttribute('aria-expanded', 'true');
        overlay.classList.remove('visible');
        overlay.setAttribute('hidden', '');
        mainContent?.classList.remove('sidebar-open');
      } else {
        sidebar.setAttribute('aria-hidden', 'true');
        toggleBtn.setAttribute('aria-expanded', 'false');
      }
    });

    // initial state
    if (isMobile()) {
      sidebar.setAttribute('aria-hidden', 'true');
      toggleBtn?.setAttribute('aria-expanded', 'false');
      overlay?.setAttribute('hidden', '');
    } else {
      sidebar.setAttribute('aria-hidden', 'false');
      toggleBtn?.setAttribute('aria-expanded', 'true');
      overlay?.setAttribute('hidden', '');
    }
  }

  /* =====================
     Initialization (single DOMContentLoaded)
  ====================== */
  document.addEventListener("DOMContentLoaded", () => {
    // Cache DOM elements
    chatBox = document.getElementById("chatBox");
    inputEl = document.getElementById("chatInput");
    sendBtn = document.getElementById("sendBtn");
    emptyState = document.getElementById("emptyState") || document.querySelector(".empty-state");
    modeBtn = document.getElementById("modeBtn");
    sidebar = document.getElementById("appSidebar") || document.querySelector(".sidebar");
    toggleBtn = document.getElementById("sidebarToggle");
    overlay = document.getElementById("sidebarOverlay");
    mainContent = document.getElementById("mainContent");
    thinkingIndicator = document.getElementById("thinkingIndicator");
    loadingIndicator = document.getElementById("loadingIndicator");
    chatList = document.getElementById("chatList");

    // Wire UI
    setupModeToggle();
    setupNavigationButtons();
    setupClearHistoryButton();
    setupQuickButtons();
    setupInputIcons();
    setupSidebarToggle();

    // Send / Enter handling (single binding)
    if (sendBtn) sendBtn.addEventListener("click", sendMessage);
    if (inputEl) {
      inputEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });
    }

    // If chatList quick buttons were not created earlier, ensure they exist
    // Load initial data
    loadChats();
    loadMode();
  });

  /* =====================
     Expose for debugging (optional)
  ====================== */
  window.__aiAssistant = {
    loadChats, loadChat, sendMessage, addMessage, markdownToHtml, openSidebar, closeSidebar
  };
})();