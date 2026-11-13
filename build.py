#!/usr/bin/env python3
"""Gerador do site Luiz Fernando Neves Advocacia.

Le content/*.json (editavel pelo painel /admin), aplica os templates abaixo e
escreve o site pronto em dist/. Usa so a biblioteca padrao do Python.
Uso: python3 build.py
"""
import json, os, re, html, shutil, hashlib, datetime, urllib.parse, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, 'dist')
TODAY = datetime.date.today().isoformat()


def load(p):
    with open(os.path.join(ROOT, p), encoding='utf-8') as f:
        return json.load(f)


def load_dir(d):
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, d, '*.json'))):
        with open(f, encoding='utf-8') as fh:
            out.append(json.load(fh))
    return sorted(out, key=lambda x: (x.get('ordem', 999), x.get('titulo', '')))


S = load('content/configuracoes.json')
HM = load('content/home.json')
OF = load('content/escritorio.json')
FAQ = load('content/faq.json')['itens']
REV = load('content/avaliacoes.json')
PRIV = load('content/privacidade.json')
ARTS = load_dir('content/artigos')
ARTS.sort(key=lambda a: (a.get('data', ''), -a.get('ordem', 0)), reverse=True)
AREAS = load_dir('content/areas')
PUBS = load_dir('content/publicos')
try:
    DIMS = load('content/_imagens.json')
except Exception:
    DIMS = {}

BASE = S['dominio'].rstrip('/')
NOME = S['nome']
CATEGORIA_AREA = {
    'plano-de-saude-e-saude-suplementar': 'Plano de saúde',
    'direito-a-saude': 'Plano de saúde',
    'direito-medico': 'Direito Médico',
    'direito-odontologico': 'Direito Odontológico',
    'erro-medico-odontologico-e-veterinario': 'Erro veterinário',
    'consultoria-juridica-preventiva': 'Direito Médico',
}
ESCAPE = html.escape


def h(s):
    return ESCAPE(str(s), quote=True)


def slug_path(*parts):
    return '/' + '/'.join(p.strip('/') for p in parts if p) + '/'


def abs_url(path):
    return BASE + path


def wa(msg=None):
    msg = msg or S['mensagem_whatsapp']
    return 'https://wa.me/%s?text=%s' % (S['whatsapp'], urllib.parse.quote(msg))


def tel_href():
    return 'tel:+' + S['whatsapp']


def img_tag(src, alt, cls='', eager=False, sizes=None):
    if not src:
        return ''
    dims = DIMS.get(src)
    wh = ' width="%d" height="%d"' % tuple(dims) if dims else ''
    load = ' fetchpriority="high"' if eager else ' loading="lazy" decoding="async"'
    sz = ' sizes="%s"' % sizes if sizes else ''
    c = ' class="%s"' % cls if cls else ''
    return '<img src="%s" alt="%s"%s%s%s%s>' % (h(src), h(alt), wh, c, load, sz)


# ---------- markdown minimo ----------
def inline(t):
    t = h(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), t)
    return t


def md(text):
    out = []
    blocks = re.split(r'\n\s*\n', text.strip())
    i = 0
    for b in blocks:
        lines = [l for l in b.split('\n') if l.strip()]
        if not lines:
            continue
        if all(l.startswith('- ') for l in lines):
            out.append('<ul>' + ''.join('<li>%s</li>' % inline(l[2:]) for l in lines) + '</ul>')
        elif all(re.match(r'^\d+\.\s', l) for l in lines):
            out.append('<ol>' + ''.join('<li>%s</li>' % inline(re.sub(r'^\d+\.\s', '', l)) for l in lines) + '</ol>')
        elif lines[0].startswith('### '):
            out.append('<h3>%s</h3>' % inline(lines[0][4:]))
        elif lines[0].startswith('## '):
            out.append('<h2>%s</h2>' % inline(lines[0][3:]))
            rest = '\n'.join(lines[1:])
            if rest.strip():
                out.append(md(rest))
        else:
            out.append('<p>%s</p>' % inline(' '.join(lines)))
    return '\n'.join(out)


def plain(text):
    t = re.sub(r'^#+\s*', '', text, flags=re.M)
    t = re.sub(r'^- ', '', t, flags=re.M)
    t = re.sub(r'\*\*?([^*]+)\*\*?', r'\1', t)
    return t


def cut(s, n):
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) <= n:
        return s
    return s[:n - 1].rsplit(' ', 1)[0].rstrip(',;:.') + '…'


def fmt_date(iso):
    meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    try:
        d = datetime.date.fromisoformat(iso)
        return '%d de %s de %d' % (d.day, meses[d.month - 1], d.year)
    except Exception:
        return iso


# ---------- assets com hash ----------
def prepare_assets():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    shutil.copytree(os.path.join(ROOT, 'static'), DIST)
    out = {}
    for kind, ext in (('css', 'css'), ('js', 'js')):
        src = os.path.join(DIST, 'assets', kind, 'site.' + ext)
        with open(src, 'rb') as f:
            data = f.read()
        hh = hashlib.md5(data).hexdigest()[:8]
        dst = os.path.join(DIST, 'assets', kind, 'site.%s.%s' % (hh, ext))
        os.rename(src, dst)
        out[kind] = '/assets/%s/site.%s.%s' % (kind, hh, ext)
    return out


ASSET = {}
PAGES = []  # (path, priority, changefreq, lastmod)


NOWIDOW = re.compile(r'(<(?:p|li|h1|h2|h3|summary|figcaption)(?: [^>]*)?>)([^<]*?\S)[ ]+([^\s<]+)(</(?:p|li|h1|h2|h3|summary|figcaption)>)')


def write(path, content):
    if path.endswith('.html') or path.endswith('/'):
        content = NOWIDOW.sub(lambda m: m.group(1) + m.group(2) + '&nbsp;' + m.group(3) + m.group(4), content)
    full = os.path.join(DIST, path.lstrip('/'))
    if full.endswith('/'):
        full = os.path.join(full, 'index.html')
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)


# ---------- logos ----------
def logo(variant='verde', cls='logo'):
    return '<img class="%s" src="/assets/logo/logo-%s.svg" alt="%s" width="196" height="99">' % (cls, variant, h(NOME))


# ---------- JSON-LD ----------
def jld(obj):
    return '<script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def org_node():
    node = {
        '@type': ['LegalService', 'Organization'],
        '@id': BASE + '/#organizacao',
        'name': NOME,
        'url': BASE + '/',
        'logo': {'@type': 'ImageObject', 'url': BASE + '/assets/logo/logo-verde.svg'},
        'image': BASE + '/assets/img/og-default.jpg',
        'description': 'Advocacia especializada em Direito da Saúde: orientação jurídica a médicos, dentistas e profissionais da saúde e defesa de pacientes e beneficiários de planos de saúde.',
        'telephone': '+' + S['whatsapp'],
        'email': S['email'],
        'areaServed': {'@type': 'Country', 'name': 'Brasil'},
        'knowsLanguage': 'pt-BR',
        'founder': {'@id': BASE + '/#advogado'},
        'employee': {'@id': BASE + '/#advogado'},
        'priceRange': '$$',
        'hasOfferCatalog': {
            '@type': 'OfferCatalog', 'name': 'Áreas de atuação',
            'itemListElement': [
                {'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': a['titulo'], 'url': abs_url(slug_path('areas-de-atuacao', a['slug']))}} for a in AREAS]},
    }
    del node['priceRange']
    same = [u for u in (S.get('instagram_url'), S.get('linkedin_url'), S.get('facebook_url'), S.get('google_avaliacoes_url')) if u]
    if same:
        node['sameAs'] = same
    if S.get('endereco_cidade'):
        node['address'] = {'@type': 'PostalAddress', 'streetAddress': S.get('endereco_rua', ''), 'addressLocality': S['endereco_cidade'], 'addressRegion': S.get('endereco_uf', ''), 'postalCode': S.get('endereco_cep', ''), 'addressCountry': 'BR'}
    notas = [r for r in REV.get('itens', []) if r.get('nota')]
    if notas:
        media = sum(float(r['nota']) for r in notas) / len(notas)
        node['aggregateRating'] = {'@type': 'AggregateRating', 'ratingValue': round(media, 1), 'reviewCount': len(notas), 'bestRating': 5}
    return node


def person_node():
    return {
        '@type': 'Person', '@id': BASE + '/#advogado',
        'name': S['advogado'], 'jobTitle': 'Advogado',
        'description': 'Advogado inscrito na OAB/%s, com atuação em Direito da Saúde.' % S['oab_uf'],
        'worksFor': {'@id': BASE + '/#organizacao'},
        'url': BASE + '/o-escritorio/',
        'image': BASE + '/assets/img/luiz-fernando-neves-hero.webp',
        'knowsAbout': ['Direito da Saúde', 'Planos de saúde', 'Direito Médico', 'Direito Odontológico', 'Direito do Consumidor', 'Direito Civil'],
        'knowsLanguage': 'pt-BR',
        'sameAs': [u for u in (S.get('instagram_url'), S.get('linkedin_url')) if u],
    }


