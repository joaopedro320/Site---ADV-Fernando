/*
 * Rastreamento da LP. Preencha os IDs abaixo e publique de novo.
 * Deixe vazio o que não for usar. Se o GTM estiver preenchido, prefira
 * configurar Pixel e GA4 dentro dele e deixar os outros dois vazios.
 * Eventos enviados ao dataLayer: whatsapp_click (wa_local), form_start,
 * generate_lead (situacao, cidade) e thank_you_view.
 */
window.LP_TRACKING = {
  gtm: "",        // ex.: "GTM-XXXXXXX"
  metaPixel: "",  // ex.: "123456789012345"
  ga4: ""         // ex.: "G-XXXXXXXXXX"
};

window.dataLayer = window.dataLayer || [];
window.lpTrack = function (event, params) {
  var data = Object.assign({ event: event }, params || {});
  window.dataLayer.push(data);
  if (window.fbq) {
    if (event === "generate_lead") window.fbq("track", "Lead", params || {});
    if (event === "whatsapp_click") window.fbq("track", "Contact", params || {});
  }
  if (window.gtag && window.LP_TRACKING.ga4 && !window.LP_TRACKING.gtm) {
    window.gtag("event", event, params || {});
  }
};

(function () {
  var c = window.LP_TRACKING;
  if (c.gtm) {
    window.dataLayer.push({ "gtm.start": new Date().getTime(), event: "gtm.js" });
    var g = document.createElement("script");
    g.async = true;
    g.src = "https://www.googletagmanager.com/gtm.js?id=" + c.gtm;
    document.head.appendChild(g);
  }
  if (c.metaPixel) {
    !function (f, b, e, v, n, t, s) { if (f.fbq) return; n = f.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments) }; if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = "2.0"; n.queue = []; t = b.createElement(e); t.async = !0; t.src = v; s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s) }(window, document, "script", "https://connect.facebook.net/en_US/fbevents.js");
    window.fbq("init", c.metaPixel);
    window.fbq("track", "PageView");
  }
  if (c.ga4 && !c.gtm) {
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + c.ga4;
    document.head.appendChild(s);
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", c.ga4);
  }
})();
