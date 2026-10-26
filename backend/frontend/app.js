/**
 * KOUMAN AI — Frontend Logic & Audio Pipeline (v0.5.0)
 * - Système de profils locaux (login screen)
 * - Gestion de sessions multiples (sidebar)
 * - Lecteur audio interactif avec contrôle de vitesse
 * - Validation bidirectionnelle FR⟷DYU (K3/K6)
 */

// --- SCÉNARIOS DE VALIDATION BIDIRECTIONNELS ---
const SCENARIOS_BIDI = [
  { id: "FR_01", direction: "fr->dyu", src_lang: "fr", tgt_lang: "dyu", cat: "Salutation",      text: "Bonjour comment allez-vous ?",                          ref: "Aw ni sɔgɔma aw ka kɛnɛ wa ?" },
  { id: "FR_02", direction: "fr->dyu", src_lang: "fr", tgt_lang: "dyu", cat: "Commerce",        text: "Je vais au marché pour acheter du riz.",                ref: "N bɛ taa sugu la ka malo san." },
  { id: "FR_03", direction: "fr->dyu", src_lang: "fr", tgt_lang: "dyu", cat: "Santé",           text: "Où se trouve le centre de santé ?",                    ref: "Dɔgɔtɔrɔso bɛ min ?" },
  { id: "FR_04", direction: "fr->dyu", src_lang: "fr", tgt_lang: "dyu", cat: "Commerce",        text: "Ce prix est très cher diminue un peu s'il te plaît.",   ref: "Sɔngɔ nin ka gɛlɛn kosɛbɛ dɔ dɔgɔya dusu la." },
  { id: "FR_05", direction: "fr->dyu", src_lang: "fr", tgt_lang: "dyu", cat: "Quotidien",       text: "Donne-moi un peu d'eau s'il te plaît.",                ref: "Jii dɔɔnin di n ma dusu la." },
  { id: "FR_06", direction: "fr->dyu", src_lang: "fr", tgt_lang: "dyu", cat: "Travail",         text: "Le travail est difficile mais il est très utile.",       ref: "Baara ka gɛlɛn nka a nafa ka bon kosɛbɛ." },
  { id: "FR_07", direction: "fr->dyu", src_lang: "fr", tgt_lang: "dyu", cat: "Présentation",    text: "Comment vous appelez-vous ?",                           ref: "Aw tɔgɔ bi di ?" },
  { id: "FR_08", direction: "fr->dyu", src_lang: "fr", tgt_lang: "dyu", cat: "Météo",           text: "Est-ce qu'il va pleuvoir aujourd'hui ?",                ref: "Sanji bɛna na bi wa ?" },
  { id: "FR_09", direction: "fr->dyu", src_lang: "fr", tgt_lang: "dyu", cat: "Langue",          text: "Je comprends la langue dioula un peu.",                 ref: "Ne bɛ dioula kan mɛn dɔɔnin." },
  { id: "FR_10", direction: "fr->dyu", src_lang: "fr", tgt_lang: "dyu", cat: "Remerciement",    text: "Merci beaucoup pour votre aide précieuse.",             ref: "I ni cɛ kosɛbɛ aw ka dɛmɛ la." },
  { id: "DYU_01", direction: "dyu->fr", src_lang: "dyu", tgt_lang: "fr", cat: "Salutation",     text: "Aw ni sɔgɔma, i ka kɛnɛ wa ?",           ref: "Bonjour, comment vas-tu ?" },
  { id: "DYU_02", direction: "dyu->fr", src_lang: "dyu", tgt_lang: "fr", cat: "Commerce",       text: "N bɛ taa sugu la bi ka malo san.",         ref: "Je vais au marché aujourd'hui pour acheter du riz." },
  { id: "DYU_03", direction: "dyu->fr", src_lang: "dyu", tgt_lang: "fr", cat: "Santé",          text: "Dɔgɔtɔrɔso bɛ min ?",                      ref: "Où se trouve le centre de santé ?" },
  { id: "DYU_04", direction: "dyu->fr", src_lang: "dyu", tgt_lang: "fr", cat: "Commerce",       text: "Sɔngɔ ka gɛlɛn kosɛbɛ, dɔ dɔgɔya.",       ref: "Le prix est trop cher, diminue un peu." },
  { id: "DYU_05", direction: "dyu->fr", src_lang: "dyu", tgt_lang: "fr", cat: "Quotidien",      text: "Jii di n ma dusu la.",                     ref: "Donne-moi de l'eau s'il te plaît." },
  { id: "DYU_06", direction: "dyu->fr", src_lang: "dyu", tgt_lang: "fr", cat: "Famille",        text: "Denmisɛn bɛ sunɔgɔ bon kɔnɔ.",            ref: "L'enfant dort dans la chambre." },
  { id: "DYU_07", direction: "dyu->fr", src_lang: "dyu", tgt_lang: "fr", cat: "Présentation",   text: "I tɔgɔ bi di ?",                            ref: "Comment t'appelles-tu ?" },
  { id: "DYU_08", direction: "dyu->fr", src_lang: "dyu", tgt_lang: "fr", cat: "Météo",          text: "Sanji bɛ na bi wa ?",                       ref: "Va-t-il pleuvoir aujourd'hui ?" },
  { id: "DYU_09", direction: "dyu->fr", src_lang: "dyu", tgt_lang: "fr", cat: "Entraide",       text: "I bɛ se ka n dɛmɛ wa ?",                   ref: "Peux-tu m'aider ?" },
  { id: "DYU_10", direction: "dyu->fr", src_lang: "dyu", tgt_lang: "fr", cat: "Remerciement",   text: "An bɛ bɛn sini, i ni cɛ kosɛbɛ.",         ref: "À demain, merci beaucoup." },
];

let activeFilter = "all";

// ==========================================================================
// GESTION DES PROFILS & SESSIONS (localStorage)
// ==========================================================================
const STORAGE_KEY = "kouman_profiles";

function loadProfiles() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); } catch { return {}; }
}

function saveProfiles(profiles) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(profiles));
}

function createProfile(name) {
  const profiles = loadProfiles();
  const id = "profile_" + Date.now();
  profiles[id] = { id, name, createdAt: Date.now(), sessions: [] };
  saveProfiles(profiles);
  return profiles[id];
}

function getProfile(id) {
  return loadProfiles()[id] || null;
}

function createSession(profileId, title = "Nouvelle conversation", mode = "fr->dyu") {
  const profiles = loadProfiles();
  const profile = profiles[profileId];
  if (!profile) return null;
  const sessionId = "sess_" + Date.now() + "_" + Math.random().toString(36).slice(2, 7);
  const session = { id: sessionId, title, mode, createdAt: Date.now(), messageCount: 0, messages: [] };
  if (!profile.sessions) profile.sessions = [];
  profile.sessions.unshift(session);
  saveProfiles(profiles);
  return session;
}

function updateSessionTitle(profileId, sessionId, title) {
  const profiles = loadProfiles();
  const profile = profiles[profileId];
  if (!profile) return;
  const session = (profile.sessions || []).find(s => s.id === sessionId);
  if (session) {
    session.title = title;
    if (session.messages) session.messageCount = session.messages.length;
  }
  saveProfiles(profiles);
}

function setSessionMode(profileId, sessionId, mode) {
  const profiles = loadProfiles();
  const profile = profiles[profileId];
  if (!profile) return;
  const session = (profile.sessions || []).find(s => s.id === sessionId);
  if (session) {
    session.mode = mode;
  }
  saveProfiles(profiles);
}

function addMessageToSession(profileId, sessionId, message) {
  const profiles = loadProfiles();
  const profile = profiles[profileId];
  if (!profile) return;
  const session = (profile.sessions || []).find(s => s.id === sessionId);
  if (!session) return;
  if (!session.messages) session.messages = [];
  session.messages.push(message);
  // Limite de sécurité pour éviter de saturer le localStorage
  if (session.messages.length > 100) {
    session.messages = session.messages.slice(-100);
  }
  session.messageCount = session.messages.length;
  saveProfiles(profiles);
}

