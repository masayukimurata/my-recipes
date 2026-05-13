import json
import os
from datetime import datetime
import pytz
from jinja2 import Environment, FileSystemLoader
# 同じリポジトリ内にある MurataRecipeEngine をインポート
from recipe_engine import MurataRecipeEngine

JST = pytz.timezone('Asia/Tokyo')

def process_recipes(rows):
    recipe_dict = {}
    for row in rows:
        rid = row['r_id']
        if rid not in recipe_dict:
            recipe_dict[rid] = {
                'r_id': rid,
                'r_name': row['r_name'],
                'remarks': row.get('remarks') or "",
                'course': row.get('course') or "",
                'category': row.get('category') or "",
                'serving_size': row.get('serving_size') or "",
                'total_cost': 0,
                'ingredients': []
            }
        recipe_dict[rid]['ingredients'].append({
            'm_name': row['m_name'],
            'usage_amount': float(row['usage_amount']) if row['usage_amount'] else 0,
            'base_unit': row['base_unit'] or "",
            'unit_price': 0,
            'line_cost': 0
        })
    return recipe_dict

def handler(event, context):
    """Netlify Functions 用のエントリポイント"""
    engine = MurataRecipeEngine()

    # Retoolから特定のレシピIDが指定されている場合を取得
    params = event.get('queryStringParameters', {})
    target_rid = params.get('r_id')

    try:
        with engine.conn.cursor() as cur:
            # 憲法に従い、publicスキーマを明示
            query = """
                SELECT r.*, ri.usage_amount, m.m_name, m.base_unit, m.m_id
                FROM public.t_recipes r
                JOIN public.t_recipe_ingredients ri ON r.r_id = ri.r_id
                JOIN public.t_merchandise_pro m ON ri.m_id = m.m_id
                WHERE m.is_active = true
            """
            if target_rid:
                query += " AND r.r_id = %s"
                cur.execute(query + " ORDER BY r.r_id;", (target_rid,))
            else:
                cur.execute(query + " ORDER BY r.r_id;")

            rows = cur.fetchall()

        if not rows:
            return {"statusCode": 404, "body": "No data found"}

        recipes = process_recipes(rows)

        # 再帰計算の実行
        for rid, data in recipes.items():
            final_cost, details = engine.calculate_cost_recursive(rid)
            engine.update_db(rid, final_cost) # DB同期

            data['total_cost'] = float(final_cost)
            for i, ing in enumerate(data['ingredients']):
                if i < len(details):
                    ing['unit_price'] = details[i]['unit_price']
                    ing['line_cost'] = details[i]['line_cost']

        # HTML生成（Netlify環境では templates フォルダのパスに注意）
        # AWS Lambda/Netlify環境用にパスを調整
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env = Environment(loader=FileSystemLoader(os.path.join(script_dir, 'templates')))
        template = env.get_template('index.html.j2')

        now_str = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
        html_content = template.render(recipes=recipes, now=now_str)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*" # Retoolからのアクセスを許可
            },
            "body": json.dumps({
                "status": "success",
                "r_id": target_rid,
                "html": html_content
            }, ensure_ascii=False)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
    finally:
        engine.close()
