/**
 * KOUMAN AI — Frontend Logic & Audio Pipeline (v0.4.0)
 * Gère l'enregistrement vocal, la lecture TTS, le chat interactif et la transparence du pipeline.
 */

// --- 10 SCÉNARIOS DE TEST VALIDÉS (K3) ---
const SCENARIOS = [
  { id: "S01", dyu: "I ni sɔgɔma, i ka kɛnɛ wa ?", cat: "Salutation", fr: "Bonjour, comment vas-tu ?" },
  { id: "S02", dyu: "N bɛ taa sugu la bi", cat: "Commerce", fr: "Je vais au marché aujourd'hui" },
  { id: "S03", dyu: "Dɔgɔtɔrɔso bɛ min ?", cat: "Santé", fr: "Où se trouve le centre de santé ?" },
  { id: "S04", dyu: "Kɛnɛya bɛ wa ?", cat: "Santé", fr: "Comment va la santé ?" },
  { id: "S05", dyu: "Sɔngɔ ka gɛlɛn kosɛbɛ", cat: "Commerce", fr: "Le prix est trop cher" },
  { id: "S06", dyu: "N bɛ a fɛ ka dɔ fɔ i ye", cat: "Conversation", fr: "J'aimerais te dire quelque chose" },
  { id: "S07", dyu: "I tɔgɔ bi di ?", cat: "Présentation", fr: "Comment t'appelles-tu ?" },
  { id: "S08", dyu: "Sanji bɛ na bi wa ?", cat: "Météo", fr: "Va-t-il pleuvoir aujourd'hui ?" },
  { id: "S09", dyu: "I bɛ se ka n dɛmɛ wa ?", cat: "Entraide", fr: "Peux-tu m'aider ?" },
  { id: "S10", dyu: "I ni cɛ kosɛbɛ i ka dɛmɛ la", cat: "Remerciement", fr: "Merci beaucoup pour ton aide" },
];

class KoumanApp {
  constructor() {
    this.apiUrl = localStorage.getItem("kouma_api_url") || "";
    this.apiKey = localStorage.getItem("kouma_api_key") || "";
    this.sessionId = localStorage.getItem("kouma_session_id") || "demo-session-" + Math.floor(Math.random() * 10000);
    localStorage.setItem("kouma_session_id", this.sessionId);

    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
    this.activeAudio = null;

    this.initDOMElements();
    this.bindEvents();
    this.renderScenarios();
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
    this.selectRate = document.getElementById("select-speaking-rate");
    this.scenariosQuickBar = document.getElementById("scenarios-quick-bar");
    this.welcomeChipsContainer = document.getElementById("welcome-chips-container");

    // Inspector
    this.inspector = document.getElementById("pipeline-inspector");
    this.btnToggleInspector = document.getElementById("btn-toggle-inspector");
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
    this.translateTimeIndicator = document.getElementById("translate-time-indicator");

    this.inputApiUrl.value = this.apiUrl;
    this.inputApiKey.value = this.apiKey;
  }

