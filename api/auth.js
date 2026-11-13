// Inicia o login com GitHub para o painel /admin (Decap CMS).
module.exports = (req, res) => {
  const id = process.env.OAUTH_CLIENT_ID;
  if (!id) { res.status(500).send('Defina OAUTH_CLIENT_ID na Vercel.'); return; }
  const host = req.headers['x-forwarded-host'] || req.headers.host;
  const redirect = `https://${host}/api/callback`;
  const state = require('crypto').randomBytes(16).toString('hex');
  res.setHeader('Set-Cookie', `oauth_state=${state}; HttpOnly; Secure; SameSite=Lax; Path=/api; Max-Age=600`);
  res.redirect(302, `https://github.com/login/oauth/authorize?client_id=${id}&redirect_uri=${encodeURIComponent(redirect)}&scope=repo,user&state=${state}`);
};