def breadcrumb(items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': abs_url(p)} for i, (n, p) in enumerate(items)]}


# ---------- layout ----------
NAV = [('O escritório', '/o-escritorio/'), ('Áreas de atuação', '/areas-de-atuacao/'), ('Para quem atuamos', '/para-quem-atuamos/'), ('Conteúdo', '/conteudo/'), ('Contato', '/contato/')]


def header(active=''):
    def link(n, p, drop=None):
        cur = ' aria-current="page"' if active == p else ''
        if drop:
            items = ''.join('<li><a href="%s">%s</a></li>' % (u, h(t)) for t, u in drop)
            return '<li class="has-sub"><a href="%s"%s>%s</a><button class="sub-toggle" aria-label="Abrir submenu de %s" aria-expanded="false"><span></span></button><ul class="sub">%s</ul></li>' % (p, cur, h(n), h(n), items)
        return '<li><a href="%s"%s>%s</a></li>' % (p, cur, h(n))
    areas = [(a['titulo_curto'], slug_path('areas-de-atuacao', a['slug'])) for a in AREAS]
    pubs = [(p['titulo_curto'], slug_path('para-quem-atuamos', p['slug'])) for p in PUBS]
    lis = ''
    for n, p in NAV:
        lis += link(n, p, areas if p == '/areas-de-atuacao/' else pubs if p == '/para-quem-atuamos/' else None)
    return '''<a class="skip" href="#conteudo-principal">Ir para o conteúdo</a>
<header class="site-header" id="topo" data-header>
  <div class="wrap header-in">
    <a class="brand" href="/" aria-label="%(nome)s, página inicial">%(logo)s<img class="logo logo-light" src="/assets/logo/logo-claro.svg" alt="" aria-hidden="true" width="196" height="99"></a>
    <nav class="main-nav" id="menu" aria-label="Menu principal"><ul>%(lis)s</ul>
      <a class="btn btn-solid nav-cta" href="%(wa)s" data-wa="header" rel="noopener" target="_blank">Fale agora</a>
    </nav>
    <button class="burger" aria-label="Abrir menu" aria-controls="menu" aria-expanded="false"><span></span><span></span></button>
  </div>
</header>''' % dict(nome=h(NOME), logo=logo('verde'), lis=lis, wa=h(wa()))


def footer():
    areas = ''.join('<li><a href="%s">%s</a></li>' % (slug_path('areas-de-atuacao', a['slug']), h(a['titulo_curto'])) for a in AREAS)
    end = ''
    if S.get('endereco_cidade'):
        end = '<li>%s</li>' % h(', '.join(x for x in (S.get('endereco_rua'), S.get('endereco_cidade'), S.get('endereco_uf')) if x))
    oab = 'OAB/%s%s' % (S['oab_uf'], (' ' + S['oab_numero']) if S.get('oab_numero') else '')
    soc = ''
    if S.get('instagram_url'):
        soc += '<li><a href="%s" target="_blank" rel="noopener me">Instagram %s</a></li>' % (h(S['instagram_url']), h(S.get('instagram_usuario', '')))
    if S.get('linkedin_url'):
        soc += '<li><a href="%s" target="_blank" rel="noopener me">LinkedIn</a></li>' % h(S['linkedin_url'])
    return '''<footer class="site-footer">
  <div class="wrap foot-grid">
    <div class="foot-brand">%(logo)s
      <p>Advocacia especializada em Direito da Saúde, com rigor técnico, análise estratégica e atendimento individualizado.</p>
      <p class="oab">Luiz Fernando Neves, %(oab)s</p>
    </div>
    <nav aria-label="Páginas do site"><h2>Navegue</h2><ul>
      <li><a href="/o-escritorio/">O escritório</a></li><li><a href="/areas-de-atuacao/">Áreas de atuação</a></li><li><a href="/para-quem-atuamos/">Para quem atuamos</a></li><li><a href="/conteudo/">Notícias e artigos</a></li><li><a href="/contato/">Contato</a></li></ul></nav>
    <nav aria-label="Áreas de atuação"><h2>Áreas de atuação</h2><ul>%(areas)s</ul></nav>
    <div><h2>Contato</h2><ul>
      <li><a href="%(wa)s" target="_blank" rel="noopener" data-wa="footer">WhatsApp %(tel)s</a></li>
      <li><a href="mailto:%(email)s">%(email)s</a></li>%(soc)s%(end)s</ul></div>
  </div>
  <div class="wrap foot-legal">
    <p>%(aviso)s</p>
    <p class="foot-line"><span>© %(ano)s %(nome)s. Todos os direitos reservados.</span> <a href="/politica-de-privacidade/">Política de privacidade</a> <a class="credit" href="https://maltabusiness.com.br/" target="_blank" rel="noopener">Desenvolvido por Malta Business</a></p>
  </div>
</footer>
<a class="wa-float" href="%(wa)s" target="_blank" rel="noopener" data-wa="flutuante" aria-label="Falar pelo WhatsApp"><svg viewBox="0 0 32 32" aria-hidden="true"><path fill="currentColor" d="M16 3C9.4 3 4 8.3 4 14.9c0 2.3.7 4.5 1.9 6.4L4 29l7.9-2c1.8 1 3.9 1.5 6.1 1.5 6.600 0 12-5.300 12-11.900S22.600 3 16 3Zm0 21.800c-1.900 0-3.800-.5-5.400-1.500l-.4-.2-4.600 1.200 1.200-4.500-.3-.5a9.600 9.600 0 0 1-1.500-5c0-5.400 4.400-9.800 10-9.800s10 4.400 10 9.800-4.500 10.500-9 10.500Zm5.400-7.300c-.3-.2-1.800-.9-2-1s-.5-.2-.7.200-.8 1-1 1.200-.4.200-.7.100a8 8 0 0 1-4-3.500c-.3-.5.300-.5.900-1.600.1-.2 0-.4 0-.5l-.9-2.200c-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.100-.8.400s-1 1-1 2.400 1 2.800 1.200 3c.1.200 2 3.100 4.900 4.300 1.800.8 2.500.8 3.400.7.5-.1 1.800-.7 2-1.400s.2-1.300.2-1.400c-.1-.2-.3-.2-.6-.4Z"/></svg></a>''' % dict(
        logo=logo('claro'), oab=h(oab), areas=areas, wa=h(wa()), tel=h(S['telefone']), email=h(S['email']), soc=soc, end=end,
        aviso=h(S['aviso_legal']), ano=datetime.date.today().year, nome=h(NOME))


def alert_dialog():
    if not HM.get('alerta_ativo'):
        return ''
    return '''<dialog class="alerta" id="alerta-golpe" aria-labelledby="alerta-t">
  <form method="dialog">
    <p class="alerta-tag">Aviso importante</p>
    <h2 id="alerta-t">%s</h2>
    <p>%s</p>
    <p class="alerta-canais">Canais oficiais: <a href="%s" target="_blank" rel="noopener">WhatsApp %s</a> e <a href="mailto:%s">%s</a></p>
    <button class="btn btn-solid" value="ok" autofocus>Entendi</button>
  </form>
</dialog>''' % (h(HM['alerta_titulo']), h(HM['alerta_texto']), h(wa()), h(S['telefone']), h(S['email']), h(S['email']))


def tracking_head():
    parts = ['<!-- Rastreamento: preencha gtm_id, meta_pixel_id e ga4_id no painel /admin (Configurações do site). Sem valor, nada é carregado. -->']
    if S.get('gtm_id'):
        parts.append("<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','%s');</script>" % h(S['gtm_id']))
    else:
        parts.append('<script>window.dataLayer=window.dataLayer||[];</script>')
    if S.get('ga4_id') and not S.get('gtm_id'):
        parts.append('<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script><script>function gtag(){dataLayer.push(arguments)}gtag("js",new Date());gtag("config","%s");</script>' % (h(S['ga4_id']), h(S['ga4_id'])))
    if S.get('meta_pixel_id') and not S.get('gtm_id'):
        parts.append("<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src='https://connect.facebook.net/en_US/fbevents.js';s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script');fbq('init','%s');fbq('track','PageView');</script>" % h(S['meta_pixel_id']))
    if S.get('verificacao_google'):
        parts.append('<meta name="google-site-verification" content="%s">' % h(S['verificacao_google']))
    return '\n'.join(parts)


def page(path, title, desc, body, active='', schema=None, og_image=None, og_type='website', robots='index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1', preload=None, lastmod=None, prio='0.7', freq='monthly', sitemap=True, extra_head=''):
    canon = abs_url(path)
    og_image = og_image or '/assets/img/og-default.jpg'
    graph = [org_node(), person_node(), {'@type': 'WebSite', '@id': BASE + '/#site', 'url': BASE + '/', 'name': NOME, 'inLanguage': 'pt-BR', 'publisher': {'@id': BASE + '/#organizacao'}}]
    graph += schema or []
    ld = jld({'@context': 'https://schema.org', '@graph': graph})
    pre = ''
    if preload:
        pre = '<link rel="preload" as="image" href="%s" fetchpriority="high"%s>' % (preload[0], (' media="%s"' % preload[1]) if len(preload) > 1 else '')
    gtm_ns = ('<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=%s" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>' % h(S['gtm_id'])) if S.get('gtm_id') else ''
    html_ = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<meta name="robots" content="%(robots)s">
<meta name="author" content="%(adv)s">
<meta name="theme-color" content="#28583F">
<link rel="canonical" href="%(canon)s">
<link rel="alternate" hreflang="pt-BR" href="%(canon)s">
<link rel="alternate" type="application/rss+xml" title="%(nome)s, notícias e artigos" href="/feed.xml">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/img/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="%(nome)s">
<meta property="og:type" content="%(ogtype)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(canon)s">
<meta property="og:image" content="%(ogimg)s">
<meta property="og:image:alt" content="%(nome)s">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title)s">
<meta name="twitter:description" content="%(desc)s">
<meta name="twitter:image" content="%(ogimg)s">
<link rel="preload" href="/assets/fonts/poppins-latin-500-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/inter-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
%(pre)s
<link rel="stylesheet" href="%(css)s">
%(extra)s
%(track)s
%(ld)s
</head>
<body class="%(bodycls)s">
%(gtmns)s
%(header)s
<main id="conteudo-principal">
%(body)s
</main>
%(footer)s
%(alert)s
<script src="/assets/js/vendor/gsap.min.js" defer></script>
<script src="/assets/js/vendor/ScrollTrigger.min.js" defer></script>
<script src="/assets/js/vendor/SplitText.min.js" defer></script>
<script src="/assets/js/vendor/lenis.min.js" defer></script>
<script src="%(js)s" defer></script>
<!-- [SLOT] Outros scripts de terceiros (chat, heatmap etc.) entram aqui, antes do </body>. -->
</body>
</html>
''' % dict(title=h(title), desc=h(desc), robots=robots, adv=h(S['advogado']), canon=canon, nome=h(NOME), ogtype=og_type,
           ogimg=abs_url(og_image), pre=pre, css=ASSET['css'], extra=extra_head, track=tracking_head(), ld=ld, gtmns=gtm_ns,
           header=header(active), body=body, footer=footer(), alert=alert_dialog() if path == '/' else '', js=ASSET['js'], bodycls='home' if path == '/' else 'inner')
    write(path, html_)
    if sitemap:
        PAGES.append((path, prio, freq, lastmod or TODAY))


# ---------- blocos reutilizaveis ----------
CAT_COR = {'Plano de saúde': 'verde', 'Direito Médico': 'verde', 'Direito Odontológico': 'verde', 'Erro veterinário': 'azul', 'Direito do Consumidor': 'azul'}
ARROW = '<svg class="ico-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>'
ARROW_L = '<svg class="ico-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 12H5m6-6-6 6 6 6" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>'
_MONO = None


def mono(cls='mono-anim'):
    """Monograma inline (as faixas diagonais da marca), animavel por CSS."""
    global _MONO
    if _MONO is None:
        raw = open(os.path.join(ROOT, 'static/assets/logo/monograma-verde.svg'), encoding='utf-8').read()
        _MONO = re.findall(r'<path[^>]*/>', raw)
    paths = ''.join(p.replace('<path ', '<path style="--k:%d" ' % i) for i, p in enumerate(_MONO))
    return '<svg class="%s" viewBox="190 195 1430 340" aria-hidden="true" focusable="false">%s</svg>' % (cls, paths)


def split_title(text, tag='h2', cls=''):
    words = h(text).split(' ')
    parts = ['<span class="w"><span style="--i:%d">%s</span></span>' % (i, w) for i, w in enumerate(words)]
    if len(parts) > 2:
        parts = parts[:-2] + ['<span class="nw">%s %s</span>' % (parts[-2], parts[-1])]
    inner = ' '.join(parts)
    return '<%s class="split %s" aria-label="%s"><span aria-hidden="true">%s</span></%s>' % (tag, cls, h(text), inner, tag)


def page_hero(eyebrow, title, lead=None, crumbs=None, cor='verde', image=None, image_alt=''):
    bc = ''
    if crumbs:
        bc = '<nav class="crumbs" aria-label="Você está em"><ol>%s</ol></nav>' % ''.join(
            '<li>%s</li>' % ('<a href="%s">%s</a>' % (p, h(n)) if p else '<span aria-current="page">%s</span>' % h(n)) for n, p in crumbs)
    fig = ''
    if image:
        fig = '<figure class="ph-fig"><div class="ph-media" data-reveal><div class="pin-in" data-speed="-0.08">%s</div></div><span class="ph-frame" aria-hidden="true"></span></figure>' % img_tag(image, image_alt or title, eager=True, sizes='(max-width:900px) 92vw, 520px')
    return '''<section class="page-hero t-%s%s">
  <div class="stripes" aria-hidden="true"></div>%s
  <div class="wrap ph-in">
    <div class="ph-copy">%s
      <p class="eyebrow">%s</p>
      %s%s
    </div>%s
  </div>
