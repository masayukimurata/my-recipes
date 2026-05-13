import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
from decimal import Decimal
from typing import List, Dict, Tuple, Any, cast

# 日本標準時 (JST) の設定
JST = pytz.timezone('Asia/Tokyo')

class MurataRecipeEngine:
    def __init__(self):
        """DB接続の初期化"""
        self.conn = self._get_db_connection()

    def _get_db_connection(self):
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("❌ .env ファイルに DATABASE_URL が設定されていません。")
        return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

    def calculate_cost_recursive(self, r_id: str) -> Tuple[Decimal, List[Dict[str, Any]]]:
        """再帰原価計算（usage_amountを使用）"""
        with self.conn.cursor() as cur:
            query = """
                SELECT i.m_id, i.usage_amount, m.unit_cost, m.is_internal_product, m.m_name
                FROM public.t_recipe_ingredients i
                JOIN public.t_merchandise_pro m ON i.m_id = m.m_id
                WHERE i.r_id = %s
            """
            cur.execute(query, (r_id,))
            ingredients = cast(List[Dict[str, Any]], cur.fetchall())

            if not ingredients:
                return Decimal('0.00'), []

            total_cost = Decimal('0.00')
            details: List[Dict[str, Any]] = []

            for item in ingredients:
                m_id = str(item.get('m_id', ''))
                m_name = str(item.get('m_name', '不明'))
                qty = Decimal(str(item.get('usage_amount') or '0'))
                is_internal = bool(item.get('is_internal_product'))

                if is_internal:
                    sub_r_id = m_id.replace('M_', '')
                    unit_price, _ = self.calculate_cost_recursive(sub_r_id)
                else:
                    unit_price = Decimal(str(item.get('unit_cost') or '0.00'))

                line_cost = qty * unit_price
                total_cost += line_cost

                details.append({
                    "m_name": m_name,
                    "quantity": float(qty),
                    "unit_price": float(unit_price),
                    "line_cost": float(line_cost)
                })

            return total_cost, details

    def update_db(self, r_id: str, cost: Decimal):
        """DBへの書き戻しと履歴保存"""
        now = datetime.now(JST)
        with self.conn.cursor() as cur:
            # 1. 履歴保存（これは常に実行）
            cur.execute("""
                INSERT INTO public.t_cost_history (target_id, calculated_at, new_cost)
                VALUES (%s, %s, %s)
            """, (r_id, now, cost))

            # 2. レシピマスタの更新（生成列でないことを前提に実行）
            cur.execute("""
                UPDATE public.t_recipes
                SET total_cost = %s
                WHERE r_id = %s
            """, (cost, r_id))

            # 【注意】t_merchandise_pro.unit_cost が生成列のため、
            # ここでの直接 UPDATE はスキップします。
            # 必要であれば、元となる数値を更新するか、DB側の計算に任せます。

            self.conn.commit()
            print(f"### [分析] 更新完了: {r_id} = {cost}円")

    def close(self):
        if self.conn:
            self.conn.close()
