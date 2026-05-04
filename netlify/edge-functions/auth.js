export default async (request, context) => {
  const auth = request.headers.get("Authorization");
  
  // ユーザー名: admin / パスワード: murata1234
  const expectedAuth = "Basic " + btoa("admin:murata1234");

  if (auth !== expectedAuth) {
    return new Response("Unauthorized", {
      status: 401,
      headers: { "WWW-Authenticate": 'Basic realm="Secure Recipe"' },
    });
  }
  return await context.next();
};
