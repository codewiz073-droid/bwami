/**
 * Frontend authentication handler
 * Manages login, signup, guest mode, and token storage
 * 
 * Flow:
 * 1. Startup: Check if user is authenticated
 *    - If yes: Show full app with sidebar
 *    - If no: Show chat-only interface (no sidebar)
 * 2. Guest can chat but cannot access premium features
 * 3. When accessing premium features: Show auth modal
 * 4. After signup/login: Reload app with full features
 */

(() => {
  let currentUser = null;
  let currentToken = null;
  let isFullAccess = false;  // true if account user, false if guest

  /* =====================
     INITIALIZATION
  ====================== */
  document.addEventListener("DOMContentLoaded", async () => {
    // Check auth status on load
    await checkAuthStatus();
  });

  /* =====================
     AUTH STATUS
  ====================== */
  async function checkAuthStatus() {
    try {
      const res = await fetch("/auth/status");
      const data = await res.json();
      
      if (data.authenticated) {
        currentUser = {
          user_id: data.user_id,
          is_guest: data.is_guest
        };
        
        // Get token from localStorage or cookie
        currentToken = localStorage.getItem("auth_token");
        isFullAccess = !data.is_guest;  // Full access only for account users
        
        showApp();
        updateUserMenu();
        updateUIForAccessLevel();
      } else {
        // Not authenticated - create automatic guest session for chat
        await createAutomaticGuestSession();
      }
    } catch (err) {
      console.error("Auth check failed:", err);
      // Fallback: create guest session
      await createAutomaticGuestSession();
    }
  }

  /* =====================
     AUTOMATIC GUEST SESSION
  ====================== */
  async function createAutomaticGuestSession() {
    try {
      const res = await fetch("/auth/guest", {
        method: "POST"
      });

      if (!res.ok) {
        console.error("Failed to create guest session");
        return;
      }

      const data = await res.json();
      currentUser = {
        user_id: data.user_id,
        is_guest: true
      };
      currentToken = data.token;
      localStorage.setItem("auth_token", data.token);
      isFullAccess = false;  // Guest has limited access
      
      showApp();
      updateUserMenu();
      updateUIForAccessLevel();
    } catch (err) {
      console.error("Guest session error:", err);
    }
  }

  /* =====================
     UPDATE UI BASED ON ACCESS LEVEL
  ====================== */
  function updateUIForAccessLevel() {
    const sidebar = document.getElementById("appSidebar");
    const chatArea = document.getElementById("mainContent");
    
    if (isFullAccess) {
      // Account user: show everything
      if (sidebar) sidebar.style.display = "flex";
      if (chatArea) chatArea.style.display = "flex";
    } else {
      // Guest user: hide sidebar, show only chat
      if (sidebar) sidebar.style.display = "none";
      if (chatArea) chatArea.style.display = "flex";
    }
  }

  /* =====================
     REQUIRE AUTH FOR FEATURES
  ====================== */
  window.requireAuth = function(featureName) {
    if (isFullAccess) {
      return true;  // User has access
    }
    
    // Guest user trying to access premium feature
    showAuthModalWithMessage(featureName);
    return false;
  };

  function showAuthModalWithMessage(featureName) {
    const modal = document.getElementById("authModal");
    const loginForm = document.getElementById("loginForm");
    
    // Show message about the feature
    let message = "Sign in to access this feature";
    if (featureName === "history") {
      message = "Sign in to access your chat history";
    } else if (featureName === "upload") {
      message = "Sign in to upload files";
    } else if (featureName === "sidebar") {
      message = "Sign in to access your dashboard";
    }
    
    // Add message if it doesn't exist
    let msgEl = modal.querySelector(".auth-message");
    if (!msgEl) {
      msgEl = document.createElement("div");
      msgEl.className = "auth-message";
      loginForm.insertBefore(msgEl, loginForm.firstChild);
    }
    msgEl.textContent = message;
    msgEl.style.color = "var(--accent-accent)";
    msgEl.style.marginBottom = "12px";
    msgEl.style.fontSize = "13px";
    
    showAuthModal();
  }

  /* =====================
     LOGIN / SIGNUP
  ====================== */
  async function handleLogin() {
    const username = document.getElementById("loginUsername")?.value.trim();
    const password = document.getElementById("loginPassword")?.value.trim();
    
    if (!username || !password) {
      alert("Please fill in all fields");
      return;
    }

    try {
      const res = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      if (!res.ok) {
        const err = await res.json();
        alert(err.error || "Login failed");
        return;
      }

      const data = await res.json();
      currentUser = {
        user_id: data.user_id,
        is_guest: data.is_guest
      };
      currentToken = data.token;
      isFullAccess = !data.is_guest;  // Update access level
      localStorage.setItem("auth_token", data.token);
      
      hideAuthModal();
      showApp();
      updateUserMenu();
      updateUIForAccessLevel();
      
      // Reload chats to show user's chats
      if (window.__aiAssistant?.loadChats) {
        window.__aiAssistant.loadChats();
      }
    } catch (err) {
      console.error("Login error:", err);
      alert("An error occurred");
    }
  }

  async function handleSignup() {
    const username = document.getElementById("signupUsername")?.value.trim();
    const email = document.getElementById("signupEmail")?.value.trim();
    const password = document.getElementById("signupPassword")?.value.trim();
    
    if (!username || !email || !password) {
      alert("Please fill in all fields");
      return;
    }

    try {
      const res = await fetch("/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password })
      });

      if (!res.ok) {
        const err = await res.json();
        alert(err.error || "Signup failed");
        return;
      }

      const data = await res.json();
      currentUser = {
        user_id: data.user_id,
        is_guest: data.is_guest
      };
      currentToken = data.token;
      isFullAccess = !data.is_guest;  // Update access level
      localStorage.setItem("auth_token", data.token);
      
      hideAuthModal();
      showApp();
      updateUserMenu();
      updateUIForAccessLevel();
      
      // Reload chats to show user's chats
      if (window.__aiAssistant?.loadChats) {
        window.__aiAssistant.loadChats();
      }
    } catch (err) {
      console.error("Signup error:", err);
      alert("An error occurred");
    }
  }

  async function handleLogout() {
    try {
      await fetch("/auth/logout", { method: "POST" });
      localStorage.removeItem("auth_token");
      currentUser = null;
      currentToken = null;
      isFullAccess = false;
      
      // Create new guest session instead of showing modal
      await createAutomaticGuestSession();
    } catch (err) {
      console.error("Logout error:", err);
    }
  }

  /* =====================
     UI HELPERS
  ====================== */
  function showAuthModal() {
    const modal = document.getElementById("authModal");
    if (modal) {
      modal.removeAttribute("hidden");
      document.body.style.overflow = "hidden";
    }
  }

  function hideAuthModal() {
    const modal = document.getElementById("authModal");
    if (modal) {
      modal.setAttribute("hidden", "");
      document.body.style.overflow = "";
    }
  }

  function showApp() {
    const sidebar = document.getElementById("appSidebar");
    const mainContent = document.getElementById("mainContent");
    if (sidebar) sidebar.style.display = "flex";
    if (mainContent) mainContent.style.display = "flex";
  }

  function updateUserMenu() {
    const userInfo = document.getElementById("userInfo");
    const signInBtn = document.getElementById("signInBtn");
    const settingsBtn = document.getElementById("settingsBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    
    if (userInfo) {
      if (isFullAccess) {
        userInfo.textContent = "Account User";
      } else {
        userInfo.textContent = "Guest (Limited)";
      }
    }
    
    // Show/hide buttons based on access level
    if (signInBtn) {
      signInBtn.style.display = isFullAccess ? "none" : "block";
    }
    if (settingsBtn) {
      settingsBtn.style.display = isFullAccess ? "block" : "none";
    }
    if (logoutBtn) {
      logoutBtn.textContent = isFullAccess ? "Logout" : "Continue as Guest";
    }
  }

  /* =====================
     EVENT SETUP
  ====================== */
  function setupAuthHandlers() {
    // Login form
    document.getElementById("loginBtn")?.addEventListener("click", handleLogin);
    document.getElementById("switchToSignup")?.addEventListener("click", (e) => {
      e.preventDefault();
      switchToSignup();
    });

    // Signup form
    document.getElementById("signupBtn")?.addEventListener("click", handleSignup);
    document.getElementById("switchToLogin")?.addEventListener("click", (e) => {
      e.preventDefault();
      switchToLogin();
    });

    // User menu
    document.getElementById("userMenuBtn")?.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleUserMenu();
    });

    document.getElementById("signInBtn")?.addEventListener("click", () => {
      showAuthModal();
      hideUserMenu();
    });

    document.getElementById("logoutBtn")?.addEventListener("click", () => {
      handleLogout();
      hideUserMenu();
    });

    // Close menu on click outside
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".user-menu-container")) {
        hideUserMenu();
      }
    });

    // Enter key handling
    document.getElementById("loginPassword")?.addEventListener("keypress", (e) => {
      if (e.key === "Enter") handleLogin();
    });

    document.getElementById("signupPassword")?.addEventListener("keypress", (e) => {
      if (e.key === "Enter") handleSignup();
    });
  }

  function switchToSignup() {
    document.getElementById("loginForm")?.classList.add("hidden");
    document.getElementById("signupForm")?.classList.remove("hidden");
  }

  function switchToLogin() {
    document.getElementById("signupForm")?.classList.add("hidden");
    document.getElementById("loginForm")?.classList.remove("hidden");
  }

  function toggleUserMenu() {
    const menu = document.getElementById("userMenu");
    if (menu) {
      menu.hasAttribute("hidden") ? menu.removeAttribute("hidden") : menu.setAttribute("hidden", "");
    }
  }

  function hideUserMenu() {
    const menu = document.getElementById("userMenu");
    if (menu) menu.setAttribute("hidden", "");
  }

  /* =====================
     PREFERENCES MANAGEMENT
  ====================== */
  async function loadPreferences() {
    if (!currentToken || isFullAccess === false) return null;  // Guests can't save preferences
    
    try {
      const res = await fetch("/user/preferences", {
        headers: {"Authorization": `Bearer ${currentToken}`}
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.error("Failed to load preferences:", e);
    }
    return null;
  }

  async function savePreferences(preferences) {
    if (!currentToken || isFullAccess === false) {
      alert("Only registered users can save preferences");
      return false;
    }
    
    try {
      const res = await fetch("/user/preferences", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${currentToken}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(preferences)
      });
      
      if (res.ok) {
        const data = await res.json();
        console.log("Preferences saved:", data);
        return true;
      } else {
        const error = await res.json();
        alert("Error saving preferences: " + error.error);
        return false;
      }
    } catch (e) {
      console.error("Failed to save preferences:", e);
      alert("Failed to save preferences: " + e.message);
      return false;
    }
  }

  /* =====================
     EXPOSE FOR SCRIPT.JS
  ====================== */
  window.__auth = {
    getCurrentToken: () => currentToken,
    getCurrentUser: () => currentUser,
    isFullAccess: () => isFullAccess,
    requireAuth: window.requireAuth,
    setupAuthHandlers,
    loadPreferences,
    savePreferences
  };

  // Setup handlers when auth modal loads
  setTimeout(setupAuthHandlers, 100);
})();
