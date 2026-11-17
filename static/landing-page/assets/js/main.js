(function () {
  "use strict";
  var WA = "5511986408203";
  var MSG_PADRAO = "Olá, vim pela página do escritório e gostaria de agendar uma consulta.";

  var ano = document.getElementById("ano");
  if (ano) ano.textContent = new Date().getFullYear();

  // Links de WhatsApp com mensagem padrão e evento
  document.querySelectorAll(".js-wa").forEach(function (a) {
    a.href = "https://wa.me/" + WA + "?text=" + encodeURIComponent(MSG_PADRAO);
    a.addEventListener("click", function () {
      window.lpTrack && window.lpTrack("whatsapp_click", { wa_local: a.dataset.waLocal || "link" });
    });
  });

  // Carta do hero: anima uma vez ao carregar
  var carta = document.querySelector(".carta");
  if (carta) requestAnimationFrame(function () { setTimeout(function () { carta.classList.add("is-on"); }, 250); });

  // Botão flutuante aparece depois do hero
  var flut = document.querySelector(".wa-float");
  var hero = document.querySelector(".hero");
  if (flut && hero && "IntersectionObserver" in window) {
    new IntersectionObserver(function (e) { flut.classList.toggle("is-on", !e[0].isIntersecting); }, { threshold: 0.05 }).observe(hero);
  } else if (flut) { flut.classList.add("is-on"); }

  // Formulário
  var form = document.getElementById("form-caso");
  if (!form) return;
  var btn = document.getElementById("f-btn");
  var wa = document.getElementById("f-wa");
  var sel = document.getElementById("f-sit");
  var iniciou = false;

  function mascara(v) {
    var d = v.replace(/\D/g, "").slice(0, 11);
    if (d.length <= 2) return d.length ? "(" + d : "";
    if (d.length <= 6) return "(" + d.slice(0, 2) + ") " + d.slice(2);
    if (d.length <= 10) return "(" + d.slice(0, 2) + ") " + d.slice(2, 6) + "-" + d.slice(6);
    return "(" + d.slice(0, 2) + ") " + d.slice(2, 7) + "-" + d.slice(7);
  }
  wa.addEventListener("input", function () { wa.value = mascara(wa.value); });
  wa.addEventListener("blur", function () {
    wa.parentElement.classList.toggle("is-err", wa.value !== "" && !wa.checkValidity());
  });

  function checar() {
    var ok = form.checkValidity();
    btn.disabled = !ok;
    form.classList.toggle("is-ok", ok);
    if (ok) wa.parentElement.classList.remove("is-err");
  }
  form.addEventListener("input", checar);
  form.addEventListener("change", checar);
  form.addEventListener("focusin", function () {
    if (!iniciou) { iniciou = true; window.lpTrack && window.lpTrack("form_start", {}); }
  });

  // Situações preenchem o select
  document.querySelectorAll(".sit__item").forEach(function (b) {
    b.addEventListener("click", function () {
      sel.value = b.dataset.sit;
      checar();
      var campo = sel.parentElement;
      document.getElementById("caso").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
      campo.classList.add("is-flash");
      setTimeout(function () { campo.classList.remove("is-flash"); }, 1800);
      setTimeout(function () { document.getElementById("f-nome").focus({ preventScroll: true }); }, 600);
    });
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!form.checkValidity()) { form.reportValidity(); return; }
    var f = new FormData(form);
    var linhas = [
      "Olá, vim pela página do escritório e gostaria de falar sobre o meu caso.",
      "",
      "*Nome:* " + f.get("nome").trim(),
      "*WhatsApp:* " + f.get("whatsapp"),
      "*Situação:* " + f.get("situacao"),
      "*Cidade:* " + f.get("cidade").trim()
    ];
    var msg = (f.get("mensagem") || "").trim();
    if (msg) linhas.push("*Resumo:* " + msg);
    var url = "https://wa.me/" + WA + "?text=" + encodeURIComponent(linhas.join("\n"));
    try { sessionStorage.setItem("lfn_wa", url); } catch (err) {}
    window.lpTrack && window.lpTrack("generate_lead", { situacao: f.get("situacao"), cidade: f.get("cidade").trim() });
    btn.disabled = true;
    setTimeout(function () { window.location.href = "/landing-page/obrigado/?s=" + encodeURIComponent(f.get("situacao")); }, 250);
  });
})();
