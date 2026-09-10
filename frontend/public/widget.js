/**
 * EmbedIQ Widget Loader — widget.js
 * Standalone vanilla JS, no dependencies, Shadow DOM style isolation.
 * < 15 KB uncompressed. Reads data-bot-id from its own <script> tag.
 *
 * postMessage Protocol:
 *   Host → Iframe: PARENT_RESIZE, THEME_UPDATE
 *   Iframe → Host: WIDGET_TOGGLE_OPEN, WIDGET_TOGGLE_CLOSE, WIDGET_UNREAD_COUNT
 */
(function () {
  'use strict';

  /* ── 1. Locate own script tag ──────────────────────────────────────────── */
  var sc = document.currentScript;
  if (!sc) return; // deferred execution guard

  var botId   = sc.getAttribute('data-bot-id');
  var apiUrl  = sc.getAttribute('data-api-url')  || 'http://localhost:8000';
  var baseUrl = sc.getAttribute('data-base-url') || (window.location.origin);
  var pos     = sc.getAttribute('data-position')  || 'bottom-right'; // bottom-right | bottom-left

  if (!botId) { console.warn('[EmbedIQ] data-bot-id is required.'); return; }

  /* ── 2. State ──────────────────────────────────────────────────────────── */
  var isOpen   = false;
  var cfg      = null;   // branding config
  var ifr      = null;   // iframe element
  var panel    = null;   // panel wrapper
  var badge    = null;   // unread badge
  var unread   = 0;
  var isMobile = function () { return window.innerWidth < 640; };

  /* ── 3. Fetch branding config ──────────────────────────────────────────── */
  function fetchConfig(cb) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', apiUrl + '/api/widget/config/' + botId, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4) return;
      if (xhr.status === 200) {
        try { cfg = JSON.parse(xhr.responseText); } catch (e) { cfg = {}; }
      } else {
        cfg = {};
      }
      cb();
    };
    xhr.send();
  }

  /* ── 4. Derive theme values ────────────────────────────────────────────── */
  function primaryColor()  { return (cfg && cfg.theme && cfg.theme.primary_color) || '#2563EB'; }
  function widgetPosition(){ return (cfg && cfg.theme && cfg.theme.position) || pos; }
  function iframeOrigin() {
    try {
      return new URL(baseUrl, window.location.href).origin;
    } catch (e) {
      return window.location.origin;
    }
  }

  function iframeUrl() {
    return baseUrl + '/widget/chat?bot_id=' + encodeURIComponent(botId)
      + '&api_url=' + encodeURIComponent(apiUrl)
      + '&parent_origin=' + encodeURIComponent(window.location.origin);
  }

  /* ── 5. SVG icons ──────────────────────────────────────────────────────── */
  var ICON_CHAT  = '<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';
  var ICON_CLOSE = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';

  /* ── 6. Build Shadow DOM host ──────────────────────────────────────────── */
  function buildWidget() {
    var color  = primaryColor();
    var isLeft = widgetPosition() === 'bottom-left';

    var hostEl = document.createElement('div');
    hostEl.id  = 'embediq-host';
    hostEl.style.cssText = [
      'position:fixed',
      'z-index:2147483647',
      isLeft ? 'left:20px' : 'right:20px',
      'bottom:20px',
    ].join(';') + ';';
    document.body.appendChild(hostEl);

    var shadow = hostEl.attachShadow({ mode: 'open' });

    /* CSS inside shadow DOM */
    var style = document.createElement('style');
    style.textContent = [
      ':host{all:initial;font-family:Inter,system-ui,sans-serif;}',
      '.btn{width:56px;height:56px;border-radius:50%;background:' + color + ';',
        'border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;',
        'color:#fff;box-shadow:0 4px 14px rgba(0,0,0,.25);',
        'transition:transform .2s,box-shadow .2s;position:relative;outline:none;}',
      '.btn:hover{transform:scale(1.07);box-shadow:0 6px 20px rgba(0,0,0,.3);}',
      '.btn:focus-visible{outline:3px solid ' + color + ';outline-offset:3px;}',
      '.badge{position:absolute;top:-5px;right:-5px;min-width:19px;height:19px;',
        'border-radius:10px;background:#ef4444;color:#fff;font-size:11px;font-weight:700;',
        'display:none;align-items:center;justify-content:center;padding:0 5px;',
        'border:2px solid #fff;}',
      '.panel{position:fixed;' + (isLeft ? 'left:20px' : 'right:20px') + ';bottom:88px;',
        'width:400px;height:600px;border-radius:16px;overflow:hidden;',
        'box-shadow:0 8px 40px rgba(0,0,0,.22);border:1px solid #e2e8f0;',
        'transform:scale(.92) translateY(18px);opacity:0;pointer-events:none;',
        'transition:transform .25s cubic-bezier(.4,0,.2,1),opacity .22s;',
        'background:#fff;display:flex;flex-direction:column;}',
      '.panel.open{transform:scale(1) translateY(0);opacity:1;pointer-events:all;}',
      '.panel.mobile{top:0;left:0 !important;right:0 !important;bottom:0;',
        'width:100% !important;height:100% !important;border-radius:0 !important;',
        'border:none !important;}',
      'iframe{width:100%;flex:1;border:none;display:block;}',
    ].join('');
    shadow.appendChild(style);

    /* Launcher button */
    var btn = document.createElement('button');
    btn.className = 'btn';
    btn.setAttribute('aria-label', 'Open EmbedIQ chat');
    btn.innerHTML = ICON_CHAT;

    badge = document.createElement('span');
    badge.className = 'badge';
    badge.setAttribute('aria-label', 'unread messages');
    btn.appendChild(badge);

    /* Chat panel */
    panel = document.createElement('div');
    panel.className = 'panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'EmbedIQ Chat');

    /* Iframe */
    ifr = document.createElement('iframe');
    ifr.src   = iframeUrl();
    ifr.title = 'EmbedIQ Chat';
    ifr.setAttribute('allow', 'clipboard-write');
    panel.appendChild(ifr);

    btn.addEventListener('click', toggleWidget);
    shadow.appendChild(panel);
    shadow.appendChild(btn);

    /* store btn ref for icon swaps */
    shadow._btn = btn;
  }

  /* ── 7. Toggle open / close ────────────────────────────────────────────── */
  function toggleWidget() { isOpen ? closeWidget() : openWidget(); }

  function openWidget() {
    isOpen = true;
    unread = 0;
    updateBadge();
    panel.classList.add('open');
    if (isMobile()) panel.classList.add('mobile');
    else panel.classList.remove('mobile');
    postToIframe({ type: 'PARENT_RESIZE', mobile: isMobile() });
  }

  function closeWidget() {
    isOpen = false;
    panel.classList.remove('open', 'mobile');
  }

  /* ── 8. Badge ──────────────────────────────────────────────────────────── */
  function updateBadge() {
    if (!badge) return;
    if (unread > 0 && !isOpen) {
      badge.textContent = unread > 9 ? '9+' : String(unread);
      badge.style.display = 'flex';
    } else {
      badge.style.display = 'none';
    }
  }

  /* ── 9. postMessage helpers ────────────────────────────────────────────── */
  function postToIframe(msg) {
    if (ifr && ifr.contentWindow) {
      try {
        ifr.contentWindow.postMessage(msg, iframeOrigin());
      } catch (e) {
        console.warn('[EmbedIQ] Unable to message widget iframe.');
      }
    }
  }

  /* ── 10. Listen for messages from iframe ───────────────────────────────── */
  window.addEventListener('message', function (e) {
    if (!ifr || !ifr.contentWindow) return;

    // Only trust messages from this widget's own iframe.
    if (e.source !== ifr.contentWindow) return;
    if (e.origin !== iframeOrigin()) return;

    if (!e.data || typeof e.data !== 'object') return;

    switch (e.data.type) {
      case 'WIDGET_TOGGLE_OPEN':
        if (!isOpen) openWidget();
        break;
      case 'WIDGET_TOGGLE_CLOSE':
        if (isOpen) closeWidget();
        break;
      case 'WIDGET_UNREAD_COUNT':
        unread = Number(e.data.count) || 0;
        updateBadge();
        break;
    }
  });

  /* ── 11. Viewport resize handler ───────────────────────────────────────── */
  window.addEventListener('resize', function () {
    if (!isOpen || !panel) return;
    if (isMobile()) panel.classList.add('mobile');
    else panel.classList.remove('mobile');
    postToIframe({ type: 'PARENT_RESIZE', mobile: isMobile() });
  });

  /* ── 12. Bootstrap ─────────────────────────────────────────────────────── */
  function init() {
    fetchConfig(function () {
      buildWidget();
      ifr.addEventListener('load', function () {
        // Send theme to iframe once loaded
        postToIframe({ type: 'THEME_UPDATE', theme: (cfg && cfg.theme) || {} });
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
