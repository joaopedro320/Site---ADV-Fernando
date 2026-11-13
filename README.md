# Site Luiz Fernando Neves Advocacia (Direito da Saúde)

Site estático gerado por `build.py` (Python, só biblioteca padrão) com painel de edição Decap CMS em `/admin`.

## Como rodar
    python3 build.py        # gera a pasta dist/
    python3 -m http.server -d dist 8000

## Deploy (Vercel)
`vercel.json` já define build (`python3 build.py`) e saída (`dist`). Conectar o repositório GitHub à Vercel.

## Painel editável (/admin)
1. Criar um OAuth App no GitHub (callback `https://SEU-DOMINIO/api/callback`).
2. Na Vercel, definir `OAUTH_CLIENT_ID` e `OAUTH_CLIENT_SECRET`.
3. Em `static/admin/config.yml`, trocar `repo` e `base_url`.
4. O cliente edita textos, artigos, áreas, FAQ, contatos e IDs de rastreamento. Fluxo editorial: cada edição vira rascunho, revisão e publicação.

## Pendências de dados (editar em Configurações do site)
Número da OAB, endereço, links de LinkedIn/Google, GTM/Pixel/GA4, avaliações reais, domínio definitivo (hoje `luizfernandoneves.com.br`), fotos finais (as dos artigos são de banco).

## SEO e IA
JSON-LD (LegalService, Person, FAQPage, Article, Service, Breadcrumb), canonical, Open Graph, sitemap.xml, robots.txt liberando rastreadores de IA, llms.txt, llms-full.txt, feed.xml, 404 e página de obrigado.
