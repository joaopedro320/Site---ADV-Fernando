// Conclui o login com GitHub e devolve o token ao painel /admin (Decap CMS).
module.exports = async (req, res) => {
  const { code, state } = req.query;
  const cookie = (req.headers.cookie || '').split(';').map(s => s.trim()).find(s => s.startsWith('oauth_state='));
  const saved = cookie ? cookie.split('=')[1] : '';
  const send = (status, content) => {
    const msg = `authorization:github:${status}:${JSON.stringify(content)}`;
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.send(`<!doctype html><script>
(function(){function r(e){window.opener.postMessage(${JSON.stringify(msg)},e.origin)}
window.addEventListener('message',r,false);window.opener.postMessage('authorizing:github','*');})();
</script>`);
  };
  if (!code || !state || state !== saved) return send('error', { message: 'Estado de login inválido. Tente novamente.' });
  try {
    const r = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ client_id: process.env.OAUTH_CLIENT_ID, client_secret: process.env.OAUTH_CLIENT_SECRET, code })
    });
    const j = await r.json();
    if (j.error) return send('error', j);
    send('success', { token: j.access_token, provider: 'github' });
  } catch (e) { send('error', { message: String(e) }); }
};