</section>''' % (cor, ' has-img' if image else '', mono('mono-anim ph-mono'), bc, h(eyebrow), split_title(title, 'h1', 'display'), ('<p class="lead fade-in">%s</p>' % h(lead)) if lead else '', fig)


def cta_band(titulo=None, texto=None, msg=None, cor='verde'):
    titulo = titulo or HM['cta_titulo']
    texto = texto or HM['cta_texto']
    return '''<section class="cta-band t-%s">
  <div class="cta-bg" aria-hidden="true">%s</div>%s
  <div class="wrap cta-in">
    <div class="reveal"><p class="eyebrow">Atendimento individualizado</p>%s<p>%s</p></div>
    <div class="cta-btns reveal"><a class="btn btn-bronze" href="%s" target="_blank" rel="noopener" data-wa="faixa-cta">Agendar pelo WhatsApp %s</a><a class="btn btn-line" href="/contato/">Enviar mensagem</a></div>
  </div>
</section>''' % (cor, img_tag('/assets/img/luiz-fernando-neves-escritorio.webp', '', sizes='100vw'), mono('mono-anim cta-mono'), split_title(titulo, 'h2', 'display'), h(texto), h(wa(msg)), ARROW)


def cta_inline(texto, msg=None, label='wa'):
    return '<p class="cta-inline"><a href="%s" target="_blank" rel="noopener" data-wa="%s"><span>%s</span> %s</a></p>' % (h(wa(msg)), label, h(texto), ARROW)


def article_card(a, extra=''):
    url = slug_path('conteudo', a['slug'])
    cor = CAT_COR.get(a['categoria'], 'verde')
    if a.get('imagem'):
        im = '<div class="card-img">%s</div>' % img_tag(a['imagem'], a['titulo'], sizes='(max-width:700px) 84vw, 380px')
    else:
        im = '<div class="card-img card-img-mono">%s</div>' % mono('mono-static')
    return '''<article class="card t-%s reveal"%s>
  <a class="card-link" href="%s">%s
  <div class="card-body"><p class="tag"><i aria-hidden="true"></i>%s</p><h3>%s</h3><p>%s</p><span class="more">Ler artigo %s</span></div></a>
</article>''' % (cor, extra, url, im, h(a['categoria']), h(a['titulo']), h(cut(a['resumo'], 140)), ARROW)


def rail(cards, label, rid=''):
    return '''<div class="rail-wrap"><div class="rail"%s tabindex="0" aria-label="%s, role para o lado">%s</div>
