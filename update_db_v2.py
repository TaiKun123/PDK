import sqlite3
from app import app, db

# 更新資料庫腳本 V2
conn = sqlite3.connect('instance/pdk.db')
cursor = conn.cursor()

print("正在為 Voucher 增加新欄位 (門檻、時間)...")

try:
    cursor.execute("ALTER TABLE voucher ADD COLUMN min_spend INTEGER DEFAULT 0")
    print("成功加入 min_spend")
except:
    print("min_spend 已存在")

try:
    cursor.execute("ALTER TABLE voucher ADD COLUMN start_time TIMESTAMP")
    cursor.execute("ALTER TABLE voucher ADD COLUMN end_time TIMESTAMP")
    print("成功加入 時間欄位")
except:
    print("時間欄位 已存在")

try:
    cursor.execute("ALTER TABLE voucher ADD COLUMN description TEXT")
    print("成功加入 description")
except:
    print("description 已存在")

conn.commit()
conn.close()
print("資料庫升級完成！")