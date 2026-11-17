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


  var calmo = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Faixas animadas: duplica o conteúdo para o loop contínuo
  document.querySelectorAll("[data-mq] .mq__track").forEach(function (t) { t.innerHTML += t.innerHTML; });

  // Carrossel de situações
  var car = document.querySelector("[data-car]");
  if (car) {
    var trk = car.querySelector(".car__track");
    var prev = document.querySelector("[data-car-prev]");
    var next = document.querySelector("[data-car-next]");
    var barra = car.querySelector(".car__barra span");
    var passo = function () { var sl = trk.querySelector(".car__slide"); return sl ? sl.getBoundingClientRect().width + 22 : 300; };
    var atual = function () {
      var max = trk.scrollWidth - trk.clientWidth;
      var r = max > 0 ? trk.scrollLeft / max : 0;
      var vis = trk.clientWidth / trk.scrollWidth;
      if (barra) { barra.style.width = (vis * 100) + "%"; barra.style.transform = "translateX(" + (r * (1 / vis - 1) * 100) + "%)"; }
      if (prev) prev.disabled = trk.scrollLeft < 4;
      if (next) next.disabled = trk.scrollLeft > max - 4;
    };
    trk.addEventListener("scroll", atual, { passive: true });
    addEventListener("resize", atual);
    atual();
    var parar = false;
    var mover = function (d) { trk.scrollBy({ left: d * passo(), behavior: calmo ? "auto" : "smooth" }); };
    if (prev) prev.addEventListener("click", function () { parar = true; mover(-1); });
    if (next) next.addEventListener("click", function () { parar = true; mover(1); });
    // arrastar com o mouse
    var arr = null, moveu = false;
    trk.addEventListener("pointerdown", function (e) { if (e.pointerType !== "mouse") return; arr = { x: e.clientX, s: trk.scrollLeft }; moveu = false; parar = true; });
    addEventListener("pointermove", function (e) { if (!arr) return; var dx = e.clientX - arr.x; if (Math.abs(dx) > 5) { moveu = true; trk.classList.add("is-drag"); } trk.scrollLeft = arr.s - dx; });
    addEventListener("pointerup", function () { if (!arr) return; arr = null; trk.classList.remove("is-drag"); });
    trk.addEventListener("click", function (e) { if (moveu) { e.stopPropagation(); e.preventDefault(); moveu = false; } }, true);
    ["touchstart", "wheel", "focusin"].forEach(function (ev) { trk.addEventListener(ev, function () { parar = true; }, { passive: true }); });
    // avança sozinho enquanto ninguém mexe
    var pausa = false;
    car.addEventListener("mouseenter", function () { pausa = true; });
    car.addEventListener("mouseleave", function () { pausa = false; });
    if (!calmo) setInterval(function () {
      if (parar || pausa || document.hidden) return;
      var r = car.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight) return;
      if (trk.scrollLeft >= trk.scrollWidth - trk.clientWidth - 4) trk.scrollTo({ left: 0, behavior: "smooth" }); else mover(1);
    }, 3800);
  }

  // Galeria do advogado
  var gal = document.querySelector("[data-gal]");
  if (gal) {
    var fotos = gal.querySelectorAll("img"), dots = gal.querySelectorAll(".adv__dots button"), gi = 0, gt;
    var ir = function (n) {
      fotos[gi].classList.remove("is-on"); dots[gi].removeAttribute("aria-current");
      gi = (n + fotos.length) % fotos.length;
      fotos[gi].classList.add("is-on"); dots[gi].setAttribute("aria-current", "true");
    };
    var auto = function () { clearInterval(gt); if (!calmo) gt = setInterval(function () { ir(gi + 1); }, 4500); };
    dots.forEach(function (d, i) { d.addEventListener("click", function () { ir(i); auto(); }); });
    auto();
  }

  // Revelar ao rolar
  var rv = document.querySelectorAll(".passos__lista li, .adv__txt, .brasil__txt, .reunir, .form, .golpe");
  rv.forEach(function (el) { el.classList.add(el.classList.contains("duo") ? "rv-duo" : "rv"); });
  document.querySelectorAll(".passos__lista li").forEach(function (el, i) { el.style.transitionDelay = (i * 0.12) + "s"; });
  document.querySelectorAll(".duo figure").forEach(function (el, i) { el.style.transitionDelay = (i * 0.25) + "s"; });
  if ("IntersectionObserver" in window && !calmo) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); } }); }, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });
    rv.forEach(function (el) { io.observe(el); });
  } else rv.forEach(function (el) { el.classList.add("is-in"); });

  // Abertura com a marca e entrada do hero
  var carta = document.querySelector(".carta");
  var heroIn = function () {
    document.documentElement.classList.add("hero-in");
    if (carta) setTimeout(function () { carta.classList.add("is-on"); }, 250);
  };
  var ld = document.getElementById("ld");
  if (ld && document.documentElement.classList.contains("ld-on")) {
    setTimeout(function () { ld.classList.add("is-out"); }, 1750);
    setTimeout(function () { ld.classList.add("is-up"); }, 2000);
    setTimeout(function () { document.documentElement.classList.remove("ld-on"); heroIn(); }, 2150);
    setTimeout(function () { ld.remove(); }, 3200);
  } else { requestAnimationFrame(heroIn); }

  // Mapa: desenha as rotas quando aparece
  document.querySelectorAll("[data-map]").forEach(function (m) {
    if (!("IntersectionObserver" in window) || calmo) { m.classList.add("is-in"); return; }
    var o = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { m.classList.add("is-in"); o.disconnect(); } }, { threshold: 0.3 });
    o.observe(m);
  });

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
  document.querySelectorAll(".sit-card").forEach(function (b) {
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