<div class="rail-bar"><div class="rail-line"><i></i></div><div class="rail-btns"><button class="rail-prev" aria-label="Anterior" disabled>%s</button><button class="rail-next" aria-label="Próximo">%s</button></div></div></div>''' % ((' id="%s"' % rid) if rid else '', h(label), cards, ARROW_L, ARROW)


def legend():
    return '<div class="legend"><span class="lg t-verde"><i></i>Saúde</span><span class="lg t-azul"><i></i>Civil e consumidor</span></div>'


def image_ribbon():
    items = ''
    for a in [x for x in ARTS if x.get('imagem')]:
        items += '<a class="rb t-%s" href="%s">%s<span><em>%s</em>%s</span></a>' % (CAT_COR.get(a['categoria'], 'verde'), slug_path('conteudo', a['slug']), img_tag(a['imagem'], '', sizes='320px'), h(a['categoria']), h(cut(a['titulo'], 60)))
    return '<section class="ribbon" data-marquee aria-label="Temas em destaque"><div class="mq-track rb-track">%s%s</div></section>' % (items, items.replace('<a class', '<a tabindex="-1" aria-hidden="true" class'))


def badge(text):
    return '''<svg class="badge" viewBox="0 0 200 200" aria-hidden="true"><defs><path id="bcirc" d="M100,100 m-78,0 a78,78 0 1,1 156,0 a78,78 0 1,1 -156,0"/></defs><text><textPath href="#bcirc" textLength="485">%s</textPath></text></svg>''' % h(text)


# ---------- paginas ----------
def build_home():
    g = HM.get('hero_galeria') or []
    gal = ''.join('<figure class="hg hg-%d">%s</figure>' % (i + 1, img_tag(src, '', sizes='240px')) for i, src in enumerate(g[:3]))
    dest = HM.get('destaques') or []
    ds = [a for s in dest for a in ARTS if a['slug'] == s] or ARTS[:4]
    slides = ''
    for i, a in enumerate(ds):
        slides += '<a class="slide%s" href="%s" %s><span class="tag">%s</span><span class="slide-t">%s</span></a>' % (
            ' is-on' if i == 0 else '', slug_path('conteudo', a['slug']), '' if i == 0 else 'tabindex="-1" aria-hidden="true"', h(a['categoria']), h(a['titulo']))
    dots = ''.join('<button class="dot%s" aria-label="Notícia %d" %s></button>' % (' is-on' if i == 0 else '', i + 1, 'aria-current="true"' if i == 0 else '') for i in range(len(ds)))
    g = ['/assets/img/plano-saude-idosos.webp', '/assets/img/direito-odontologico.webp', '/assets/img/home-care.webp']
    gal = ''.join('<figure class="hg hg-%d">%s</figure>' % (i + 1, img_tag(src, '', eager=True, sizes='260px').replace(' fetchpriority="high"', ' decoding="async"')) for i, src in enumerate(g))
    dest = HM.get('destaques') or []
    ds = [a for s in dest for a in ARTS if a['slug'] == s] or ARTS[:4]
    slides = ''
    for i, a in enumerate(ds):
        slides += '<a class="slide%s" href="%s" %s><span class="tag">%s</span><span class="slide-t">%s</span></a>' % (
            ' is-on' if i == 0 else '', slug_path('conteudo', a['slug']), '' if i == 0 else 'tabindex="-1" aria-hidden="true"', h(a['categoria']), h(a['titulo']))
    dots = ''.join('<button class="dot%s" aria-label="Notícia %d" %s></button>' % (' is-on' if i == 0 else '', i + 1, 'aria-current="true"' if i == 0 else '') for i in range(len(ds)))
    hero = '''<section class="hero" data-hero>
  <div class="stripes" aria-hidden="true"></div>
  <div class="wrap hero-in">
    <div class="hero-copy">
      <p class="eyebrow fade-in">%(eb)s</p>
      %(t)s
      <p class="lead fade-in" style="--d:.7s">%(x)s</p>
      <div class="hero-cta fade-in" style="--d:.9s"><a class="btn btn-solid" href="%(wa)s" target="_blank" rel="noopener" data-wa="hero">%(c1)s %(arr)s</a><a class="btn btn-ghost" href="/areas-de-atuacao/">%(c2)s</a></div>
      <div class="hero-legend fade-in" style="--d:1.1s">%(lg)s</div>
    </div>
    <div class="hero-visual">
      %(mono)s
      <figure class="hero-photo"><picture><source media="(max-width:760px)" srcset="/assets/img/luiz-fernando-neves-hero-m.webp"><img src="/assets/img/luiz-fernando-neves-hero.webp" width="1600" height="1067" fetchpriority="high" alt="Luiz Fernando Neves, advogado de Direito da Saúde, em seu escritório"></picture></figure>
      %(gal)s
      %(badge)s
      <div class="news" aria-label="Notícias e artigos em destaque" data-carousel>
        <p class="news-h">Notícias e artigos</p>
        <div class="slides" aria-live="polite">%(slides)s</div>
        <div class="news-ctl"><div class="dots">%(dots)s</div><div class="arrows"><button class="prev" aria-label="Anterior">%(arrl)s</button><button class="next" aria-label="Próxima">%(arr)s</button></div></div>
      </div>
    </div>
  </div>
</section>''' % dict(eb=h(HM['hero_eyebrow']), t=split_title(HM['hero_titulo'], 'h1', 'display hero-t'), x=h(HM['hero_texto']), wa=h(wa()), c1=h(HM['hero_cta_principal']), c2=h(HM['hero_cta_secundario']),
                     arr=ARROW, arrl=ARROW_L, lg=legend(), mono=mono('mono-anim hero-mono'), gal=gal, badge=badge('Direito da Saúde · OAB/%s · Luiz Fernando Neves · ' % S['oab_uf']), slides=slides, dots=dots)
    statement = '''<section class="statement-sec">%s<div class="wrap">
  <p class="statement" data-words>%s</p>
  <ul class="counters"><li><span class="num" data-count="%d">%d</span><span class="num-l">áreas de atuação</span></li><li><span class="num" data-count="%d">%d</span><span class="num-l">frentes de atendimento</span></li><li><span class="num" data-count="%d">%d</span><span class="num-l">artigos publicados</span></li><li><span class="num">OAB/%s</span><span class="num-l">advogado regularmente inscrito</span></li></ul>
</div></section>''' % (mono('mono-anim st-mono'), h(HM.get('statement', OF['principios'][1])), len(AREAS), len(AREAS), len(PUBS), len(PUBS), len(ARTS), len(ARTS), h(S['oab_uf']))
    mq_items = ''.join('<span class="t-%s">%s</span>' % (a['cor'], h(a['titulo_curto'])) for a in AREAS)
    mq = '<div class="marquee" data-marquee aria-hidden="true"><div class="mq-track">%s%s</div></div>' % (mq_items, mq_items)
    _nums_unused = '''<section class="nums"><div class="wrap nums-in">
  <div class="num reveal"><strong data-count="%d">0</strong><span>áreas de atuação</span></div>
  <div class="num reveal"><strong data-count="%d">0</strong><span>frentes de atendimento</span></div>
  <div class="num reveal"><strong data-count="%d">0</strong><span>artigos publicados</span></div>
  <div class="num reveal"><strong>OAB/%s</strong><span>advogado inscrito</span></div>
</div></section>''' % (len(AREAS), len(PUBS), len(ARTS), h(S['oab_uf']))
    pubs = ''
    for i, p in enumerate(PUBS):
        pubs += '''<a class="pub t-%s reveal" href="%s">%s<span class="pub-shade"></span><span class="pub-n">0%d</span><span class="pub-c"><span class="pub-k">%s</span><h3>%s</h3><p>%s</p><span class="more">Saiba mais %s</span></span></a>''' % (
            p['cor'], slug_path('para-quem-atuamos', p['slug']), img_tag(p.get('imagem'), '', sizes='(max-width:900px) 92vw, 400px'), i + 1, 'Saúde' if p['cor'] == 'verde' else 'Civil e consumidor', h(p['titulo_curto']), h(p['resumo']), ARROW)
    publicos = '''<section class="sec" id="para-quem-atuamos"><div class="wrap">
  <header class="sec-h row"><div><p class="eyebrow reveal">Atendimento</p>%s</div><p class="reveal">%s</p></header>
  <div class="pubs">%s</div></div></section>''' % (split_title(HM['publicos_titulo'], 'h2', 'display'), h(HM['publicos_texto']), pubs)
    rows = ''
    for a in AREAS:
        rows += '<li class="reveal t-%s"><a href="%s"><span class="row-n">%s</span><span class="row-t"><strong>%s</strong><em>%s</em></span><span class="row-a">%s</span></a></li>' % (
            a['cor'], slug_path('areas-de-atuacao', a['slug']), h(a['numero']), h(a['titulo_curto']), h(a['subtitulo']), ARROW)
    areas = '''<section class="sec sec-sand" id="areas"><div class="wrap areas-grid">
  <header class="sec-h sticky"><p class="eyebrow reveal">O que fazemos</p>%s<p class="reveal">%s</p>%s<a class="btn btn-ghost reveal" href="/areas-de-atuacao/">Ver todas as áreas %s</a></header>
  <ol class="rows">%s</ol></div></section>''' % (split_title(HM['areas_titulo'], 'h2', 'display'), h(HM['areas_texto']), legend(), ARROW, rows)
    tl = ''.join('<li class="tl-h t-%s"><span class="tl-y">%s</span><span class="tl-p">%s</span><strong>%s</strong><em>%s</em></li>' % (t['cor'], h(t['ano']), h(t['periodo']), h(t['titulo']), h(t['instituicao'])) for t in OF['linha_do_tempo'])
    escr = '''<section class="sec escr"><div class="wrap escr-grid">
  <figure class="escr-fig"><div class="escr-img" data-reveal><div class="pin-in" data-speed="-0.1">%s</div></div>%s</figure>
  <div class="escr-copy"><p class="eyebrow reveal">O escritório</p>%s
  <p class="reveal">%s</p><p class="reveal">%s</p>
  <a class="btn btn-solid reveal" href="/o-escritorio/">Conheça o escritório %s</a></div></div>
