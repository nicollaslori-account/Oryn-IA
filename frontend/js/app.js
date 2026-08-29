/* ============================================================
   ORYN — app.js
   Vanilla JS: chat streaming, vision, FLUX.2/Wan generation,
   search, files, settings, themes, i18n.
   ============================================================ */

(function () {
  "use strict";

  var I18N = window.ORYN_I18N || {};
  var t = I18N.t || (function (k) { return k; });

  function $(s) { return document.querySelector(s); }
  function $$(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }

  /* ---------------- utils ---------------- */

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function md(src) {
    var s = esc(src);
    s = s.replace(/```([\s\S]*?)```/g, function (_, c) { return "<pre><code>" + c.trim() + "</code></pre>"; });
    s = s.replace(/`([^`\n]+)`/g, "<code>$1</code>");
    s = s.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, '<img src="$2" alt="$1">');
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/__([^_]+)__/g, "<strong>$1</strong>");
    s = s.replace(/(^|[*_\W])\*([^*\n]+)\*(?!\*)/g, "$1<em>$2</em>");
    s = s.replace(/(^|[^*_\w])_([^_\n]+)_(?!_)/g, "$1<em>$2</em>");

    var blocks = s.split(/\n{2,}/);
    var out = blocks.map(function (b) {
      b = b.trim();
      if (!b) return "";
      if (/^<pre>/.test(b)) return b;
      var h = b.match(/^(#{1,6})\s+(.*)$/m);
      if (h) return "<h" + h[1].length + ">" + inlineLine(h[2]) + "</h" + h[1].length + ">";
      var ul = b.split("\n").filter(Boolean);
      if (/^(\*|-)\s+/.test(ul[0])) {
        return "<ul>" + ul.map(function (l) { return "<li>" + inlineLine(l.replace(/^(\*|-)\s+/, "")) + "</li>"; }).join("") + "</ul>";
      }
      if (/^\d+\.\s+/.test(ul[0])) {
        return "<ol>" + ul.map(function (l) { return "<li>" + inlineLine(l.replace(/^\d+\.\s+/, "")) + "</li>"; }).join("") + "</ol>";
      }
      if (b.indexOf("&gt; ") === 0) {
        return "<blockquote>" + ul.map(function (l) { return inlineLine(l.replace(/^&gt;\s?/, "")); }).join("<br>") + "</blockquote>";
      }
      if (/^[-*_=]{3,}$/.test(b)) return "<hr>";
      return "<p>" + inlineLine(b.replace(/\n/g, "<br>")) + "</p>";
    });
    return out.join("\n");

    function inlineLine(x) {
      x = x.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
      x = x.replace(/__([^_]+)__/g, "<strong>$1</strong>");
      x = x.replace(/`([^`]+)`/g, "<code>$1</code>");
      x = x.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, '<img src="$2" alt="$1">');
      x = x.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
      return x;
    }
  }

  function toast(msg, type) {
    var box = $("#toasts");
    var el = document.createElement("div");
    el.className = "toast" + (type ? " " + type : "");
    el.textContent = msg;
    box.appendChild(el);
    setTimeout(function () { el.style.opacity = "0"; }, 3800);
    setTimeout(function () { el.remove(); }, 4200);
  }

  function fmtBytes(n) {
    if (n == null) return "";
    if (n < 1024) return n + " B";
    if (n < 1048576) return (n / 1024).toFixed(1) + " KB";
    return (n / 1048576).toFixed(1) + " MB";
  }

  function api(path, opts) {
    opts = opts || {};
    return fetch(path, opts).then(function (r) {
      return r.json().catch(function () { return { error: "Resposta inválida do servidor." }; }).then(function (data) {
        if (!r.ok) { var e = new Error((data && data.error) || r.status); e.data = data; throw e; }
        return data;
      });
    });
  }

  function mediaUrl(f) {
    return "/api/media?filename=" + encodeURIComponent(f.filename) +
      "&subfolder=" + encodeURIComponent(f.subfolder || "") +
      "&type=" + encodeURIComponent(f.type || "output");
  }

  function readFileAsDataURL(file) {
    return new Promise(function (resolve, reject) {
      var fr = new FileReader();
      fr.onload = function () { resolve(fr.result); };
      fr.onerror = reject;
      fr.readAsDataURL(file);
    });
  }

  /* ---------------- state ---------------- */

  var LS_SETTINGS = "oryn-settings";
  var LS_CONVOS = "oryn-conversations";

  var DEFAULT_SETTINGS = {
    lang: "ptBR",
    theme: "dark",
    custom: { primary: "#7c5cff", bg: "#0b0b0f", cards: "#17171f", text: "#eceaf2" },
    model: "",
    visionModel: "",
    temperature: 0.7,
    context: 8192,
    memory: true,
    animations: true,
    ollamaUrl: "http://127.0.0.1:11434",
    comfyuiUrl: "http://127.0.0.1:8188",
    comfyRoot: "C:\\ComfyUI\\ComfyUI",
    remoteUrl: "",
    imageDefault: "kontext_flux_2_klein", // server override
    videoDefault: "wan_5b"
  };

  var settings = loadSettings();
  var conversations = loadConvos();
  var currentConvo = null;
  var composerAttachments = [];
  var chatting = false;
  var abortCtl = null;
  var visionImage = null;
  var vidAnimImage = null; // {dataUrl} user file or {filename,subfolder,type} comfy ref
  var jobs = {}; // promptId -> element
  var statusTimer = null;

  function loadSettings() {
    try {
      var raw = localStorage.getItem(LS_SETTINGS);
      if (!raw) return JSON.parse(JSON.stringify(DEFAULT_SETTINGS));
      var s = JSON.parse(raw);
      return Object.assign({}, DEFAULT_SETTINGS, s);
    } catch (e) { return JSON.parse(JSON.stringify(DEFAULT_SETTINGS)); }
  }

  function saveSettings() {
    try { localStorage.setItem(LS_SETTINGS, JSON.stringify(settings)); } catch (e) { }
  }

  function loadConvos() {
    try {
      var raw = localStorage.getItem(LS_CONVOS);
      return raw ? JSON.parse(raw) : [];
    } catch (e) { return []; }
  }

  function saveConvos() {
    try { localStorage.setItem(LS_CONVOS, JSON.stringify(conversations)); } catch (e) { }
  }

  /* ---------------- i18n / theme ---------------- */

  function applyLang() {
    I18N.setLanguage(settings.lang);
    I18N.applyI18n(document);
    document.documentElement.lang = settings.lang.replace("ptBR", "pt-BR");
    refreshConvoList();
    refreshSettingsUi();
    refreshViewLabel();
  }

  function applyTheme() {
    var th = settings.theme;
    document.body.setAttribute("data-theme", th);
    if (th === "custom") {
      var c = settings.custom || {};
      var s = document.body.style;
      s.setProperty("--cust-primary", c.primary || "#7c5cff");
      s.setProperty("--cust-bg", c.bg || "#0b0b0f");
      s.setProperty("--cust-cards", c.cards || "#17171f");
      s.setProperty("--cust-text", c.text || "#eceaf2");
    }
    document.body.classList.toggle("no-anim", !settings.animations);
    var st = $("#setTheme");
    if (st) st.value = th;
  }

  function refreshViewLabel() {
    var v = $("#mainNav .nav-item.is-active");
    if (v) $("#viewLabel").textContent = t("nav." + v.getAttribute("data-view"));
  }

  function switchView(name) {
    $$("#mainNav .nav-item").forEach(function (b) {
      b.classList.toggle("is-active", b.getAttribute("data-view") === name);
    });
    $$(".view").forEach(function (v) {
      v.classList.toggle("is-active", v.id === "view-" + name);
    });
    $("#sidebar").classList.remove("open");
    refreshViewLabel();
  }

  function selectChatTool(name) {
    var tabs = $$(".chat-tools .ct-tab");
    var panels = $$(".chat-tools .ct-panel");
    var isOpen = false;
    tabs.forEach(function (b) {
      if (b.getAttribute("data-ttab") === name && b.classList.contains("is-active")) isOpen = true;
      b.classList.toggle("is-active", !isOpen && b.getAttribute("data-ttab") === name);
    });
    panels.forEach(function (p) {
      p.classList.toggle("hidden", isOpen || p.getAttribute("data-ttp") !== name);
    });
  }

  /* ---------------- conversations ---------------- */

  function newConvo() {
    currentConvo = { id: "c" + Date.now(), title: "", messages: [] };
    conversations.unshift(currentConvo);
    saveConvos();
    refreshConvoList();
    $("#welcomeScreen").classList.remove("hidden");
    $("#chatMessages").innerHTML = "";
  }

  function selectConvo(id) {
    currentConvo = conversations.find(function (c) { return c.id === id; }) || null;
    renderConvo();
    refreshConvoList();
  }

  function deleteConvo(id) {
    conversations = conversations.filter(function (c) { return c.id !== id; });
    if (currentConvo && currentConvo.id === id) {
      currentConvo = null;
      $("#welcomeScreen").classList.remove("hidden");
      $("#chatMessages").innerHTML = "";
    }
    saveConvos();
    refreshConvoList();
  }

  function refreshConvoList() {
    var list = $("#conversationList");
    if (!list) return;
    list.innerHTML = "";
    conversations.slice(0, 30).forEach(function (c) {
      var btn = document.createElement("button");
      btn.className = "convo-item" + (currentConvo && currentConvo.id === c.id ? " is-active" : "");
      btn.type = "button";
      var name = document.createElement("span");
      name.className = "convo-name";
      name.textContent = c.title || "ORYN";
      btn.appendChild(name);
      var del = document.createElement("button");
      del.className = "convo-del";
      del.type = "button";
      del.title = t("chat.delete");
      del.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>';
      del.addEventListener("click", function (e) { e.stopPropagation(); deleteConvo(c.id); });
      btn.appendChild(del);
      btn.addEventListener("click", function () { selectConvo(c.id); });
      list.appendChild(btn);
    });
  }

  function renderConvo() {
    $("#chatMessages").innerHTML = "";
    if (currentConvo && currentConvo.messages.length) {
      $("#welcomeScreen").classList.add("hidden");
      currentConvo.messages.forEach(function (m) {
        renderMessage(m.role, m.content, m.images, true);
      });
    } else {
      if (currentConvo) $("#welcomeScreen").classList.remove("hidden");
    }
    scrollChat();
  }

  function renderMessage(role, content, images, fromHistory) {
    var wrap = $("#chatMessages");
    var msg = document.createElement("div");
    msg.className = "msg " + role;

    var meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = role === "user" ? t("chat.you") : t("chat.assistant");
    msg.appendChild(meta);

    var bubble = document.createElement("div");
    bubble.className = "bubble";

    if (images && images.length) {
      var att = document.createElement("div");
      att.className = "attachments";
      images.forEach(function (img) {
        var im = document.createElement("img");
        im.className = "attach-thumb";
        im.src = img;
        att.appendChild(im);
      });
      bubble.appendChild(att);
    }

    var body = document.createElement("div");
    body.className = "md-body" + (role === "user" ? " user-body" : "");
    body.innerHTML = role === "assistant" ? (md(content) || '<span class="empty-body">\u2026</span>') : esc(content);
    bubble.appendChild(body);

    // actions (only live messages)
    if (role === "assistant" && !fromHistory) {
      var acts = document.createElement("div");
      acts.className = "actions";
      acts.appendChild(actionBtn(t("chat.copy"), "M19 9l2 2v4a2 2 0 0 1-2 2h-4M3 7a2 2 0 0 1 2-2h4l2 2h4a2 2 0 0 1 2 2v4", function () {
        copyText(content);
      }));
      acts.appendChild(actionBtn(t("chat.regenerate"), "M21 12a9 9 0 1 1-2.64-6.36M21 3v6h-6", function () {
        regenerate();
      }));
      msg.appendChild(acts);
    }
    if (role === "user" && !fromHistory) {
      var acts2 = document.createElement("div");
      acts2.className = "actions";
      acts2.appendChild(actionBtn(t("chat.copy"), "M19 9l2 2v4a2 2 0 0 1-2 2h-4M3 7a2 2 0 0 1 2-2h4l2 2h4a2 2 0 0 1 2 2v4", function () {
        copyText(content);
      }));
      msg.appendChild(acts2);
    }

    msg.appendChild(bubble);
    wrap.appendChild(msg);
    return { msg: msg, body: body };
  }

  function actionBtn(label, icon, cb) {
    var b = document.createElement("button");
    b.type = "button";
    b.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="' + icon + '"/></svg><span>' + esc(label) + "</span>";
    b.addEventListener("click", cb);
    return b;
  }

  function copyText(text) {
    var done = function () { toast(t("chat.copied"), "ok"); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text, done); });
    } else { fallbackCopy(text, done); }
  }

  function fallbackCopy(text, done) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); done(); } catch (e) { }
    ta.remove();
  }

  function scrollChat() {
    var el = $("#chatMessages");
    if (el) el.scrollTop = el.scrollHeight;
  }

  /* ---------------- chat streaming ---------------- */

  function uiLanguageName() {
    var lang = (I18N.getLanguage && I18N.getLanguage()) || settings.lang;
    return (I18N.LANG_NAMES && I18N.LANG_NAMES[lang]) || lang;
  }

  function replyLanguageInstruction() {
    var name = uiLanguageName();
    return "You are ORYN, an AI assistant running 100% on the user's own computer. " +
      "RULE: ALWAYS write your ENTIRE reply in this language: " + name + ". " +
      "Never write in any other language, even if the user writes in another language or asks you to change.";
  }

  function buildMessages(prompt, images) {
    var msgs = (currentConvo ? currentConvo.messages : []).slice();
    if (!settings.memory) msgs = [];
    var recent = msgs.slice(-12);
    var content = prompt;
    var finalize = function () {
      recent.unshift({ role: "system", content: replyLanguageInstruction() });
      recent.push({ role: "user", content: content, images: images && images.length ? images : undefined });
      return recent;
    };
    if (searchOn) {
      return fetchSearchContext(prompt).then(function (ctx) {
        if (ctx) content = ctx + "\n\n---\n\n" + prompt;
        return finalize();
      });
    }
    return Promise.resolve(finalize());
  }

  function fetchSearchContext(prompt) {
    return api("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: prompt })
    }).then(function (data) {
      if (!data.results || !data.results.length) return "";
      var lines = data.results.slice(0, 5).map(function (r, i) {
        return (i + 1) + ". " + r.title + " — " + r.body + " (" + r.href + ")";
      });
      return "[Resultados da web]\n" + lines.join("\n");
    }).catch(function () { return ""; });
  }

  var searchOn = false;

  function gatherComposer() {
    var imgs = [];
    var texts = [];
    composerAttachments.forEach(function (a) {
      if (a.isImage) { imgs.push(a.dataUrl); return; }
      var b64 = (a.dataUrl || "").split(",")[1] || "";
      try {
        var bin = atob(b64);
        var bytes = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        var txt = new TextDecoder().decode(bytes).slice(0, 6000);
        if (txt) texts.push(a.name + ":\n" + txt);
      } catch (e) { /* ignora */ }
    });
    return { imgs: imgs, texts: texts };
  }

  function sendMessage(prompt, images, quiet) {
    if (chatting) return;
    prompt = (prompt != null ? prompt : "").trim();

    var comp = gatherComposer();
    if (images == null) images = comp.imgs.slice();
    if (!images.length && visionImage) images = [visionImage];
    var notes = comp.texts;
    if (notes.length) prompt = (notes.join("\n\n") + "\n\n" + prompt).trim();

    if (!prompt && !images.length) return;

    if (!currentConvo) newConvo();
    if (!currentConvo.title && prompt) {
      currentConvo.title = prompt.slice(0, 42);
      refreshConvoList();
    }

    if (!quiet) {
      currentConvo.messages.push({ role: "user", content: prompt, images: images.length ? images : undefined });
      saveConvos();
      refreshConvoList();
      $("#welcomeScreen").classList.add("hidden");
      renderMessage("user", prompt, images, false);
   }
    $("#promptInput").value = "";
    autoResize();
    clearAttachments();
    scrollChat();

    // assistant placeholder with typing dots
    var via = renderMessage("assistant", "\u2026", null, false);
    var body = via.body;
    body.innerHTML = '<span class="typing"><span></span><span></span><span></span></span>';
    scrollChat();

    chatting = true;
    var replyAcc = "";
    $("#sendBtn").classList.add("hidden");
    $("#stopBtn").classList.remove("hidden");

    abortCtl = typeof AbortController !== "undefined" ? new AbortController() : null;

    buildMessages(prompt, images).then(function (messages) {
      var payload = {
        model: settings.model || "oryn:14b",
        messages: messages,
        temperature: settings.temperature,
        context: settings.context
      };
      return fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: abortCtl ? abortCtl.signal : undefined
      });
    }).then(function (resp) {
      if (!resp.ok) {
        return resp.json().then(function (d) {
          throw new Error(d.error || t("errors.chat"));
        });
      }
      var reader = resp.body.getReader();
      var decoder = new TextDecoder();
      var acc = "";
      body.classList.remove("user-body");
      body.innerHTML = '<span class="cursor"></span>';

      function pump() {
        return reader.read().then(function (res) {
          if (res.done) {
            body.querySelector(".cursor").remove();
            finish(true, replyAcc);
            return;
          }
          var lines = decoder.decode(res.value, { stream: true }).split("\n");
          lines.forEach(function (line) {
            if (!line.trim()) return;
            var obj = null;
            try { obj = JSON.parse(line); } catch (e) { return; }
            if (obj.error) throwStreamError(obj.error);
            if (obj.message && obj.message.content) {
              acc += obj.message.content;
              replyAcc = acc;
              if (acc) body.innerHTML = md(acc) + '<span class="cursor"></span>';
              scrollChat();
            }
          });
          return pump();
        }).catch(function (err) {
          if (err.name === "AbortError") { finish(false); return; }
          throw err;
        });
      }

      function throwStreamError(msgText) {
        body.innerHTML = "";
        body.classList.add("error-bubble");
        body.textContent = msgText;
        finish(false);
      }

      return pump();
    }).catch(function (err) {
      var msgEl = body;
      msgEl.innerHTML = "";
      msgEl.classList.add("error-bubble");
      msgEl.textContent = err && err.message ? err.message : t("errors.chat");
      finish(false);
    });
  }

  function finish(ok, replyText) {
    chatting = false;
    $("#sendBtn").classList.remove("hidden");
    $("#stopBtn").classList.add("hidden");
    if (ok && replyText && currentConvo) {
      currentConvo.messages.push({ role: "assistant", content: replyText });
    }
    saveConvos();
    refreshConvoList();
    scrollChat();
  }

  function stopChat() {
    if (abortCtl) abortCtl.abort();
  }

  function regenerate() {
    if (!currentConvo || chatting) return;
    var msgs = currentConvo.messages;
    while (msgs.length && msgs[msgs.length - 1].role === "assistant") msgs.pop();
    saveConvos();
    $("#chatMessages").innerHTML = "";
    renderConvo();
    var lastUser = null;
    for (var i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].role === "user") { lastUser = msgs[i]; break; }
    }
    if (!lastUser) { renderConvo(); return; }
    sendMessage(lastUser.content || "", lastUser.images || [], true);
  }

  /* ---------------- composer ---------------- */

  function autoResize() {
    var ta = $("#promptInput");
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  }

  function clearAttachments() {
    composerAttachments = [];
    $("#attachPreviewRow").innerHTML = "";
    $("#attachPreviewRow").classList.add("hidden");
  }

  function addAttachment(item) {
    composerAttachments.push(item);
    var row = $("#attachPreviewRow");
    row.classList.remove("hidden");
    var pill = document.createElement("div");
    pill.className = "preview-pill";
    if (item.isImage) {
      var im = document.createElement("img");
      im.src = item.dataUrl;
      pill.appendChild(im);
    }
    var name = document.createElement("span");
    name.textContent = item.name;
    pill.appendChild(name);
    var x = document.createElement("button");
    x.className = "x";
    x.type = "button";
    x.textContent = "\u00d7";
    x.addEventListener("click", function () {
      composerAttachments = composerAttachments.filter(function (a) { return a !== item; });
      pill.remove();
      if (!composerAttachments.length) row.classList.add("hidden");
    });
    pill.appendChild(x);
    row.appendChild(pill);
  }

  function handleAttachFiles(fileList) {
    var files = Array.prototype.slice.call(fileList || []);
    files.slice(0, 6).forEach(function (file) {
      if (file.size > 8 * 1024 * 1024) return;
      readFileAsDataURL(file).then(function (url) {
        var isImage = /^image\//.test(file.type);
        addAttachment({ name: file.name, dataUrl: url, isImage: isImage, type: file.type, file: file });
      });
    });
  }

  /* ---------------- vision ---------------- */

  function setVisionImage(url) {
    visionImage = url;
    $("#visionPreview").src = url;
    $("#visionPreviewBox").classList.remove("hidden");
    $("#visionAnswer").classList.add("hidden");
  }

  function askVision() {
    var q = $("#visionAskInput").value.trim();
    if (!visionImage) return;
    if (!q) { toast(t("gen.needPrompt"), "warn"); return; }
    $("#visionAskBtn").disabled = true;
    $("#visionAskBtn").textContent = t("vision.analyzing");
    var box = $("#visionAnswer");
    box.classList.remove("hidden");
    box.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';

    buildMessages(q, [visionImage]).then(function (messages) {
      return fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: settings.visionModel || settings.model || "oryn:14b",
          messages: messages,
          temperature: settings.temperature,
          context: settings.context
        })
      });
    }).then(function (resp) {
      return resp.text();
    }).then(function (raw) {
      var acc = "";
      raw.split("\n").forEach(function (line) {
        if (!line.trim()) return;
        var obj = null;
        try { obj = JSON.parse(line); } catch (e) { return; }
        if (obj.message && obj.message.content) acc += obj.message.content;
        if (obj.error) acc = obj.error;
      });
      box.innerHTML = acc ? md(acc) : "<p>\u2026</p>";
    }).catch(function (err) {
      box.classList.add("error-bubble");
      box.textContent = err && err.message ? err.message : t("errors.chat");
    }).finally(function () {
      $("#visionAskBtn").disabled = false;
      $("#visionAskBtn").textContent = t("vision.analyze");
    });
  }

  /* ---------------- image generation ---------------- */

  function aspectSize(ar, base) {
    base = base || 1024;
    var map = { "1:1": [1024, 1024], "16:9": [1344, 768], "9:16": [768, 1344], "4:3": [1152, 864], "3:4": [864, 1152], "21:9": [1408, 608] };
    var size = map[ar] || [1024, 1024];
    return { width: size[0], height: size[1] };
  }

  function generateImage() {
    var prompt = $("#imgPrompt").value.trim();
    if (!prompt) { toast(t("gen.needPrompt"), "warn"); return; }
    var size = aspectSize($("#imgAR").value, 1024);
    var seed = parseInt($("#imgSeed").value, 10) || 0;
    var batch = parseInt($("#imgBatch").value, 10) || 1;
    var status = $("#imgStatus");
    status.className = "gen-status working";
    status.textContent = t("images.loading");
    $("#imgGenerateBtn").disabled = true;

    api("/api/generate/image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: prompt,
        width: size.width,
        height: size.height,
        seed: seed,
        batch: batch
      })
    }).then(function (data) {
      clearEmpty("#imgGrid");
      for (var i = 0; i < batch; i++) {
        var tile = loadingTile(data.promptId + ":" + i);
        $("#imgGrid").appendChild(tile);
      }
      jobs[data.promptId] = { el: $("#imgGrid"), label: t("images.loading"), type: "image" };
      startPolling(data.promptId, "image");
      status.className = "gen-status";
      status.textContent = t("gen.submitted") + " \u00b7 " + t("gen.taskId") + " " + data.promptId.slice(0, 8);
    }).catch(function (err) {
      status.className = "gen-status error";
      status.textContent = err && err.message ? err.message : t("gen.serverDown");
      toast(t("gen.serverDown"), "err");
    }).finally(function () {
      $("#imgGenerateBtn").disabled = false;
    });
  }

  function loadingTile(id) {
    var tile = document.createElement("div");
    tile.className = "loading-tile";
    tile.dataset.tile = id;
    tile.innerHTML = '<div class="spinner"></div><div class="progress-state"><span></span><span></span></div>';
    return tile;
  }

  function clearEmpty(gridSel) {
    var grid = $(gridSel);
    Array.prototype.slice.call(grid.querySelectorAll(".empty-state")).forEach(function (e) { e.remove(); });
  }

  /* ---------------- video generation ---------------- */

  function videoParams() {
    return {
      prompt: $("#vidPrompt").value.trim(),
      model: $("#vidModel").value,
      duration: parseInt($("#vidDuration").value, 10) || 5,
      fps: parseInt($("#vidFps").value, 10) || 24
    };
  }

  function generateVideo() {
    var p = videoParams();
    if (!p.prompt && !vidAnimImage) { toast(t("gen.needPrompt"), "warn"); return; }
    var isI2V = vidAnimImage != null;
    if (isI2V) p.model = "wan_5b";

    var status = $("#vidStatus");
    status.className = "gen-status working";
    status.textContent = isI2V ? t("gen.animating") : t("videos.loading");
    $("#vidGenerateBtn").disabled = true;

    var prep;
    if (isI2V) {
      if (vidAnimImage.filename) {
        // comfy reference image
        prep = Promise.resolve({ startImage: { filename: vidAnimImage.filename, subfolder: vidAnimImage.subfolder || "", type: vidAnimImage.type || "output" } });
      } else if (vidAnimImage.dataUrl) {
        // user image -> upload to comfy input first
        prep = fetch(vidAnimImage.dataUrl).then(function (r) { return r.blob(); }).then(function (blob) {
          var fd = new FormData();
          fd.append("files", blob, "upload.png");
          return api("/api/upload/comfyui", { method: "POST", body: fd });
        }).then(function (d) {
          var up = d.files && d.files[0];
          if (!up || !up.name) throw new Error("Falha no upload da imagem.");
          return { startImage: { filename: up.name, subfolder: up.subfolder || "", type: "input" } };
        });
      } else {
        prep = Promise.resolve({});
      }
    } else {
      prep = Promise.resolve({});
    }

    prep.then(function (extra) {
      return api("/api/generate/video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.assign({}, p, extra))
      });
    }).then(function (data) {
      clearEmpty("#vidGrid");
      var tile = loadingTile(data.promptId);
      $("#vidGrid").appendChild(tile);
      jobs[data.promptId] = { el: $("#vidGrid"), label: t("videos.loading"), type: "video" };
      startPolling(data.promptId, "video");
      status.className = "gen-status";
      status.textContent = t("gen.submitted") + " \u00b7 " + t("gen.taskId") + " " + data.promptId.slice(0, 8);
    }).catch(function (err) {
      status.className = "gen-status error";
      status.textContent = err && err.message ? err.message : t("gen.serverDown");
      toast(err && err.message ? err.message : t("gen.serverDown"), "err");
    }).finally(function () {
      $("#vidGenerateBtn").disabled = false;
    });
  }

  /* ---------------- generation polling ---------------- */

  function startPolling(promptId, kind) {
    setTimeout(pollJob, 1500, promptId, kind);
  }

  function pollJob(promptId, kind) {
    api("/api/generate/status/" + encodeURIComponent(promptId))
      .then(function (data) {
        var job = jobs[promptId];
        var grid = job ? job.el : null;
        if (!grid) return;
        var tiles = Array.prototype.slice.call(grid.querySelectorAll('[data-tile^="' + promptId + '"]'));
        if (data.state === "queued" || data.state === "running") {
          tiles.forEach(function (tile) {
            var spans = tile.querySelectorAll(".progress-state span");
            if (spans[0]) spans[0].textContent = data.state === "queued" ? t("videos.queued") : t("videos.processing");
            if (spans[1]) spans[1].textContent = "\u25cf";
          });
          setTimeout(pollJob, 2000, promptId, kind);
        } else if (data.state === "complete") {
          var list = data.files || [];
          if (!list.length) {
            tiles.forEach(function (tile) { tile.remove(); });
            showError(grid, t("gen.noFile"));
            return;
          }
          tiles.forEach(function (tile) { tile.remove(); });
          list.forEach(function (f) {
            grid.appendChild(kind === "image" ? mediaImageCard(f, promptId) : mediaVideoCard(f, promptId));
          });
        } else if (data.state === "error") {
          tiles.forEach(function (tile) { tile.remove(); });
          showError(grid, data.error || t("gen.serverDown"));
        }
      })
      .catch(function () {
        var job = jobs[promptId];
        if (job) {
          var tiles = Array.prototype.slice.call(job.el.querySelectorAll('[data-tile^="' + promptId + '"]'));
          tiles.forEach(function (tile) { tile.remove(); });
          showError(job.el, t("gen.serverDown"));
        }
      });
  }

  function showError(grid, msgText) {
    var box = document.createElement("div");
    box.className = "empty-state";
    var title = document.createElement("div");
    title.className = "empty-title";
    title.textContent = t("gen.errorTitle");
    var sub = document.createElement("div");
    sub.className = "empty-sub";
    sub.textContent = msgText;
    box.appendChild(title);
    box.appendChild(sub);
    grid.appendChild(box);
  }

  function mediaImageCard(f, promptId) {
    var card = document.createElement("div");
    card.className = "media-card";
    card.dataset.tile = promptId;
    var img = document.createElement("img");
    img.src = mediaUrl(f);
    img.alt = f.filename;
    img.loading = "lazy";
    var tools = document.createElement("div");
    tools.className = "media-tools";

    var dl = document.createElement("button");
    dl.type = "button";
    dl.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/></svg><span>' + esc(t("images.download")) + "</span>";
    dl.addEventListener("click", function () { downloadFile(mediaUrl(f)); });
    tools.appendChild(dl);

    var anim = document.createElement("button");
    anim.type = "button";
    anim.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="3"/><path d="m10 9 5 3-5 3Z"/></svg><span>' + esc(t("images.animate")) + "</span>";
    anim.addEventListener("click", function () {
      vidAnimImage = { filename: f.filename, subfolder: f.subfolder || "", type: f.type || "output" };
      switchView("videos");
      $("#vidModeSeg .seg-btn[data-vidmode='i2v']").click();
      $("#vidPrompt").focus();
    });
    tools.appendChild(anim);

    var reseed = document.createElement("button");
    reseed.type = "button";
    reseed.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.64-6.36M21 3v6h-6"/></svg><span>' + esc(t("images.regenerate")) + "</span>";
    reseed.addEventListener("click", function () {
      var p = $("#imgPrompt").value.trim();
      if (p) generateImage();
    });
    tools.appendChild(reseed);

    card.appendChild(img);
    card.appendChild(tools);
    return card;
  }

  function downloadFile(url) {
    var name = "";
    try { name = decodeURIComponent(url.split("filename=")[1] || "").split("&")[0]; } catch (e) { }
    var a = document.createElement("a");
    a.href = url;
    a.download = name || "oryn_media";
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { document.body.removeChild(a); }, 50);
  }

  function mediaVideoCard(f, promptId) {
    var card = document.createElement("div");
    card.className = "media-card";
    card.dataset.tile = promptId;
    var v = document.createElement("video");
    v.src = mediaUrl(f);
    v.controls = true;
    v.loop = true;
    v.muted = true;
    v.playsInline = true;
    v.onloadedmetadata = function () { v.currentTime = 0.1; };
    var tools = document.createElement("div");
    tools.className = "media-tools";
    var dl = document.createElement("button");
    dl.type = "button";
    dl.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/></svg><span>' + esc(t("images.download")) + "</span>";
    dl.addEventListener("click", function () { downloadFile(mediaUrl(f)); });
    tools.appendChild(dl);
    card.appendChild(v);
    card.appendChild(tools);
    return card;
  }

  /* ---------------- video animate mode ---------------- */

  function setVidMode(mode) {
    $$("#vidModeSeg .seg-btn").forEach(function (b) {
      b.classList.toggle("is-active", b.getAttribute("data-vidmode") === mode);
    });
    $("#vidImgBox").classList.toggle("hidden", mode !== "i2v");
    $("#vidModel").disabled = mode === "i2v";
    if (mode === "i2v") {
      $("#vidModel").value = "wan_5b";
      if (!$("#vidPrompt").value.trim()) $("#vidPrompt").value = "Smooth subtle camera movement, cinematic lighting";
    }
  }

  /* ---------------- search ---------------- */

  function runSearch(query) {
    query = (query || $("#searchInput").value).trim();
    if (!query) return;
    var out = $("#searchResults");
    var extra = $("#searchExtra");
    out.innerHTML = '<div class="empty-state"><div class="spinner"></div><div class="empty-title">' + esc(t("search.searching")) + "</div></div>";
    $("#searchBtn").disabled = true;

    api("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query })
    }).then(function (data) {
      $("#searchBtn").disabled = false;
      if (!data.results || !data.results.length) {
        out.innerHTML = '<div class="empty-state"><div class="empty-title">' + esc(t("search.emptyTitle")) + '</div><div class="empty-sub">' + esc(t("search.emptySub")) + "</div></div>";
        return;
      }
      extra.classList.remove("hidden");
      extra.innerHTML = "<strong>" + esc(t("search.resultsFor")) + "</strong> \u201c" + esc(query) + "\u201d";
      out.innerHTML = "";
      data.results.forEach(function (r) {
        var card = document.createElement("div");
        card.className = "sr-card";
        var title = document.createElement("h3");
        var a = document.createElement("a");
        a.href = r.href;
        a.target = "_blank";
        a.rel = "noopener";
        a.textContent = r.title || r.href;
        title.appendChild(a);
        var src = document.createElement("div");
        src.className = "sr-src";
        src.textContent = r.href || "";
        var desc = document.createElement("div");
        desc.className = "sr-desc";
        desc.textContent = r.body || "";
        var acts = document.createElement("div");
        acts.className = "sr-actions";
        var use = document.createElement("button");
        use.className = "btn btn-sm";
        use.type = "button";
        use.textContent = t("search.useInChat");
        use.addEventListener("click", function () {
          switchView("chat");
          $("#promptInput").value = r.title + "\n" + (r.body || "");
          autoResize();
          $("#promptInput").focus();
        });
        acts.appendChild(use);
        card.appendChild(title);
        card.appendChild(src);
        card.appendChild(desc);
        card.appendChild(acts);
        out.appendChild(card);
      });
    }).catch(function (err) {
      $("#searchBtn").disabled = false;
      out.innerHTML = '<div class="empty-state"><div class="empty-title">' + esc(t("gen.errorTitle")) + '</div><div class="empty-sub">' + esc((err && err.message) || t("gen.serverDown")) + "</div></div>";
    });
  }

  /* ---------------- files ---------------- */

  function handleFiles(files) {
    Array.prototype.slice.call(files).slice(0, 12).forEach(function (file) {
      var item = document.createElement("div");
      item.className = "f-item";
      var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("width", "20"); svg.setAttribute("height", "20");
      svg.setAttribute("viewBox", "0 0 24 24");
      svg.setAttribute("fill", "none"); svg.setAttribute("stroke", "currentColor");
      svg.setAttribute("stroke-width", "2"); svg.setAttribute("stroke-linecap", "round"); svg.setAttribute("stroke-linejoin", "round");
      svg.innerHTML = '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/>';
      var meta = document.createElement("div");
      meta.className = "f-meta";
      var name = document.createElement("div");
      name.className = "f-name";
      name.textContent = file.name;
      var size = document.createElement("div");
      size.className = "f-size";
      size.textContent = fmtBytes(file.size);
      meta.appendChild(name);
      meta.appendChild(size);
      item.appendChild(svg);
      item.appendChild(meta);
      item.addEventListener("click", function () { previewFile(file); });
      $("#fileList").appendChild(item);
    });
  }

  function previewFile(file) {
    if (file.size > 6 * 1024 * 1024) { toast(file.name + " > 6MB \u2014 preview limitado a textos.", "warn"); return; }
    readFileAsDataURL(file).then(function (dataUrl) {
      return api("/api/files/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: file.name, dataUrl: dataUrl, type: file.type })
      });
    }).then(function (data) {
      var panel = $("#filePreviewPanel");
      panel.classList.remove("hidden");
      $("#filePreviewName").textContent = file.name;
      var bodyEl = $("#filePreviewContent");
      bodyEl.innerHTML = "";
      if (data.kind === "image") {
        var im = document.createElement("img");
        im.src = data.preview;
        bodyEl.appendChild(im);
      } else if (data.kind === "markdown") {
        bodyEl.innerHTML = '<div class="md-body">' + data.preview + "</div>";
      } else if (data.kind === "text") {
        var pre = document.createElement("pre");
        pre.textContent = data.preview;
        bodyEl.appendChild(pre);
      } else {
        bodyEl.innerHTML = '<div class="empty-state"><div class="empty-sub">' + esc(t("vision.statusMissing")) + "</div></div>";
      }
    }).catch(function (err) {
      toast((err && err.message) || "Erro no preview.", "err");
    });
  }

  function bindDrop(el, handler) {
    ["dragenter", "dragover"].forEach(function (ev) {
      el.addEventListener(ev, function (e) {
        e.preventDefault();
        el.classList.add("drag");
      });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      el.addEventListener(ev, function (e) {
        e.preventDefault();
        el.classList.remove("drag");
      });
    });
    el.addEventListener("drop", function (e) {
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
        handler(e.dataTransfer.files);
      }
    });
  }

  /* ---------------- settings ---------------- */

  function refreshSettingsUi() {
    var langSel = $("#setLang");
    if (langSel) {
      langSel.innerHTML = "";
      Object.keys(I18N.LANG_NAMES).forEach(function (code) {
        var o = document.createElement("option");
        o.value = code;
        o.textContent = I18N.LANG_NAMES[code];
        if (code === settings.lang) o.selected = true;
        langSel.appendChild(o);
      });
    }
    var th = $("#setTheme");
    if (th) {
      th.innerHTML = "";
      ["dark", "light", "purple", "blue", "green", "yellow", "black", "white", "custom"].forEach(function (k) {
        var o = document.createElement("option");
        o.value = k;
        o.textContent = t("settings.theme" + k.charAt(0).toUpperCase() + k.slice(1));
        if (k === settings.theme) o.selected = true;
        th.appendChild(o);
      });
    }
    if (settings.custom) {
      $("#custPrimary").value = settings.custom.primary || "#7c5cff";
      $("#custBg").value = settings.custom.bg || "#0b0b0f";
      $("#custCards").value = settings.custom.cards || "#17171f";
      $("#custText").value = settings.custom.text || "#eceaf2";
    }
    $("#setAnimations").checked = !!settings.animations;
    $("#setMemory").checked = !!settings.memory;
    $("#setTemp").value = settings.temperature;
    $("#setTempVal").textContent = settings.temperature;
    $("#setContext").value = String(settings.context);
    $("#setOllama").value = settings.ollamaUrl || "";
    $("#setComfy").value = settings.comfyuiUrl || "";
    $("#setComfyRoot").value = settings.comfyRoot || "";
    $("#setRemoteUrl").value = settings.remoteUrl || "";
    if ($("#setModel").options.length === 0) {
      // model options populated from server status
    }
    $("#setImageDefault").value = settings.imageDefault || "";
    $("#setVideoDefault").value = settings.videoDefault || "";
  }

  function populateModelSelects(models, serverCfg) {
    var mSel = $("#setModel");
    mSel.innerHTML = "";
    var list = (models && models.length) ? models : (serverCfg && serverCfg.models) || [];
    var chatList = list.filter(function (n) {
      var b = String(n).toLowerCase();
      return b.indexOf("oryn") !== -1 || b.indexOf("coder") !== -1;
    });
    var opted = settings.model;
    if (!opted || chatList.indexOf(opted) === -1) opted = chatList[0] || "oryn:14b";
    chatList.forEach(function (name) {
      var o = document.createElement("option");
      o.value = name;
      o.textContent = name;
      if (name === opted) o.selected = true;
      mSel.appendChild(o);
    });
    if (!chatList.length) {
      var o = document.createElement("option");
      o.value = "oryn:14b";
      o.textContent = "oryn:14b";
      mSel.appendChild(o);
    }

    var vSel = $("#setVisionModel");
    vSel.innerHTML = "";
    var vmodels = list.filter(function (n) {
      var b = n.toLowerCase().split(":", 1)[0];
      return b.indexOf("llava") === 0 || b.indexOf("gemma3") === 0 || n.toLowerCase().indexOf("vision") !== -1 || n.toLowerCase().indexOf("vl") !== -1;
    });
    var vlist = vmodels.length ? vmodels : list;
    var optedVision = settings.visionModel;
    if (!optedVision && vmodels.length) optedVision = vmodels[0];
    if (optedVision && vlist.indexOf(optedVision) === -1) optedVision = "";
    var vo = document.createElement("option");
    vo.value = "";
    vo.textContent = "\u2014";
    vSel.appendChild(vo);
    vlist.forEach(function (name) {
      var o = document.createElement("option");
      o.value = name;
      o.textContent = name;
      if (name === optedVision) o.selected = true;
      vSel.appendChild(o);
    });
    settings.visionModel = optedVision;

    [{ sel: $("#setImageDefault"), val: settings.imageDefault, opts: ["kontext_flux_2_klein", "flux-schnell", "flux-dev"] },
     { sel: $("#setVideoDefault"), val: settings.videoDefault, opts: ["wan_5b", "wan_14b"] }].forEach(function (row) {
      if (!row.sel) return;
      row.sel.innerHTML = "";
      row.opts.forEach(function (name) {
        var o = document.createElement("option");
        o.value = name;
        o.textContent = name;
        if (name === row.val) o.selected = true;
        row.sel.appendChild(o);
      });
    });
  }

  function refreshStatus() {
    api("/api/status").then(function (st) {
      populateModelSelects(st.models, st);
      var pill = $("#sysPill");
      var dot = $("#sysDot");
      if (st.comfyui && st.ollama) {
        pill.title = t("status.backend") + " \u00b7 " + t("status.online");
        dot.className = "sys-dot ok";
      } else if (!st.comfyui && !st.ollama) {
        pill.title = t("status.ollama") + " / " + t("status.comfyui") + " \u00b7 " + t("status.offline");
        dot.className = "sys-dot bad";
      } else {
        dot.className = "sys-dot bad";
      }
      if (st.disk_free_gb !== null && st.disk_free_gb !== undefined) {
        pill.title += " \u00b7 " + t("status.disk") + ": " + st.disk_free_gb + " GB";
      }

      // gauges
      var gauges = [
        { k: "backend", label: t("status.backend"), ok: !!st.backend },
        { k: "ollama", label: t("status.ollama"), ok: !!st.ollama },
        { k: "comfyui", label: t("status.comfyui"), ok: !!st.comfyui },
        { k: "flux", label: t("status.flux"), ok: !!st.flux_klein },
        { k: "wan5", label: t("status.wan5"), ok: !!st.wan_5b },
        { k: "wan14", label: t("status.wan14"), ok: !!st.wan_14b }
      ];
      var g = $("#modelGauges");
      g.innerHTML = "";
      gauges.forEach(function (row) {
        var el = document.createElement("div");
        el.className = "mg-row" + (row.ok ? " ok" : " bad");
        var top = document.createElement("div");
        top.className = "mg-top";
        var l = document.createElement("span");
        l.className = "mg-label";
        l.textContent = row.label;
        var s = document.createElement("span");
        s.className = "mg-state";
        s.textContent = row.ok ? t("status.ready") : t("status.missing");
        top.appendChild(l);
        top.appendChild(s);
        var bar = document.createElement("div");
        bar.className = "mg-bar";
        var fill = document.createElement("div");
        fill.className = "mg-fill";
        fill.style.width = row.ok ? "100%" : "10%";
        bar.appendChild(fill);
        el.appendChild(top);
        el.appendChild(bar);
        g.appendChild(el);
      });

      // vision status
      var vs = $("#visionStatus");
      if (vs) {
        vs.className = "vis-state " + (st.vision ? "ok" : "bad");
        vs.innerHTML = '<span class="dot"></span>' + esc(st.vision ? t("vision.statusReady") : t("vision.statusMissing"));
      }
    }).catch(function () {
      var dot = $("#sysDot");
      if (dot) { dot.className = "sys-dot bad"; }
    });
    return Promise.resolve();
  }

  function refreshModelsList() {
    api("/api/config").then(function (cfg) {
      var list = $("#modelsList");
      list.innerHTML = "";
      var files = cfg.model_files || {};
      Object.keys(files).forEach(function (k) {
        var el = document.createElement("span");
        el.className = "m-item " + (files[k] ? "yes" : "no");
        el.textContent = k + (files[k] ? " \u2713" : " \u2717");
        el.title = files[k] || "missing";
        list.appendChild(el);
      });
    }).catch(function () { });
  }

  function saveAllSettings() {
    settings.lang = $("#setLang").value;
    settings.theme = $("#setTheme").value;
    settings.animations = $("#setAnimations").checked;
    settings.memory = $("#setMemory").checked;
    settings.temperature = parseFloat($("#setTemp").value) || 0.7;
    settings.context = parseInt($("#setContext").value, 10) || 8192;
    settings.model = $("#setModel").value;
    settings.visionModel = $("#setVisionModel").value;
    settings.ollamaUrl = $("#setOllama").value.trim() || "http://127.0.0.1:11434";
    settings.comfyuiUrl = $("#setComfy").value.trim() || "http://127.0.0.1:8188";
    settings.comfyRoot = $("#setComfyRoot").value.trim();
    settings.remoteUrl = $("#setRemoteUrl").value.trim();
    settings.imageDefault = $("#setImageDefault").value;
    settings.videoDefault = $("#setVideoDefault").value;
    settings.custom = {
      primary: $("#custPrimary").value,
      bg: $("#custBg").value,
      cards: $("#custCards").value,
      text: $("#custText").value
    };
    saveSettings();
    applyLang();
    applyTheme();

    var status = $("#setStatus");
    status.className = "gen-status working";
    status.textContent = "\u2026";
    api("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ollamaUrl: settings.ollamaUrl, comfyuiUrl: settings.comfyuiUrl })
    }).then(function () {
      status.className = "gen-status ok";
      status.textContent = t("settings.saved");
      setTimeout(function () { status.textContent = ""; }, 3000);
      refreshStatus();
    }).catch(function (err) {
      status.className = "gen-status error";
      status.textContent = (err && err.message) || t("gen.serverDown");
    });
  }

  /* ---------------- init ---------------- */

  function init() {
    applyLang();
    applyTheme();

    // nav
    $$("#mainNav .nav-item").forEach(function (b) {
      b.addEventListener("click", function () { switchView(b.getAttribute("data-view")); });
    });
    $$(".chat-tools .ct-tab").forEach(function (b) {
      b.addEventListener("click", function () { selectChatTool(b.getAttribute("data-ttab")); });
    });
    $("#newChatBtn").addEventListener("click", newConvo);
    $("#menuToggle").addEventListener("click", function () { $("#sidebar").classList.toggle("open"); });
    $("#themeToggleBtn").addEventListener("click", function () {
      var order = ["dark", "light", "purple", "blue", "green", "yellow", "black", "white"];
      var idx = order.indexOf(settings.theme);
      settings.theme = order[(idx + 1) % order.length];
      saveSettings();
      applyTheme();
      var th = $("#setTheme");
      if (th) th.value = settings.theme;
    });

    // composer
    $("#sendBtn").addEventListener("click", function () { sendMessage($("#promptInput").value, null); });
    $("#stopBtn").addEventListener("click", stopChat);
    $("#promptInput").addEventListener("input", autoResize);
    $("#promptInput").addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage($("#promptInput").value, null);
      }
    });
    $("#attachBtn").addEventListener("click", function () { $("#attachInput").click(); });
    $("#attachInput").addEventListener("change", function (e) { handleAttachFiles(e.target.files); e.target.value = ""; });
    $("#searchToggleBtn").addEventListener("click", function () {
      searchOn = !searchOn;
      $("#searchToggleBtn").classList.toggle("on", searchOn);
    });
    $$(".sugg .chip").forEach(function (c) {
      c.addEventListener("click", function () { switchView("chat"); sendMessage(c.textContent.trim(), null); });
    });

    // vision
    $("#visionDrop").addEventListener("click", function () { $("#visionImgInput").click(); });
    $("#visionPickBtn").addEventListener("click", function (e) { e.stopPropagation(); $("#visionImgInput").click(); });
    $("#visionImgInput").addEventListener("change", function (e) {
      var f = e.target.files && e.target.files[0];
      if (f) readFileAsDataURL(f).then(setVisionImage);
      e.target.value = "";
    });
    bindDrop($("#visionDrop"), function (files) {
      if (files[0]) readFileAsDataURL(files[0]).then(setVisionImage);
    });
    $("#visionAskBtn").addEventListener("click", askVision);
    $("#visionAskInput").addEventListener("keydown", function (e) { if (e.key === "Enter") askVision(); });

    // images
    $("#imgGenerateBtn").addEventListener("click", generateImage);
    $("#imgSeedRand").addEventListener("click", function () { $("#imgSeed").value = Math.floor(Math.random() * 0xffffffff); });
    $("#imgPrompt").addEventListener("keydown", function (e) { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) generateImage(); });

    // videos
    $("#vidGenerateBtn").addEventListener("click", generateVideo);
    $("#vidModeSeg").addEventListener("click", function (e) {
      var btn = e.target.closest(".seg-btn");
      if (btn) setVidMode(btn.getAttribute("data-vidmode"));
    });
    $("#vidImgDrop").addEventListener("click", function () { $("#vidImgInput").click(); });
    $("#vidImgPickBtn").addEventListener("click", function (e) { e.stopPropagation(); $("#vidImgInput").click(); });
    $("#vidImgInput").addEventListener("change", function (e) {
      var f = e.target.files && e.target.files[0];
      if (f) {
        readFileAsDataURL(f).then(function (url) {
          vidAnimImage = { dataUrl: url };
          $("#vidImgPreview").src = url;
          $("#vidImgPreview").classList.remove("hidden");
          $("#vidImgDrop").classList.add("hidden");
        });
      }
      e.target.value = "";
    });
    bindDrop($("#vidImgDrop"), function (files) {
      if (files[0]) {
        readFileAsDataURL(files[0]).then(function (url) {
          vidAnimImage = { dataUrl: url };
          $("#vidImgPreview").src = url;
          $("#vidImgPreview").classList.remove("hidden");
          $("#vidImgDrop").classList.add("hidden");
        });
      }
    });

    // search
    $("#searchBtn").addEventListener("click", function () { runSearch(); });
    $("#searchInput").addEventListener("keydown", function (e) { if (e.key === "Enter") runSearch(); });

    // files
    $("#filesDrop").addEventListener("click", function () { $("#filesInput").click(); });
    $("#filesPickBtn").addEventListener("click", function (e) { e.stopPropagation(); $("#filesInput").click(); });
    $("#filesInput").addEventListener("change", function (e) { handleFiles(e.target.files); e.target.value = ""; });
    bindDrop($("#filesDrop"), handleFiles);

    // settings
    $("#saveSettingsBtn").addEventListener("click", saveAllSettings);
    $("#setLang").addEventListener("change", function () {
      settings.lang = this.value;
      saveSettings();
      applyLang();
    });
    $("#setTheme").addEventListener("change", function () {
      settings.theme = this.value;
      saveSettings();
      applyTheme();
    });
    $("#setAnimations").addEventListener("change", function () {
      settings.animations = this.checked;
      saveSettings();
      applyTheme();
    });
    ["custPrimary", "custBg", "custCards", "custText"].forEach(function (id) {
      $("#" + id).addEventListener("input", function () {
        settings.theme = "custom";
        settings.custom = settings.custom || {};
        settings.custom[id.replace("cust", "").toLowerCase()] = this.value;
        saveSettings();
        applyTheme();
        var th = $("#setTheme");
        if (th) th.value = "custom";
      });
    });
    $("#resetThemeBtn").addEventListener("click", function () {
      settings.custom = JSON.parse(JSON.stringify(DEFAULT_SETTINGS.custom));
      if (settings.theme === "custom") settings.theme = "dark";
      saveSettings();
      applyTheme();
      refreshSettingsUi();
    });
    $("#setTemp").addEventListener("input", function () { $("#setTempVal").textContent = this.value; });
    $("#refreshModelsBtn").addEventListener("click", function () { refreshModelsList(); toast(t("status.checking"), "ok"); });

    // bootstrap config from server
    api("/api/config").then(function (cfg) {
      if (cfg.ollamaUrl) settings.ollamaUrl = cfg.ollamaUrl;
      if (cfg.comfyuiUrl) settings.comfyuiUrl = cfg.comfyuiUrl;
      saveSettings();
      refreshSettingsUi();
    }).catch(function () { refreshSettingsUi(); });

    refreshStatus();
    refreshModelsList();
    setInterval(function () { refreshStatus(); }, 45000);

    // animate shortcut from search entries etc.
    switchView("chat");
  }

  document.addEventListener("DOMContentLoaded", init);

  window.ORYN = {
    t: t, md: md, generateVideo: generateVideo, generateImage: generateImage,
    sendMessage: sendMessage, switchView: switchView,
    mediaImageCard: mediaImageCard, mediaVideoCard: mediaVideoCard, downloadFile: downloadFile
  };
})();