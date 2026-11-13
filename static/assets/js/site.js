/* Luiz Fernando Neves Advocacia · site.js
   Base sem dependencias + camada de movimento com GSAP, ScrollTrigger, SplitText e Lenis (assets/js/vendor). */
(function(){
  'use strict';
  var d=document,w=window,root=d.documentElement;
  root.classList.add('js');
  var $=function(s,c){return (c||d).querySelector(s)},$$=function(s,c){return Array.prototype.slice.call((c||d).querySelectorAll(s))};
  var reduce=w.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fine=w.matchMedia('(hover:hover) and (pointer:fine)').matches;
  var store={get:function(k){try{return sessionStorage.getItem(k)}catch(e){return null}},set:function(k,v){try{sessionStorage.setItem(k,v)}catch(e){}}};
  function track(name,params){try{w.dataLayer=w.dataLayer||[];w.dataLayer.push(Object.assign({event:name},params||{}));if(w.fbq&&name==='whatsapp_click')w.fbq('track','Contact');}catch(e){}}
  function raf(fn){var t=false;return function(){if(!t){t=true;requestAnimationFrame(function(){t=false;fn()})}}}
  var lenis=null;

  /* hero: titulo cabe na largura */
  function fitHero(){$$('.hero-a,.hero-b').forEach(function(el){
    el.style.fontSize='';if(w.innerWidth<=760)return;
    var max=w.innerWidth*.94,cs=parseFloat(getComputedStyle(el).fontSize),sp=d.createElement('span');
    sp.style.cssText='position:absolute;visibility:hidden;white-space:nowrap;font:inherit;letter-spacing:inherit;text-transform:inherit';sp.textContent=el.textContent;el.appendChild(sp);
    var wd=sp.getBoundingClientRect().width;sp.remove();if(wd>max)el.style.fontSize=(cs*max/wd)+'px'})}
  function footH(){var hf=$('.hero-foot'),hero=$('.hero');if(hf&&hero)hero.style.setProperty('--foot-h',hf.offsetHeight+'px')}
  fitHero();footH();w.addEventListener('resize',function(){fitHero();footH()});

  /* cabecalho: fundo ao rolar, some ao descer */
  var hd=$('[data-header]'),bar,lastY=0;
  if(hd){bar=d.createElement('div');bar.className='progress';bar.setAttribute('aria-hidden','true');hd.appendChild(bar)}
  function onScroll(y){
    y=typeof y==='number'?y:(w.scrollY||0);
    if(hd){hd.classList.toggle('is-stuck',y>40);
      if(!d.body.classList.contains('menu-open')&&w.innerWidth>900){
        if(y>600&&y>lastY+3)hd.classList.add('hidden');else if(y<lastY-3||y<600)hd.classList.remove('hidden')}}
    var h=root.scrollHeight-w.innerHeight;if(bar)bar.style.setProperty('--p',h>0?Math.min(1,y/h):0);
    lastY=y;
  }
  w.addEventListener('scroll',function(){onScroll()},{passive:true});onScroll();

  /* menu mobile */
  var burger=$('.burger'),nav=$('#menu');
  if(burger&&nav){
    burger.addEventListener('click',function(){
      var o=nav.classList.toggle('is-open');burger.setAttribute('aria-expanded',o);burger.setAttribute('aria-label',o?'Fechar menu':'Abrir menu');
      d.body.classList.toggle('menu-open',o);if(lenis){o?lenis.stop():lenis.start()}else root.style.overflow=o?'hidden':'';
    });
    $$('.sub-toggle').forEach(function(b){b.addEventListener('click',function(){var o=b.parentNode.classList.toggle('open');b.setAttribute('aria-expanded',o)})});
    d.addEventListener('keydown',function(e){if(e.key==='Escape'&&nav.classList.contains('is-open'))burger.click()});
  }

  /* escalonamento e entradas simples (CSS) */
  $$('.pubs,.rows,.steps,.area-cards,.faq,.rail,.princs,.form-cols').forEach(function(g){$$('.reveal',g).forEach(function(el,i){el.style.setProperty('--rd',(i%4)*110+'ms')})});
  var targets=$$('.reveal,.split,.mono-anim,.steps li');
  if('IntersectionObserver' in w&&!reduce){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('is-in');io.unobserve(e.target)}})},{threshold:.15,rootMargin:'0px 0px -40px 0px'});
    targets.forEach(function(el){io.observe(el)});
  }else targets.forEach(function(el){el.classList.add('is-in')});


  /* linha do tempo no mobile: dica de arrastar */
  (function(){var trk=$('[data-htl-track]');if(!trk)return;var tip=$('.htl-swipe'),wrap=trk.parentNode;
    function st(){var max=trk.scrollWidth-trk.clientWidth;wrap.classList.toggle('end',trk.scrollLeft>max-8);if(trk.scrollLeft>20&&tip)tip.classList.add('gone')}
    trk.addEventListener('scroll',raf(st),{passive:true});st();
    if('IntersectionObserver' in w&&!reduce){var o=new IntersectionObserver(function(es){if(es[0].isIntersecting&&w.innerWidth<=1100){trk.classList.add('hint');o.disconnect()}},{threshold:.6});o.observe(trk)}
  })();

  /* carrossel de noticias do hero */
  $$('[data-carousel]').forEach(function(c){
    var sl=$$('.slide',c),dots=$$('.dot',c),i=0,tm;
    if(sl.length<2)return;
    function go(n){i=(n+sl.length)%sl.length;
      sl.forEach(function(s,k){var on=k===i;s.classList.toggle('is-on',on);s.setAttribute('aria-hidden',on?'false':'true');s.tabIndex=on?0:-1});
      dots.forEach(function(x,k){x.classList.toggle('is-on',k===i);if(k===i)x.setAttribute('aria-current','true');else x.removeAttribute('aria-current')})}
    function play(){if(reduce)return;stop();tm=setInterval(function(){go(i+1)},5500)}
    function stop(){clearInterval(tm)}
    $('.next',c).addEventListener('click',function(){go(i+1);play()});
    $('.prev',c).addEventListener('click',function(){go(i-1);play()});
    dots.forEach(function(x,k){x.addEventListener('click',function(){go(k);play()})});
    c.addEventListener('mouseenter',stop);c.addEventListener('mouseleave',play);c.addEventListener('focusin',stop);c.addEventListener('focusout',play);
    play();
  });

  /* trilhos (carrosseis de cards) */
  $$('.rail-wrap').forEach(function(wr){
    var rail=$('.rail',wr),prev=$('.rail-prev',wr),next=$('.rail-next',wr),line=$('.rail-line i',wr);
    function upd(){var max=rail.scrollWidth-rail.clientWidth;prev.disabled=rail.scrollLeft<4;next.disabled=rail.scrollLeft>max-4;
      line.style.setProperty('--rp',Math.max(.08,Math.min(1,(rail.scrollLeft+rail.clientWidth)/rail.scrollWidth)))}
    function step(dir){var c=$(':scope>:not([hidden])',rail);rail.scrollBy({left:dir*((c?c.offsetWidth:360)+24),behavior:'smooth'})}
    prev.addEventListener('click',function(){step(-1)});next.addEventListener('click',function(){step(1)});
    rail.addEventListener('scroll',raf(upd),{passive:true});w.addEventListener('resize',upd);
    rail.addEventListener('keydown',function(e){if(e.key==='ArrowRight')step(1);if(e.key==='ArrowLeft')step(-1)});
    wr._upd=upd;upd();
  });

  /* filtro de artigos */
  var chips=$$('.chip'),lista=$('#lista-artigos');
  if(chips.length&&lista){
    chips.forEach(function(ch){ch.addEventListener('click',function(){
      chips.forEach(function(x){x.classList.toggle('is-on',x===ch)});
      var cat=ch.getAttribute('data-cat');
      $$('.card',lista).forEach(function(card){card.hidden=!!cat&&card.getAttribute('data-cat')!==cat;if(!card.hidden)card.classList.add('is-in')});
      lista.scrollTo({left:0});var wr=lista.closest('.rail-wrap');setTimeout(function(){wr&&wr._upd&&wr._upd()},80);
    })});
  }

  /* aviso de golpe: uma vez por sessao, depois da abertura */
  function alerta(delay){var al=$('#alerta-golpe');
    if(al&&typeof al.showModal==='function'&&store.get('alerta-golpe')!=='1'){setTimeout(function(){try{al.showModal();store.set('alerta-golpe','1')}catch(e){}},delay)}}

  /* rastreio e formulario */
  d.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[data-wa]');if(a)track('whatsapp_click',{wa_local:a.getAttribute('data-wa'),page_path:location.pathname})});
  var f=$('#form-contato');
  if(f){
    var btn=$('button[type=submit]',f),req=$$('[required]',f);
    function ok(){return req.every(function(x){return x.type==='checkbox'?x.checked:x.value.trim().length>=(parseInt(x.getAttribute('minlength'))||1)})}
    function upd(){btn.disabled=!ok()}
    f.addEventListener('input',upd);f.addEventListener('change',upd);upd();
    f.addEventListener('submit',function(e){
      e.preventDefault();
      if(!ok()){req.forEach(function(x){x.classList.toggle('is-bad',x.type==='checkbox'?!x.checked:!x.value.trim())});return}
      var v=function(n){return f.elements[n].value.trim()};
      var msg='Olá, meu nome é '+v('nome')+'.\nAssunto: '+v('assunto')+'.\n'+v('mensagem')+'\nMeu WhatsApp: '+v('telefone');
      track('lead_form_submit',{assunto:v('assunto')});
      w.open(f.getAttribute('data-wa')+'?text='+encodeURIComponent(msg),'_blank','noopener');
      location.href='/obrigado/';
    });
  }

  /* ======================= MOVIMENTO ======================= */
  var hasGsap=!!(w.gsap&&w.ScrollTrigger)&&!reduce;
  if(!hasGsap){
    root.classList.remove('js');
    root.classList.add('hero-go');
    $$('[data-count]').forEach(function(el){el.textContent=String(el.getAttribute('data-count')).padStart(2,'0')});
    alerta(2500);return;
  }
  root.classList.add('motion');
  gsap.registerPlugin(ScrollTrigger);if(w.SplitText)gsap.registerPlugin(SplitText);
  var EASE='expo.out';

  /* rolagem suave */
  if(w.Lenis){
    lenis=new Lenis({duration:1.15,easing:function(t){return Math.min(1,1.001-Math.pow(2,-10*t))},smoothWheel:true});
    lenis.on('scroll',function(e){ScrollTrigger.update();onScroll(e.scroll)});
    gsap.ticker.add(function(t){lenis.raf(t*1000)});gsap.ticker.lagSmoothing(0);
    $$('a[href^="#"]').forEach(function(a){a.addEventListener('click',function(e){var id=a.getAttribute('href');if(id.length>1&&d.querySelector(id)){e.preventDefault();lenis.scrollTo(id,{offset:-90})}})});
  }

  function fades(){
    gsap.utils.toArray('[data-fade]').forEach(function(el){
      if(el.closest('.hero'))return;
      gsap.fromTo(el,{opacity:0,y:30},{opacity:1,y:0,duration:1.2,ease:EASE,scrollTrigger:{trigger:el,start:'top 92%',once:true}});
    });
    gsap.utils.toArray('[data-split]').forEach(function(el){
      var lines=w.SplitText?new SplitText(el,{type:'words,lines',linesClass:'sl'}).lines:[el];
      gsap.set(lines,{y:46,opacity:0});
      ScrollTrigger.create({trigger:el,start:'top 90%',once:true,onEnter:function(){gsap.to(lines,{y:0,opacity:1,duration:1.3,ease:EASE,stagger:.09})}});
    });
  }
  /* imagens: revelacao + parallax interno */
  function media(){
    gsap.utils.toArray('[data-reveal]').forEach(function(el){
      var im=el.querySelector('img');
      var tl=gsap.timeline({scrollTrigger:{trigger:el,start:'top 90%'}});
      tl.fromTo(el,{clipPath:'inset(100% 0% 0% 0%)'},{clipPath:'inset(0% 0% 0% 0%)',duration:1.6,ease:'expo.inOut'});
      if(im)tl.fromTo(im,{scale:1.35},{scale:1,duration:2,ease:EASE},0);
    });
    gsap.utils.toArray('[data-speed]').forEach(function(el){
      var sp=parseFloat(el.getAttribute('data-speed'))||-.1;
      gsap.fromTo(el,{yPercent:-sp*50},{yPercent:sp*50,ease:'none',scrollTrigger:{trigger:el.parentElement,start:'top bottom',end:'bottom top',scrub:true}});
    });
    // cards e fotos dos publicos entram em sequencia
    ScrollTrigger.batch('.pub,.area-card,.rb',{start:'top 92%',once:true,onEnter:function(b){gsap.fromTo(b,{opacity:0,y:60},{opacity:1,y:0,duration:1.2,ease:EASE,stagger:.1,overwrite:true})}});
  }
  /* frase: palavras acendem com a rolagem */
  function words(){
    $$('[data-words]').forEach(function(el){
      if(!w.SplitText)return;var ws=new SplitText(el,{type:'words'}).words;
      gsap.fromTo(ws,{color:'rgba(255,255,255,.16)'},{color:'rgba(255,255,255,1)',ease:'none',stagger:.1,scrollTrigger:{trigger:el,start:'top 80%',end:'bottom 40%',scrub:true}});
    });
  }
  function counters(){
    $$('[data-count]').forEach(function(el){
      var to=parseInt(el.getAttribute('data-count'),10),o={v:0};el.textContent='00';
      ScrollTrigger.create({trigger:el,start:'top 90%',once:true,onEnter:function(){gsap.to(o,{v:to,duration:2.2,ease:'power3.out',onUpdate:function(){el.textContent=String(Math.round(o.v)).padStart(2,'0')}})}});
    });
  }
  /* faixas que aceleram com a rolagem */
  function marquee(){
    $$('[data-marquee] .mq-track').forEach(function(tr){
      var x=0,dir=-1,base=tr.classList.contains('rb-track')?.45:.7,speed=base,half=function(){return tr.scrollWidth/2};
      ScrollTrigger.create({trigger:tr,start:'top bottom',end:'bottom top',onUpdate:function(s){dir=s.direction===1?-1:1;speed=base+Math.min(Math.abs(s.getVelocity())/300,8)}});
      var paused=false;tr.addEventListener('mouseenter',function(){paused=true});tr.addEventListener('mouseleave',function(){paused=false});
      gsap.ticker.add(function(){if(paused)return;x+=dir*speed;speed+=(base-speed)*.05;var h=half();if(x<=-h)x+=h;if(x>0)x-=h;tr.style.transform='translate3d('+x+'px,0,0)'});
    });
  }
  /* linha do tempo horizontal fixa */
  function htl(){
    var sec=$('[data-htl]');if(!sec)return;
    var trk=$('[data-htl-track]',sec),pbar=$('[data-htl-bar]',sec),pin=$('.htl-pin',sec);
    var mm=gsap.matchMedia();
    mm.add('(min-width: 1101px)',function(){
      var dist=function(){return Math.max(0,trk.scrollWidth-(w.innerWidth-trk.getBoundingClientRect().left)+40)};
      gsap.to(trk,{x:function(){return -dist()},ease:'none',scrollTrigger:{trigger:sec,pin:pin,start:'top top',end:function(){return '+='+dist()},scrub:1,invalidateOnRefresh:true,onUpdate:function(s){if(pbar)pbar.style.transform='scaleX('+s.progress+')'}}});
      $$('.htl-i',trk).forEach(function(li,i){gsap.fromTo(li,{opacity:.25,y:30},{opacity:1,y:0,ease:'none',scrollTrigger:{trigger:sec,start:function(){return 'top+='+(i*dist()/($$('.htl-i',trk).length))+' 70%'},end:'+=280',scrub:true}})});
      return function(){gsap.set(trk,{clearProps:'transform'})};
    });
  }
  /* hero: entrada depois da abertura + leve parallax da colagem */
  function heroAnim(){
    root.classList.add('hero-go');
    var hv=$('.hero-visual');if(!hv)return;
    gsap.to(hv,{yPercent:-6,ease:'none',scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom top',scrub:true}});
    if(fine){var gs=$$('.hg,.hero-mono',hv);$('.hero').addEventListener('pointermove',function(e){var x=e.clientX/w.innerWidth-.5,y=e.clientY/w.innerHeight-.5;
      gs.forEach(function(g,n){var kk=(n+1)*8;g.style.marginLeft=(x*kk).toFixed(1)+'px';g.style.marginTop=(y*kk).toFixed(1)+'px'})})}
  }
  /* abertura com a marca (uma vez por sessao) */
  function loader(done){
    if(!$('[data-hero]')||store.get('lfn_seen')){done();return}
    store.set('lfn_seen','1');
    var mono=$('.st-mono');var markSvg=mono?mono.outerHTML.replace('mono-anim st-mono','loader-mark'):'';
    var el=d.createElement('div');el.className='loader';el.setAttribute('aria-hidden','true');
    el.innerHTML='<div class="loader-in">'+markSvg+'<img class="loader-word" src="'+(($('.logo-light')||{}).getAttribute?$('.logo-light').getAttribute('src'):'')+'" alt=""><span class="loader-bar"><i></i></span></div>';
    d.body.appendChild(el);if(lenis)lenis.stop();
    var paths=$$('.loader-mark path',el);
    var tl=gsap.timeline({onComplete:function(){el.remove();if(lenis)lenis.start()}});
    tl.fromTo(paths,{opacity:0,xPercent:-30,yPercent:30},{opacity:1,xPercent:0,yPercent:0,duration:1,ease:EASE,stagger:.1})
      .to($('.loader-word',el),{clipPath:'inset(0 0% 0 0)',duration:1.1,ease:'expo.inOut'},.35)
      .to($('.loader-bar i',el),{scaleX:1,duration:1.3,ease:'expo.inOut'},.35)
      .to($('.loader-in',el),{opacity:0,y:-30,duration:.6,ease:'power3.in'},1.75)
      .to(el,{yPercent:-100,duration:1.1,ease:'expo.inOut'},2)
      .add(function(){done()},2.15);
  }
  /* botoes magneticos + cursor */
  function pointer(){
    if(!fine)return;
    $$('.btn,.rail-btns button,.wa-float').forEach(function(b){
      var xTo=gsap.quickTo(b,'x',{duration:.6,ease:'power3.out'}),yTo=gsap.quickTo(b,'y',{duration:.6,ease:'power3.out'});
      b.addEventListener('mousemove',function(e){var r=b.getBoundingClientRect();xTo((e.clientX-r.left-r.width/2)*.25);yTo((e.clientY-r.top-r.height/2)*.35)});
      b.addEventListener('mouseleave',function(){xTo(0);yTo(0)});
    });
    var c=d.createElement('div');c.className='cursor';d.body.appendChild(c);
    var cx=gsap.quickTo(c,'x',{duration:.35,ease:'power3.out'}),cy=gsap.quickTo(c,'y',{duration:.35,ease:'power3.out'});
    w.addEventListener('mousemove',function(e){cx(e.clientX);cy(e.clientY);c.classList.add('on')},{passive:true});
    d.addEventListener('mouseleave',function(){c.classList.remove('on')});
    d.addEventListener('mouseover',function(e){var t=e.target.closest&&e.target.closest('a,button,summary');c.classList.toggle('link',!!t)});
  }
  /* transicao entre paginas */
  function transitions(){
    var cur=d.createElement('div');cur.className='curtain';d.body.appendChild(cur);
    d.addEventListener('click',function(e){
      var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;
      var href=a.getAttribute('href')||'';
      if(e.defaultPrevented||e.metaKey||e.ctrlKey||e.shiftKey||a.target==='_blank'||a.hasAttribute('download'))return;
      if(href.charAt(0)==='#'||/^(mailto:|tel:)/.test(href)||a.origin!==w.location.origin)return;
      if(a.pathname===w.location.pathname&&a.hash)return;
      e.preventDefault();
      gsap.fromTo(cur,{yPercent:100},{yPercent:0,duration:.7,ease:'expo.inOut',onComplete:function(){w.location.href=a.href}});
    });
    w.addEventListener('pageshow',function(e){if(e.persisted)gsap.set(cur,{yPercent:100})});
  }
  function innerEntrance(){
    var cur=d.createElement('div');cur.className='curtain';cur.style.transform='translateY(0)';d.body.appendChild(cur);
    gsap.to(cur,{yPercent:-100,duration:1,ease:'expo.inOut',delay:.05,onComplete:function(){cur.remove()}});
  }

  function init(){
    [fades,media,words,counters,marquee,htl,pointer,transitions].forEach(function(fn){try{fn()}catch(e){w.console&&console.warn(e)}});
    if($('[data-hero]'))loader(function(){heroAnim();alerta(3200)});
    else{innerEntrance();alerta(2500)}
    w.addEventListener('load',function(){ScrollTrigger.refresh()});
  }
  if(d.fonts&&d.fonts.ready)d.fonts.ready.then(init);else init();
})();
