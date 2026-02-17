import sqlite3
import os

# 1. 鎖定資料庫位置
# 通常在 instance/pdk.db，但有些環境在 pdk.db，這裡做個自動檢查
db_path = 'instance/pdk.db'
if not os.path.exists(db_path):
    db_path = 'pdk.db'
    if not os.path.exists(db_path):
        print("❌ 找不到 pdk.db，請確認您的資料庫檔案在哪裡！")
        exit()

print(f"正在連接資料庫：{db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 2. 定義要新增的欄位清單
# (欄位名稱, 資料型態, 預設值)
new_columns = [
    ('valid_days', 'INTEGER', '30'),
    ('min_spend', 'INTEGER', '0'),
    ('start_time', 'TIMESTAMP', 'NULL'),
    ('end_time', 'TIMESTAMP', 'NULL'),
    ('description', 'TEXT', 'NULL')
]

print("開始檢查並修復 Voucher 表格欄位...")

for col_name, col_type, default_val in new_columns:
    try:
        # 嘗試新增欄位
        if default_val == 'NULL':
            sql = f"ALTER TABLE voucher ADD COLUMN {col_name} {col_type}"
        else:
            sql = f"ALTER TABLE voucher ADD COLUMN {col_name} {col_type} DEFAULT {default_val}"
            
        cursor.execute(sql)
        print(f"✅ 成功新增欄位: {col_name}")
    except sqlite3.OperationalError as e:
        # 如果錯誤訊息包含 "duplicate column name"，代表欄位已經存在，不用擔心
        if "duplicate column name" in str(e):
            print(f"ℹ️ 欄位已存在，跳過: {col_name}")
        else:
            print(f"❌ 新增 {col_name} 失敗: {e}")

# 3. 儲存變更
conn.commit()
conn.close()

print("-" * 30)
print("🎉 資料庫修復完成！請重新啟動 app.py")