export default async (request, context) => {
  const auth = request.headers.get("Authorization");
  
  // あなたが設定した「正解」
  const expectedAuth = "Basic " + btoa("admin:murata1234");

  // もし一致しないなら、何が届いているのかをレスポンスで教えてもらう
  if (auth !== expectedAuth) {
    return new Response(
      `Auth Error!\nExpected: "${expectedAuth}"\nReceived: "${auth}"`, 
      { status: 401 }
    );
  }

  return await context.next();
};