function deleteSession(profileId, sessionId) {
  const profiles = loadProfiles();
  const profile = profiles[profileId];
  if (!profile) return;
  profile.sessions = (profile.sessions || []).filter(s => s.id !== sessionId);
  saveProfiles(profiles);
}

// ==========================================================================
// ÉCRAN DE LOGIN
// ==========================================================================
class LoginScreen {
  constructor(onLogin) {
    this.onLogin = onLogin;
    this.el = document.getElementById("login-screen");
    this.profilesContainer = document.getElementById("login-profiles");
    this.inputName = document.getElementById("input-new-profile-name");
    this.btnCreate = document.getElementById("btn-create-profile");
    this.render();
    this.bindEvents();
  }

  render() {
    const profiles = loadProfiles();
    const list = Object.values(profiles);
    this.profilesContainer.innerHTML = "";

    if (list.length > 0) {
      // Divider
      const div = document.createElement("div");
      div.className = "login-divider";
      div.textContent = "Choisir un profil";
      this.profilesContainer.appendChild(div);

      list.sort((a, b) => (b.lastActive || b.createdAt) - (a.lastActive || a.createdAt)).forEach(profile => {
        const btn = document.createElement("button");
        btn.className = "profile-btn";
        const convCount = (profile.sessions || []).length;
        btn.innerHTML = `
          <div class="p-avatar">${profile.name.charAt(0).toUpperCase()}</div>
          <div>
            <div class="p-name">${this.escapeHtml(profile.name)}</div>
            <div class="p-meta">${convCount} conversation${convCount !== 1 ? "s" : ""}</div>
          </div>
        `;
        btn.addEventListener("click", () => this.selectProfile(profile.id));
        this.profilesContainer.appendChild(btn);
      });

      // Divider before new
      const div2 = document.createElement("div");
      div2.className = "login-divider";
      div2.textContent = "Nouveau profil";
      this.profilesContainer.appendChild(div2);
    }
  }

  bindEvents() {
    this.btnCreate.addEventListener("click", () => this.createAndLogin());
    this.inputName.addEventListener("keydown", (e) => {
      if (e.key === "Enter") this.createAndLogin();
    });
  }

  createAndLogin() {
    const name = this.inputName.value.trim();
    if (!name) {
      this.inputName.focus();
      this.inputName.style.borderColor = "rgba(239,68,68,0.6)";
      setTimeout(() => this.inputName.style.borderColor = "", 1200);
      return;
    }
    const profile = createProfile(name);
    this.selectProfile(profile.id);
  }

  selectProfile(profileId) {
    const profiles = loadProfiles();
    if (profiles[profileId]) {
      profiles[profileId].lastActive = Date.now();
      saveProfiles(profiles);
    }
    this.el.style.animation = "loginCardOut 0.3s ease forwards";
    this.el.style.cssText += "animation: loginCardOut 0.3s ease forwards;";
    setTimeout(() => {
      this.el.style.display = "none";
      this.onLogin(profileId);
    }, 300);
  }

  escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
}

// ==========================================================================
// APPLICATION PRINCIPALE
// ==========================================================================
class KoumanApp {
  constructor(profileId) {
    // Nettoyer l'instance précédente si elle existe (retour depuis logout)
    if (window.koumanApp && window.koumanApp !== this) {
      window.koumanApp.destroy();
    }

    this.profileId = profileId;
    this.profile = getProfile(profileId);
    this.apiUrl = localStorage.getItem("kouma_api_url") || "";
    this.apiKey = localStorage.getItem("kouma_api_key") || "";
    this.currentSessionId = null;
    this.currentSession = null;
    this.pendingDeleteSessionId = null;

    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
    this.isProcessingVoice = false;  // Guard anti-double-envoi
    this.activeAudio = null;
    this.voiceLang = "fr";  // Langue de la voix : "dyu" ou "fr"
    this.currentMode = "fr->dyu";  // Mode par défaut : Français ➔ Dioula

    this.initDOMElements();
    this.bindEvents();

    // Charger ou créer une session par défaut
    const sessions = this.profile.sessions || [];
    if (sessions.length > 0) {
      this.loadSession(sessions[0].id);
    } else {
      this.newConversation();
    }

    this.renderScenarios();
    this.renderSidebar();
    this.checkHealth();
  }

  initDOMElements() {
    // Onglets
    this.tabChat = document.getElementById("tab-btn-chat");
    this.tabTranslate = document.getElementById("tab-btn-translate");
    this.paneChat = document.getElementById("pane-chat");
    this.paneTranslate = document.getElementById("pane-translate");

    // Chat
    this.messagesContainer = document.getElementById("messages-container");
    this.welcomeHero = document.getElementById("welcome-hero");
    this.chatInput = document.getElementById("chat-input-text");
    this.btnSend = document.getElementById("btn-send-message");
    this.btnRecord = document.getElementById("btn-record-voice");
    this.micIcon = document.getElementById("mic-icon");
    this.btnVoiceLang = document.getElementById("btn-voice-lang");
    this.selectRate = document.getElementById("select-speaking-rate");
    this.scenariosQuickBar = document.getElementById("scenarios-quick-bar");
    this.welcomeChipsContainer = document.getElementById("welcome-chips-container");
    this.welcomeUsername = document.getElementById("welcome-username");
    this.headerConvName = document.getElementById("header-conv-name");

    // Mode de conversation
    this.btnChatModeSelector = document.getElementById("btn-chat-mode-selector");
    this.chatModeDropdown = document.getElementById("chat-mode-dropdown");
    this.chatModeIcon = document.getElementById("chat-mode-icon");
    this.chatModeLabel = document.getElementById("chat-mode-label");

    // Sidebar
    this.sidebar = document.getElementById("sessions-sidebar");
    this.sidebarOverlay = document.getElementById("sidebar-overlay");
    this.sessionsList = document.getElementById("sessions-list");
    this.sidebarProfileName = document.getElementById("sidebar-profile-name");
    this.sidebarProfileMeta = document.getElementById("sidebar-profile-meta");
    this.sidebarAvatar = document.getElementById("sidebar-avatar");
    this.btnNewConv = document.getElementById("btn-new-conversation");
    this.btnOpenSidebar = document.getElementById("btn-open-sidebar");
    this.btnCloseSidebar = document.getElementById("btn-close-sidebar");
    this.btnLogout = document.getElementById("btn-logout");

    // Inspector
    this.inspector = document.getElementById("pipeline-inspector");
    this.inspectorOverlay = document.getElementById("inspector-overlay");
    this.btnCloseInspector = document.getElementById("btn-close-inspector");
    this.btnToggleInspector = document.getElementById("btn-toggle-inspector");
    this.welcomeFilterBar = document.getElementById("welcome-filter-bar");
    this.statTotalMs = document.getElementById("stat-total-ms");
    this.statSttMs = document.getElementById("stat-stt-ms");
    this.stepSttText = document.getElementById("step-stt-text");
    this.statMtInMs = document.getElementById("stat-mt-in-ms");
    this.stepMtInText = document.getElementById("step-mt-in-text");
    this.statLlmMs = document.getElementById("stat-llm-ms");
    this.stepLlmText = document.getElementById("step-llm-text");
    this.statLlmName = document.getElementById("stat-llm-name");
    this.statMtOutMs = document.getElementById("stat-mt-out-ms");
    this.stepMtOutText = document.getElementById("step-mt-out-text");
    this.statTtsMs = document.getElementById("stat-tts-ms");
    this.stepTtsText = document.getElementById("step-tts-text");
    this.inspectorStatusBadge = document.getElementById("inspector-status-badge");

    // Statut & Modal
    this.statusBadge = document.getElementById("server-status-badge");
    this.statusText = document.getElementById("server-status-text");
    this.modalSettings = document.getElementById("modal-settings");
    this.btnOpenSettings = document.getElementById("btn-open-settings");
    this.btnCloseSettings = document.getElementById("btn-close-settings");
    this.btnSaveSettings = document.getElementById("btn-save-settings");
    this.inputApiUrl = document.getElementById("input-api-url");
    this.inputApiKey = document.getElementById("input-api-key");

    // Modal suppression
    this.modalDeleteConv = document.getElementById("modal-delete-conv");
    this.btnCancelDelete = document.getElementById("btn-cancel-delete");
    this.btnCancelDelete2 = document.getElementById("btn-cancel-delete-2");
    this.btnConfirmDelete = document.getElementById("btn-confirm-delete");

    // Traducteur Direct
    this.selectSrcLang = document.getElementById("select-src-lang");
    this.selectTgtLang = document.getElementById("select-tgt-lang");
    this.translateSrcText = document.getElementById("translate-src-text");
    this.translateTgtText = document.getElementById("translate-tgt-text");
    this.btnRunTranslate = document.getElementById("btn-run-translate");
    this.btnSwapLanguages = document.getElementById("btn-swap-languages");
    this.btnClearSrc = document.getElementById("btn-clear-src");
    this.btnCopyTgt = document.getElementById("btn-copy-tgt");
    this.btnListenDirect = document.getElementById("btn-listen-direct-tts");
    this.btnDirectTtsSpeed = document.getElementById("btn-direct-tts-speed");
    this.translateTimeIndicator = document.getElementById("translate-time-indicator");

    this.inputApiUrl.value = this.apiUrl;
    this.inputApiKey.value = this.apiKey;

    // Welcome username
    if (this.welcomeUsername) {
      this.welcomeUsername.textContent = `${this.profile.name} !`;
    }

    // Sidebar profile info
    if (this.sidebarProfileName) {
      this.sidebarProfileName.textContent = this.profile.name;
    }
    if (this.sidebarAvatar) {
      this.sidebarAvatar.textContent = this.profile.name.charAt(0).toUpperCase();
    }
  }