  bindEvents() {
    // Navigation
    this.tabChat.addEventListener("click", () => this.switchTab("chat"));
    this.tabTranslate.addEventListener("click", () => this.switchTab("translate"));

    // Chat actions
    this.btnSend.addEventListener("click", () => this.sendTextMessage());
    this.chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendTextMessage();
      }
    });

    // Voice recording
    this.btnRecord.addEventListener("click", () => this.toggleVoiceRecording());

    // Inspector toggle
    this.btnToggleInspector.addEventListener("click", () => {
      const isVisible = this.inspector.style.display !== "none";
      this.inspector.style.display = isVisible ? "none" : "flex";
    });

    // Settings modal
    this.btnOpenSettings.addEventListener("click", () => this.modalSettings.classList.add("open"));
    this.btnCloseSettings.addEventListener("click", () => this.modalSettings.classList.remove("open"));
    this.btnSaveSettings.addEventListener("click", () => this.saveSettings());

    // Direct Translate
    this.btnRunTranslate.addEventListener("click", () => this.runDirectTranslate());
    this.btnSwapLanguages.addEventListener("click", () => this.swapLanguages());
    this.btnClearSrc.addEventListener("click", () => {
      this.translateSrcText.value = "";
      this.translateTgtText.value = "";
    });
    this.btnCopyTgt.addEventListener("click", () => {
      if (this.translateTgtText.value) {
        navigator.clipboard.writeText(this.translateTgtText.value);
        this.showToast("Traduction copiée !");
      }
    });
    this.btnListenDirect.addEventListener("click", () => {
      const text = this.translateTgtText.value || this.translateSrcText.value;
      if (text) {
        this.playTTS(text, parseFloat(this.selectRate.value) || 0.75);
      }
    });
  }

  switchTab(tab) {
    if (tab === "chat") {
      this.tabChat.classList.add("active");
      this.tabTranslate.classList.remove("active");
      this.paneChat.classList.add("active");
      this.paneTranslate.classList.remove("active");
    } else {
      this.tabChat.classList.remove("active");
      this.tabTranslate.classList.add("active");
      this.paneChat.classList.remove("active");
      this.paneTranslate.classList.add("active");
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
    if (this.apiKey) {
      headers["X-API-Key"] = this.apiKey;
    }
    return headers;
  }

  async checkHealth() {
    try {
      this.statusBadge.className = "badge-status loading";
      this.statusText.textContent = "Connexion...";

      const res = await fetch(`${this.apiUrl}/health`);
      if (!res.ok) throw new Error("Statut non ok");
      const data = await res.json();

      this.statusBadge.className = "badge-status";
      this.statusText.textContent = `En ligne (${data.translator?.name || "NLLB"})`;
      if (data.llm_model) {
        this.statLlmName.textContent = `Modèle : ${data.llm_model}`;
      }
    } catch (e) {
      this.statusBadge.className = "badge-status error";
      this.statusText.textContent = "Hors ligne (Vérifier clé/serveur)";
    }
  }

  renderScenarios() {
    this.scenariosQuickBar.innerHTML = "";
    this.welcomeChipsContainer.innerHTML = "";

    SCENARIOS.forEach((item) => {
      // Pour le welcome hero
      const chip = document.createElement("button");
      chip.className = "chip-btn";
      chip.innerHTML = `<span class="chip-category">${item.cat}</span> <span>${item.dyu}</span>`;
      chip.addEventListener("click", () => this.injectScenario(item.dyu));
      this.welcomeChipsContainer.appendChild(chip);

      // Pour la barre rapide au-dessus de l'input
      const quickChip = document.createElement("button");
      quickChip.className = "chip-btn";
      quickChip.innerHTML = `<strong>${item.id}:</strong> ${item.dyu}`;
      quickChip.addEventListener("click", () => this.injectScenario(item.dyu));
      this.scenariosQuickBar.appendChild(quickChip);
    });
  }

  injectScenario(text) {
    this.chatInput.value = text;
    this.chatInput.focus();
  }

  async sendTextMessage() {
    const text = this.chatInput.value.trim();
    if (!text) return;

    if (this.welcomeHero) {
      this.welcomeHero.style.display = "none";
    }

    this.appendMessage("user", text);
    this.chatInput.value = "";
    this.btnSend.disabled = true;

    // Reset inspector
    this.inspectorStatusBadge.textContent = "Traitement...";
    this.stepSttText.textContent = "Mode texte (pas d'audio entrant)";
    this.statSttMs.textContent = "0 ms";
    this.stepMtInText.textContent = "Traduction en cours...";

    const t0 = performance.now();

    try {
      const response = await fetch(`${this.apiUrl}/api/v1/chat?debug=true`, {
        method: "POST",
        headers: this.getHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          session_id: this.sessionId,
          lang: "dyu",
          message: text,
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error?.message || `Erreur serveur (${response.status})`);
      }

      const data = await response.json();
      const elapsed = Math.round(performance.now() - t0);

      this.appendMessage("bot", data.reply, true);
      this.updateInspectorFromDebug(data.debug, elapsed);

      // Lancer automatiquement la voix dioula
      this.playTTS(data.reply, parseFloat(this.selectRate.value) || 0.75);

    } catch (err) {
      this.appendMessage("bot", `⚠️ ${err.message}`);
      this.inspectorStatusBadge.textContent = "Erreur";
    } finally {
      this.btnSend.disabled = false;
    }
  }

  async toggleVoiceRecording() {
    if (this.isRecording) {
      this.stopVoiceRecording();
    } else {
      await this.startVoiceRecording();
    }
  }

  async startVoiceRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioChunks = [];
      this.mediaRecorder = new MediaRecorder(stream);

      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) this.audioChunks.push(e.data);
      };

      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: "audio/wav" });
        stream.getTracks().forEach((track) => track.stop());
        this.sendVoiceMessage(audioBlob);
      };

      this.mediaRecorder.start();
      this.isRecording = true;
      this.btnRecord.classList.add("recording");
      this.micIcon.textContent = "⏹️";
      this.showToast("Enregistrement en cours... Parlez en Dioula");
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
    if (this.welcomeHero) {
      this.welcomeHero.style.display = "none";
    }

    this.appendMessage("user", "🎤 [Audio vocal envoyé, transcription en cours...]");
    const rate = parseFloat(this.selectRate.value) || 0.75;

    const formData = new FormData();
    formData.append("session_id", this.sessionId);
    formData.append("lang", "dyu");
    formData.append("speaking_rate", rate);
    formData.append("file", audioBlob, "enregistrement.wav");

    this.inspectorStatusBadge.textContent = "Pipeline vocal en cours...";
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

      // Met à jour la bulle de l'utilisateur avec la vraie transcription
      const lastUserMsg = this.messagesContainer.querySelector(".message-row.user:last-child .msg-text");
      if (lastUserMsg) {
        lastUserMsg.textContent = `🎙️ « ${data.user_transcript} »`;
      }

      this.appendMessage("bot", data.reply_text, true, data.audio_base64);
      this.updateInspectorFromVoice(data, elapsed);

      // Joue directement l'audio retourné
      if (data.audio_base64) {
        this.playBase64Audio(data.audio_base64);
      }

    } catch (err) {
      this.appendMessage("bot", `⚠️ ${err.message}`);
      this.inspectorStatusBadge.textContent = "Erreur";
    }
  }

  appendMessage(sender, text, canPlayAudio = false, base64Audio = null) {
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

    if (canPlayAudio) {
      const meta = document.createElement("div");
      meta.className = "msg-meta";

      const playBtn = document.createElement("button");
      playBtn.className = "msg-audio-play";
      playBtn.innerHTML = `<span>🔊</span> Écouter`;
      playBtn.addEventListener("click", () => {
        if (base64Audio) {
          this.playBase64Audio(base64Audio);
        } else {
          this.playTTS(text, parseFloat(this.selectRate.value) || 0.75);
        }
      });

      meta.appendChild(playBtn);
      bubble.appendChild(meta);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    this.messagesContainer.appendChild(row);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }

  updateInspectorFromDebug(debug, totalMs) {
    this.inspectorStatusBadge.textContent = "Terminé";
    this.statTotalMs.textContent = `${totalMs} ms`;

    if (debug) {
      this.stepMtInText.textContent = debug.fr_input || "—";
      this.stepLlmText.textContent = debug.fr_reply || "—";
      this.stepMtOutText.textContent = "Traduction Dioula synthétisée.";

      const timings = debug.timings_ms || {};
      this.statMtInMs.textContent = timings.mt_in ? `${Math.round(timings.mt_in)} ms` : "— ms";
      this.statLlmMs.textContent = timings.llm ? `${Math.round(timings.llm)} ms` : "— ms";
      this.statMtOutMs.textContent = timings.mt_out ? `${Math.round(timings.mt_out)} ms` : "— ms";
    }
  }

  updateInspectorFromVoice(data, totalMs) {
    this.inspectorStatusBadge.textContent = "Terminé (Vocal)";
    this.statTotalMs.textContent = `${totalMs} ms`;

    this.stepSttText.textContent = data.user_transcript || "—";
    this.stepTtsText.textContent = "Audio généré via Meta MMS-TTS Dioula";

    const timings = data.timings_ms || {};
    this.statSttMs.textContent = timings.stt ? `${Math.round(timings.stt)} ms` : "— ms";
    this.statMtInMs.textContent = timings.mt_in ? `${Math.round(timings.mt_in)} ms` : "— ms";
    this.statLlmMs.textContent = timings.llm ? `${Math.round(timings.llm)} ms` : "— ms";
    this.statMtOutMs.textContent = timings.mt_out ? `${Math.round(timings.mt_out)} ms` : "— ms";
    this.statTtsMs.textContent = timings.tts ? `${Math.round(timings.tts)} ms` : "— ms";

    if (data.debug) {
      this.stepMtInText.textContent = data.debug.fr_input || "—";
      this.stepLlmText.textContent = data.debug.fr_reply || "—";
    }
  }

  async playTTS(text, rate = 0.75) {
    try {
      this.showToast("Génération de la voix dioula...");
      const res = await fetch(`${this.apiUrl}/api/v1/audio/synthesize`, {
        method: "POST",
        headers: this.getHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          text: text,
          lang: "dyu",
          speaking_rate: rate,
        }),
      });
      if (!res.ok) throw new Error("Erreur TTS");
      const data = await res.json();
      this.playBase64Audio(data.audio_base64);
    } catch (e) {
      console.warn("TTS échoué:", e);
    }
  }

  playBase64Audio(base64String) {
    if (this.activeAudio) {
      this.activeAudio.pause();
    }
    const audio = new Audio(`data:audio/wav;base64,${base64String}`);
    this.activeAudio = audio;
    audio.play().catch((e) => console.log("Lecture auto bloquée par le navigateur:", e));
  }

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

    if (this.translateSrcText.value) {
      this.runDirectTranslate();
    }
  }

  showToast(msg) {
    let toast = document.getElementById("kouman-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "kouman-toast";
      toast.style.cssText = `
        position: fixed; bottom: 24px; right: 24px; background: rgba(18, 24, 38, 0.95);
        color: #f59e0b; padding: 12px 20px; border-radius: 9999px; font-size: 0.85rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5); border: 1px solid rgba(245, 158, 11, 0.3);
        z-index: 999; backdrop-filter: blur(10px); transition: all 0.3s ease;
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

// Initialisation au chargement du DOM
document.addEventListener("DOMContentLoaded", () => {
  window.koumanApp = new KoumanApp();
});
