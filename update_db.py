import sqlite3
from app import app, db, Voucher, UserVoucher # 引入新定義的 class

# 確保在 Flask Context 下執行，這樣 db.create_all 才能運作
with app.app_context():
    print("正在建立新的 Voucher 與 UserVoucher 表格...")
    db.create_all() # 這行會自動檢查，只建立還不存在的表格 (User, Order 舊的不會被影響)
    print("表格建立完成！")

# 接著檢查 User 與 Order 的新欄位 (如果你剛剛還沒做過欄位擴充)
# 如果剛剛做過了，這段執行會自動跳過，很安全
conn = sqlite3.connect('instance/pdk.db') # 確認您的 db 路徑
cursor = conn.cursor()

print("正在檢查 User 與 Order 欄位...")
try:
    cursor.execute("ALTER TABLE user ADD COLUMN member_tier TEXT DEFAULT 'Pure'")
    cursor.execute("ALTER TABLE user ADD COLUMN total_spend INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE user ADD COLUMN orders_count INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE user ADD COLUMN member_expiry TIMESTAMP")
    cursor.execute("ALTER TABLE user ADD COLUMN birthday DATE")
    cursor.execute("ALTER TABLE user ADD COLUMN referral_code TEXT")
    cursor.execute("ALTER TABLE user ADD COLUMN used_referral BOOLEAN DEFAULT 0")
    print("User 新欄位加入成功")
except:
    print("User 欄位已存在，跳過")

try:
    cursor.execute("ALTER TABLE 'order' ADD COLUMN referrer_id INTEGER")
    cursor.execute("ALTER TABLE 'order' ADD COLUMN final_total INTEGER")
    print("Order 新欄位加入成功")
except:
    print("Order 欄位已存在，跳過")

conn.commit()
conn.close()
print("Step 1 資料庫擴充：全部完成！")