</section>''' % (
        img_tag('/assets/img/luiz-fernando-neves-escritorio.webp', 'Luiz Fernando Neves em sua mesa de trabalho, com livros de Direito Médico', sizes='(max-width:900px) 92vw, 560px'),
        badge('Rigor técnico · Estratégia · Proximidade · '), split_title('Rigor técnico e atendimento próximo a quem cuida e a quem precisa de cuidados', 'h2', 'display'),
        h(OF['texto'][0]), h(OF['texto'][1]), ARROW)
    passos = ''.join('<li class="reveal"><span class="step-n">0%d</span><h3>%s</h3><p>%s</p></li>' % (i + 1, h(p['titulo']), h(p['texto'])) for i, p in enumerate(HM['metodo_passos']))
    metodo = '''<section class="sec sec-verde">%s<div class="wrap"><header class="sec-h"><p class="eyebrow reveal">Como trabalhamos</p>%s</header><ol class="steps">%s</ol></div></section>''' % (mono('mono-anim metodo-mono'), split_title(HM['metodo_titulo'], 'h2', 'display'), passos)
    cards = ''.join(article_card(a) for a in ARTS)
    conteudo = '''<section class="sec"><div class="wrap"><header class="sec-h row"><div><p class="eyebrow reveal">Conteúdo</p>%s<p class="reveal">%s</p></div><a class="btn btn-ghost reveal" href="/conteudo/">Todos os artigos %s</a></header>%s</div></section>''' % (
        split_title(HM['conteudo_titulo'], 'h2', 'display'), h(HM['conteudo_texto']), ARROW, rail(cards, 'Artigos'))
    rev = ''
    if REV.get('itens'):
        rv = ''.join('<figure class="rev reveal"><div class="stars" role="img" aria-label="%s de 5 estrelas">%s</div><blockquote>%s</blockquote><figcaption>%s</figcaption></figure>' % (h(r.get('nota', 5)), '★' * int(float(r.get('nota', 5))), h(r['texto']), h(r['autor'])) for r in REV['itens'])
        link = ('<a class="btn btn-ghost" href="%s" target="_blank" rel="noopener">Ver avaliações no Google</a>' % h(S['google_avaliacoes_url'])) if S.get('google_avaliacoes_url') else ''
        rev = '<section class="sec sec-sand"><div class="wrap"><header class="sec-h"><p class="eyebrow">Google</p>%s<p>%s</p></header>%s%s</div></section>' % (split_title(REV['titulo'], 'h2', 'display'), h(REV['texto']), rail(rv, 'Avaliações'), link)
    body = hero + statement + publicos + mq + areas + escr + timeline() + image_ribbon() + metodo + conteudo + rev + faq_section() + cta_band()
    sch = [{'@type': 'WebPage', '@id': BASE + '/#pagina', 'url': BASE + '/', 'name': 'Advogado de Direito da Saúde', 'isPartOf': {'@id': BASE + '/#site'}, 'about': {'@id': BASE + '/#organizacao'}, 'inLanguage': 'pt-BR'}, faq_ld()]
    page('/', 'Advogado de Direito da Saúde | %s' % NOME, 'Advocacia especializada em Direito da Saúde: orientação a médicos, dentistas e profissionais da saúde e defesa de pacientes e beneficiários de planos de saúde.',
         body, schema=sch, preload=('/assets/img/luiz-fernando-neves-hero.webp', '(min-width:761px)'), prio='1.0', freq='weekly')


def faq_section():
    its = ''.join('<details class="reveal"><summary><span class="faq-n">%02d</span><span class="faq-q">%s</span></summary><div class="faq-a"><p>%s</p></div></details>' % (i + 1, h(f['pergunta']), h(f['resposta'])) for i, f in enumerate(FAQ))
    return '<section class="sec sec-faq"><div class="wrap faq-grid"><header class="sec-h sticky"><p class="eyebrow reveal">Dúvidas</p>%s<p class="reveal">Respostas objetivas sobre os temas mais procurados. Cada caso tem particularidades, e a análise individual é indispensável.</p><a class="btn btn-solid reveal" href="%s" target="_blank" rel="noopener" data-wa="faq">Tirar uma dúvida %s</a></header><div class="faq">%s</div></div></section>' % (split_title(HM['faq_titulo'], 'h2', 'display'), h(wa()), ARROW, its)


def faq_ld():
    return {'@type': 'FAQPage', '@id': BASE + '/#faq', 'mainEntity': [{'@type': 'Question', 'name': f['pergunta'], 'acceptedAnswer': {'@type': 'Answer', 'text': f['resposta']}} for f in FAQ]}


def timeline():
    its = ''
    for t in OF['linha_do_tempo']:
        its += '<li class="htl-i t-%s"><span class="htl-y">%s</span><span class="htl-dot" aria-hidden="true"></span><div class="htl-card"><p class="htl-p">%s</p><h3>%s</h3><p class="htl-inst">%s</p></div></li>' % (t['cor'], h(t['ano']), h(t['periodo']), h(t['titulo']), h(t['instituicao']))
    return '''<section class="htl" id="trajetoria" data-htl><div class="htl-pin">
  <div class="htl-head"><p class="eyebrow">Linha do tempo</p><h2 class="display" data-split>%s</h2><p data-fade>%s</p><span class="htl-progress" aria-hidden="true"><i data-htl-bar></i></span><p class="htl-hint" data-fade>Role para percorrer</p></div>
  <p class="htl-swipe" aria-hidden="true"><span class="hand"></span>Arraste para o lado <svg viewBox="0 0 24 24"><path d="M4 12h15m-6-6 6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.5"/></svg></p>
  <div class="htl-wrap"><ol class="htl-track" data-htl-track style="--n:%d">%s</ol></div>
</div></section>''' % (h(OF['linha_titulo']), h(OF['linha_texto']), len(OF['linha_do_tempo']), its)


def build_office():
    o = OF
    forms = ''.join('<div class="form-col reveal"><h3>%s</h3><ul class="checks">%s</ul></div>' % (h(g['titulo']), ''.join('<li>%s</li>' % h(i) for i in g['itens'])) for g in o['formacao'])
    princ = ''.join('<div class="princ reveal"><span class="princ-n">0%d</span><p>%s</p></div>' % (i + 1, h(t)) for i, t in enumerate(o['principios']))
    body = page_hero('O escritório', o['titulo'], o['subtitulo'], [('Início', '/'), ('O escritório', None)], 'verde', '/assets/img/luiz-fernando-neves-hero.webp', 'Luiz Fernando Neves em seu escritório') + '''
<section class="sec"><div class="wrap prose-grid">
  <div class="prose"><p class="eyebrow reveal">Atuação</p>%s%s</div>
  <div class="duo"><figure class="duo-a" data-reveal><div class="pin-in" data-speed="-0.1">%s</div></figure><figure class="duo-b" data-reveal><div class="pin-in" data-speed="-0.14">%s</div></figure>%s%s</div>
</div></section>
<section class="quote-band"><div class="stripes" aria-hidden="true"></div><div class="wrap"><blockquote class="reveal">%s</blockquote><p class="reveal">%s, OAB/%s</p></div></section>
<section class="sec sec-sand adv"><div class="wrap two">
  <header class="sec-h sticky"><p class="eyebrow reveal">Advogado</p>%s<div class="adv-tags reveal"><span class="t-verde">Direito da Saúde</span><span class="t-verde">Direito Médico</span><span class="t-verde">Direito Odontológico</span><span class="t-azul">Processo Civil</span></div></header>
  <div class="prose">%s</div>