  bindEvents() {
    // Navigation tabs
    this.tabChat.addEventListener("click", () => this.switchTab("chat"));
    this.tabTranslate.addEventListener("click", () => this.switchTab("translate"));

    // Chat actions
    this.btnSend.addEventListener("click", () => this.sendTextMessage());
    this.chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); this.sendTextMessage(); }
    });
    this.btnRecord.addEventListener("click", () => this.toggleVoiceRecording());

    // Toggle langue voix
    this.btnVoiceLang?.addEventListener("click", () => {
      this.voiceLang = this.voiceLang === "dyu" ? "fr" : "dyu";
      const isDyu = this.voiceLang === "dyu";
      if (this.btnVoiceLang) {
        this.btnVoiceLang.textContent = isDyu ? "🗣️" : "🇫🇷";
        this.btnVoiceLang.title = isDyu ? "Voix en Dioula (cliquer pour passer en Français)" : "Voix en Français (cliquer pour passer en Dioula)";
      }
      this.showToast(isDyu ? "🎙️ Voix : Dioula" : "🎙️ Voix : Français");
    });

    // Sélecteur de mode de conversation dans le Header
    this.btnChatModeSelector?.addEventListener("click", (e) => {
      e.stopPropagation();
      this.chatModeDropdown?.classList.toggle("open");
    });

    document.addEventListener("click", (e) => {
      if (!e.target.closest(".chat-mode-selector-wrapper")) {
        this.chatModeDropdown?.classList.remove("open");
      }
    });

    this.chatModeDropdown?.querySelectorAll(".mode-dropdown-item").forEach((item) => {
      item.addEventListener("click", () => {
        const mode = item.dataset.mode;
        if (mode) {
          this.setConversationMode(mode, true);
          this.chatModeDropdown?.classList.remove("open");
        }
      });
    });

    this.bindWelcomeModes();

    // Sidebar
    this.btnOpenSidebar?.addEventListener("click", () => this.openSidebar());
    this.btnCloseSidebar?.addEventListener("click", () => this.closeSidebar());
    this.sidebarOverlay?.addEventListener("click", () => this.closeSidebar());
    this.btnNewConv?.addEventListener("click", () => { this.newConversation(); this.closeSidebar(); });
    this.btnLogout?.addEventListener("click", () => this.logout());

    // Inspector toggle
    const toggleInspector = () => {
      const isMobile = window.innerWidth <= 1024;
      if (isMobile) {
        const isOpen = this.inspector.classList.contains("open");
        this.inspector.classList.toggle("open", !isOpen);
        if (this.inspectorOverlay) this.inspectorOverlay.classList.toggle("open", !isOpen);
      } else {
        this.inspector.classList.toggle("collapsed");
      }
    };
    this.btnToggleInspector?.addEventListener("click", toggleInspector);
    this.btnCloseInspector?.addEventListener("click", () => {
      this.inspector.classList.remove("open");
      if (this.inspectorOverlay) this.inspectorOverlay.classList.remove("open");
    });
    if (this.inspectorOverlay) {
      this.inspectorOverlay.addEventListener("click", () => {
        this.inspector.classList.remove("open");
        this.inspectorOverlay.classList.remove("open");
      });
    }

    // Filtres scénarios
    if (this.welcomeFilterBar) {
      this.welcomeFilterBar.querySelectorAll(".filter-chip").forEach((btn) => {
        btn.addEventListener("click", () => {
          this.welcomeFilterBar.querySelectorAll(".filter-chip").forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");
          activeFilter = btn.dataset.dir || "all";
          this.renderScenarios();
        });
      });
    }

    // Settings modal
    this.btnOpenSettings?.addEventListener("click", () => this.modalSettings.classList.add("open"));
    this.btnCloseSettings?.addEventListener("click", () => this.modalSettings.classList.remove("open"));
    this.btnSaveSettings?.addEventListener("click", () => this.saveSettings());

    // Delete conv modal
    this.btnCancelDelete?.addEventListener("click", () => this.modalDeleteConv.classList.remove("open"));
    this.btnCancelDelete2?.addEventListener("click", () => this.modalDeleteConv.classList.remove("open"));
    this.btnConfirmDelete?.addEventListener("click", () => this.confirmDeleteSession());

    // Direct Translate
    this.btnRunTranslate?.addEventListener("click", () => this.runDirectTranslate());
    this.btnSwapLanguages?.addEventListener("click", () => this.swapLanguages());
    this.btnClearSrc?.addEventListener("click", () => {
      this.translateSrcText.value = "";
      this.translateTgtText.value = "";
    });
    this.btnCopyTgt?.addEventListener("click", () => {
      if (this.translateTgtText.value) {
        navigator.clipboard.writeText(this.translateTgtText.value);
        this.showToast("Traduction copiée !");
      }
    });

    // Direct TTS speed
    let directSpeed = 0.75;
    const directSpeeds = [0.6, 0.75, 0.9, 1.0, 1.25, 1.5];
    if (this.btnDirectTtsSpeed) {
      this.btnDirectTtsSpeed.addEventListener("click", () => {
        const idx = directSpeeds.indexOf(directSpeed);
        directSpeed = directSpeeds[(idx + 1) % directSpeeds.length];
        this.btnDirectTtsSpeed.querySelector("strong").textContent = `${directSpeed}x`;
        if (this.activeAudio) {
          this.activeAudio.playbackRate = directSpeed;
          this.activeAudio.preservesPitch = true;
        }
        this.showToast(`Vitesse : ${directSpeed}x`);
      });
    }

    this.btnListenDirect?.addEventListener("click", () => {
      const text = this.translateTgtText.value || this.translateSrcText.value;
      if (text) this.playTTS(text, directSpeed);
    });
  }

  // =====================================================================
  // SIDEBAR & SESSIONS
  // =====================================================================
  openSidebar() {
    this.sidebar.classList.add("open");
    this.sidebarOverlay.classList.add("open");
  }

  closeSidebar() {
    this.sidebar.classList.remove("open");
    this.sidebarOverlay.classList.remove("open");
  }

  renderSidebar() {
    const profile = getProfile(this.profileId);
    if (!profile) return;
    const sessions = profile.sessions || [];

    if (this.sidebarProfileMeta) {
      const n = sessions.length;
      this.sidebarProfileMeta.textContent = `${n} conversation${n !== 1 ? "s" : ""}`;
    }

    this.sessionsList.innerHTML = "";

    if (sessions.length === 0) {
      const empty = document.createElement("div");
      empty.style.cssText = "padding: 1rem 0.75rem; font-size: 0.8rem; color: var(--text-dim); text-align: center;";
      empty.textContent = "Aucune conversation";
      this.sessionsList.appendChild(empty);
      return;
    }

    sessions.forEach(session => {
      const item = document.createElement("div");
      item.className = "session-item" + (session.id === this.currentSessionId ? " active" : "");
      const msgCount = (session.messages ? session.messages.length : (session.messageCount || 0));
      const countLabel = msgCount > 0 ? `${msgCount} msg · ` : "";
      item.innerHTML = `
        <span class="session-item-icon">💬</span>
        <div class="session-item-body">
          <div class="session-item-title">${this.escapeHtml(session.title)}</div>
          <div class="session-item-meta">${countLabel}${this.formatDate(session.createdAt)}</div>
        </div>
        <button class="session-item-del" title="Supprimer" data-id="${session.id}">🗑</button>
      `;
      item.addEventListener("click", (e) => {
        if (e.target.closest(".session-item-del")) return;
        this.loadSession(session.id);
        this.closeSidebar();
      });
      item.querySelector(".session-item-del").addEventListener("click", (e) => {
        e.stopPropagation();
        this.askDeleteSession(session.id);
      });
      this.sessionsList.appendChild(item);
    });
  }

  newConversation() {
    // Si la session courante est déjà vide et toute neuve, inutile d'en créer une autre
    if (this.currentSession && (!this.currentSession.messages || this.currentSession.messages.length === 0) && this.currentSession.title === "Nouvelle conversation") {
      this.clearMessages();
      this.chatInput.focus();
      return;
    }
    const session = createSession(this.profileId, "Nouvelle conversation", "fr->dyu");
    if (!session) return;
    this.profile = getProfile(this.profileId);
    this.currentSessionId = session.id;
    this.currentSession = session;
    this.clearMessages();
    this.updateHeaderTitle("Nouvelle conversation");
    this.setConversationMode("fr->dyu", false);
    this.renderSidebar();
    this.chatInput.focus();
  }

  loadSession(sessionId) {
    const profile = getProfile(this.profileId);
    const session = (profile?.sessions || []).find(s => s.id === sessionId);
    if (!session) return;
    this.profile = profile;
    this.currentSessionId = sessionId;
    this.currentSession = session;

    // Arrêter tout audio en cours de lecture
    if (this.activeAudio) {
      try { this.activeAudio.pause(); } catch (e) {}
      this.activeAudio = null;
    }

    // Réinitialise l'affichage
    this.clearMessages();
    this.updateHeaderTitle(session.title || "Conversation");
    this.setConversationMode(session.mode || "fr->dyu", false);
    this.renderSidebar();

    // Restaurer l'historique des messages sauvegardés de cette session
    const messages = session.messages || [];
    if (messages.length > 0) {
      if (this.welcomeHero) this.welcomeHero.style.display = "none";
      messages.forEach(msg => {
        this.appendMessage(msg.sender, msg.text, msg.canPlayAudio, null, false);
      });
      // Scroll vers le bas
      setTimeout(() => {
        if (this.messagesContainer) {
          this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
      }, 50);
    }
  }

  bindWelcomeModes() {
    const container = document.getElementById("welcome-modes-grid");
    if (!container) return;
    container.querySelectorAll(".welcome-mode-card").forEach((card) => {
      card.addEventListener("click", () => {
        const mode = card.dataset.mode;
        if (mode) {
          this.setConversationMode(mode, true);
          this.chatInput.focus();
        }
      });
    });
  }

  setConversationMode(mode, notify = false) {
    const validModes = ["fr->dyu", "dyu->fr", "dyu->dyu", "fr->fr"];
    if (!validModes.includes(mode)) mode = "fr->dyu";
    this.currentMode = mode;

    if (this.currentSessionId && this.profileId) {
      setSessionMode(this.profileId, this.currentSessionId, mode);
      if (this.currentSession) this.currentSession.mode = mode;
    }

    const modeLabels = {
      "fr->dyu": { icon: "🇫🇷 ➔ 🗣️", label: "Français ➔ Dioula", hint: "Écrivez en Français (Kouman répondra en Dioula)...", voice: "fr" },
      "dyu->fr": { icon: "🗣️ ➔ 🇫🇷", label: "Dioula ➔ Français", hint: "Sɛbɛn kɛ dioulakan na (Kouman répondra en Français)...", voice: "dyu" },
      "dyu->dyu": { icon: "🗣️ ➔ 🗣️", label: "Dioula ➔ Dioula", hint: "Sɛbɛn kɛ dioulakan na (Discussion 100% Dioula)...", voice: "dyu" },
      "fr->fr": { icon: "🇫🇷 ➔ 🇫🇷", label: "Français ➔ Français", hint: "Écrivez en Français (Discussion 100% Français)...", voice: "fr" },
    };

    const cfg = modeLabels[mode];

    // Header badge
    if (this.chatModeIcon) this.chatModeIcon.textContent = cfg.icon;
    if (this.chatModeLabel) this.chatModeLabel.textContent = cfg.label;

    // Dropdown active item
    this.chatModeDropdown?.querySelectorAll(".mode-dropdown-item").forEach((it) => {
      it.classList.toggle("active", it.dataset.mode === mode);
    });

    // Welcome cards active item
    const welcomeGrid = document.getElementById("welcome-modes-grid");
    welcomeGrid?.querySelectorAll(".welcome-mode-card").forEach((c) => {
      c.classList.toggle("active", c.dataset.mode === mode);
    });

    // Input placeholder
    if (this.chatInput) {
      this.chatInput.placeholder = cfg.hint;
    }

    // Default voice lang for mic
    this.voiceLang = cfg.voice;
    if (this.btnVoiceLang) {
      const isDyu = this.voiceLang === "dyu";
      this.btnVoiceLang.textContent = isDyu ? "🗣️" : "🇫🇷";
      this.btnVoiceLang.title = isDyu
        ? "Micro : Dioula (cliquer pour passer en Français)"
        : "Micro : Français (cliquer pour passer en Dioula)";
    }

    if (notify) {
      this.showToast(`Mode activé : ${cfg.label}`);
    }
  }

  clearMessages() {
    // Réinitialise le conteneur de messages et réaffiche le welcome hero
    this.messagesContainer.innerHTML = "";
    if (this.welcomeHero) {
      const hero = document.createElement("div");
      hero.className = "welcome-hero";
      hero.id = "welcome-hero";
      hero.innerHTML = `
        <div class="welcome-badge">🌍 Intelligence Artificielle Locale & Vocale</div>
        <h2>I bisimila ! <span id="welcome-username">${this.escapeHtml(this.profile.name)} !</span></h2>
        <p>Posez vos questions par écrit ou au micro en <strong>Dioula</strong> ou en <strong>Français</strong>.<br>Kouman traduit, raisonne et vous répond avec la voix.</p>

        <!-- 🎯 Choix du Mode d'échange au début de conversation -->
        <div class="welcome-modes-section">
          <div class="welcome-modes-title">
            <span class="welcome-modes-icon">🎯</span>
            <span>Choisissez le mode d'échange pour cette conversation :</span>
          </div>
          <div class="welcome-modes-grid" id="welcome-modes-grid">
            <button class="welcome-mode-card ${this.currentMode === "fr->dyu" ? "active" : ""}" data-mode="fr->dyu">
              <div class="card-flags">🇫🇷 ➔ 🗣️</div>
              <div class="card-title">Français ➔ Dioula</div>
              <div class="card-desc">Vous vous exprimez en Français, Kouman répond en Dioula avec audio.</div>
            </button>
            <button class="welcome-mode-card ${this.currentMode === "dyu->fr" ? "active" : ""}" data-mode="dyu->fr">
              <div class="card-flags">🗣️ ➔ 🇫🇷</div>
              <div class="card-title">Dioula ➔ Français</div>
              <div class="card-desc">Vous vous exprimez en Dioula, Kouman répond en Français.</div>
            </button>
            <button class="welcome-mode-card ${this.currentMode === "dyu->dyu" ? "active" : ""}" data-mode="dyu->dyu">
              <div class="card-flags">🗣️ ➔ 🗣️</div>
              <div class="card-title">Dioula ➔ Dioula</div>
              <div class="card-desc">Conversation intégrale en Dioula avec synthèse vocale.</div>
            </button>
            <button class="welcome-mode-card ${this.currentMode === "fr->fr" ? "active" : ""}" data-mode="fr->fr">
              <div class="card-flags">🇫🇷 ➔ 🇫🇷</div>
              <div class="card-title">Français ➔ Français</div>
              <div class="card-desc">Conversation intégrale en Français fluide.</div>
            </button>
          </div>
        </div>

        <div class="pipeline-tech-pills">
          <span class="tech-pill">🧠 <strong>NLLB-200</strong> Dioula</span>
          <span class="tech-pill">⚡ <strong>Claude Sonnet 5</strong></span>
          <span class="tech-pill">🎙️ <strong>MMS-TTS & Whisper</strong></span>
        </div>
        <div class="scenarios-section-header">
          <div class="scenarios-section-title">✨ Scénarios rapides</div>
          <div class="direction-filter-bar" id="welcome-filter-bar">
            <button class="filter-chip ${activeFilter === "all" ? "active" : ""}" data-dir="all">🌐 Tous</button>
            <button class="filter-chip ${activeFilter === "fr->dyu" ? "active" : ""}" data-dir="fr->dyu">🇫🇷 ➔ 🗣️</button>
            <button class="filter-chip ${activeFilter === "dyu->fr" ? "active" : ""}" data-dir="dyu->fr">🗣️ ➔ 🇫🇷</button>
          </div>
        </div>
        <div class="quick-chips-grid" id="welcome-chips-container"></div>
      `;
      this.messagesContainer.appendChild(hero);
      this.welcomeHero = hero;
      this.welcomeChipsContainer = hero.querySelector("#welcome-chips-container");
      this.welcomeFilterBar = hero.querySelector("#welcome-filter-bar");

      // Re-bind filtres scenarios
      this.welcomeFilterBar?.querySelectorAll(".filter-chip").forEach((btn) => {
        btn.addEventListener("click", () => {
          this.welcomeFilterBar.querySelectorAll(".filter-chip").forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");
          activeFilter = btn.dataset.dir || "all";
          this.renderScenarios();
        });
      });

      this.bindWelcomeModes();
      this.renderScenarios();
    }
  }

  updateHeaderTitle(title) {
    if (this.headerConvName) this.headerConvName.textContent = title;
  }

  askDeleteSession(sessionId) {
    this.pendingDeleteSessionId = sessionId;
    this.modalDeleteConv.classList.add("open");
  }

  confirmDeleteSession() {
    if (!this.pendingDeleteSessionId) return;
    const wasActive = this.pendingDeleteSessionId === this.currentSessionId;
    deleteSession(this.profileId, this.pendingDeleteSessionId);
    this.pendingDeleteSessionId = null;
    this.modalDeleteConv.classList.remove("open");
    this.profile = getProfile(this.profileId);
    this.renderSidebar();

    if (wasActive) {
      const profile = getProfile(this.profileId);
      const sessions = profile?.sessions || [];
      if (sessions.length > 0) this.loadSession(sessions[0].id);
      else this.newConversation();
    }
  }

  logout() {
    this.destroy();
    document.getElementById("app-container").style.display = "none";
    const loginScreen = document.getElementById("login-screen");
    loginScreen.style.display = "flex";
    loginScreen.style.animation = "";
    new LoginScreen((profileId) => {
      document.getElementById("app-container").style.display = "flex";
      window.koumanApp = new KoumanApp(profileId);
    });
  }

  /**
   * Nettoie les ressources de cette instance (micro, audio, listeners).
   * Appelé avant de recréer une nouvelle instance KoumanApp.
   */
  destroy() {
    // Arrêter l'enregistrement si actif
    if (this.mediaRecorder && this.isRecording) {
      try { this.mediaRecorder.stop(); } catch (e) {}
    }
    // Arrêter l'audio si en cours
    if (this.activeAudio) {
      try { this.activeAudio.pause(); } catch (e) {}
      this.activeAudio = null;
    }
    this.isProcessingVoice = false;
    this.isRecording = false;
  }

  formatDate(ts) {
    const d = new Date(ts);
    const now = new Date();
    const diffMs = now - d;
    if (diffMs < 60000) return "À l'instant";
    if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)} min`;
    if (diffMs < 86400000) return `${Math.floor(diffMs / 3600000)} h`;
    return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
  }

  escapeHtml(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // =====================================================================
  // TABS & SETTINGS
  // =====================================================================
  switchTab(tab) {
    if (tab === "chat") {
      this.tabChat.classList.add("active"); this.tabTranslate.classList.remove("active");
      this.paneChat.classList.add("active"); this.paneTranslate.classList.remove("active");
    } else {
      this.tabChat.classList.remove("active"); this.tabTranslate.classList.add("active");
      this.paneChat.classList.remove("active"); this.paneTranslate.classList.add("active");
    }
  }

  saveSettings() {
    this.apiUrl = this.inputApiUrl.value.trim().replace(/\/$/, "");
    this.apiKey = this.inputApiKey.value.trim();
    localStorage.setItem("kouma_api_url", this.apiUrl);
    localStorage.setItem("kouma_api_key", this.apiKey);
    this.modalSettings.classList.remove("open");
    this.checkHealth();
  }

  getHeaders(extra = {}) {
    const headers = { ...extra };
    if (this.apiKey) headers["X-API-Key"] = this.apiKey;
    return headers;
  }

  async checkHealth() {
    try {
      this.statusBadge.className = "badge-status loading";
      this.statusText.textContent = "...";
      const res = await fetch(`${this.apiUrl}/health`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      this.statusBadge.className = "badge-status";
      this.statusText.textContent = `En ligne`;
      if (data.llm_model) this.statLlmName.textContent = `Modèle : ${data.llm_model}`;
    } catch {
      this.statusBadge.className = "badge-status error";
      this.statusText.textContent = "Hors ligne";
    }
  }

  // =====================================================================
  // SCÉNARIOS
  // =====================================================================
  renderScenarios() {
    if (!this.scenariosQuickBar || !this.welcomeChipsContainer) return;
    this.scenariosQuickBar.innerHTML = "";
    this.welcomeChipsContainer.innerHTML = "";

    const visible = activeFilter === "all"
      ? SCENARIOS_BIDI
      : SCENARIOS_BIDI.filter((s) => s.direction === activeFilter);

    visible.forEach((item) => {
      const isDyuSrc = item.src_lang === "dyu";
      const dirIcon = isDyuSrc ? "🗣️ ➔ 🇫🇷" : "🇫🇷 ➔ 🗣️";

      const card = document.createElement("div");
      card.className = "bidi-card";
      card.innerHTML = `
        <div class="bidi-card-top">
          <span class="bidi-tag">${item.cat}</span>
          <span class="bidi-dir-badge">${dirIcon}</span>
        </div>
        <div class="bidi-card-text">${item.text}</div>
        <div class="bidi-card-ref">« ${item.ref} »</div>
      `;
      card.addEventListener("click", () => this.injectScenarioBidi(item));
      this.welcomeChipsContainer.appendChild(card);

      const pill = document.createElement("button");
      pill.className = "quick-pill";
      pill.innerHTML = `<strong>${item.id}</strong> <span>${item.text}</span>`;
      pill.title = `${item.cat} — Réf : ${item.ref}`;
      pill.addEventListener("click", () => this.injectScenarioBidi(item));
      this.scenariosQuickBar.appendChild(pill);
    });
  }

  injectScenarioBidi(item) {
    const isTranslateTab = this.paneTranslate.classList.contains("active");
    if (isTranslateTab) {
      this.selectSrcLang.value = item.src_lang;
      this.selectTgtLang.value = item.tgt_lang;
      this.translateSrcText.value = item.text;
      this.translateTgtText.value = "";
      this.translateTimeIndicator.textContent = `Réf : ${item.ref}`;
      this.runDirectTranslate();
    } else {
      this.chatInputLang = item.src_lang;
      this.chatInput.value = item.text;
      this.chatInput.focus();
    }
  }

  // =====================================================================
  // CHAT TEXT
  // =====================================================================
  async sendTextMessage() {
    const text = this.chatInput.value.trim();
    if (!text) return;

    // Cacher le welcome hero
    if (this.welcomeHero) this.welcomeHero.style.display = "none";

    this.appendMessage("user", text, false, null, true);
    this.chatInput.value = "";
    this.btnSend.disabled = true;

    // Détection de consigne explicite dans le texte ("réponds en français" / "réponds en dioula")
    const lower = text.toLowerCase();
    let dynamicTgt = null;
    if (/\b(r[ée]ponds?|parle|dis(?:-moi)?|explique)\s+(?:-moi\s+)?(?:en\s+)?français\b/i.test(lower) || /\b(?:en\s+)?français\s*(?:svp|s['’]il te plaît)?$/i.test(lower)) {
      dynamicTgt = "fr";
    } else if (/\b(r[ée]ponds?|parle|dis(?:-moi)?|explique|kouman)\s+(?:-moi\s+)?(?:en\s+)?(?:dioula|dyu|jula)\b/i.test(lower) || /\b(a\s+f[ɔo]|kouman)\s+(?:dioula|jula|dioulakan|tubabukan)\b/i.test(lower) || /\b(?:en\s+)?(?:dioula|dyu|jula)\s*(?:svp|s['’]il te plaît)?$/i.test(lower)) {
      dynamicTgt = lower.includes("tubabukan") ? "fr" : "dyu";
    }

    const [modeSrc, modeTgt] = (this.currentMode || "fr->dyu").split("->");

    if (dynamicTgt && dynamicTgt !== modeTgt) {
      this.setConversationMode(`${modeSrc}->${dynamicTgt}`, false);
      this.showToast(`Langue de réponse : ${dynamicTgt === "fr" ? "Français 🇫🇷" : "Dioula 🗣️"}`);
    }

    const effectiveTgt = dynamicTgt || modeTgt || "dyu";

    // Auto-detect langue du message
    const isDyuInput = /[ɛɔɲŋ]/i.test(text) || /\b(aw|ni|sɔgɔma|tile|wula|su|kɛnɛ|baa|dɔn|taa|sugu|san|di|wa|ce|kosɛbɛ|i|an|u|ka)\b/i.test(text);
    const lang = this.chatInputLang || (isDyuInput ? "dyu" : modeSrc);
    this.chatInputLang = null;

    // Mise à jour du titre de la session (premier message)
    if (this.currentSession && (!this.currentSession.messages || this.currentSession.messages.length <= 1)) {
      const title = text.length > 40 ? text.slice(0, 40) + "…" : text;
      updateSessionTitle(this.profileId, this.currentSessionId, title);
      this.profile = getProfile(this.profileId);
      this.currentSession = (this.profile.sessions || []).find(s => s.id === this.currentSessionId);
      this.updateHeaderTitle(title);
      this.renderSidebar();
    } else {
      updateSessionTitle(this.profileId, this.currentSessionId, this.currentSession?.title || "Conversation");
    }

    // Reset inspector
    this.inspectorStatusBadge.textContent = "Traitement...";
    this.stepSttText.textContent = "Mode texte";
    this.statSttMs.textContent = "0 ms";
    this.stepMtInText.textContent = lang === "fr" ? "Message en français." : "Traduction en cours...";
    const t0 = performance.now();

    try {
      const response = await fetch(`${this.apiUrl}/api/v1/chat?debug=true`, {
        method: "POST",
        headers: this.getHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ session_id: this.currentSessionId, lang, tgt_lang: effectiveTgt, message: text }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error?.message || `Erreur serveur (${response.status})`);
      }

      const data = await response.json();
      const elapsed = Math.round(performance.now() - t0);
      const replyLang = data.lang || effectiveTgt;
      const canPlayAudio = replyLang === "dyu";
      this.appendMessage("bot", data.reply, canPlayAudio, null, true);
      this.updateInspectorFromDebug(data.debug, elapsed, lang);
      if (canPlayAudio) this.playTTS(data.reply, parseFloat(this.selectRate.value) || 0.75);

    } catch (err) {
      this.appendMessage("bot", `⚠️ ${err.message}`, false, null, false);
      this.inspectorStatusBadge.textContent = "Erreur";
    } finally {
      this.btnSend.disabled = false;
    }
  }

  // =====================================================================
  // VOICE RECORDING
  // =====================================================================
  async toggleVoiceRecording() {
    if (this.isRecording) this.stopVoiceRecording();
    else await this.startVoiceRecording();
  }

  async startVoiceRecording() {
    try {
      // Contraintes optimales pour la reconnaissance vocale
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      this.audioChunks = [];
      this.mediaRecorder = new MediaRecorder(stream);
      this.mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) this.audioChunks.push(e.data); };
      this.mediaRecorder.onstop = () => {
        const mimeType = this.mediaRecorder.mimeType || "audio/webm";
        const audioBlob = new Blob(this.audioChunks, { type: mimeType });
        stream.getTracks().forEach(t => t.stop());
        this.sendVoiceMessage(audioBlob);
      };
      this.mediaRecorder.start();
      this.isRecording = true;
      this.btnRecord.classList.add("recording");
      this.micIcon.textContent = "⏹️";
      const langLabel = this.voiceLang === "fr" ? "Français 🇫🇷" : "Dioula 🗣️";
      this.showToast(`Enregistrement… Parlez en ${langLabel}`);
    } catch (err) {
      alert("Impossible d'accéder au micro : " + err.message);
    }
  }

  stopVoiceRecording() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;
      this.btnRecord.classList.remove("recording");
      this.micIcon.textContent = "🎙️";
    }
  }

  async sendVoiceMessage(audioBlob) {
    // Guard anti-double-envoi : on rejette si un envoi est déjà en cours
    if (this.isProcessingVoice) return;
    this.isProcessingVoice = true;

    if (this.welcomeHero) this.welcomeHero.style.display = "none";
    // Placeholder temporaire non sauvegardé dans l'historique
    this.appendMessage("user", "🎤 [Audio vocal envoyé, transcription en cours...]", false, null, false);
    const [modeSrc, modeTgt] = (this.currentMode || "fr->dyu").split("->");
    const rate = parseFloat(this.selectRate.value) || 0.75;
    const lang = this.voiceLang || modeSrc;
    const tgt_lang = modeTgt || "dyu";
    const ext = audioBlob.type.includes("webm") ? "webm" : (audioBlob.type.includes("mp4") ? "mp4" : "wav");
    const formData = new FormData();
    formData.append("session_id", this.currentSessionId);
    formData.append("lang", lang);
    formData.append("tgt_lang", tgt_lang);
    formData.append("speaking_rate", rate);
    formData.append("file", audioBlob, `enregistrement.${ext}`);
    this.inspectorStatusBadge.textContent = "Pipeline vocal...";
    this.stepSttText.textContent = "Reconnaissance vocale Whisper...";
    const t0 = performance.now();

    try {
      const response = await fetch(`${this.apiUrl}/api/v1/chat/voice?debug=true`, {
        method: "POST",
        headers: this.getHeaders(),
        body: formData,
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error?.message || `Erreur serveur vocal (${response.status})`);
      }
      const data = await response.json();
      const elapsed = Math.round(performance.now() - t0);
      const lastUserMsg = this.messagesContainer.querySelector(".message-row.user:last-child .msg-text");
      const userTranscript = `🎙️ « ${data.user_transcript} »`;
      if (lastUserMsg) lastUserMsg.textContent = userTranscript;

      const replyLang = data.reply_lang || data.lang || tgt_lang;

      // Si l'utilisateur a demandé oralement de changer la langue de réponse ("réponds en français" / "en dioula")
      if (replyLang === "fr" && modeTgt !== "fr") {
        this.setConversationMode(`${modeSrc}->fr`, false);
        this.showToast("Langue de réponse : Français 🇫🇷");
      } else if (replyLang === "dyu" && modeTgt !== "dyu") {
        this.setConversationMode(`${modeSrc}->dyu`, false);
        this.showToast("Langue de réponse : Dioula 🗣️");
      }

      // Sauvegarder la vraie transcription dans l'historique de la session
      const userMsgObj = {
        sender: "user",
        text: userTranscript,
        canPlayAudio: false,
        timestamp: Date.now()
      };
      addMessageToSession(this.profileId, this.currentSessionId, userMsgObj);
      if (this.currentSession) {
        if (!this.currentSession.messages) this.currentSession.messages = [];
        this.currentSession.messages.push(userMsgObj);
        this.currentSession.messageCount = this.currentSession.messages.length;
      }

      // Mise à jour du titre si premier échange de la conversation
      if (this.currentSession && (!this.currentSession.messages || this.currentSession.messages.length <= 2)) {
        const title = data.user_transcript.length > 40 ? data.user_transcript.slice(0, 40) + "…" : data.user_transcript;
        updateSessionTitle(this.profileId, this.currentSessionId, title);
        this.profile = getProfile(this.profileId);
        this.currentSession = (this.profile.sessions || []).find(s => s.id === this.currentSessionId);
        this.updateHeaderTitle(title);
        this.renderSidebar();
      }

      const canPlayAudio = !!data.audio_base64 || replyLang === "dyu";

      // Ajoute le message bot avec un player inline si audio disponible
      this.appendMessage("bot", data.reply_text, canPlayAudio, data.audio_base64, true);
      this.updateInspectorFromVoice(data, elapsed);

      // Auto-play via le player inline : simuler un clic sur le bouton Écouter
      if (data.audio_base64) {
        const lastBotPlayer = this.messagesContainer.querySelector(".message-row.bot:last-child .player-play-btn");
        if (lastBotPlayer) setTimeout(() => lastBotPlayer.click(), 200);
      }
    } catch (err) {
      const lastUserMsg = this.messagesContainer.querySelector(".message-row.user:last-child .msg-text");
      if (lastUserMsg && lastUserMsg.textContent.includes("en cours...")) {
        lastUserMsg.textContent = "🎤 [Échec de l'envoi vocal]";
      }
      this.appendMessage("bot", `⚠️ ${err.message}`, false, null, false);
      this.inspectorStatusBadge.textContent = "Erreur";
    } finally {
      this.isProcessingVoice = false;
    }
  }

  // =====================================================================
  // MESSAGES
  // =====================================================================
  appendMessage(sender, text, canPlayAudio = false, base64Audio = null, save = true) {
    const row = document.createElement("div");
    row.className = `message-row ${sender}`;
    const avatar = document.createElement("div");
    avatar.className = "msg-avatar";
    avatar.textContent = sender === "bot" ? "🌍" : "👤";
    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    const textEl = document.createElement("div");
    textEl.className = "msg-text";
    textEl.textContent = text;
    bubble.appendChild(textEl);
    if (canPlayAudio) bubble.appendChild(this.createAudioPlayer(text, base64Audio));
    row.appendChild(avatar);
    row.appendChild(bubble);
    this.messagesContainer.appendChild(row);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

    // Sauvegarde persistante dans l'historique de la session
    if (save && this.currentSessionId && this.profileId) {
      const msgObj = {
        sender,
        text,
        canPlayAudio: !!canPlayAudio,
        timestamp: Date.now()
      };
      addMessageToSession(this.profileId, this.currentSessionId, msgObj);
      if (this.currentSession) {
        if (!this.currentSession.messages) this.currentSession.messages = [];
        this.currentSession.messages.push(msgObj);
        this.currentSession.messageCount = this.currentSession.messages.length;
      }
      this.renderSidebar();
    }
  }

  /**
   * Lecteur audio interactif avec contrôle de vitesse en direct (playbackRate).
   */
  createAudioPlayer(text, base64Audio = null) {
    const player = document.createElement("div");
    player.className = "msg-audio-player";
    let currentBase64 = base64Audio;
    let audioElement = null;
    let isPlaying = false;
    let currentSpeed = parseFloat(this.selectRate?.value) || 0.75;
    const speeds = [0.6, 0.75, 0.9, 1.0, 1.25, 1.5];

    const playBtn = document.createElement("button");
    playBtn.className = "player-play-btn";
    playBtn.innerHTML = `<span class="icon">▶</span> <span class="label">Écouter</span>`;

    const progressTrack = document.createElement("div");
    progressTrack.className = "player-progress-track";
    const progressBar = document.createElement("div");
    progressBar.className = "player-progress-bar";
    progressTrack.appendChild(progressBar);

    const timeLabel = document.createElement("span");
    timeLabel.className = "player-time-label";
    timeLabel.textContent = "0:00";

    const speedBtn = document.createElement("button");
    speedBtn.className = "player-speed-btn";
    speedBtn.title = "Cliquer pour modifier la vitesse";
    speedBtn.innerHTML = `<span>⚡</span> <strong>${currentSpeed}x</strong>`;
    speedBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const idx = speeds.indexOf(currentSpeed);
      currentSpeed = speeds[(idx + 1) % speeds.length];
      speedBtn.querySelector("strong").textContent = `${currentSpeed}x`;
      if (audioElement) { audioElement.playbackRate = currentSpeed; audioElement.preservesPitch = true; }
      this.showToast(`Vitesse : ${currentSpeed}x`);
    });

    const updatePlayState = (playing) => {
      isPlaying = playing;
      if (playing) {
        playBtn.classList.add("playing");
        playBtn.querySelector(".icon").textContent = "⏸";
        playBtn.querySelector(".label").textContent = "Pause";
      } else {
        playBtn.classList.remove("playing");
        playBtn.querySelector(".icon").textContent = "▶";
        playBtn.querySelector(".label").textContent = "Écouter";
      }
    };

    playBtn.addEventListener("click", async () => {
      if (isPlaying && audioElement) { audioElement.pause(); updatePlayState(false); return; }
      if (!currentBase64) {
        playBtn.disabled = true;
        playBtn.querySelector(".label").textContent = "Chargement...";
        try {
          const res = await fetch(`${this.apiUrl}/api/v1/audio/synthesize`, {
            method: "POST",
            headers: this.getHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify({ text, lang: "dyu", speaking_rate: 0.75 }),
          });
          if (!res.ok) throw new Error("Erreur TTS");
          const data = await res.json();
          currentBase64 = data.audio_base64;
        } catch {
          this.showToast("Erreur de synthèse vocale");
          playBtn.disabled = false;
          playBtn.querySelector(".label").textContent = "Écouter";
          return;
        }
        playBtn.disabled = false;
      }
      if (this.activeAudio && this.activeAudio !== audioElement) {
        this.activeAudio.pause();
        if (this.activeAudio._onStopCallback) this.activeAudio._onStopCallback();
      }
      if (!audioElement) {
        audioElement = new Audio(`data:audio/wav;base64,${currentBase64}`);
        audioElement.preservesPitch = true;
        audioElement.playbackRate = currentSpeed;
        audioElement.addEventListener("timeupdate", () => {
          if (audioElement.duration) {
            progressBar.style.width = `${(audioElement.currentTime / audioElement.duration) * 100}%`;
            const fmt = (s) => `${Math.floor(s/60)}:${Math.floor(s%60).toString().padStart(2,"0")}`;
            timeLabel.textContent = `${fmt(audioElement.currentTime)} / ${fmt(audioElement.duration)}`;
          }
        });
        audioElement.addEventListener("ended", () => { updatePlayState(false); progressBar.style.width = "0%"; timeLabel.textContent = "0:00"; });
        audioElement._onStopCallback = () => updatePlayState(false);
      } else {
        audioElement.playbackRate = currentSpeed;
      }
      this.activeAudio = audioElement;
      audioElement.play().then(() => updatePlayState(true)).catch(e => console.log("Audio bloqué:", e));
    });

    player.appendChild(playBtn);
    player.appendChild(progressTrack);
    player.appendChild(timeLabel);
    player.appendChild(speedBtn);
    return player;
  }

  // =====================================================================
  // INSPECTOR
  // =====================================================================
  updateInspectorFromDebug(debug, totalMs, lang = "dyu") {
    this.inspectorStatusBadge.textContent = "Terminé";
    this.statTotalMs.textContent = `${totalMs} ms`;
    if (debug) {
      if (lang === "fr") {
        this.stepMtInText.textContent = "Message rédigé en français.";
        this.stepLlmText.textContent = debug.fr_reply || "—";
        this.stepMtOutText.textContent = "Réponse en français.";
        this.statMtInMs.textContent = "0 ms";
        this.statLlmMs.textContent = debug.timings_ms?.llm ? `${Math.round(debug.timings_ms.llm)} ms` : "— ms";
        this.statMtOutMs.textContent = "0 ms";
      } else {
        this.stepMtInText.textContent = debug.fr_input || "—";
        this.stepLlmText.textContent = debug.fr_reply || "—";
        this.stepMtOutText.textContent = "Traduction Dioula générée.";
        const t = debug.timings_ms || {};
        this.statMtInMs.textContent = t.mt_in ? `${Math.round(t.mt_in)} ms` : "— ms";
        this.statLlmMs.textContent = t.llm ? `${Math.round(t.llm)} ms` : "— ms";
        this.statMtOutMs.textContent = t.mt_out ? `${Math.round(t.mt_out)} ms` : "— ms";
      }
    }
  }

  updateInspectorFromVoice(data, totalMs) {
    this.inspectorStatusBadge.textContent = "Terminé (Vocal)";
    this.statTotalMs.textContent = `${totalMs} ms`;
    this.stepSttText.textContent = data.user_transcript || "—";
    this.stepTtsText.textContent = "Audio généré via Meta MMS-TTS Dioula";
    const t = data.timings_ms || {};
    this.statSttMs.textContent = t.stt ? `${Math.round(t.stt)} ms` : "— ms";
    this.statMtInMs.textContent = t.mt_in ? `${Math.round(t.mt_in)} ms` : "— ms";
    this.statLlmMs.textContent = t.llm ? `${Math.round(t.llm)} ms` : "— ms";
    this.statMtOutMs.textContent = t.mt_out ? `${Math.round(t.mt_out)} ms` : "— ms";
    this.statTtsMs.textContent = t.tts ? `${Math.round(t.tts)} ms` : "— ms";
    if (data.debug) {
      this.stepMtInText.textContent = data.debug.fr_input || "—";
      this.stepLlmText.textContent = data.debug.fr_reply || "—";
    }
  }

  // =====================================================================
  // TTS / AUDIO
  // =====================================================================
  async playTTS(text, rate = 0.75) {
    try {
      this.showToast("Génération de la voix dioula...");
      const res = await fetch(`${this.apiUrl}/api/v1/audio/synthesize`, {
        method: "POST",
        headers: this.getHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ text, lang: "dyu", speaking_rate: rate }),
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      this.playBase64Audio(data.audio_base64);
    } catch { console.warn("TTS échoué"); }
  }

  playBase64Audio(base64String) {
    if (this.activeAudio) this.activeAudio.pause();
    const audio = new Audio(`data:audio/wav;base64,${base64String}`);
    this.activeAudio = audio;
    audio.play().catch(e => console.log("Lecture bloquée:", e));
  }

  // =====================================================================
  // TRADUCTEUR DIRECT
  // =====================================================================
  async runDirectTranslate() {
    const text = this.translateSrcText.value.trim();
    if (!text) return;
    const src = this.selectSrcLang.value;
    const tgt = this.selectTgtLang.value;
    this.translateTgtText.value = "Traduction en cours...";
    const t0 = performance.now();
    try {
      const res = await fetch(`${this.apiUrl}/api/v1/translate`, {
        method: "POST",
        headers: this.getHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ text, src, tgt }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error?.message || "Erreur de traduction");
      }
      const data = await res.json();
      const elapsed = Math.round(performance.now() - t0);
      this.translateTgtText.value = data.translation;
      this.translateTimeIndicator.textContent = `Délai NLLB : ${data.time_ms || elapsed} ms`;
    } catch (e) {
      this.translateTgtText.value = `⚠️ ${e.message}`;
    }
  }

  swapLanguages() {
    const tmpLang = this.selectSrcLang.value;
    this.selectSrcLang.value = this.selectTgtLang.value;
    this.selectTgtLang.value = tmpLang;
    const tmpText = this.translateSrcText.value;
    this.translateSrcText.value = this.translateTgtText.value;
    this.translateTgtText.value = tmpText;
    if (this.translateSrcText.value) this.runDirectTranslate();
  }

  // =====================================================================
  // TOAST
  // =====================================================================
  showToast(msg) {
    let toast = document.getElementById("kouman-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "kouman-toast";
      toast.style.cssText = `
        position: fixed; bottom: 24px; right: 24px; background: rgba(18, 24, 38, 0.95);
        color: #f59e0b; padding: 12px 20px; border-radius: 9999px; font-size: 0.85rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5); border: 1px solid rgba(245, 158, 11, 0.3);
        z-index: 9999; backdrop-filter: blur(10px); transition: all 0.3s ease;
      `;
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = "1";
    toast.style.transform = "translateY(0)";
    clearTimeout(this._toastTimeout);
    this._toastTimeout = setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
    }, 2800);
  }
}

// ==========================================================================
// DÉMARRAGE
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  // Ajouter l'animation de sortie pour le login
  const style = document.createElement("style");
  style.textContent = `
    @keyframes loginCardOut {
      to { opacity: 0; transform: scale(0.95); }
    }
  `;
  document.head.appendChild(style);

  // Toujours afficher le login en premier
  new LoginScreen((profileId) => {
    document.getElementById("app-container").style.display = "flex";
    window.koumanApp = new KoumanApp(profileId);
  });
});
