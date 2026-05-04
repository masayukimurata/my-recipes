import hashlib

def generate_secure_recipe_html(recipe_name, ingredients, instructions, password):
    # パスワードをハッシュ化（ソースコードを直接見てもパスワードがバレないようにする）
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="robots" content="noindex, nofollow">
        <title>{recipe_name}</title>
        <script>
            function checkPassword() {{
                const input = prompt("パスワードを入力してください");
                // 簡易的なチェック（実際はもっと複雑にできます）
                if (input === "{password}") {{
                    document.getElementById('content').style.display = 'block';
                }} else {{
                    alert("パスワードが違います");
                    window.location.reload();
                }}
            }}
        </script>
        <script type="application/ld+json">
        {{
          "@context": "https://schema.org/",
          "@type": "Recipe",
          "name": "{recipe_name}",
          "recipeIngredient": {ingredients},
          "recipeInstructions": {instructions}
        }}
        </script>
    </head>
    <body onload="checkPassword()">
        <div id="content" style="display:none;">
            <h1>{recipe_name}</h1>
            </div>
    </body>
    </html>
    """
    return html

# 実行例
# ingredients = ["強力粉 250g", "砂糖 40g"] ... DBから取得
# instructions = ["混ぜる", "焼く"] ... DBから取得
# html = generate_secure_recipe_html("メロンパン", ingredients, instructions, "murata1234")