</div></section>
%s
<section class="sec sec-sand"><div class="wrap"><header class="sec-h"><p class="eyebrow reveal">Princípios</p>%s</header><div class="princs">%s</div></div></section>
<section class="sec"><div class="wrap"><header class="sec-h"><p class="eyebrow reveal">Atualização constante</p>%s</header><div class="form-cols">%s</div></div></section>''' % (
        split_title('Direito da Saúde, do conflito à prevenção', 'h2', 'display'), ''.join('<p class="reveal">%s</p>' % h(t) for t in o['texto']),
        img_tag('/assets/img/processo-etico-crm.webp', 'Profissional da saúde analisando documentos', sizes='(max-width:900px) 60vw, 340px'), img_tag('/assets/img/plano-saude-idosos.webp', 'Paciente em atendimento médico', sizes='(max-width:900px) 60vw, 300px'), badge('Rigor técnico · Estratégia · Proximidade · '), mono('mono-anim duo-mono'),
        h(o['destaque_frase']), h(S['advogado']), h(S['oab_uf']),
        split_title(o['advogado_titulo'], 'h2', 'display'), ''.join('<p class="reveal">%s</p>' % h(t) for t in o['advogado_texto']),
        timeline(), split_title(o['principios_titulo'], 'h2', 'display'), princ, split_title(o['formacao_titulo'], 'h2', 'display'), forms) + cta_band()
    sch = [{'@type': 'AboutPage', 'url': abs_url('/o-escritorio/'), 'name': o['titulo'], 'about': {'@id': BASE + '/#organizacao'}, 'inLanguage': 'pt-BR'}, breadcrumb([('Início', '/'), ('O escritório', '/o-escritorio/')])]
    page('/o-escritorio/', 'O escritório de Direito da Saúde | Luiz Fernando Neves', 'Conheça o escritório e o advogado Luiz Fernando Neves: atuação em Direito da Saúde, formação em Direito Médico e atendimento individualizado.', body, '/o-escritorio/', sch, og_image='/assets/img/luiz-fernando-neves-hero.webp', prio='0.8')


def side(title, items_html, cor, wa_msg, label):
    return '<aside class="detail-side t-%s"><div class="side-card"><h2 class="h-sm">%s</h2><ul class="side-list">%s</ul></div><div class="side-card side-cta">%s<p>Cada situação é única.</p><a class="btn btn-bronze" href="%s" target="_blank" rel="noopener" data-wa="%s">Agendar consulta %s</a></div></aside>' % (
        cor, h(title), items_html, mono('mono-static side-mono'), h(wa(wa_msg)), label, ARROW)


def build_areas():
    cards = ''
    for a in AREAS:
        its = ''.join('<li>%s</li>' % h(i) for i in a['itens'][:3])
        u = slug_path('areas-de-atuacao', a['slug'])
        cards += '''<article class="area-card t-%s reveal" id="%s"><a class="area-img" href="%s" tabindex="-1" aria-hidden="true">%s</a><div class="area-body"><span class="area-n">%s <i>%s</i></span><h2><a href="%s">%s</a></h2><p class="area-sub">%s</p><ul>%s</ul><a class="more" href="%s">Ver detalhes %s</a></div></article>''' % (
            a['cor'], h(a['slug']), u, img_tag(a.get('imagem'), '', sizes='(max-width:700px) 92vw, 560px'), h(a['numero']), 'Saúde' if a['cor'] == 'verde' else 'Civil e consumidor', u, h(a['titulo_curto']), h(a['subtitulo']), its, u, ARROW)
    body = page_hero('Áreas de atuação', 'Oito frentes de atuação em Direito da Saúde e relações de consumo', 'Da saúde suplementar ao direito civil, cada caso começa pela análise da documentação e termina com uma estratégia clara.', [('Início', '/'), ('Áreas de atuação', None)], 'verde', '/assets/img/plano-saude-negativa.webp') + '<section class="sec"><div class="wrap"><div class="sec-h">%s</div><div class="area-cards">%s</div></div></section>' % (legend(), cards) + cta_band()
    sch = [{'@type': 'CollectionPage', 'url': abs_url('/areas-de-atuacao/'), 'name': 'Áreas de atuação', 'about': {'@id': BASE + '/#organizacao'}, 'inLanguage': 'pt-BR'}, breadcrumb([('Início', '/'), ('Áreas de atuação', '/areas-de-atuacao/')]),
           {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': a['titulo'], 'url': abs_url(slug_path('areas-de-atuacao', a['slug']))} for i, a in enumerate(AREAS)]}]
    page('/areas-de-atuacao/', 'Áreas de atuação em Direito da Saúde | Luiz Fernando Neves', 'Plano de saúde, direito à saúde, direito médico e odontológico, erro médico, consultoria preventiva, direito do consumidor e civil. Conheça as áreas de atuação.', body, '/areas-de-atuacao/', sch, prio='0.9')
    for a in AREAS:
        path = slug_path('areas-de-atuacao', a['slug'])
        cat = CATEGORIA_AREA.get(a['slug'])
        rel = [x for x in ARTS if x['categoria'] == cat] if cat else []
        rel = rel + [x for x in ARTS if x not in rel and CAT_COR.get(x['categoria']) == a['cor']]
        rel = rel + [x for x in ARTS if x not in rel]
        relh = '<section class="sec sec-sand"><div class="wrap"><header class="sec-h"><p class="eyebrow reveal">Leia também</p>%s</header>%s</div></section>' % (split_title('Artigos sobre o tema', 'h2', 'display'), rail(''.join(article_card(x) for x in rel[:6]), 'Artigos relacionados'))
        outras = ''.join('<li class="t-%s"><a href="%s"%s><i></i>%s</a></li>' % (o['cor'], slug_path('areas-de-atuacao', o['slug']), ' aria-current="page"' if o['slug'] == a['slug'] else '', h(o['titulo_curto'])) for o in AREAS)
        msg = 'Olá, vim pelo site e gostaria de falar sobre: %s.' % a['titulo']
        body = page_hero('Área de atuação %s' % a['numero'], a['titulo'], a['subtitulo'], [('Início', '/'), ('Áreas de atuação', '/areas-de-atuacao/'), (a['titulo_curto'], None)], a['cor'], a.get('imagem')) + '''
<section class="sec t-%s"><div class="wrap detail-grid">
  <div class="detail-main">
    <div class="prose">%s</div>
    <div class="list-box reveal"><h2 class="h-sm">%s</h2><ul class="checks">%s</ul></div>
    <div class="reveal">%s</div>
  </div>
  %s
</div></section>%s''' % (a['cor'], ''.join('<p class="reveal">%s</p>' % h(p) for p in a['paragrafos']), h(a['rotulo_lista'].rstrip(':') or 'Principais situações'), ''.join('<li>%s</li>' % h(i) for i in a['itens']),
            cta_inline(a['cta'], msg, 'area-cta'), side('Outras áreas', outras, a['cor'], msg, 'area'), relh) + cta_band(cor=a['cor'])
        sch = [{'@type': 'Service', '@id': abs_url(path) + '#servico', 'name': a['titulo'], 'serviceType': a['titulo'], 'description': a['descricao_seo'], 'url': abs_url(path), 'provider': {'@id': BASE + '/#organizacao'}, 'areaServed': {'@type': 'Country', 'name': 'Brasil'}, 'inLanguage': 'pt-BR'},
               breadcrumb([('Início', '/'), ('Áreas de atuação', '/areas-de-atuacao/'), (a['titulo_curto'], path)])]
        page(path, '%s | Luiz Fernando Neves' % a['titulo'], a['descricao_seo'], body, '/areas-de-atuacao/', sch, og_image=a.get('imagem'), prio='0.8')


def build_publics():
    cards = ''
    for i, p in enumerate(PUBS):
        cards += '''<a class="pub t-%s reveal" href="%s">%s<span class="pub-shade"></span><span class="pub-n">0%d</span><span class="pub-c"><span class="pub-k">%s</span><h2>%s</h2><p>%s</p><span class="more">Saiba mais %s</span></span></a>''' % (
            p['cor'], slug_path('para-quem-atuamos', p['slug']), img_tag(p.get('imagem'), '', sizes='(max-width:900px) 92vw, 400px'), i + 1, 'Saúde' if p['cor'] == 'verde' else 'Civil e consumidor', h(p['titulo_curto']), h(p['resumo']), ARROW)
    body = page_hero('Para quem atuamos', 'Três frentes de atendimento, um mesmo cuidado com cada caso', 'Profissionais da saúde, pacientes e beneficiários de planos de saúde e clientes de direito civil e do consumidor.', [('Início', '/'), ('Para quem atuamos', None)], 'verde', '/assets/img/plano-saude-idosos.webp') + '<section class="sec"><div class="wrap"><div class="sec-h">%s</div><div class="pubs">%s</div></div></section>' % (legend(), cards) + faq_section() + cta_band()
    sch = [{'@type': 'CollectionPage', 'url': abs_url('/para-quem-atuamos/'), 'name': 'Para quem atuamos', 'inLanguage': 'pt-BR'}, breadcrumb([('Início', '/'), ('Para quem atuamos', '/para-quem-atuamos/')]), faq_ld()]
    page('/para-quem-atuamos/', 'Para quem atuamos | Luiz Fernando Neves Advocacia', 'Advocacia para profissionais da saúde, pacientes e beneficiários de planos de saúde e clientes de direito civil e do consumidor.', body, '/para-quem-atuamos/', sch, prio='0.8')
    for p in PUBS:
        path = slug_path('para-quem-atuamos', p['slug'])
        secs = ''
        for s in p['secoes']:
            inner = ''
            for g in s.get('grupos', []):
                inner += '<div class="grupo"><h3>%s</h3><ul class="checks">%s</ul></div>' % (h(g['titulo']), ''.join('<li>%s</li>' % h(i) for i in g['itens']))
            if s.get('grupos'):
                inner = '<div class="grupos">%s</div>' % inner
            if s.get('itens'):
                tag = 'ol' if s.get('numerada') else 'ul'
                inner += '<%s class="%s">%s</%s>' % (tag, 'numlist' if s.get('numerada') else 'checks', ''.join('<li>%s</li>' % h(i) for i in s['itens']), tag)
            if s.get('paragrafos'):
                inner += ''.join('<p>%s</p>' % h(t) for t in s['paragrafos'])
            secs += '<section class="pub-sec%s reveal"><h2>%s</h2>%s</section>' % (' pub-destaque' if s.get('destaque') else '', h(s['titulo']), inner)
        outros = ''.join('<li class="t-%s"><a href="%s"%s><i></i>%s</a></li>' % (o['cor'], slug_path('para-quem-atuamos', o['slug']), ' aria-current="page"' if o['slug'] == p['slug'] else '', h(o['titulo_curto'])) for o in PUBS)
        msg = 'Olá, vim pelo site (%s) e gostaria de agendar uma consulta.' % p['titulo_curto']
        rel = [x for x in ARTS if CAT_COR.get(x['categoria']) == p['cor']]
        rel = (rel + [x for x in ARTS if x not in rel])[:6]
        relh = '<section class="sec sec-sand"><div class="wrap"><header class="sec-h"><p class="eyebrow reveal">Leia também</p>%s</header>%s</div></section>' % (split_title('Conteúdos para você', 'h2', 'display'), rail(''.join(article_card(x) for x in rel), 'Artigos')) if rel else ''
        body = page_hero(p['eyebrow'], p['titulo'], None, [('Início', '/'), ('Para quem atuamos', '/para-quem-atuamos/'), (p['titulo_curto'], None)], p['cor'], p.get('imagem')) + '''
