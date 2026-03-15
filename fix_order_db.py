from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # 在 order 表格加入 LINE Pay 交易序號欄位
        db.session.execute(text('ALTER TABLE "order" ADD COLUMN linepay_transaction_id VARCHAR(50);'))
        db.session.commit()
        print("✅ 太棒了！訂單資料庫更新成功，現在可以下單了！")
    except Exception as e:
        print("⚠️ 發生錯誤:", e)