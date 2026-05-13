// 一時的なテスト用コード（auth.jsをこれで上書きしてpush）
export default async (request, context) => {
  const auth = request.headers.get("Authorization");
  
  // 直接値を指定してテスト
  const expectedAuth = "Basic " + btoa("admin:murata1234"); // 仮のパスワード

  if (auth !== expectedAuth) {
    return new Response(`Your Header: ${auth}`, { // 送られてきたヘッダーを返す
      status: 401,
      headers: { "WWW-Authenticate": 'Basic realm="Secure Recipe"' },
    });
  }
  return await context.next();
};
