from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # 使用原生 SQL 語法，輕輕地在 user 表格加上 real_name 欄位
        db.session.execute(text('ALTER TABLE user ADD COLUMN real_name VARCHAR(100);'))
        db.session.commit()
        print("✅ 太棒了！成功在資料庫加入 real_name 欄位！資料完全沒遺失！")
    except Exception as e:
        print("⚠️ 發生狀況（可能欄位已經存在了）：", e)