<section class="sec t-%s"><div class="wrap detail-grid">
  <div class="detail-main"><div class="prose lead-prose">%s</div>%s%s</div>
  %s
</div></section>%s''' % (p['cor'], ''.join('<p class="reveal">%s</p>' % h(t) for t in p['intro']), secs, cta_inline(p['cta'], msg, 'publico-cta'), side('Outros atendimentos', outros, p['cor'], msg, 'publico'), relh) + cta_band(cor=p['cor'])
        sch = [{'@type': 'WebPage', 'url': abs_url(path), 'name': p['eyebrow'], 'description': p['descricao_seo'], 'about': {'@id': BASE + '/#organizacao'}, 'inLanguage': 'pt-BR'}, breadcrumb([('Início', '/'), ('Para quem atuamos', '/para-quem-atuamos/'), (p['titulo_curto'], path)])]
        page(path, '%s | Luiz Fernando Neves' % p['eyebrow'], p['descricao_seo'], body, '/para-quem-atuamos/', sch, og_image=p.get('imagem'), prio='0.8')


def build_articles():
    cats = []
    for a in ARTS:
        if a['categoria'] not in cats:
            cats.append(a['categoria'])
    chips = '<div class="chips" role="group" aria-label="Filtrar por tema"><button class="chip is-on" data-cat="">Todos</button>%s</div>' % ''.join('<button class="chip t-%s" data-cat="%s"><i></i>%s</button>' % (CAT_COR.get(c, 'verde'), h(c), h(c)) for c in cats)
    cards = ''.join(article_card(a, ' data-cat="%s"' % h(a['categoria'])) for a in ARTS)
    body = page_hero('Notícias e artigos', 'Informação jurídica clara sobre saúde, planos e direitos', 'Artigos sobre planos de saúde, direito médico e odontológico, erro médico e direitos de pacientes e profissionais.', [('Início', '/'), ('Conteúdo', None)], 'verde', '/assets/img/reajuste-plano-saude.webp') + '<section class="sec"><div class="wrap">%s%s</div></section>' % (chips, rail(cards, 'Artigos', 'lista-artigos')) + image_ribbon() + cta_band()
    sch = [{'@type': 'CollectionPage', 'url': abs_url('/conteudo/'), 'name': 'Notícias e artigos', 'inLanguage': 'pt-BR'}, breadcrumb([('Início', '/'), ('Conteúdo', '/conteudo/')]),
           {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': a['titulo'], 'url': abs_url(slug_path('conteudo', a['slug']))} for i, a in enumerate(ARTS)]}]
    page('/conteudo/', 'Notícias e artigos sobre Direito da Saúde | Luiz Fernando Neves', 'Artigos sobre plano de saúde, reajustes, home care, bariátrica, direito médico e odontológico, erro veterinário e mais, com linguagem clara.', body, '/conteudo/', sch, prio='0.8', freq='weekly')
    for a in ARTS:
        path = slug_path('conteudo', a['slug'])
        cor = CAT_COR.get(a['categoria'], 'verde')
        words = len(plain(a['texto']).split())
        mins = max(1, round(words / 200))
        rel = [x for x in ARTS if x['slug'] != a['slug'] and x['categoria'] == a['categoria']]
        rel += [x for x in ARTS if x['slug'] != a['slug'] and x not in rel]
        cover = '<figure class="art-cover reveal">%s</figure>' % img_tag(a['imagem'], a['titulo'], eager=True, sizes='(max-width:900px) 92vw, 760px') if a.get('imagem') else ''
        msg = 'Olá, li o artigo “%s” e gostaria de agendar uma consulta.' % a['titulo']
        cta = cta_inline(a['cta'], msg, 'artigo-cta') if a.get('cta') else ''
        areas_l = ''.join('<li class="t-%s"><a href="%s"><i></i>%s</a></li>' % (x['cor'], slug_path('areas-de-atuacao', x['slug']), h(x['titulo_curto'])) for x in AREAS)
        body = '''<article class="art t-%s">
<header class="art-head"><div class="stripes" aria-hidden="true"></div>%s<div class="wrap narrow"><nav class="crumbs" aria-label="Você está em"><ol><li><a href="/">Início</a></li><li><a href="/conteudo/">Conteúdo</a></li><li><span aria-current="page">%s</span></li></ol></nav>
<p class="tag"><i aria-hidden="true"></i>%s</p>%s
<p class="art-meta"><span>Por %s</span> <span aria-hidden="true">·</span> <time datetime="%s">%s</time> <span aria-hidden="true">·</span> <span>%d min de leitura</span></p></div></header>
<div class="wrap art-grid"><div class="art-main">%s<div class="prose art-body">%s</div>%s
<p class="disclaimer">Este conteúdo tem caráter informativo e não substitui a análise individual do seu caso por um advogado.</p></div>
%s</div>
</article>
<section class="sec sec-sand"><div class="wrap"><header class="sec-h"><p class="eyebrow reveal">Continue lendo</p>%s</header>%s</div></section>''' % (
            cor, mono('mono-anim ph-mono'), h(cut(a['titulo'], 60)), h(a['categoria']), split_title(a['titulo'], 'h1', 'display'), h(S['advogado']), h(a['data']), h(fmt_date(a['data'])), mins, cover, md(a['texto']), cta,
            side('Áreas de atuação', areas_l, cor, msg, 'artigo'), split_title('Outros artigos', 'h2', 'display'), rail(''.join(article_card(x) for x in rel[:6]), 'Outros artigos')) + cta_band(cor=cor)
        img = a['imagem'] if a.get('imagem') else '/assets/img/og-default.jpg'
        sch = [{'@type': 'Article', '@id': abs_url(path) + '#artigo', 'headline': a['titulo'], 'description': cut(a['resumo'], 200), 'inLanguage': 'pt-BR', 'datePublished': a['data'], 'dateModified': a.get('atualizado', a['data']),
                'author': {'@id': BASE + '/#advogado'}, 'publisher': {'@id': BASE + '/#organizacao'}, 'mainEntityOfPage': abs_url(path), 'articleSection': a['categoria'], 'image': abs_url(img), 'wordCount': words},
               breadcrumb([('Início', '/'), ('Conteúdo', '/conteudo/'), (a['titulo'], path)])]
        t = cut(a['titulo'], 46) + ' | Luiz Fernando Neves'
        page(path, t, cut(a['resumo'], 155), body, '/conteudo/', sch, og_image=img, og_type='article', lastmod=a['data'], prio='0.7')


def build_contact():
    areas = ['Plano de saúde', 'Direito à saúde', 'Direito médico', 'Direito odontológico', 'Erro médico, odontológico ou veterinário', 'Consultoria preventiva', 'Direito do consumidor', 'Direito civil', 'Outro assunto']
    opts = ''.join('<option>%s</option>' % h(a) for a in areas)
    end = ''
    if S.get('endereco_cidade'):
        end = '<li><span>Endereço</span><strong>%s</strong></li>' % h(', '.join(x for x in (S.get('endereco_rua'), S.get('endereco_cidade'), S.get('endereco_uf'), S.get('endereco_cep')) if x))
    ig = ('<li><span>Instagram</span><a href="%s" target="_blank" rel="noopener me">%s</a></li>' % (h(S['instagram_url']), h(S.get('instagram_usuario', '')))) if S.get('instagram_url') else ''
    body = page_hero('Contato', 'Agende uma consulta e receba uma orientação adequada ao seu caso', 'Conte brevemente sua situação. O atendimento é individualizado e respeita o ritmo e a urgência de cada pessoa.', [('Início', '/'), ('Contato', None)], 'verde', '/assets/img/luiz-fernando-neves-escritorio.webp') + '''
<section class="sec"><div class="wrap contact-grid">
  <div class="contact-info reveal"><h2 class="h-sm">Canais de atendimento</h2><ul class="info-list">
    <li><span>WhatsApp</span><a href="%(wa)s" target="_blank" rel="noopener" data-wa="contato">%(tel)s</a></li>
    <li><span>E-mail</span><a href="mailto:%(email)s">%(email)s</a></li>%(ig)s%(end)s</ul>
    <div class="note"><h3>Para agilizar o atendimento</h3><p>Se possível, tenha em mãos o relatório médico, a resposta do plano por escrito, o contrato e os protocolos de atendimento.</p></div>
  </div>
  <form class="form reveal" id="form-contato" novalidate data-wa="https://wa.me/%(num)s" aria-label="Formulário de contato">
    <h2 class="h-sm">Envie sua mensagem</h2>
    <label>Nome completo<input name="nome" required autocomplete="name" minlength="3"></label>
    <label>WhatsApp com DDD<input name="telefone" type="tel" required autocomplete="tel" inputmode="tel" minlength="10" placeholder="(11) 90000-0000"></label>
    <label>Assunto<select name="assunto" required><option value="">Selecione</option>%(opts)s</select></label>
    <label>Conte brevemente a situação<textarea name="mensagem" rows="5" required minlength="10"></textarea></label>
    <label class="check"><input type="checkbox" name="lgpd" required><span>Concordo em enviar estas informações ao escritório para fins de contato, conforme a <a href="/politica-de-privacidade/">política de privacidade</a>.</span></label>
    <p class="form-note">Ao enviar, o WhatsApp abrirá com a sua mensagem pronta. Não envie documentos sensíveis antes do início do atendimento.</p>
    <button class="btn btn-solid" type="submit" disabled>Enviar pelo WhatsApp</button>
  </form>
