export default async (request, context) => {
  const auth = request.headers.get("Authorization");
  
  // Netlifyの「金庫」からパスワードを読み出す設定
  const password = Netlify.env.get("SECRET_PASSWORD");
  const expectedAuth = "Basic " + btoa("admin:" + password);

  if (auth !== expectedAuth) {
    return new Response("Unauthorized", {
      status: 401,
      headers: { "WWW-Authenticate": 'Basic realm="Secure Recipe"' },
    });
  }
  return await context.next();
};
