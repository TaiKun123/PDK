from app import app, db, Voucher

def init_vouchers():
    with app.app_context():
        # 1. 避免重複建立
        if Voucher.query.first():
            print("折扣券定義已存在，跳過初始化。")
            return

        print("開始建立標準折扣券...")

        # --- 定義列表 ---
        vouchers = [
            # --- Type A: 活動券 (Activity) - 不可疊加，單次擇一 ---
            # 1. IG 打卡
            Voucher(title='IG打卡獎勵', discount_value=50, voucher_type='activity'),
            # 2. 公益活動
            Voucher(title='公益活動感謝', discount_value=100, voucher_type='activity'),
            
            # 3. 生日禮金 (分等級)
            # Pure 會員 (150元? 您原本說200，後來範例寫150，這裡我先設150，您可自行修改)
            Voucher(title='生日禮金-Pure', discount_value=150, voucher_type='activity'),
            # Deep 會員 (200元)
            Voucher(title='生日禮金-Deep', discount_value=200, voucher_type='activity'),
            # Keep 會員 (300元)
            Voucher(title='生日禮金-Keep', discount_value=300, voucher_type='activity'),

            # --- Type B: 獎勵券 (Reward) - 可疊加 ---
            # 4. 邀請朋友獎勵
            Voucher(title='邀請朋友獎勵', discount_value=100, voucher_type='reward'),
        ]

        db.session.add_all(vouchers)
        db.session.commit()
        print("折扣券初始化完成！請刪除此檔案或保留備用。")

if __name__ == '__main__':
    init_vouchers()