</div></section>''' % dict(wa=h(wa()), tel=h(S['telefone']), email=h(S['email']), ig=ig, end=end, opts=opts, num=S['whatsapp'])
    sch = [{'@type': 'ContactPage', 'url': abs_url('/contato/'), 'name': 'Contato', 'about': {'@id': BASE + '/#organizacao'}, 'inLanguage': 'pt-BR'}, breadcrumb([('Início', '/'), ('Contato', '/contato/')])]
    page('/contato/', 'Contato e agendamento de consulta | Luiz Fernando Neves', 'Agende uma consulta com o advogado Luiz Fernando Neves. Atendimento por WhatsApp e e-mail para pacientes, beneficiários e profissionais da saúde.', body, '/contato/', sch, prio='0.8')


def build_misc():
    body = page_hero('Privacidade', PRIV['titulo'], 'Atualizado em %s' % fmt_date(PRIV['atualizado_em']), [('Início', '/'), ('Política de privacidade', None)]) + '<section class="sec"><div class="wrap narrow"><div class="prose">%s</div></div></section>' % md(PRIV['texto'])
    page('/politica-de-privacidade/', 'Política de privacidade | Luiz Fernando Neves Advocacia', 'Como tratamos os dados pessoais de quem visita o site ou entra em contato com o escritório, conforme a LGPD.', body, prio='0.2', freq='yearly')
    body = page_hero('Mensagem enviada', 'Obrigado pelo contato', 'Recebemos a sua mensagem e retornaremos assim que possível. Se for urgente, fale pelo WhatsApp.') + '<section class="sec"><div class="wrap narrow center"><a class="btn btn-solid" href="%s" target="_blank" rel="noopener">Falar pelo WhatsApp</a> <a class="btn btn-ghost" href="/">Voltar ao início</a></div></section>' % h(wa())
    page('/obrigado/', 'Obrigado | Luiz Fernando Neves Advocacia', 'Mensagem recebida.', body, robots='noindex,nofollow', sitemap=False)
    body = page_hero('Erro 404', 'Página não encontrada', 'O endereço pode ter mudado ou não existir mais. Use os links abaixo para continuar.') + '<section class="sec"><div class="wrap narrow center"><a class="btn btn-solid" href="/">Ir para o início</a> <a class="btn btn-ghost" href="/areas-de-atuacao/">Áreas de atuação</a> <a class="btn btn-ghost" href="/conteudo/">Notícias e artigos</a></div></section>'
    page('/404.html', 'Página não encontrada | Luiz Fernando Neves Advocacia', 'Página não encontrada.', body, robots='noindex,follow', sitemap=False)


def build_files():
    # sitemap
    urls = ''.join('<url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>' % (abs_url(p), lm, fr, pr) for p, pr, fr, lm in sorted(PAGES))
    write('/sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % urls)
    bots = ['GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-User', 'Claude-SearchBot', 'anthropic-ai', 'PerplexityBot', 'Perplexity-User', 'Google-Extended', 'Applebot-Extended', 'Bingbot', 'Googlebot', 'CCBot', 'cohere-ai', 'Meta-ExternalAgent', 'Bytespider', 'DuckAssistBot', 'YouBot', 'MistralAI-User']
    rb = '# Permitimos rastreadores de buscadores e de assistentes de IA nas páginas públicas.\n'
    for b in bots:
        rb += 'User-agent: %s\nAllow: /\nDisallow: /admin/\nDisallow: /api/\nDisallow: /obrigado/\n\n' % b
    rb += 'User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /api/\nDisallow: /obrigado/\n\nSitemap: %s/sitemap.xml\n' % BASE
    write('/robots.txt', rb)
    # llms.txt
    L = ['# %s' % NOME, '', '> Advocacia especializada em Direito da Saúde. Orientação jurídica a médicos, dentistas e profissionais da saúde e defesa dos direitos de pacientes e beneficiários de planos de saúde. Advogado: %s (OAB/%s). Atendimento em todo o Brasil por WhatsApp e e-mail.' % (S['advogado'], S['oab_uf']), '',
         'Contato: WhatsApp %s, e-mail %s.' % (S['telefone'], S['email']), '', '## Áreas de atuação', '']
    for a in AREAS:
        L.append('- [%s](%s): %s' % (a['titulo'], abs_url(slug_path('areas-de-atuacao', a['slug'])), a['descricao_seo']))
    L += ['', '## Para quem atuamos', '']
    for p in PUBS:
        L.append('- [%s](%s): %s' % (p['eyebrow'], abs_url(slug_path('para-quem-atuamos', p['slug'])), p['descricao_seo']))
    L += ['', '## Artigos', '']
    for a in ARTS:
        L.append('- [%s](%s): %s' % (a['titulo'], abs_url(slug_path('conteudo', a['slug'])), cut(a['resumo'], 160)))
    L += ['', '## Institucional', '', '- [O escritório](%s)' % abs_url('/o-escritorio/'), '- [Contato](%s)' % abs_url('/contato/'), '- [Versão completa em texto](%s/llms-full.txt)' % BASE, '']
    write('/llms.txt', '\n'.join(L))
    F = ['# %s' % NOME, '', '> Advocacia especializada em Direito da Saúde (OAB/%s). Conteúdo informativo; cada caso exige análise individual.' % S['oab_uf'], '', '## O escritório', ''] + OF['texto'] + OF['advogado_texto'] + OF['principios'] + ['']
    for a in AREAS:
        F += ['## %s' % a['titulo'], '', a['subtitulo'], ''] + a['paragrafos'] + [''] + ['- %s' % i for i in a['itens']] + ['', a['cta'], '']
    for p in PUBS:
        F += ['## %s' % p['eyebrow'], '', p['titulo'], ''] + p['intro'] + ['']
        for s in p['secoes']:
            F += ['### %s' % s['titulo'], ''] + s.get('paragrafos', [])
            for g in s.get('grupos', []):
                F += ['**%s**' % g['titulo']] + ['- %s' % i for i in g['itens']]
            F += ['- %s' % i for i in s.get('itens', [])] + ['']
    F += ['## Perguntas frequentes', '']
    for f in FAQ:
        F += ['**%s**' % f['pergunta'], f['resposta'], '']
    for a in ARTS:
        F += ['## %s' % a['titulo'], '', '%s (%s)' % (a['categoria'], fmt_date(a['data'])), '', a['texto'], '', a['cta'], '', abs_url(slug_path('conteudo', a['slug'])), '']
    write('/llms-full.txt', '\n'.join(F))
    # rss
    items = ''.join('<item><title>%s</title><link>%s</link><guid isPermaLink="true">%s</guid><pubDate>%s</pubDate><category>%s</category><description>%s</description></item>' % (
        h(a['titulo']), abs_url(slug_path('conteudo', a['slug'])), abs_url(slug_path('conteudo', a['slug'])), datetime.datetime.strptime(a['data'], '%Y-%m-%d').strftime('%a, %d %b %Y 09:00:00 -0300'), h(a['categoria']), h(cut(a['resumo'], 200))) for a in ARTS)
    write('/feed.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>%s, notícias e artigos</title><link>%s/conteudo/</link><description>Informação jurídica sobre Direito da Saúde.</description><language>pt-BR</language>%s</channel></rss>\n' % (h(NOME), BASE, items))
    write('/site.webmanifest', json.dumps({'name': NOME, 'short_name': 'Luiz Fernando Neves', 'start_url': '/', 'display': 'standalone', 'background_color': '#F6F1E7', 'theme_color': '#28583F', 'lang': 'pt-BR',
                                          'icons': [{'src': '/assets/img/icon-192.png', 'sizes': '192x192', 'type': 'image/png'}, {'src': '/assets/img/icon-512.png', 'sizes': '512x512', 'type': 'image/png'}]}, ensure_ascii=False, indent=2))
    mono = open(os.path.join(ROOT, 'static/assets/logo/monograma-claro.svg'), encoding='utf-8').read()
    fav = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#28583F"/><svg x="6" y="21" width="52" height="22" viewBox="190 195 1430 340">%s</svg></svg>' % re.sub(r'^<svg[^>]*>|</svg>$', '', mono)
    write('/favicon.svg', fav)


def main():
    global ASSET
    ASSET = prepare_assets()
    build_home(); build_office(); build_areas(); build_publics(); build_articles(); build_contact(); build_misc(); build_files()
    print('OK: %d páginas em dist/' % (len(PAGES) + 2))


if __name__ == '__main__':
    main()
