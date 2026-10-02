/* ============================================================
   MaderaRey — detección de origen (Facebook / Google) para WhatsApp
   ------------------------------------------------------------
   Lee ?utm_source=... o ?gclid=... de la URL al entrar en CUALQUIER
   página del sitio, y lo recuerda durante toda la visita (sessionStorage),
   aunque el visitante navegue por varias páginas del catálogo antes
   de escribir por WhatsApp.

   Se usa para añadir una etiqueta de origen al texto del mensaje de
   WhatsApp ("Fuente: Facebook" / "Fuente: Google Ads"), y así poder
   comprobar a simple vista, dentro del propio WhatsApp, de dónde
   viene cada contacto — sin depender de las estadísticas de clics
   de Google Ads, que no siempre cuentan bien.

   Cómo generar tráfico ya etiquetado:
   - Enlaces publicados en Facebook / Instagram / Marketplace / feed
     del catálogo → añadir al final: ?utm_source=facebook
   - Google Ads → no hace falta tocar nada: con el autotagging activado
     (activado por defecto), Google añade "gclid=..." automáticamente.
   ============================================================ */
(function () {
  'use strict';
  var STORAGE_KEY = 'mr_lead_source';

  function detect() {
    var params = new URLSearchParams(window.location.search);
    var src = (params.get('utm_source') || '').toLowerCase();
    if (src.indexOf('facebook') !== -1 || src.indexOf('fb') !== -1 || src.indexOf('instagram') !== -1) {
      return 'facebook';
    }
    if (src === 'google' || params.has('gclid')) {
      return 'google';
    }
    return null;
  }

  function resolve() {
    var found = detect();
    if (found) {
      try { sessionStorage.setItem(STORAGE_KEY, found); } catch (e) {}
      return found;
    }
    try {
      var stored = sessionStorage.getItem(STORAGE_KEY);
      if (stored) return stored;
    } catch (e) {}
    return null;
  }

  var LABELS = { facebook: 'Facebook', google: 'Google Ads' };
  var source = resolve();

  window.MR_leadSource = source;

  // Añade "Fuente: ..." al final del texto si se conoce el origen;
  // si no (visita directa / buscador / no etiquetada), deja el texto igual.
  window.MR_tagWAText = function (text) {
    if (!source) return text;
    return text + '\n\nFuente: ' + LABELS[source];
  };
})();
