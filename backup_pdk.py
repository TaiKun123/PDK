import shutil
import os
from datetime import datetime

# --- 設定區 ---
DB_NAME = 'pdk.db'
# ------------------

def backup_to_desktop():
    # 1. 自動取得「桌面」路徑 (Windows/Mac 通用)
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    backup_folder = os.path.join(desktop_path, "PDK_備份")

    # 2. 如果桌面沒有「PDK_備份」資料夾，就建立一個
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
        print(f"📁 已在桌面建立資料夾: {backup_folder}")

    # 3. 尋找 pdk.db (在程式所在資料夾，或是 instance 資料夾)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, DB_NAME)
    instance_db_path = os.path.join(base_dir, 'instance', DB_NAME)
    
    source_path = None
    if os.path.exists(db_path):
        source_path = db_path
    elif os.path.exists(instance_db_path):
        source_path = instance_db_path
    
    if not source_path:
        print(f"❌ 錯誤：找不到 {DB_NAME}！")
        return

    # 4. 產生備份檔名 (加上日期時間)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    backup_filename = f"pdk_備份_{timestamp}.db"
    destination_path = os.path.join(backup_folder, backup_filename)

    # 5. 執行複製
    try:
        shutil.copy2(source_path, destination_path)
        print(f"✅ 備份成功！")
        print(f"💾 檔案已存到桌面: {destination_path}")
    except Exception as e:
        print(f"❌ 備份失敗: {e}")

if __name__ == "__main__":
    print("正在將資料庫備份到桌面...")
    backup_to_desktop()
    input("\n請按 Enter 鍵結束...")