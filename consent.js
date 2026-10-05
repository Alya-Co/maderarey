/* ============================================================
   MaderaRey — gestor de consentimiento de cookies
   Google Consent Mode v2 (modo "básico": las etiquetas de Google
   NO se cargan en absoluto hasta que el usuario da su consentimiento
   para la categoría correspondiente).
   ============================================================ */
(function () {
  'use strict';

  var COOKIE_NAME = 'cookie_consent';
  var COOKIE_DAYS = 365;
  var GA4_ID = 'G-8CH1ZTZCZS';
  var ADS_ID = 'AW-11471104634';
  var ADS_CONVERSION_LABEL = 'AW-11471104634/0txFCKLJ65EdEPrU7N0q';

  /* ---------- cookies propias (solo para recordar la decisión) ---------- */
  function getCookie(name) {
    var m = document.cookie.match('(?:^|; )' + name + '=([^;]*)');
    return m ? decodeURIComponent(m[1]) : null;
  }
  function setCookie(name, value, days) {
    var expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = name + '=' + encodeURIComponent(value) + '; expires=' + expires + '; path=/; SameSite=Lax';
  }
  function readConsent() {
    var raw = getCookie(COOKIE_NAME);
    if (!raw) return null;
    try { return JSON.parse(raw); } catch (e) { return null; }
  }

  /* ---------- gtag stub (dataLayer siempre existe; gtag.js se carga solo si hay consentimiento) ---------- */
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = window.gtag || gtag;

  var loaded = { script: false, analytics: false, ads: false };

  function loadGtagScript(cb) {
    if (loaded.script) { cb(); return; }
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA4_ID;
    s.onload = function () { loaded.script = true; cb(); };
    document.head.appendChild(s);
  }

  function applyConsent(consent) {
    window.__ccConsent = consent;
    if (!consent.analytics && !consent.ads) return; // nada que cargar
    loadGtagScript(function () {
      gtag('consent', 'default', {
        'analytics_storage': consent.analytics ? 'granted' : 'denied',
        'ad_storage': consent.ads ? 'granted' : 'denied',
        'ad_user_data': consent.ads ? 'granted' : 'denied',
        'ad_personalization': consent.ads ? 'granted' : 'denied'
      });
      gtag('js', new Date());
      if (consent.analytics && !loaded.analytics) {
        gtag('config', GA4_ID);
        loaded.analytics = true;
      }
      if (consent.ads && !loaded.ads) {
        gtag('config', ADS_ID);
        loaded.ads = true;
      }
    });
  }

  function saveConsent(consent) {
    consent.ts = new Date().toISOString();
    setCookie(COOKIE_NAME, JSON.stringify(consent), COOKIE_DAYS);
    applyConsent(consent);
  }

  /* ---------- conversión: clic en botón/enlace de WhatsApp ---------- */
  window.ccTrackWhatsApp = function () {
    if (window.__ccConsent && window.__ccConsent.ads && loaded.ads) {
      gtag('event', 'conversion', { send_to: ADS_CONVERSION_LABEL });
    }
  };

  /* ---------- estilos del banner/panel ---------- */
  function injectStyles() {
    if (document.getElementById('cc-styles')) return;
    var style = document.createElement('style');
    style.id = 'cc-styles';
    style.textContent =
      '#cc-banner{position:fixed;left:0;right:0;bottom:0;z-index:9999;background:#fff;border-top:2px solid #2E7D32;box-shadow:0 -4px 20px rgba(0,0,0,0.12);padding:16px 20px;font-family:\'Segoe UI\',system-ui,-apple-system,sans-serif;}' +
      '#cc-banner-inner{max-width:1000px;margin:0 auto;display:flex;align-items:center;gap:20px;flex-wrap:wrap;}' +
      '#cc-text{flex:1 1 320px;font-size:13px;line-height:1.5;color:#333;margin:0;}' +
      '#cc-text a{color:#1B5E20;text-decoration:underline;}' +
      '#cc-actions{display:flex;gap:10px;flex-wrap:wrap;flex:0 0 auto;}' +
      '.cc-btn{font-family:inherit;font-size:13px;font-weight:600;padding:10px 18px;border-radius:8px;cursor:pointer;border:1px solid #2E7D32;white-space:nowrap;}' +
      '.cc-btn-solid{background:#2E7D32;color:#fff;}' +
      '.cc-btn-solid:hover{background:#1B5E20;}' +
      '.cc-btn-ghost{background:#fff;color:#2E7D32;}' +
      '.cc-btn-ghost:hover{background:#F1F8E9;}' +
      '#cc-panel{position:fixed;left:0;right:0;bottom:0;z-index:10000;background:#fff;border-top:2px solid #2E7D32;box-shadow:0 -4px 20px rgba(0,0,0,0.16);padding:20px;font-family:\'Segoe UI\',system-ui,-apple-system,sans-serif;max-height:80vh;overflow-y:auto;}' +
      '#cc-panel-inner{max-width:640px;margin:0 auto;}' +
      '#cc-panel-inner h3{font-size:17px;color:#1B5E20;margin-bottom:14px;}' +
      '.cc-row{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:12px 0;border-bottom:1px solid #eee;}' +
      '.cc-row strong{font-size:13px;color:#1A1A1A;}' +
      '.cc-row p{font-size:12px;color:#666;margin-top:3px;}' +
      '.cc-row input{margin-top:3px;width:18px;height:18px;flex-shrink:0;}' +
      '#cc-panel-actions{margin-top:16px;display:flex;justify-content:flex-end;}' +
      '@media (max-width:640px){#cc-banner-inner{flex-direction:column;align-items:stretch;}#cc-actions{justify-content:stretch;}#cc-actions .cc-btn{flex:1;}}';
    document.head.appendChild(style);
  }

  /* ---------- banner ---------- */
  function buildBanner() {
    injectStyles();
    var wrap = document.createElement('div');
    wrap.id = 'cc-banner';
    wrap.innerHTML =
      '<div id="cc-banner-inner">' +
        '<p id="cc-text">Usamos cookies técnicas necesarias para el funcionamiento del sitio y, si nos lo permites, cookies de analítica y publicidad para mejorar la web y medir nuestras campañas. Puedes aceptar, rechazar o configurar tu preferencia. Más información en nuestra <a href="cookies.html">Política de Cookies</a>.</p>' +
        '<div id="cc-actions">' +
          '<button type="button" id="cc-configure" class="cc-btn cc-btn-ghost">Configurar</button>' +
          '<button type="button" id="cc-reject" class="cc-btn cc-btn-ghost">Rechazar</button>' +
          '<button type="button" id="cc-accept" class="cc-btn cc-btn-solid">Aceptar</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(wrap);

    document.getElementById('cc-accept').addEventListener('click', function () {
      saveConsent({ analytics: true, ads: true });
      removeUI();
    });
    document.getElementById('cc-reject').addEventListener('click', function () {
      saveConsent({ analytics: false, ads: false });
      removeUI();
    });
    document.getElementById('cc-configure').addEventListener('click', function () {
      showPanel();
    });
  }

  function removeUI() {
    var b = document.getElementById('cc-banner');
    if (b) b.remove();
    var p = document.getElementById('cc-panel');
    if (p) p.remove();
  }

  function showPanel() {
    injectStyles();
    var old = document.getElementById('cc-panel');
    if (old) old.remove();
    var current = readConsent() || window.__ccConsent || { analytics: false, ads: false };
    var panel = document.createElement('div');
    panel.id = 'cc-panel';
    panel.innerHTML =
      '<div id="cc-panel-inner">' +
        '<h3>Configurar cookies</h3>' +
        '<div class="cc-row"><div><strong>Técnicas</strong><p>Necesarias para el funcionamiento del sitio (recordar tu preferencia de cookies). Siempre activas.</p></div><input type="checkbox" checked disabled></div>' +
        '<div class="cc-row"><div><strong>Analítica</strong><p>Google Analytics 4 — estadísticas de uso anónimas del sitio.</p></div><input type="checkbox" id="cc-cb-analytics"' + (current.analytics ? ' checked' : '') + '></div>' +
        '<div class="cc-row"><div><strong>Publicidad</strong><p>Google Ads — medición de conversiones de nuestras campañas publicitarias.</p></div><input type="checkbox" id="cc-cb-ads"' + (current.ads ? ' checked' : '') + '></div>' +
        '<div id="cc-panel-actions">' +
          '<button type="button" id="cc-panel-save" class="cc-btn cc-btn-solid">Guardar preferencias</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(panel);
    document.getElementById('cc-panel-save').addEventListener('click', function () {
      saveConsent({
        analytics: document.getElementById('cc-cb-analytics').checked,
        ads: document.getElementById('cc-cb-ads').checked
      });
      removeUI();
    });
  }

  /* enlace permanente "Configurar cookies" (footer / política de cookies) */
  window.openCookieSettings = function () {
    showPanel();
  };

  /* ---------- arranque ---------- */
  document.addEventListener('DOMContentLoaded', function () {
    var saved = readConsent();
    if (saved) {
      applyConsent(saved);
    } else {
      buildBanner();
    }

    // Enlaces estáticos de WhatsApp (index.html, y cualquier <a href*="wa.me">)
    document.querySelectorAll('a[href*="wa.me"]').forEach(function (el) {
      el.addEventListener('click', window.ccTrackWhatsApp);
    });
  });
})();
