from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from sqlalchemy import extract
from flask_mail import Mail, Message
from datetime import datetime, timedelta # 確保引入這兩個# ★★★ 新增：寄信模組
from threading import Thread # ★★★ 新增這行
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix # ★★★ 1. 確保有引入這行
import os
import requests # 用來發送 API 請求
import json
import datetime
import random
import string# ★★★ 新增：隨機數模組
import hmac
import hashlib
import base64
import uuid
import google.generativeai as genai

app = Flask(__name__)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
# ==============================================================================
# 1. 設定 (Configuration) - 智慧切換資料庫
# ==============================================================================
# 嘗試讀取 Render 的環境變數
db_url = os.environ.get('DATABASE_URL')

# 如果有讀到，且開頭是 postgres://，要修正為 postgresql:// (這是 Render 的小特例)
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# 如果讀得到雲端網址就用雲端的，讀不到(在自己電腦)就用原本的 pdk.db
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///pdk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_super_secret_key_change_this_in_production' 

# ★★★ 修正：智慧切換 Cookie 安全限制 (解決本地端無法登入的問題)
if os.environ.get('DATABASE_URL'):
    # 如果是在 Render 上 (有資料庫網址)，就開啟嚴格模式
    app.config['SESSION_COOKIE_SECURE'] = True
else:
    # 如果是在本機測試 (http)，就關閉嚴格模式
    app.config['SESSION_COOKIE_SECURE'] = False

app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# ★★★ 新增：Gmail 寄信設定 ★★★
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'pdk.salon.office@gmail.com'  # 請確認這是您剛剛申請密碼的那個 Gmail 帳號
app.config['MAIL_PASSWORD'] = 'ibxlwikvoolpemqw'      # ★★★ 您的應用程式密碼 (已去空白)
app.config['MAIL_DEFAULT_SENDER'] = ('P.D.K Official', 'pdk.salon.office@gmail.com')

mail = Mail(app) # 初始化 Mail 元件

# ★★★ 新增：設定圖片上傳路徑 ★★★
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 允許上傳的圖片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# ==========================================
# ★ 第三方登入設定 (OAuth)
# ==========================================
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),        
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

line = oauth.register(
    name='line',
    client_id=os.environ.get('LINE_LOGIN_ID'),
    client_secret=os.environ.get('LINE_LOGIN_SECRET'),
    server_metadata_url='https://access.line.me/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid profile email'
    }
)
# --- ★★★ Brevo 高速寄信函式 ★★★ ---
def send_via_brevo(to_email, subject, html_content):
    url = "https://api.brevo.com/v3/smtp/email"
    # 從 Render 環境變數讀取金鑰 (如果本機測試讀不到，請確保有設定或暫時貼上)
    api_key = os.environ.get('BREVO_API_KEY') 
    
    if not api_key:
        print("❌ 錯誤：找不到 BREVO_API_KEY，無法寄信")
        return

    payload = {
        "sender": {"name": "P.D.K Official", "email": "pdk.salon.office@gmail.com"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": api_key
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201, 202]:
            print(f"✅ Brevo 寄信成功！回應: {response.status_code}")
        else:
            print(f"❌ Brevo 寄信失敗: {response.text}")
    except Exception as e:
        print(f"❌ 連線錯誤: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- 工具函式：產生唯一推薦碼 ---
def generate_unique_referral_code():
    chars = string.ascii_uppercase + string.digits # 大寫英文 + 數字
    while True:
        code = ''.join(random.choices(chars, k=8))
        # 檢查資料庫是否已經有人用過這組碼，如果有就重跑，直到唯一
        if not User.query.filter_by(referral_code=code).first():
            return code

# ★★★ 新增：Jinja2 自定義過濾器 ★★★
# 用於將資料庫中的 JSON 字串（cart_items）轉回列表，讓 HTML 可以用迴圈跑商品明細
@app.template_filter('from_json')
def from_json_filter(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except:
        return []

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # 若沒登入，導向的頁面

# ==========================================
# ★ LINE Pay 金流設定 & 加密工具 ★
# ==========================================
if os.environ.get('DATABASE_URL'):
    # Render 正式環境
    LINE_PAY_ID = os.environ.get('LINE_PAY_ID')
    LINE_PAY_SECRET = os.environ.get('LINE_PAY_SECRET')
    LINE_PAY_API_URL = "https://api-pay.line.me"
    SERVER_URL = "https://pdk-office.onrender.com"
else:
    # 本地測試環境 (Ngrok)
    LINE_PAY_ID = "2009436575" 
    LINE_PAY_SECRET = "b36da8e2174c8787cf43756332d4fedb"
    LINE_PAY_API_URL = "https://sandbox-api-pay.line.me"
    SERVER_URL = "https://unilingual-nonviviparously-camron.ngrok-free.dev"

# 產生 LINE Pay V3 專用簽名 (HMAC-SHA256)
def generate_line_pay_signature(uri, request_body, nonce):
    secret = LINE_PAY_SECRET
    message = secret + uri + request_body + nonce
    signature = base64.b64encode(hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
    return signature

# ==============================================================================
# 2. 資料庫模型 (Models) - 核心地基
# ==============================================================================

# ★★★ 新增：使用者/會員模型 ★★★
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100))
    real_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    store_info = db.Column(db.String(100))
    role = db.Column(db.String(20), default='customer')
    
    # 時間欄位
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    
    # --- 會員等級與消費紀錄 ---
    member_tier = db.Column(db.String(20), default='General')  # Pure, Deep, Keep
    total_spend = db.Column(db.Integer, default=0)          # 一年內累積消費
    orders_count = db.Column(db.Integer, default=0)         # 一年內累積單數 (修正：只留這一個)
    member_expiry = db.Column(db.DateTime, default=datetime.datetime.now) 
    free_shipping_quota = db.Column(db.Integer, default=0)  # Keep 會員免運次數
    
    # --- 生日與推薦機制 ---
    birthday = db.Column(db.Date, nullable=True)            # 生日
    
    referral_code = db.Column(db.String(20), unique=True)   # 自己的推薦碼
    used_referral = db.Column(db.Boolean, default=False)    # 是否填過別人的碼
    
    # ★★★ 新增：紀錄是誰推薦了我 (解決報錯關鍵) ★★★
    referrer_id = db.Column(db.Integer, nullable=True)      
    
    # 關聯
    coupons = db.relationship('UserVoucher', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ★★★ 升級：商品模型 (改為資料庫管理) ★★★
class Product(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(200)) # 新增：預留圖片路徑
    tag_image = db.Column(db.String(200))  # ★★★ 新增：標籤介紹圖 ★★★
    volume = db.Column(db.String(50))
# ★★★ 新增：收藏清單模型 (Wishlist) ★★★
class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.String(50), db.ForeignKey('product.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

# ★★★ 升級：訂單模型 (關聯使用者) ★★★
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # ★★★ 新增：推薦人 ID (紀錄是誰介紹這筆訂單的) ★★★
    referrer_id = db.Column(db.Integer, nullable=True) 

    customer_name = db.Column(db.String(50), nullable=False)
    customer_email = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    shipping_method = db.Column(db.String(20))
    address = db.Column(db.String(200))
    payment_method = db.Column(db.String(20))
    
    # ★★★ LINE Pay 專屬交易序號
    linepay_transaction_id = db.Column(db.String(50), nullable=True)
    
    total_amount = db.Column(db.Integer)
    discount_amount = db.Column(db.Integer, default=0)
    
    discount_promo = db.Column(db.Integer, default=0)   # 優惠碼折抵
    discount_voucher = db.Column(db.Integer, default=0) # 優惠券折抵
    discount_member = db.Column(db.Integer, default=0)  # 會員等級折抵
    
    shipping_fee = db.Column(db.Integer, default=100)
    final_total = db.Column(db.Integer)         # 最終金額
    
    cart_items = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    paid_at = db.Column(db.DateTime, nullable=True) # 付款時間

    # 建立關聯 (方便查詢下單者)
    user = db.relationship('User', foreign_keys=[user_id], backref='orders')
    
# ==============================================================================
# ★★★ 新增區塊 1：優惠券相關模型 (Coupon Models) ★★★
# ==============================================================================

class Coupon(db.Model):
    __tablename__ = 'coupon'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False) # 優惠碼 (例如: VIP888)
    name = db.Column(db.String(50), nullable=False)              # 優惠券名稱 (例如: 新客首購禮)
    
    # 折扣類型: 'fixed' (折抵現金) / 'percent' (打折)
    discount_type = db.Column(db.String(10), nullable=False) 
    
    # 數值: 若 fixed 存 100 (折100元); 若 percent 存 10 (打9折/折10%)
    discount_value = db.Column(db.Integer, nullable=False) 
    
    min_spend = db.Column(db.Integer, default=0) # 最低消費門檻
    
    # 期限設定
    start_date = db.Column(db.DateTime, default=datetime.datetime.now)
    end_date = db.Column(db.DateTime, nullable=True) # 若為 Null 代表永久有效
    
    # 數量限制
    usage_limit = db.Column(db.Integer, default=999999) # 全站總共可被用幾次
    used_count = db.Column(db.Integer, default=0)       # 已經被使用幾次
    
    # ★ 單人限制：0 代表不限，1 代表每人限用一次
    per_user_limit = db.Column(db.Integer, default=1) 
    
    is_active = db.Column(db.Boolean, default=True) # 手動開關
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class CouponUsage(db.Model):
    __tablename__ = 'coupon_usage'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupon.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    used_at = db.Column(db.DateTime, default=datetime.datetime.now)

# Flask-Login 載入使用者
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ★★★ 新增：全域變數注入 (讓所有模板都能拿到收藏清單) ★★★
@app.context_processor
def inject_wishlist():
    if current_user.is_authenticated:
        # 抓取該使用者的所有收藏
        wishes = Wishlist.query.filter_by(user_id=current_user.id).all()
        # 回傳 ID 列表，例如 ['sh_001', 'hc_002']
        return {'current_user_wishlist_ids': [w.product_id for w in wishes]}
    return {'current_user_wishlist_ids': []}

# ----------------------
# 5. 折扣券定義表 (升級版)
# ----------------------
class Voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)        # 券名
    discount_value = db.Column(db.Integer, nullable=False)      # 折扣金額
    voucher_type = db.Column(db.String(20), default='activity') # activity(互斥) / reward(可疊加)
    
    # ★ 新增：最低消費門檻 (0 代表不限制)
    min_spend = db.Column(db.Integer, default=0)
    
    # ★ 新增：發放後的有效天數 (例如: 領取後 30 天內有效)
    valid_days = db.Column(db.Integer, default=30)
    
    # ★ 新增：活動上架期間 (例如: 只有 2/14 ~ 2/16 可以領這張券)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    
    description = db.Column(db.String(200)) # 備註說明
    is_active = db.Column(db.Boolean, default=True)

# ----------------------
# 6. ★新增★ 會員持有折扣券表 (UserVoucher)
#    用途：記錄哪個會員擁有了哪張券 (歸戶)
# ----------------------
class UserVoucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    voucher_id = db.Column(db.Integer, db.ForeignKey('voucher.id'), nullable=False)
    
    is_used = db.Column(db.Boolean, default=False)      # 是否已使用
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)  # 獲得時間
    expiry_date = db.Column(db.DateTime, nullable=True) # 到期日 (可選)

    # 建立關聯，方便查詢
    voucher = db.relationship('Voucher') 
    # 讓 User 表格也能反向查到 (需配合 User 表格的修改，或直接用查詢語法)

# ==============================================================================
# 3. 初始化 (Seeds) - 自動建立資料
# ==============================================================================
def create_initial_data():
    db.create_all()
    
    # 1. 檢查並建立預設管理員
    if not User.query.filter_by(email='admin@pdk.com').first():
        print("建立預設管理員帳號...")
        admin = User(email='admin@pdk.com', name='系統管理員', role='admin')
        admin.set_password('1234') # ★★★ 這裡設定預設密碼 ★★★
        db.session.add(admin)
        db.session.commit()
    # ★★★ 新增：建立本機測試用的普通會員帳號 ★★★
    if not User.query.filter_by(email='test@pdk.com').first():
        print("建立測試會員帳號...")
        test_user = User(
            email='test@pdk.com', 
            name='測試專員', 
            real_name='陳測試', 
            phone='0912345678', 
            role='customer',
            member_tier='Pure'
        )
        test_user.set_password('1234') # 密碼一樣設為 1234 方便你測試
        db.session.add(test_user)
        db.session.commit()
    # 2. 檢查並建立預設商品
    if not Product.query.first():
        print("初始化商品資料庫...")
        products = [
            Product(id="sh_001", name="淨屑舒活洗髮精", category="shampoo", price=700, description="1.清除油脂 2.滋養髮根 3.強韌成長"),
            Product(id="sh_002", name="輕柔活力洗髮精", category="shampoo", price=700, description="1.深層控油 2.強健髮根 3.蓬鬆清爽"),
            Product(id="sh_003", name="翅藻植翠洗髮精", category="shampoo", price=700, description="1.平衡油脂 2.鎖水保濕 3.輕盈蓬鬆"),
            Product(id="sh_004", name="淨化控油調理洗髮精", category="shampoo", price=850, description="1.油脂平衡 2.植萃淨化 3.賦活蓬鬆"),
            Product(id="sh_005", name="極致燙染修復洗髮精", category="shampoo", price=850, description="1.賦活修復 2.鎖水護色 3.極致補水"),
            Product(id="co_001", name="翅藻植翠極致乳", category="conditioner", price=700, description="1.深層滋養 2.強韌髮芯 3.護色彈力"),
            Product(id="co_002", name="極致燙染修復護理素", category="conditioner", price=850, description="1.深層修復 2.強韌彈性 3.高效保濕"),
            Product(id="hc_001", name="摩洛哥Q10精華修復液", category="haircare", price=500, description="1.抗氧防護 2.強韌養分 3.瞬效柔滑"),
            Product(id="hc_002", name="黃金堅果E油", category="haircare", price=500, description="1.雙重防禦 2.鎖色持久 3.撫平毛躁"),
            Product(id="hc_003", name="芳香質感精華乳", category="haircare", price=350, description="1.平衡調理 2.修補水分 3.護色功能"),
            Product(id="hc_004", name="彈力亮澤修復液", category="haircare", price=350, description="1.護色修復 2.減少毛躁 3.閃亮健康"),
            Product(id="op_001", name="PLASTIC WAX", category="otherproduct", price=400, description="1.強力造型 2.造型再現")
        ]
        db.session.add_all(products)
        db.session.commit()
def create_default_vouchers():
    """
    初始化資料庫：如果沒有這些折扣券，就自動建立。
    ★ 修改：更新為系統實際使用的名稱 (Pure/Deep/Keep)
    """
    
    # 定義要建立的券清單 (這是修正後的正確版本)
    default_vouchers = [
        # --- 1. 生日禮金系列 (配合系統自動發放的名稱) ---
        {
            "title": "Pure 會員生日禮",  # 改成這個名字
            "discount_value": 150,
            "voucher_type": "activity",  
            "min_spend": 0,
            "valid_days": 365,
            "description": "祝您生日快樂！Pure 會員專屬禮金"
        },
        {
            "title": "Deep 會員生日禮",  # 改成這個名字
            "discount_value": 200,
            "voucher_type": "activity",
            "min_spend": 0,
            "valid_days": 365,
            "description": "祝您生日快樂！Deep 會員專屬禮金"
        },
        {
            "title": "Keep 會員生日禮",  # 改成這個名字
            "discount_value": 300,
            "voucher_type": "activity",
            "min_spend": 0,
            "valid_days": 365,
            "description": "祝您生日快樂！Keep 會員專屬禮金"
        },

        # --- 2. 推薦獎勵券 ---
        {
            "title": "好友推薦獎勵",     # 改成這個名字
            "discount_value": 100,
            "voucher_type": "reward",   # 獎勵券 (可疊加)
            "min_spend": 500,
            "valid_days": 365,
            "description": "感謝您的推薦！這是給您的獎勵"
        }
    ]

    print("--- 開始檢查/建立預設折扣券 (Vouchers) ---")
    
    for data in default_vouchers:
        # 使用 title (券名) 來檢查是否已經存在
        existing = Voucher.query.filter_by(title=data['title']).first()
        
        if not existing:
            print(f"正在建立: {data['title']} (${data['discount_value']})")
            
            new_voucher = Voucher(
                title=data['title'],
                discount_value=data['discount_value'],
                voucher_type=data['voucher_type'],
                min_spend=data['min_spend'],
                valid_days=data['valid_days'],
                description=data.get('description', ''),
                is_active=True,
                start_time=None,
                end_time=None
            )
            db.session.add(new_voucher)
        else:
            print(f"已存在，跳過: {data['title']}")

    try:
        db.session.commit()
        print("--- 預設折扣券初始化完成 ---")
    except Exception as e:
        db.session.rollback()
        print(f"建立折扣券失敗: {e}")

# ---------------------------------------------------
# ★★★ P.D.K 核心算錢大腦 (含推薦碼折抵) ★★★
# ---------------------------------------------------
def calculate_order_price(user, cart_items, selected_user_vouchers=[], promo_code_obj=None, shipping_method='home', referral_code=None):
    
    # 1. 商品小計
    subtotal = 0
    for item in cart_items:
        price = int(item.get('price', 0))
        qty = int(item.get('quantity') or item.get('count') or item.get('qty') or 1)
        subtotal += price * qty
    
    # 2. 計算折扣細項
    
    # A. 優惠碼 (Promo Code)
    val_promo = promo_code_obj.discount_value if promo_code_obj else 0
    
    # B. 優惠券 (Vouchers)
    voucher_cap = 600 if subtotal >= 1500 else 300
    raw_voucher_sum = 0
    for uv in selected_user_vouchers:
        if subtotal >= uv.voucher.min_spend: 
            raw_voucher_sum += uv.voucher.discount_value
    
    val_voucher = min(raw_voucher_sum, voucher_cap)

    # ★★★ C. 推薦碼 (Referral Code) - 新增邏輯 ★★★
    val_referral = 0
    valid_referrer = None
    
    # 只有當用戶「還沒用過推薦碼」且「有輸入代碼」時才檢查
    if user.is_authenticated and not user.used_referral and referral_code:
        # 尋找代碼的主人
        referrer = User.query.filter_by(referral_code=referral_code).first()
        
        # 驗證：代碼存在 且 不是自己推薦自己
        if referrer and referrer.id != user.id:
            val_referral = 50 # 推薦碼現折 50 元
            valid_referrer = referrer

    # D. 現金折抵總額 (優惠碼 + 優惠券 + 推薦碼) - 不能超過商品總額
    cash_discount_total = min(val_promo + val_voucher + val_referral, subtotal)
    
    # 3. 會員等級折扣 (Member Tier)
    # 是用「扣除現金折抵後」的餘額來計算 % 數
    remaining_amount = subtotal - cash_discount_total
    if remaining_amount < 0:
        remaining_amount = 0
    val_member = 0
    
    if user.is_authenticated:
        if user.member_tier == 'Keep':
            val_member = int(remaining_amount * 0.10) # 9折
        elif user.member_tier == 'Deep':
            val_member = int(remaining_amount * 0.05) # 95折
            
    # 4. 運費計算
    shipping_fee = 0
    original_shipping = 100 if shipping_method == 'home' else 20
    shipping_fee = original_shipping
    
    if subtotal >= 2000:
        shipping_fee = 0
    elif user.is_authenticated:
        if user.member_tier == 'Deep' and shipping_method == 'store':
            shipping_fee = 0
        elif user.member_tier == 'Keep' and user.free_shipping_quota > 0:
            shipping_fee = 0

    # 5. 最終金額
    total_discount = cash_discount_total + val_member
    final_total = subtotal - total_discount + shipping_fee
    
    return {
        'subtotal': subtotal,
        'final_total': max(int(final_total), 1),
        'shipping_fee': shipping_fee,
        'discount_total': total_discount,
        
        # 詳細拆帳數據
        'val_promo': val_promo,
        'val_voucher': val_voucher,
        'val_referral': val_referral, # 回傳推薦碼折多少
        'val_member': val_member,
        'referrer_obj': valid_referrer # 回傳推薦人物件
    }

# ==============================================================================
# 4. 前台路由 (Frontend Routes)
# ==============================================================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/member_promotions')
def member_promotions():
    return render_template('member_promotions.html')

# --- 最新活動頁面 ---
@app.route('/promotions')
def promotions():
    return render_template('promotions.html')

@app.route('/shampoo')
def shampoo_page():
    # 加上 .order_by(Product.id) 讓前台依照編號排序
    products = Product.query.filter_by(category='shampoo').order_by(Product.id).all()
    page_info = {'title_zh': '洗髮精', 'title_en': 'SHAMPOO'}
    return render_template('shampoo.html', products=products, page_info=page_info)

@app.route('/quiz')
def quiz_page():
    # 撈出所有商品，打包給前端 JS
    all_products = Product.query.all()
    product_dict = {}
    for p in all_products:
        product_dict[p.id] = {
            'name': p.name,
            'price': p.price,
            'image': url_for('static', filename=p.image) if p.image else '',
            'description': p.description or ""  # ★★★ 新增：把資料庫的商品描述抓出來
        }
    return render_template('quiz.html', products_json=json.dumps(product_dict))
# ==========================================
# ★ P.D.K AI 智能諮詢師 (Gemini 串接)
# ==========================================
# 設定 API Key
gemini_api_key = os.environ.get('GEMINI_API_KEY')
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

# PDK AI 的最高指導原則 (System Prompt)
PDK_SYSTEM_PROMPT = """
你現在是台灣頂級沙龍品牌「P.D.K」的資深線上 AI 諮詢師。
你的說話風格：俐落、專業、有經驗、不講客套話、直切重點。不要使用過多的表情符號，語氣像一位在沙龍裡為客人檢視頭皮的真實設計師。

【最高指導原則】
1. 保養邏輯：「先救頭皮，再修髮絲」。洗髮精針對頭皮狀況挑選，潤護產品針對髮絲受損程度挑選。
2. 對話節奏：引導式問答。每次只問 1 到 2 個問題，不要一次問完所有事情。從「頭皮出油/敏感狀況」開始問起，接著問「染燙受損狀況」，最後問「日常吹整習慣(如使用電棒)」。
3. 圖片分析：如果客人上傳了圖片，請像專業設計師一樣，先客觀描述你看到的髮況（例如：看起來髮尾有些分岔、頭皮有點泛紅），再給出建議。
4. 最終推薦：在收集完足夠資訊後，請給出一段【髮況分析】，並給出明確的【命定配方】(1款洗髮精 + 1款護理素 + 1款免沖洗護髮/頭皮水)。

【P.D.K 產品圖鑑與對應邏輯】
- 洗髮精 (洗頭皮為主)：
  1. 淨化控油調理洗髮精：極度出油、頭皮味重、下午就塌。
  2. 輕柔活力洗髮精：一般出油、想要無重力蓬鬆感。
  3. 淨屑舒活洗髮精：有頭皮屑、容易乾癢。
  4. 翅藻植翠洗髮精：正常/偏乾頭皮、想要水感平衡。
  5. 極致燙染修復洗髮精：剛漂髮、重度染燙受損 (這是特例，以救髮絲為主)。
- 潤護乳 (修護髮絲)：
  1. 極致燙染修復護理素：漂髮、重度受損、稻草髮。
  2. 翅藻植翠極致乳：一般受損、未染燙的日常保養。
- 免沖洗與頭皮保養：
  1. 全方位頭皮調理液(頭皮水)：頭皮發炎、紅癢、想強健髮根。
  2. 彈力亮澤護色修護液(水/噴霧狀)：常用電棒/離子夾、需要抗熱防護、剛漂髮。
  3. 芳香質感精華乳(乳狀)：不喜歡油膩感、吹髮前保濕打底。
  4. 黃金堅果E油(油狀)：極度乾枯、分岔嚴重、需要強烈光澤。
  5. 摩洛哥Q10精華修復液(油/精華狀)：易斷裂、脆弱、細軟髮、容易打結。

切記：絕對不要推薦造型用的「髮蠟」，我們專注於理療與保養。如果客人一開始只說「你好」，請主動詢問他的頭皮出油狀況。
"""

@app.route('/ai_consult')
@login_required
def ai_consult():
    return render_template('ai_test.html')

@app.route('/api/ai_chat', methods=['POST'])
@login_required
def api_ai_chat():
    if not gemini_api_key:
        return jsonify({'success': False, 'message': '系統未設定 AI 金鑰，請聯絡管理員。'})
    
    data = request.get_json()
    user_msg = data.get('message', '')
    image_base64 = data.get('image', None) # 接收圖片
    chat_history = data.get('history', []) # 接收過去的對話紀錄
    
    try:
        # 使用 Gemini 1.5 Flash 模型 (速度快、支援看圖)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-latest",
            system_instruction=PDK_SYSTEM_PROMPT
        )
        
        # 整理歷史紀錄格式給 Gemini
        formatted_history = []
        for msg in chat_history:
            role = "user" if msg['sender'] == 'user' else "model"
            formatted_history.append({"role": role, "parts": [msg['text']]})
            
        chat = model.start_chat(history=formatted_history)
        
        # 處理客人傳來的訊息 (判斷有沒有附照片)
        if image_base64:
            # 將 Base64 轉回圖片物件
            image_data = base64.b64decode(image_base64.split(',')[1])
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_data
            }
            response = chat.send_message([user_msg, image_part])
        else:
            response = chat.send_message(user_msg)
            
        return jsonify({'success': True, 'reply': response.text})
        
    except Exception as e:
        print(f"AI 錯誤: {e}")
        return jsonify({'success': False, 'message': '抱歉，設計師目前在忙，請稍後再試！'})
@app.route('/category/<string:cat_name>')
def category_page(cat_name):
    category_data = {
        'shampoo': {'title_zh': '洗髮精', 'title_en': 'SHAMPOO'},
        'conditioner': {'title_zh': '潤髮乳', 'title_en': 'CONDITIONER'},
        'haircare': {'title_zh': '頭髮護理', 'title_en': 'HAIR CARE'},
        'otherproduct': {'title_zh': '其他產品', 'title_en': 'OTHERS'}
    }
    page_info = category_data.get(cat_name, {'title_zh': '精選商品', 'title_en': 'PRODUCTS'})
    # 加上 .order_by(Product.id) 讓前台依照編號排序
    products = Product.query.filter_by(category=cat_name).order_by(Product.id).all()
    return render_template('shampoo.html', products=products, page_info=page_info)

# ★★★ 修改這裡：改成讀取資料庫，並使用通用模版 ★★★
@app.route('/product/<product_id>')
def product_page(product_id):
    # 去資料庫抓這個商品，抓不到會回傳 404
    product = Product.query.get_or_404(product_id)
    # 傳給通用的 product_detail.html
    return render_template('product_detail.html', product=product)
# ==========================================
# ★ 試用品活動專區
# ==========================================
TOTAL_TRIAL_QUOTA = 100  # ★ 這裡設定總份數，以後想加碼直接改這裡
@app.route('/trial_checkout')
@login_required
def trial_checkout():
    # 1. 計算目前已經發放了幾份 (排除已取消的訂單)
    used_trial_count = Order.query.filter(
        Order.order_no.startswith('TRIAL-'),
        Order.status != 'cancelled'
    ).count()
    
    remaining_quota = max(0, TOTAL_TRIAL_QUOTA - used_trial_count)
    progress_percent = min(100, int((used_trial_count / TOTAL_TRIAL_QUOTA) * 100))

    # 2. 檢查是否已經領過 (防呆機制：一人一次)
    has_trial = Order.query.filter(
        Order.user_id == current_user.id, 
        Order.order_no.startswith('TRIAL-')
    ).first()
    
    if has_trial:
        flash('您已經參與過試用品活動囉！', 'warning')
        return redirect(url_for('home'))
        
    # 把進度條資料傳給前端
    return render_template('trial_checkout.html', 
                           total_quota=TOTAL_TRIAL_QUOTA, 
                           remaining_quota=remaining_quota, 
                           progress_percent=progress_percent)

@app.route('/submit_trial_order', methods=['POST'])
@login_required
def submit_trial_order():
    # ★ 防呆 1：檢查是否已經被搶光了 (防止客人在頁面停留太久，別人已經搶完)
    used_trial_count = Order.query.filter(
        Order.order_no.startswith('TRIAL-'),
        Order.status != 'cancelled'
    ).count()
    
    if used_trial_count >= TOTAL_TRIAL_QUOTA:
        flash('非常抱歉，限量試用品已被索取完畢！', 'error')
        return redirect(url_for('home'))

    # ★ 防呆 2：檢查是否已經領過
    if Order.query.filter(Order.user_id == current_user.id, Order.order_no.startswith('TRIAL-')).first():
        flash('您已經參與過試用品活動囉！', 'error')
        return redirect(url_for('home'))

    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        store_name = request.form.get('store_name')
        payment_method = request.form.get('payment_method')
        
        # ★★★ 修改：分別抓取洗髮精與護髮油，並組合成字串 ★★★
        trial_shampoo = request.form.get('trial_shampoo') 
        trial_oil = request.form.get('trial_oil')
        selected_product = f"{trial_shampoo} ＋ {trial_oil}" 
        
        update_profile = request.form.get('update_profile')
        # 智慧回填會員資料
        if not current_user.real_name or update_profile == 'yes':
            current_user.real_name = name
        if not current_user.phone or update_profile == 'yes':
            current_user.phone = phone
        if not current_user.store_info or update_profile == 'yes':
            current_user.store_info = store_name

        # 建立試用品專屬訂單編號
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        rand_num = random.randint(1000, 9999)
        order_no = f"TRIAL-{date_str}-{rand_num}"

        # 虛擬購物車內容 (寫入訂單明細供後台查看)
        cart_items = [{"name": f"【試用品】{selected_product}", "price": 38, "qty": 1, "image": ""}]

        new_order = Order(
            order_no=order_no,
            user_id=current_user.id,
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            shipping_method='store', # 強制超商
            address=store_name,
            payment_method=payment_method,
            total_amount=0,       # 商品 $0
            shipping_fee=38,      # 物流處理費 $38
            discount_amount=0,
            final_total=38,       # 總計 $38
            cart_items=json.dumps(cart_items, ensure_ascii=False),
            status='pending'
        )

        db.session.add(new_order)
        db.session.commit()

        # 如果是 LINE Pay，走相同的 LINE Pay 流程
        if payment_method == 'linepay':
            uri = "/v3/payments/request"
            nonce = str(uuid.uuid4())
            
            line_product = {
                "id": "trial_1",
                "name": f"P.D.K 試用品領取物流費",
                "quantity": 1,
                "price": 38
            }

            payload = {
                "amount": 38,
                "currency": "TWD",
                "orderId": order_no,
                "packages": [{
                    "id": "pack_trial",
                    "amount": 38,
                    "name": "P.D.K 試用品",
                    "products": [line_product]
                }],
                "redirectUrls": {
                    "confirmUrl": f"{SERVER_URL}/linepay/confirm",
                    "cancelUrl": f"{SERVER_URL}/trial_checkout"
                }
            }
            
            payload_str = json.dumps(payload)
            signature = generate_line_pay_signature(uri, payload_str, nonce)
            headers = {
                "Content-Type": "application/json",
                "X-LINE-ChannelId": LINE_PAY_ID,
                "X-LINE-Authorization-Nonce": nonce,
                "X-LINE-Authorization": signature
            }
            
            res = requests.post(LINE_PAY_API_URL + uri, headers=headers, data=payload_str)
            res_data = res.json()
            
            if res_data.get('returnCode') == '0000':
                return redirect(res_data['info']['paymentUrl']['web'])
            else:
                flash(f"LINE Pay 請求失敗: {res_data.get('returnMessage')}", 'error')
                return redirect(url_for('trial_checkout'))
        try:
            print("正在嘗試寄送試用品確認信...")
            send_trial_confirmation_email(new_order, selected_product)  # ★ 使用試用品專屬信件
            send_merchant_trial_email(new_order, selected_product)      # ★ 使用試用品專屬信件
        except Exception as e:
            print(f"試用品寄信失敗: {e}")
            
        return render_template('trial_success.html', 
                               order_id=order_no, 
                               name=name, 
                               final_total=38, 
                               payment_method=payment_method, 
                               order=new_order)

    except Exception as e:
        print(f"Submit Trial Order Error: {e}")
        db.session.rollback()
        return f"建立失敗: {str(e)}", 500
# ----------------------
# 結帳頁面 (修改：傳送折扣券資料給前端)
# ----------------------
@app.route('/checkout')
@login_required  # ★ 強制登入才能結帳
def checkout_page():
    # 1. 抓取會員「未使用」且「未過期」的折扣券
    my_vouchers = []
    now = datetime.datetime.now()
    
    # 搜尋該使用者的 UserVoucher，且 is_used=False
    raw_vouchers = UserVoucher.query.filter_by(user_id=current_user.id, is_used=False).all()
    
    for uv in raw_vouchers:
        # A. 檢查是否過期
        if uv.expiry_date and uv.expiry_date < now:
            continue
        # B. 檢查 Voucher 定義檔是否還上架中
        if not uv.voucher.is_active:
            continue
            
        # C. 轉換成字典格式 (因為 SQLAlchemy 物件不能直接轉 JSON 給前端 JS 用)
        my_vouchers.append({
            'id': uv.id,
            'expiry_date': uv.expiry_date.strftime('%Y-%m-%d') if uv.expiry_date else '永久',
            'voucher': {
                'title': uv.voucher.title,
                'voucher_type': uv.voucher.voucher_type,
                'min_spend': uv.voucher.min_spend,
                'discount_value': uv.voucher.discount_value
            }
        })

    # 2. 回傳頁面 (將 vouchers 傳進去)
    return render_template('checkout.html', vouchers=my_vouchers)

# ★★★ 新增：處理「點擊愛心」的動作 (AJAX) ★★★
@app.route('/toggle_wishlist', methods=['POST'])
@login_required
def toggle_wishlist():
    data = request.get_json()
    p_id = data.get('product_id')
    
    # 檢查是否已收藏
    wish = Wishlist.query.filter_by(user_id=current_user.id, product_id=p_id).first()
    
    if wish:
        db.session.delete(wish) # 已收藏 -> 移除
        action = 'removed'
    else:
        new_wish = Wishlist(user_id=current_user.id, product_id=p_id) # 未收藏 -> 新增
        db.session.add(new_wish)
        action = 'added'
        
    db.session.commit()
    return jsonify({'success': True, 'action': action})

# ★★★ 新增：「我的收藏」頁面 (共用 shampoo.html 模板) ★★★
@app.route('/wishlist')
@login_required
def wishlist_page():
    # 1. 找出該使用者的所有收藏紀錄
    wishes = Wishlist.query.filter_by(user_id=current_user.id).all()
    p_ids = [w.product_id for w in wishes]
    
    # 2. 如果有收藏，去 Product 資料表抓出這些商品的完整資料
    if p_ids:
        products = Product.query.filter(Product.id.in_(p_ids)).all()
    else:
        products = []
        
    # 3. 設定頁面標題，並重用 shampoo.html
    page_info = {'title_zh': '我的收藏', 'title_en': 'MY WISHLIST'}
    
    # 傳入 is_wishlist_page=True，方便前端做特殊處理
    return render_template('shampoo.html', products=products, page_info=page_info, is_wishlist_page=True)

# ==============================================================================
# ★★★ 新增：Email 寄送輔助函式 (放在路由之前) ★★★
# ==============================================================================
# 修改 1：訂單確認信 (給客人) - 改用 Brevo
def send_order_confirmation_email(order):
    try:
        # 準備信件內容 (這裡簡單轉成字串，您也可以之後優化成 HTML)
        subject = f"【P.D.K】訂單確認通知 (編號：{order.order_no})"
        content = f"""
        <html>
        <body>
            <h2>感謝您的訂單！</h2>
            <p>親愛的 {order.customer_name}，我們已經收到您的訂單。</p>
            <p>訂單編號：{order.order_no}</p>
            <p>訂單金額：NT$ {order.final_total}</p>
            <p>我們會盡快為您安排出貨。</p>
        </body>
        </html>
        """
        # 使用背景發送 (Thread)
        Thread(target=send_via_brevo, args=(order.customer_email, subject, content)).start()
        print(f"✅ 訂單確認信已排入背景發送 (訂單 {order.order_no})")
    except Exception as e:
        print(f"❌ 訂單確認信發送失敗: {e}")

# 修改 2：商家通知信 (給您自己) - 改用 Brevo
def send_merchant_new_order_email(order):
    try:
        subject = f"【新訂單】#{order.order_no} - {order.customer_name} - ${order.final_total}"
        # 這裡的收件人請改成您自己的 Email
        merchant_email = "pdk.salon.office@gmail.com" 
        
        content = f"""
        <html>
        <body>
            <h2>老闆，有新訂單了！</h2>
            <p>訂單編號：{order.order_no}</p>
            <p>顧客姓名：{order.customer_name}</p>
            <p>訂單金額：NT$ {order.final_total}</p>
            <p>請記得登入後台查看詳細內容並安排出貨。</p>
        </body>
        </html>
        """
        # 使用背景發送 (Thread)
        Thread(target=send_via_brevo, args=(merchant_email, subject, content)).start()
        print(f"✅ 商家通知信已排入背景發送")
    except Exception as e:
        print(f"❌ 商家通知信發送失敗: {e}")

# 修改：折扣券通知信 - 改用 Brevo + 背景發送
def send_voucher_notification_email(user, voucher_title, amount, description):
    try:
        subject = f"【P.D.K】恭喜獲得 ${amount} 折扣券！"
        content = f"""
        <html>
        <body>
            <h2>恭喜您獲得專屬優惠！</h2>
            <p>親愛的 {user.name} 您好，</p>
            <p>我們已將一張 <b>{voucher_title}</b> 存入您的帳戶。</p>
            <p>折抵金額：NT$ {amount}</p>
            <p>說明：{description}</p>
            <p><a href="{url_for('home', _external=True)}">立即使用</a></p>
        </body>
        </html>
        """
        Thread(target=send_via_brevo, args=(user.email, subject, content)).start()
        print(f"✅ 折扣券通知信已背景發送至 {user.email}")
    except Exception as e:
        print(f"❌ 寄送折扣券通知信失敗: {e}")
        

def send_shipping_notification_email(order):
    try:
        subject = f"【P.D.K】商品出貨通知 (編號：{order.order_no})"
        content = f"""
        <html>
        <body>
            <h2>您的商品已出貨！</h2>
            <p>親愛的 {order.customer_name}，</p>
            <p>您的訂單 <b>{order.order_no}</b> 已經安排出貨。</p>
            <p>感謝您的耐心等待，商品將在近期送達。</p>
        </body>
        </html>
        """
        # 改用 Brevo 背景發送
        Thread(target=send_via_brevo, args=(order.customer_email, subject, content)).start()
        print(f"✅ 出貨通知信已排入背景發送 (訂單 {order.order_no})")
    except Exception as e:
        print(f"❌ 出貨通知信發送失敗: {e}")
# --- 試用品活動專屬寄信 ---
def send_trial_confirmation_email(order, product_name):
    try:
        subject = f"【P.D.K】試用品活動！感謝您的參與"
        content = f"""
        <html>
        <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
            <p>{order.customer_name} 您好，</p>
            <p>感謝您參與 P.D.K 的專屬體驗活動！我們已成功收到您的試用品索取申請囉。</p>
            <p>訂單編號：{order.order_no}<br>
            索取商品：{product_name}<br>
            物流費用：NT$ 38</p>
            <p>我們將於 1-3 個工作天內為您安排出貨，商品送達指定的 7-11 門市時會再以簡訊通知您。<br>
            期待 P.D.K 能為您的頭皮與髮絲帶來更好的養護體驗！</p>
        </body>
        </html>
        """
        Thread(target=send_via_brevo, args=(order.customer_email, subject, content)).start()
        print(f"✅ 試用品確認信已排入背景發送 (訂單 {order.order_no})")
    except Exception as e:
        print(f"❌ 試用品確認信發送失敗: {e}")

def send_merchant_trial_email(order, product_name):
    try:
        subject = f"【試用品新單】#{order.order_no} - {order.customer_name} 索取了試用品"
        merchant_email = "pdk.salon.office@gmail.com" 
        
        content = f"""
        <html>
        <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
            <h2>老闆，活動有人參加了，有客人索取試用品！</h2>
            <p>訂單編號：{order.order_no}</p>
            <p>顧客姓名：{order.customer_name}</p>
            <p>索取商品：{product_name}</p>
            <p>請登入後台的「試用品訂單」專區查看詳細資訊並安排出貨。</p>
        </body>
        </html>
        """
        Thread(target=send_via_brevo, args=(merchant_email, subject, content)).start()
        print(f"✅ 商家試用單通知信已排入背景發送")
    except Exception as e:
        print(f"❌ 商家試用單通知信發送失敗: {e}")
# ==============================================================================
# ★★★ 新增區塊 2：優惠券檢查 API (給前端 JS 呼叫) ★★★
# ==============================================================================

@app.route('/api/check_coupon', methods=['POST'])
def check_coupon():
    # 1. 檢查是否登入
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': '請先登入會員即可使用優惠券'})

    data = request.get_json()
    code = data.get('code', '').upper().strip()
    cart_total = int(data.get('amount', 0)) # 前端傳來的商品小計

    coupon = Coupon.query.filter_by(code=code).first()
    
    # 2. 檢查基本存在與啟用
    if not coupon:
        return jsonify({'success': False, 'message': '優惠碼不存在'})
    if not coupon.is_active:
        return jsonify({'success': False, 'message': '此優惠活動已結束'})

    # 3. 檢查日期
    now = datetime.datetime.now()
    if coupon.start_date and now < coupon.start_date:
        return jsonify({'success': False, 'message': '優惠活動尚未開始'})
    if coupon.end_date and now > coupon.end_date:
        return jsonify({'success': False, 'message': '優惠券已過期'})

    # 4. 檢查全站總數量
    if coupon.used_count >= coupon.usage_limit:
        return jsonify({'success': False, 'message': '此優惠券已被兌換完畢'})

    # 5. ★ 檢查個人使用次數 (查詢 CouponUsage 表)
    if coupon.per_user_limit > 0:
        user_usage = CouponUsage.query.filter_by(user_id=current_user.id, coupon_id=coupon.id).count()
        if user_usage >= coupon.per_user_limit:
            return jsonify({'success': False, 'message': '您已使用過此優惠券，無法重複使用'})

    # 6. 檢查最低消費門檻 (提供精確提示)
    if cart_total < coupon.min_spend:
        diff = coupon.min_spend - cart_total
        return jsonify({'success': False, 'message': f'未達使用門檻，再消費 NT${diff} 即可使用！'})

    # 7. 計算折扣
    discount_amount = 0
    if coupon.discount_type == 'fixed':
        discount_amount = coupon.discount_value
    elif coupon.discount_type == 'percent':
        # 例如 10 代表 10% off (打九折) -> 折扣 = 總價 * 0.1
        discount_amount = int(cart_total * (coupon.discount_value / 100))

    # 避免折扣大於總金額
    if discount_amount > cart_total:
        discount_amount = cart_total

    return jsonify({
        'success': True,
        'discount_amount': discount_amount,
        'message': f'優惠券已套用！折抵 NT${discount_amount}'
    })

# ---------------------------------------------------
# ★★★ 會員等級檢查與更新機制 ★★★
# ---------------------------------------------------

def check_membership_upgrade(user):
    # 1. 撈出該用戶「有效」的訂單
    # 只計算「已付款、已出貨、已完成」
    valid_statuses = ['paid', 'shipped', 'done']
    
    valid_orders = Order.query.filter(
        Order.user_id == user.id,
        Order.status.in_(valid_statuses),
        ~Order.order_no.startswith('TRIAL-')
    ).all()

    # 2. 計算累積數據
    # 規則：消費金額 = 實付總額 (final_total) - 運費 (shipping_fee)
    current_spend = 0
    for order in valid_orders:
        final = order.final_total or 0
        shipping = order.shipping_fee or 0
        # 確保不會變成負數
        item_spend = max(0, final - shipping)
        current_spend += item_spend

    current_order_count = len(valid_orders)

    # 3. 更新用戶數據庫 (即時更新顯示)
    user.total_spend = current_spend
    user.orders_count = current_order_count

    # 4. 判斷新等級 (由最高級往下判斷)
    new_tier = 'General' # 預設

    # Keep: 滿5000元 或 滿5單
    if current_spend >= 5000 or current_order_count >= 5:
        new_tier = 'Keep'
    # Deep: 滿2500元
    elif current_spend >= 2500:
        new_tier = 'Deep'
    # Pure: 只要有 1 單有效訂單
    elif current_order_count >= 1:
        new_tier = 'Pure'
        
    # 5. 執行升降級邏輯
    old_tier = user.member_tier  # ★ 先記住舊等級，用於比較

    if old_tier != new_tier:
        print(f"用戶 {user.name} 等級變更: {old_tier} -> {new_tier}")

        # --- A. 處理免運額度 ---
        # 升級到 Keep (發放 5 次免運)
        if new_tier == 'Keep' and old_tier != 'Keep':
            # 只有當目前沒有額度時才補滿，避免重複觸發
            if user.free_shipping_quota == 0:
                user.free_shipping_quota = 5
        
        # 從 Keep 降級 (收回免運)
        if old_tier == 'Keep' and new_tier != 'Keep':
            user.free_shipping_quota = 0
            
        # --- B. 更新等級與效期 ---
        user.member_tier = new_tier
        # 升級或變更後，效期展延一年
        user.member_expiry = datetime.datetime.now() + datetime.timedelta(days=365)

        # --- C. 自動產生推薦碼 (流水號格式) ---
        if new_tier in ['Pure', 'Deep', 'Keep'] and not user.referral_code:
            user.referral_code = f"PDK-{user.id:06d}"
            print(f"已產生推薦碼: {user.referral_code}")

        # --- D. ★★★ 新增：升級時順便檢查並補發生日禮金 ★★★ ---
        # 條件：升級到有資格的等級 + 有設定生日 + 生日是這個月
        if new_tier in ['Pure', 'Deep', 'Keep'] and user.birthday:
            today = datetime.date.today()
            if user.birthday.month == today.month:
                
                # 定義各等級金額
                rewards = {'Pure': 150, 'Deep': 200, 'Keep': 300}
                amount = rewards.get(new_tier, 0)
                
                if amount > 0:
                    # 1. 找券的母本，沒有就自動建立 (防呆)
                    v_title = f"{new_tier} 會員生日禮"
                    voucher = Voucher.query.filter_by(title=v_title).first()
                    
                    if not voucher:
                        print(f"建立缺少的生日券母本: {v_title}")
                        voucher = Voucher(
                            title=v_title,
                            discount_value=amount,
                            voucher_type='activity',
                            min_spend=0,
                            valid_days=365,
                            description=f'祝您生日快樂！{new_tier} 會員專屬禮金'
                        )
                        db.session.add(voucher)
                        db.session.flush() # 取得 ID

                    # 2. 檢查「今年」是否已經領過這張券 (避免重複發)
                    # 邏輯：檢查 360 天內是否有領過同一個 ID 的券
                    check_start = datetime.datetime.now() - datetime.timedelta(days=360)
                    has_received = UserVoucher.query.filter(
                        UserVoucher.user_id == user.id,
                        UserVoucher.voucher_id == voucher.id,
                        UserVoucher.created_at >= check_start
                    ).first()

                    if not has_received:
                        print(f"★ {user.name} 升級且為當月壽星，補發生日禮金！")
                        new_uv = UserVoucher(
                            user_id=user.id,
                            voucher_id=voucher.id,
                            expiry_date=datetime.datetime.now() + datetime.timedelta(days=365)
                        )
                        db.session.add(new_uv)
                        # 這裡可以視需求呼叫寄信函式

    db.session.commit()
# ----------------------
# 提交訂單路由 (Final Fix)
# ----------------------
@app.route('/submit_order', methods=['POST'])
@login_required 
def submit_order():
    try:
        # 1. 接收資料
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        shipping_method = request.form.get('shipping_method')
        payment_method = request.form.get('payment_method')
        
        # 2. 折扣與推薦碼
        raw_code = request.form.get('promo_code')
        promo_code_str = raw_code.strip().upper() if raw_code else None
        voucher_ids_str = request.form.get('selected_vouchers') 
        
        referral_code_input = request.form.get('referral_code')
        if referral_code_input:
            referral_code_input = referral_code_input.strip()

        # 3. 購物車與地址
        cart_data_str = request.form.get('cart_data')
        cart_items = json.loads(cart_data_str) if cart_data_str else []
        
        address = ""
        if shipping_method == 'home':
            city = request.form.get('city') or ""
            district = request.form.get('district') or ""
            addr_detail = request.form.get('address') or ""
            address = f"{city}{district}{addr_detail}"
        elif shipping_method == 'store':
            store_name = request.form.get('store_name') or "未指定"
            address = store_name

        # 準備物件
        valid_promo_obj = None
        if promo_code_str:
            c = Coupon.query.filter_by(code=promo_code_str).first()
            if c and c.is_active:
                valid_promo_obj = c

        selected_user_vouchers = []
        if voucher_ids_str:
            v_ids = voucher_ids_str.split(',') 
            for vid in v_ids:
                if vid.isdigit():
                    uv = UserVoucher.query.get(int(vid))
                    if uv and uv.user_id == current_user.id and not uv.is_used:
                        selected_user_vouchers.append(uv)

        # 4. ★★★ 呼叫算錢大腦 ★★★
        result = calculate_order_price(
            user=current_user,
            cart_items=cart_items,
            selected_user_vouchers=selected_user_vouchers,
            promo_code_obj=valid_promo_obj,
            shipping_method=shipping_method,
            referral_code=referral_code_input 
        )
        
        # 5. 扣除免運次數
        if result['shipping_fee'] == 0 and result['subtotal'] < 2000:
            if current_user.member_tier == 'Keep' and current_user.free_shipping_quota > 0:
                current_user.free_shipping_quota -= 1

        # 6. 建立訂單
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        rand_num = random.randint(1000, 9999)
        order_no = f"PDK-{date_str}-{rand_num}"

        # ★★★ 修正點：統一使用 result 回傳的推薦人 (避免邏輯不一致) ★★★
        valid_referrer = result.get('referrer_obj')
        
        store_name = request.form.get('store_name') # 確保有抓到超商門市
        update_profile = request.form.get('update_profile') # 抓取是否打勾

        # ==========================================
        # ★★★ 智慧回填與更新會員資料 ★★★
        # ==========================================
        if current_user.is_authenticated:
            # 1. 靜默更新 (情境 A)：如果資料庫原本是空的，直接幫他填入
            if not current_user.real_name:
                current_user.real_name = name
            if not current_user.phone:
                current_user.phone = phone
            
            if shipping_method == 'home' and not current_user.address:
                current_user.address = address
            elif shipping_method == 'store' and not current_user.store_info:
                current_user.store_info = store_name

            # 2. 勾勾更新 (情境 C)：如果客人有打勾「設為預設」
            if update_profile == 'yes':
                current_user.real_name = name
                current_user.phone = phone
                if shipping_method == 'home':
                    current_user.address = address
                elif shipping_method == 'store':
                    current_user.store_info = store_name
        new_order = Order(
            order_no=order_no,
            user_id=current_user.id,
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            shipping_method=shipping_method,
            address=address,
            payment_method=payment_method,
            
            total_amount=result['subtotal'],
            shipping_fee=result['shipping_fee'],
            discount_amount=result['discount_total'],
            final_total=result['final_total'],
            
            discount_promo=result['val_promo'],
            discount_voucher=result['val_voucher'],
            discount_member=result['val_member'],
            
            # 這裡只記錄推薦人，不發獎勵
            referrer_id=valid_referrer.id if valid_referrer else None,
            cart_items=json.dumps(cart_items, ensure_ascii=False),
            status='pending'
        )

        db.session.add(new_order)
        db.session.flush()

        # 7. 核銷優惠券與代碼
        if valid_promo_obj:
            usage = CouponUsage(user_id=current_user.id, coupon_id=valid_promo_obj.id, order_id=new_order.id)
            valid_promo_obj.used_count += 1
            db.session.add(usage)

        for uv in selected_user_vouchers:
            uv.is_used = True
        
        # ★★★ 標記用戶已使用過推薦 (只能用一次) ★★★
        if valid_referrer:
            current_user.used_referral = True

        db.session.commit()

        # 8. 檢查升級
        try:
            check_membership_upgrade(current_user)
        except:
            pass
        
        # ==========================================
        # ★ 9. 判斷付款方式：如果是 LINE Pay，跳轉去付款
        # ==========================================
        if payment_method == 'linepay':
            uri = "/v3/payments/request"
            nonce = str(uuid.uuid4())
            
            # --- 🚀 升級版：動態抓取購物車「所有」商品名稱與數量 ---
            display_name = "P.D.K 官網訂單"
            img_url = ""
            
            if cart_items:
                # 1. 把所有商品名稱和數量串起來 (例如: 洗髮精 x1 + 潤髮乳 x2)
                item_details = []
                for item in cart_items:
                    item_name = item.get('name', 'P.D.K 商品')
                    qty = item.get('quantity') or item.get('count') or item.get('qty') or 1
                    item_details.append(f"{item_name} x{qty}")
                
                # 用 " + " 把文字連起來
                display_name = " + ".join(item_details)
                
                # 如果字數太長 (超過 100 字)，LINE Pay 會報錯，所以我們做個截斷保護
                if len(display_name) > 100:
                    display_name = display_name[:95] + " 等商品"
                
                # 2. 抓取第一張圖片當作代表圖
                raw_img = cart_items[0].get('image', '')
                if raw_img:
                    if raw_img.startswith('http'):
                        img_url = raw_img
                    elif raw_img.startswith('/'):
                        img_url = f"{SERVER_URL}{raw_img}"
                    else:
                        img_url = f"{SERVER_URL}/{raw_img}"

            # 建立 LINE Pay 產品明細字典 (打包成一個安全的商品)
            line_product = {
                "id": "prod_1",
                "name": display_name,  # ★ 畫面會顯示：洗髮精 x1 + 潤髮乳 x2
                "quantity": 1,         # 數量固定寫 1 (整筆訂單打包算一個金額)
                "price": result['final_total']
            }
            if img_url:
                line_product["imageUrl"] = img_url

            # 準備給 LINE Pay 的訂單資料
            payload = {
                "amount": result['final_total'],
                "currency": "TWD",
                "orderId": order_no,
                "packages": [{
                    "id": "pack_1",
                    "amount": result['final_total'],
                    "name": "P.D.K 官網訂單",
                    "products": [line_product]
                }],
                "redirectUrls": {
                    "confirmUrl": f"{SERVER_URL}/linepay/confirm", # 付款成功後回傳這裡
                    "cancelUrl": f"{SERVER_URL}/checkout"          # 取消付款回結帳頁
                },
                # ==========================================
                # ★★★ 新增：結帳時預設加入官方帳號好友 ★★★
                # ==========================================
                "options": {
                    "addFriends": [
                        {
                            "type": "lineAt",
                            "idList": ["@213nuoyq"]  # ★ 你的 P.D.K 官方帳號 ID
                        }
                    ]
                }
            }
            
            payload_str = json.dumps(payload)
            
            signature = generate_line_pay_signature(uri, payload_str, nonce)
            
            headers = {
                "Content-Type": "application/json",
                "X-LINE-ChannelId": LINE_PAY_ID,
                "X-LINE-Authorization-Nonce": nonce,
                "X-LINE-Authorization": signature
            }
            
            # 發送請求給 LINE Pay
            res = requests.post(LINE_PAY_API_URL + uri, headers=headers, data=payload_str)
            res_data = res.json()
            
            if res_data.get('returnCode') == '0000':
                # 成功拿到專屬付款網址，把客人導向該網址
                payment_url = res_data['info']['paymentUrl']['web']
                return redirect(payment_url)
            else:
                flash(f"LINE Pay 請求失敗: {res_data.get('returnMessage')}", 'error')
                return redirect(url_for('checkout_page'))

        # ==========================================
        # ★ 10. 如果不是 LINE Pay (貨到付款/轉帳)，直接完成並寄信
        # ==========================================
        try:
            print("正在嘗試寄送訂單確認信...")
            send_order_confirmation_email(new_order)
            send_merchant_new_order_email(new_order)
        except Exception as e:
            print(f"寄信失敗，但訂單已建立。錯誤原因: {e}")
        
        return render_template('order_success.html', 
                               order_id=order_no, 
                               name=name, 
                               final_total=result['final_total'],
                               payment_method=payment_method,
                               order=new_order)

    except Exception as e:
        print(f"Submit Order Error: {e}")
        db.session.rollback()
        return f"訂單建立失敗: {str(e)}", 500


# ==============================================================================
# ★★★ LINE Pay 授權與確認路由 ★★★
# ==============================================================================
@app.route('/linepay/confirm')
def linepay_confirm():
    # 1. LINE Pay 會把交易序號跟訂單編號放在網址後面傳回來
    transaction_id = request.args.get('transactionId')
    order_no = request.args.get('orderId')

    if not transaction_id or not order_no:
        flash('找不到交易序號，付款失敗', 'error')
        return redirect(url_for('home'))

    # 2. 去資料庫找這筆訂單
    order = Order.query.filter_by(order_no=order_no).first()
    if not order:
        flash('找不到此訂單', 'error')
        return redirect(url_for('home'))

    # 3. 執行 Confirm API (告訴 LINE Pay：我確實要收這筆錢了)
    uri = f"/v3/payments/{transaction_id}/confirm"
    nonce = str(uuid.uuid4())
    payload = {
        "amount": order.final_total,
        "currency": "TWD"
    }
    payload_str = json.dumps(payload)
    signature = generate_line_pay_signature(uri, payload_str, nonce)
    
    headers = {
        "Content-Type": "application/json",
        "X-LINE-ChannelId": LINE_PAY_ID,
        "X-LINE-Authorization-Nonce": nonce,
        "X-LINE-Authorization": signature
    }

    try:
        res = requests.post(LINE_PAY_API_URL + uri, headers=headers, data=payload_str)
        res_data = res.json()

        if res_data.get('returnCode') == '0000':
            # ★★★ 付款成功！更新資料庫 ★★★
            order.status = 'paid'  # 狀態改為已付款
            order.paid_at = datetime.datetime.now()
            order.linepay_transaction_id = transaction_id # 存入專屬交易碼
            db.session.commit()

            # ★★★ 新增分流：判斷是一般訂單還是試用品訂單 ★★★
            try:
                if order.order_no.startswith('TRIAL-'):
                    # 試用品訂單：抓取商品名稱並寄專屬信
                    cart_data = json.loads(order.cart_items)
                    product_name = cart_data[0].get('name', '').replace('【試用品】', '').strip()
                    send_trial_confirmation_email(order, product_name)
                    send_merchant_trial_email(order, product_name)
                else:
                    # 一般訂單：寄一般信
                    send_order_confirmation_email(order)
                    send_merchant_new_order_email(order)
            except Exception as e:
                print(f"寄信失敗: {e}")

            # ★★★ 導向畫面也要分流 ★★★
            if order.order_no.startswith('TRIAL-'):
                return render_template('trial_success.html',
                                       order_id=order.order_no,
                                       name=order.customer_name,
                                       final_total=order.final_total,
                                       payment_method='linepay',
                                       order=order)
            else:
                return render_template('order_success.html',
                                       order_id=order.order_no,
                                       name=order.customer_name,
                                       final_total=order.final_total,
                                       payment_method='linepay',
                                       order=order)
        else:
            flash(f"付款失敗: {res_data.get('returnMessage')}", 'error')
            return redirect(url_for('checkout_page'))

    except Exception as e:
        print(f"LINE Pay Confirm Error: {e}")
        flash('付款確認發生錯誤，請聯絡官方 LINE 客服', 'error')
        return redirect(url_for('home'))

@app.route('/api/check_referral', methods=['POST'])
@login_required
def check_referral():
    data = request.get_json()
    code = data.get('code', '').strip()
    
    # 1. 基本檢查
    if not code:
        return jsonify({'valid': False, 'msg': '請輸入推薦碼'})
    
    # 2. 檢查是否已經使用過 (一生一次)
    if current_user.used_referral:
        return jsonify({'valid': False, 'msg': '您已經使用過好友推薦優惠了'})
        
    # 3. 檢查是否是自己的碼
    if current_user.referral_code == code:
        return jsonify({'valid': False, 'msg': '不能使用自己的推薦碼'})

    # 4. 查詢資料庫是否存在此碼
    referrer = User.query.filter_by(referral_code=code).first()
    
    if referrer:
        return jsonify({'valid': True, 'msg': '推薦碼有效！折抵 $50'})
    else:
        return jsonify({'valid': False, 'msg': '無效的推薦碼'})

# ==========================================
# ★ 結帳頁面專用：即時檢查 Email 是否撞號 API
# ==========================================
@app.route('/api/check_email', methods=['POST'])
def check_email():
    data = request.get_json()
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({'exists': False})
        
    user = User.query.filter_by(email=email).first()
    
    # 如果客人有登入，而且輸入的是「他自己的 Email」，那就不算撞號
    if current_user.is_authenticated and user and user.id == current_user.id:
        return jsonify({'exists': False})
        
    # 如果找到了，就代表被別人註冊走了
    if user:
        return jsonify({'exists': True})
        
    return jsonify({'exists': False})
# ==============================================================================
# 5. 會員與後台路由 (Auth & Admin Routes)
# ==============================================================================

# ★★★ 新增：AJAX 傳送驗證碼 API ★★★
@app.route('/send_verification_code', methods=['POST'])
def send_verification_code():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': '請輸入 Email'})
    
    # 檢查 Email 是否已註冊
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': '此 Email 已經註冊過了，請直接登入'})

    # 產生 6 位數驗證碼
    code = str(random.randint(100000, 999999))
    
    # 將驗證碼存入 Session
    session['verification_code'] = code
    session['verification_email'] = email

    # 準備信件內容
    msg = Message("【P.D.K】您的註冊驗證碼", recipients=[email])
    msg.body = f"""
親愛的顧客您好，

歡迎加入 P.D.K 會員！
您的註冊驗證碼為：{code}

請在註冊頁面輸入此代碼以完成驗證。
(此驗證碼 10 分鐘內有效)

P.D.K 團隊 敬上
"""

    # ★★★ 關鍵修改：使用 Thread (執行緒) 在背景寄信 ★★★
    # 這樣網頁就會立刻回應，不會卡住轉圈圈
    Thread(target=send_via_brevo, args=(email, "【P.D.K】您的註冊驗證碼", msg.body)).start()

    return jsonify({'success': True, 'message': '驗證碼已發送！(請稍後檢查信箱)'})


# ★★★ 新增：會員註冊路由 ★★★
@app.route('/register', methods=['GET', 'POST'])
def register():
    # 如果已經登入，直接回首頁
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # ★★★ 新增：取得並檢查驗證碼 ★★★
        input_code = request.form.get('verification_code')
        server_code = session.get('verification_code')
        server_email = session.get('verification_email')

        # 1. 檢查驗證碼是否存在或正確
        if not input_code or input_code != server_code:
            flash('驗證碼錯誤或已過期，請重新發送')
            return redirect(url_for('register'))
        
        # 2. 檢查使用者是否偷偷換了 Email (用 A 驗證，結果註冊 B)
        if email != server_email:
            flash('Email 與驗證時不符，請重新驗證')
            return redirect(url_for('register'))

        # 3. 基本密碼檢查
        if password != confirm_password:
            flash('兩次密碼輸入不一致')
            return redirect(url_for('register'))
        
        # 4. 再次檢查 Email 是否已被註冊 (雙重保險)
        user = User.query.filter_by(email=email).first()
        if user:
            flash('此 Email 已經被註冊過')
            return redirect(url_for('register'))

        # 5. 建立新使用者
        new_user = User(
            email=email,
            name=name,
            phone=phone,
            role='customer'
        )
        new_user.set_password(password)

        # 6. 存入資料庫
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # ★★★ 註冊成功後，清除 Session 驗證碼 (釋放記憶體) ★★★
            session.pop('verification_code', None)
            session.pop('verification_email', None)
            
            # 直接幫他登入
            login_user(new_user)
            flash('歡迎加入 P.D.K！註冊成功')
            return redirect(url_for('home'))
            
        except Exception as e:
            print(e)
            flash('註冊失敗，系統發生錯誤')
            return redirect(url_for('register'))

    return render_template('register.html')

# ==============================================================================
# ★★★ 修改：將登入拆分為 前台會員(login) 與 後台管理(admin_login) ★★★
# ==============================================================================

# 1. 前台會員登入 (路由：/login)
@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (前面的程式碼不用動) ...

    if request.method == 'POST':
        email = request.form.get('email') 
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.role == 'admin':
                flash('管理員請由後台入口登入', 'error')
                return redirect(url_for('admin_login'))
            
            login_user(user) # 使用者登入成功

            # ==========================================
            # ★★★ 新增：登入時自動檢查並補發生日禮金 ★★★
            # ==========================================
            try:
                # 1. 檢查是否有資格 (Pure/Deep/Keep 且 有設定生日)
                if user.member_tier in ['Pure', 'Deep', 'Keep'] and user.birthday:
                    today = datetime.date.today()
                    # 2. 檢查是否生日當月
                    if user.birthday.month == today.month:
                        # 3. 檢查今年是否領過 (避免重複發)
                        # 定義該等級的金額
                        rewards = {'Pure': 150, 'Deep': 200, 'Keep': 300}
                        amount = rewards.get(user.member_tier, 0)
                        
                        v_title = f"{user.member_tier} 會員生日禮"
                        # 找券的母本 ID
                        voucher = Voucher.query.filter_by(title=v_title).first()
                        
                        if voucher:
                            # 檢查過去 360 天內有沒有領過這張券
                            check_start = datetime.datetime.now() - datetime.timedelta(days=360)
                            has_received = UserVoucher.query.filter(
                                UserVoucher.user_id == user.id,
                                UserVoucher.voucher_id == voucher.id,
                                UserVoucher.created_at >= check_start
                            ).first()
                            
                            if not has_received:
                                # 沒領過 -> 發放！
                                expiry = datetime.datetime.now() + datetime.timedelta(days=365)
                                new_uv = UserVoucher(
                                    user_id=user.id,
                                    voucher_id=voucher.id,
                                    expiry_date=expiry
                                )
                                db.session.add(new_uv)
                                db.session.commit()
                                flash(f'生日快樂！已發送 {user.member_tier} 會員專屬生日禮金 ${amount}！', 'success')
            except Exception as e:
                print(f"登入生日檢查錯誤: {e}")
            # ==========================================
            # ★★★ 結束新增 ★★★
            # ==========================================

            # ★★★ 修正：判斷是否有 next 參數，有的話就跳回原本的頁面
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            flash('帳號或密碼錯誤', 'error')
            
    return render_template('login.html')

# ==========================================
# ★ Google 一鍵登入路由
# ==========================================
@app.route('/login/google')
def login_google():
    next_page = request.args.get('next')
    if next_page:
        session['next_url'] = next_page
    # 產生回傳網址 (會自動對應到下面的 authorize_google 函式)
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def authorize_google():
    # 1. 接收 Google 傳回來的資料
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if not user_info:
        flash('無法取得 Google 授權資料，請稍後再試。', 'error')
        return redirect(url_for('login'))
        
    google_email = user_info.get('email')
    google_name = user_info.get('name')
    
    # 2. 核心邏輯：去資料庫尋找這個 Email
    user = User.query.filter_by(email=google_email).first()
    
    if user:
        # 【情境 A】老客人：直接登入 (完美整併)
        login_user(user)
        flash(f'歡迎回來，{user.name}！', 'success')
    else:
        # 【情境 B】新客人：靜默註冊
        import secrets
        import string
        from werkzeug.security import generate_password_hash
        
        # 隨機產生一組 16 碼的亂碼當作密碼 (因為他是用 Google 登入，不需要記密碼)
        random_pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        
        new_user = User(
            email=google_email,
            name=google_name, # 這裡會存入他在 Google 的暱稱
            password_hash=generate_password_hash(random_pwd),
            member_tier='General', # 預設給予 Pure 會員
            # phone 和 address 留空，等結帳時再觸發「智慧回填」
        )
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('Google 登入成功！歡迎加入 P.D.K', 'success')
    next_page = session.pop('next_url', None) # 拿出來的同時清空暫存
    if next_page:
        return redirect(next_page)
    # 3. 登入成功後，把客人導向首頁或會員中心
    return redirect(url_for('home')) # 假設你的會員頁面路由叫做 member_profile，如果不對請改成對應的名稱

# ==========================================
# ★★★ 全新寫法：捨棄 Authlib，純 API LINE 一鍵登入 ★★★
# ==========================================
@app.route('/login/line')
def login_line():
    next_page = request.args.get('next')
    if next_page:
        session['next_url'] = next_page
    # 1. 產生安全碼防偽造，並存入 session
    state = str(uuid.uuid4())
    session['line_state'] = state
    
    # 2. 準備參數
    client_id = os.environ.get('LINE_LOGIN_ID')
    redirect_uri = url_for('authorize_line', _external=True)
    
    # 3. 手動組合 LINE 登入網址 (包含積極加好友 bot_prompt=aggressive)
    line_auth_url = (
        f"https://access.line.me/oauth2/v2.1/authorize"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
        f"&scope=profile%20openid%20email"
        f"&bot_prompt=aggressive"
    )
    return redirect(line_auth_url)

@app.route('/login/line/callback')
def authorize_line():
    error = request.args.get('error')
    if error:
        flash('您已取消 LINE 登入授權。', 'warning')
        return redirect(url_for('login'))
    # 1. 檢查安全碼是否正確
    code = request.args.get('code')
    state = request.args.get('state')
    
    if state != session.get('line_state'):
        flash('登入狀態異常，請重新嘗試。', 'error')
        return redirect(url_for('login'))
        
    client_id = os.environ.get('LINE_LOGIN_ID')
    client_secret = os.environ.get('LINE_LOGIN_SECRET')
    redirect_uri = url_for('authorize_line', _external=True)

    # 2. 拿 code 去跟 LINE 換取 Access Token (通行證)
    token_url = 'https://api.line.me/oauth2/v2.1/token'
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }
    token_res = requests.post(token_url, data=token_data)
    token_json = token_res.json()
    
    if 'access_token' not in token_json:
        flash('無法取得 LINE 授權，請稍後再試。', 'error')
        return redirect(url_for('login'))

    # 3. 用 Access Token 獲取使用者基本資料 (姓名、ID)
    headers = {'Authorization': f"Bearer {token_json['access_token']}"}
    profile_res = requests.get('https://api.line.me/v2/profile', headers=headers)
    profile_json = profile_res.json()

    # 4. 把難搞的 id_token 丟給 LINE 官方幫我們解密拿 Email
    email_data = {}
    if 'id_token' in token_json:
        verify_res = requests.post('https://api.line.me/oauth2/v2.1/verify', data={
            'id_token': token_json['id_token'],
            'client_id': client_id
        })
        email_data = verify_res.json()

    # 5. 整理我們需要的資料
    line_id = profile_json.get('userId')
    line_name = profile_json.get('displayName')
    line_email = email_data.get('email')

    # ★ 防呆：如果 LINE 沒給 Email，假造一個專屬 Email
    if not line_email:
        line_email = f"{line_id}@line.pdk.com"
    
    # --- 下方的登入與註冊邏輯完全維持原樣 ---
    user = User.query.filter_by(email=line_email).first()
    
    if user:
        login_user(user)
        flash(f'歡迎回來，{user.name}！', 'success')
    else:
        import secrets
        import string
        from werkzeug.security import generate_password_hash
        
        random_pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        
        new_user = User(
            email=line_email,
            name=line_name,
            password_hash=generate_password_hash(random_pwd),
            member_tier='General', 
        )
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('LINE 登入成功！歡迎加入 P.D.K', 'success')
        
    next_page = session.pop('next_url', None) # 拿出來的同時清空暫存
    if next_page:
        return redirect(next_page)
        
    return redirect(url_for('home'))

# 2. 後台管理員登入 (路由：/admin/login)
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # 如果已經登入且是管理員，直接進後台
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin_orders'))

    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # ★ 嚴格檢查：只有 admin 角色才能從這裡登入
            if user.role != 'admin':
                error = "您沒有權限進入後台"
            else:
                login_user(user)
                return redirect(url_for('admin_orders'))
        else:
            error = "帳號或密碼錯誤"
    
    # ★★★ 這裡渲染原本的 admin/login.html ★★★
    return render_template('admin/login.html', error=error)

@app.route('/logout')
@app.route('/admin/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# ==============================================================================
# ★★★ 新增區塊 4：後台優惠券管理 (Admin Coupon Routes) ★★★
# ==============================================================================
# ----------------------
# 後台管理：手動發放折扣券 (IG/公益用)
# ----------------------
@app.route('/admin/issue_voucher', methods=['GET', 'POST'])
@login_required
def admin_issue_voucher():
    # 1. 權限檢查：只有 admin 可以進來
    if current_user.role != 'admin':
        flash('權限不足', 'danger')
        return redirect(url_for('index'))

    # 2. 抓出所有「活動類 (activity)」的券供選擇
    # (通常我們不會手動發「邀請獎勵」，那個是系統發的，所以這裡只撈 activity)
    manual_vouchers = Voucher.query.filter_by(voucher_type='activity', is_active=True).all()

    if request.method == 'POST':
        target_email = request.form.get('email')
        voucher_id = request.form.get('voucher_id')

        # A. 找會員
        user = User.query.filter_by(email=target_email).first()
        if not user:
            flash('找不到此會員 Email', 'danger')
            return redirect(url_for('admin_issue_voucher'))

        # B. 檢查會員資格 (Pure 以上才能領?)
        # 根據您的規則：需下單過一次(Pure)才能有折扣券功能
        # 如果您希望嚴格執行，可以把下面這行註解打開：
        if user.orders_count == 0:
            flash('此會員尚未成為 Pure 會員，無法發放折扣券', 'warning')
            return redirect(url_for('admin_issue_voucher'))

        # C. 找券
        voucher = Voucher.query.get(voucher_id)
        
        # D. 發放 (建立關聯)
        # 設定到期日：這裡先設定為 365 天後過期，您也可以改成 None (不過期)
        expiry = datetime.datetime.now() + datetime.timedelta(days=365)
        
        new_uv = UserVoucher(
            user_id=user.id, 
            voucher_id=voucher.id,
            expiry_date=expiry
        )
        db.session.add(new_uv)
        db.session.commit()

        flash(f'成功！已發送 [{voucher.title}] 給 {user.name}', 'success')
        return redirect(url_for('admin_issue_voucher'))

    return render_template('admin/issue_voucher.html', vouchers=manual_vouchers)

# ----------------------
# 後台：折扣券管理列表 (新增/編輯/發放)
# ----------------------
@app.route('/admin/vouchers', methods=['GET', 'POST'])
@login_required
def admin_vouchers():
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    if request.method == 'POST':
        # 接收表單資料
        title = request.form.get('title')
        discount = int(request.form.get('discount'))
        v_type = request.form.get('voucher_type')
        min_spend = int(request.form.get('min_spend', 0)) # 新增
        valid_days = int(request.form.get('valid_days', 30))
        desc = request.form.get('description')
        
        # 處理時間 (如果沒填就是 None)
        start_str = request.form.get('start_time')
        end_str = request.form.get('end_time')
        
        start_time = datetime.datetime.strptime(start_str, '%Y-%m-%dT%H:%M') if start_str else None
        end_time = datetime.datetime.strptime(end_str, '%Y-%m-%dT%H:%M') if end_str else None

        new_v = Voucher(
            title=title,
            discount_value=discount,
            voucher_type=v_type,
            min_spend=min_spend,
            valid_days=valid_days,
            start_time=start_time,
            end_time=end_time,
            description=desc
        )
        db.session.add(new_v)
        db.session.commit()
        flash('折扣券建立成功！', 'success')
        return redirect(url_for('admin_vouchers'))

    vouchers = Voucher.query.all()
    # 這裡不使用 extends base.html，改用完整 HTML 回傳，解決您的 Error
    return render_template('admin/vouchers.html', vouchers=vouchers)

# ----------------------
# 後台：編輯特定折扣券 & 發放給會員
# ----------------------
@app.route('/admin/vouchers/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_voucher_detail(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    voucher = Voucher.query.get_or_404(id)

    if request.method == 'POST':
        if 'update_voucher' in request.form:
            voucher.title = request.form.get('title')
            voucher.discount_value = int(request.form.get('discount'))
            voucher.min_spend = int(request.form.get('min_spend', 0))
            voucher.valid_days = int(request.form.get('valid_days'))
            voucher.description = request.form.get('description')
            
            # 時間處理
            start_str = request.form.get('start_time')
            end_str = request.form.get('end_time')
            if start_str: voucher.start_time = datetime.datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
            if end_str: voucher.end_time = datetime.datetime.strptime(end_str, '%Y-%m-%dT%H:%M')
            else: voucher.end_time = None # 允許清除結束時間

            voucher.is_active = 'is_active' in request.form
            db.session.commit()
            flash('設定已更新', 'success')

        elif 'issue_to_user' in request.form:
            # (這裡維持原本發放邏輯，不變)
            target_email = request.form.get('target_email')
            user = User.query.filter_by(email=target_email).first()
            if not user:
                flash(f'找不到會員：{target_email}', 'danger')
            else:
                expiry = None
                if voucher.valid_days > 0:
                    expiry = datetime.datetime.now() + datetime.timedelta(days=voucher.valid_days)
                new_uv = UserVoucher(user_id=user.id, voucher_id=voucher.id, expiry_date=expiry)
                db.session.add(new_uv)
                db.session.commit()
                flash(f'已成功發送給 {user.name}', 'success')

        return redirect(url_for('admin_voucher_detail', id=voucher.id))

    return render_template('admin/voucher_detail.html', voucher=voucher)

# 1. 優惠券列表
@app.route('/admin/coupons')
@login_required
def admin_coupons():
    if current_user.role != 'admin': return redirect(url_for('home'))
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('admin/coupons.html', coupons=coupons)

# 2. 新增/編輯優惠券
@app.route('/admin/coupon/edit', methods=['GET', 'POST'])
@app.route('/admin/coupon/edit/<int:coupon_id>', methods=['GET', 'POST'])
@login_required
def admin_coupon_edit(coupon_id=None):
    if current_user.role != 'admin': return redirect(url_for('home'))
    
    coupon = None
    if coupon_id:
        coupon = Coupon.query.get_or_404(coupon_id)
        
    if request.method == 'POST':
        code = request.form.get('code').upper()
        name = request.form.get('name')
        discount_type = request.form.get('discount_type')
        discount_value = int(request.form.get('discount_value'))
        min_spend = int(request.form.get('min_spend'))
        usage_limit = int(request.form.get('usage_limit'))
        per_user_limit = int(request.form.get('per_user_limit'))
        
        start_str = request.form.get('start_date')
        end_str = request.form.get('end_date')
        
        # 日期轉換 (HTML datetime-local 回傳格式為 'YYYY-MM-DDTHH:MM')
        start_date = datetime.datetime.strptime(start_str, '%Y-%m-%dT%H:%M') if start_str else datetime.datetime.now()
        end_date = datetime.datetime.strptime(end_str, '%Y-%m-%dT%H:%M') if end_str else None
        
        is_active = True if request.form.get('is_active') else False

        if coupon: # 編輯
            coupon.code = code
            coupon.name = name
            coupon.discount_type = discount_type
            coupon.discount_value = discount_value
            coupon.min_spend = min_spend
            coupon.usage_limit = usage_limit
            coupon.per_user_limit = per_user_limit
            coupon.start_date = start_date
            coupon.end_date = end_date
            coupon.is_active = is_active
        else: # 新增
            new_coupon = Coupon(
                code=code, name=name, discount_type=discount_type, discount_value=discount_value,
                min_spend=min_spend, usage_limit=usage_limit, per_user_limit=per_user_limit,
                start_date=start_date, end_date=end_date, is_active=is_active
            )
            db.session.add(new_coupon)
            
        db.session.commit()
        return redirect(url_for('admin_coupons'))

    return render_template('admin/coupon_form.html', coupon=coupon)

# 3. 刪除優惠券
@app.route('/admin/coupon/delete', methods=['POST'])
@login_required
def delete_coupon():
    if current_user.role != 'admin': return redirect(url_for('home'))
    c_id = request.form.get('coupon_id')
    coupon = Coupon.query.get(c_id)
    if coupon:
        db.session.delete(coupon)
        db.session.commit()
    return redirect(url_for('admin_coupons'))

# ==============================================================================
# ★★★ 新增：忘記密碼功能 (Forgot Password) ★★★
# ==============================================================================

# 1. 忘記密碼頁面 (輸入 Email)
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # ★★★ 新增：精準阻擋 LINE 假造信箱 ★★★
        if '@line.pdk.com' in email:
            flash('您是使用 LINE 快速註冊的會員，請直接點擊 LINE 按鈕登入。')
            return redirect(url_for('login'))
        
        # 檢查 Email 是否存在於資料庫
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('此 Email 尚未註冊會員')
            return redirect(url_for('forgot_password'))

        # 產生 6 位數驗證碼
        code = str(random.randint(100000, 999999))
        
        # 存入 Session (暫存)
        session['reset_code'] = code
        session['reset_email'] = email

        try:
            # 寄信
            msg = Message("【P.D.K】重設密碼驗證信", recipients=[email])
            msg.body = f"""
親愛的 P.D.K 會員您好，

我們收到了您重設密碼的請求。
您的驗證碼為：{code}

請回到網頁輸入此代碼以設定新密碼。
若您未發出此請求，請忽略此信件。
"""
            mail.send(msg)
            flash('驗證碼已發送至您的信箱，請查收')
            return redirect(url_for('reset_password'))
            
        except Exception as e:
            print(e)
            flash('寄信失敗，請稍後再試')
            return redirect(url_for('forgot_password'))

    return render_template('auth/forgot_password.html')


# 2. 重設密碼頁面 (輸入驗證碼 + 新密碼)
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        input_code = request.form.get('code')
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 從 Session 取得正確的驗證碼與 Email
        server_code = session.get('reset_code')
        reset_email = session.get('reset_email')

        # 驗證
        if not input_code or input_code != server_code:
            flash('驗證碼錯誤或已過期')
            return redirect(url_for('reset_password'))

        if new_password != confirm_password:
            flash('兩次密碼輸入不一致')
            return redirect(url_for('reset_password'))

        # 寫入資料庫 (更新密碼)
        user = User.query.filter_by(email=reset_email).first()
        if user:
            user.set_password(new_password) # 加密並更新
            db.session.commit()
            
            # 清除 Session
            session.pop('reset_code', None)
            session.pop('reset_email', None)
            
            flash('密碼重設成功！請使用新密碼登入')
            return redirect(url_for('login'))
        else:
            flash('系統錯誤，找不到使用者')
            return redirect(url_for('forgot_password'))

    return render_template('auth/reset_password.html')

# ==============================================================================
# ★★★ 修改：將會員功能拆成兩個路由 ★★★
# ==============================================================================

# ----------------------
# 1. 我的資料 (修改個人檔案)
# ----------------------
@app.route('/member', methods=['GET', 'POST'])
@login_required
def member():
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_real_name = request.form.get('real_name')
        new_phone = request.form.get('phone')
        new_address = request.form.get('address')
        new_store = request.form.get('store_info')
        
        # 生日欄位
        new_birthday_str = request.form.get('birthday')
        
        if new_name and new_phone:
            current_user.name = new_name
            current_user.real_name = new_real_name
            current_user.phone = new_phone
            current_user.address = new_address
            current_user.store_info = new_store
            
            # 生日處理邏輯
            if not current_user.birthday and new_birthday_str:
                try:
                    # 嘗試兩種常見寫法，確保能夠轉換成功
                    try:
                        # 情況 A: 如果是用 from datetime import datetime
                        b_date = datetime.strptime(new_birthday_str, '%Y-%m-%d').date()
                    except AttributeError:
                        # 情況 B: 如果是用 import datetime
                        b_date = datetime.datetime.strptime(new_birthday_str, '%Y-%m-%d').date()
                    
                    current_user.birthday = b_date
                    flash('生日設定成功！', 'success')
                except Exception as e:
                    print(f"生日轉換錯誤: {e}")
                    flash('生日格式錯誤，請重新選擇', 'error')

            try:
                db.session.commit()
                flash('個人資料更新成功！', 'success')
            except Exception as e:
                db.session.rollback()
                print(f"資料庫存檔錯誤: {e}")
                flash('更新失敗，請稍後再試', 'error')
        else:
            flash('請填寫完整資料', 'error')
            
        return redirect(url_for('member'))

    return render_template('member.html')
# ----------------------
# 2. 我的帳號 (Dashboard - 會員儀表板)
# ----------------------
@app.route('/my_account')
@login_required
def dashboard():
    # 1. 取得目前累積數據 (如果沒有則為 0)
    current_total = current_user.total_spend if current_user.total_spend else 0
    current_count = current_user.orders_count if current_user.orders_count else 0
    
    # 預設變數
    next_tier = "Deep"
    gap_amount = 0
    gap_orders = 0  # ★★★ 新增：還差幾單
    progress_percent = 0
    
    # 2. 判斷升級邏輯
    if current_user.member_tier == 'Pure' or current_count < 1:
        # --- 目前是 Pure (或一般)，目標 -> Deep ---
        # 條件：消費滿 2500 (Deep 只看金額)
        target_money = 2500
        next_tier = "Deep"
        
        # 計算差距 (金額)
        gap_amount = max(0, target_money - current_total)
        # Deep 不看訂單數，所以 gap_orders 設為 0 或顯示不適用
        gap_orders = 0 
        
        # 計算進度 %
        progress_percent = min(100, int((current_total / target_money) * 100))
        
    elif current_user.member_tier == 'Deep':
        # --- 目前是 Deep，目標 -> Keep ---
        # 條件：消費滿 5000 或 訂單滿 5 單 (兩者擇一)
        next_tier = "Keep"
        target_money = 5000
        target_orders = 5
        
        # A. 計算金額差距
        gap_amount = max(0, target_money - current_total)
        money_progress = int((current_total / target_money) * 100)
        
        # B. 計算訂單差距 (總數 5 - 目前累積)
        # 這就是您要修正的邏輯：看"總累積"，不是"升級後新增"
        gap_orders = max(0, target_orders - current_count)
        order_progress = int((current_count / target_orders) * 100)
        
        # C. 決定進度條顯示誰 (顯示進度比較快的那個)
        progress_percent = max(money_progress, order_progress)
        progress_percent = min(100, progress_percent)
        
    else: 
        # --- 目前是 Keep (最高級) ---
        next_tier = "Max"
        gap_amount = 0
        gap_orders = 0
        progress_percent = 100

    # 2. 統計有效優惠券
    now = datetime.datetime.now()
    valid_vouchers_count = 0
    if current_user.coupons:
        for uv in current_user.coupons:
            if not uv.is_used and uv.voucher.is_active:
                if not uv.expiry_date or uv.expiry_date > now:
                    valid_vouchers_count += 1

    # 3. 推薦碼使用次數
    referral_count = User.query.filter_by(referrer_id=current_user.id).count()

    return render_template('dashboard.html', 
                           next_tier=next_tier,
                           gap_amount=gap_amount,
                           gap_orders=gap_orders, # ★★★ 記得把這個傳給網頁
                           progress=progress_percent,
                           voucher_count=valid_vouchers_count,
                           referral_count=referral_count)

# 2. 訂單查詢 (獨立頁面)
@app.route('/my_orders')
@login_required
def my_orders():
    # 抓取目前登入使用者的訂單
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

# --- 後台路由 (需權限驗證) ---

@app.route('/admin/orders')
@login_required # ★★★ 確保已登入
def admin_orders():
    # ★★★ 確保是管理員
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('q', '').strip()

    # 排除 TRIAL- 訂單，讓一般訂單畫面乾淨
    query = Order.query.filter(~Order.order_no.startswith('TRIAL-'))
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    if search_query:
        query = query.filter(or_(
            Order.order_no.contains(search_query),
            Order.customer_name.contains(search_query),
            Order.customer_phone.contains(search_query)
        ))

    query = query.order_by(Order.created_at.desc())
    per_page = 10
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    orders = pagination.items

    today = datetime.date.today()
    today_start = datetime.datetime.combine(today, datetime.time.min)
    
    dashboard = {
        'total_orders': Order.query.count(),
        'today_orders': Order.query.filter(Order.created_at >= today_start).count(),
        'pending_ship': Order.query.filter(or_(Order.status == 'pending', Order.status == 'paid')).count(),
        'today_revenue': db.session.query(db.func.sum(Order.total_amount)).filter(Order.created_at >= today_start).scalar() or 0,
        
        'cnt_all': Order.query.count(),
        'cnt_pending': Order.query.filter_by(status='pending').count(),
        'cnt_paid': Order.query.filter_by(status='paid').count(),
        'cnt_shipped': Order.query.filter_by(status='shipped').count(),
        'cnt_done': Order.query.filter_by(status='done').count(),
        'cnt_cancelled': Order.query.filter_by(status='cancelled').count(),
    }

    return render_template('admin/orders.html', 
                           orders=orders, 
                           pagination=pagination, 
                           status_filter=status_filter,
                           search_query=search_query,
                           dashboard=dashboard)

@app.route('/admin/trial_orders')
@login_required
def admin_trial_orders():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('q', '').strip()

    # ★★★ 只抓 TRIAL- 開頭的訂單
    query = Order.query.filter(Order.order_no.startswith('TRIAL-'))
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    if search_query:
        query = query.filter(or_(
            Order.order_no.contains(search_query),
            Order.customer_name.contains(search_query),
            Order.customer_phone.contains(search_query)
        ))

    query = query.order_by(Order.created_at.desc())
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    orders = pagination.items

    return render_template('admin/trial_orders.html', orders=orders, pagination=pagination, status_filter=status_filter, search_query=search_query)

@app.route('/admin/order/<int:order_id>')
@login_required
def admin_order_detail(order_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    order = Order.query.get_or_404(order_id)
    items = []
    try:
        if order.cart_items:
            items = json.loads(order.cart_items)
    except:
        items = []

    # ★★★ 新增：建立商品對照表 (Product Map) ★★★
    # 用途：如果訂單裡的商品沒存照片，我們可以用 ID 來這裡查現在的最新照片
    all_products = Product.query.all()
    product_map = {p.id: p for p in all_products} 
    # 這樣我們就可以用 product_map['sh_001'].image 查到照片了

    return render_template('admin/order_detail.html', order=order, items=items, product_map=product_map)

# ---------------------------------------------------
# ★★★ 後台：更新訂單狀態 (含推薦獎勵發放) ★★★
# ---------------------------------------------------
@app.route('/admin/order/update_status', methods=['POST'])
@login_required
def update_order_status():
    order_id = request.form.get('order_id')
    new_status = request.form.get('status')
    source_page = request.form.get('source_page')
    
    order = Order.query.get(order_id)
    if order:
        old_status = order.status
        order.status = new_status
        
        if new_status == 'shipped' and old_status != 'shipped':
            send_shipping_notification_email(order)
        
        if new_status == 'paid' and not order.paid_at:
            order.paid_at = datetime.datetime.now()
            
        # ★★★ 觸發推薦獎勵 (僅在變為 done 時) ★★★
        if new_status == 'done' and old_status != 'done' and order.referrer_id:
            referrer = User.query.get(order.referrer_id)
            
            # 檢查推薦人存在，且確保不重複發放 (這裡簡單檢查該訂單是否已處理過，實務上可加欄位標記)
            # 這裡我們假設訂單完成只會觸發一次，或者您可以在 Order 加一個 is_referral_paid 欄位
            if referrer:
                reward_title = '好友推薦獎勵'
                # 1. 找母本，沒有就建
                reward_voucher = Voucher.query.filter_by(title=reward_title).first()
                if not reward_voucher:
                    reward_voucher = Voucher(
                        title=reward_title,
                        discount_value=100,
                        voucher_type='reward', # 可疊加
                        min_spend=500,
                        valid_days=365,        # ★ 設定效期 1 年
                        description='成功邀請好友下單獎勵'
                    )
                    db.session.add(reward_voucher)
                    db.session.flush()
                
                # 2. 發給使用者
                expiry = datetime.datetime.now() + datetime.timedelta(days=365)
                new_uv = UserVoucher(
                    user_id=referrer.id,
                    voucher_id=reward_voucher.id,
                    expiry_date=expiry
                    
                )
                db.session.add(new_uv)
                
                # 3. ★ 寄信通知
                send_voucher_notification_email(referrer, reward_title, 100, "感謝您推薦好友加入 P.D.K！")
                
                print(f"★ 已發送推薦獎勵券並寄信給: {referrer.name}")

        db.session.commit()
        
        if order.user:
            check_membership_upgrade(order.user)
            
        flash(f'訂單 {order.order_no} 狀態已更新為 {new_status}', 'success')
    
    if source_page == 'detail':
        return redirect(url_for('admin_order_detail', order_id=order_id))
    else:
        return redirect(url_for('admin_orders'))

@app.route('/admin/order/delete', methods=['POST'])
@login_required
def delete_order():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    order_id = request.form.get('order_id')
    order = Order.query.get(order_id)
    if order:
        # ★★★ 解決外鍵衝突：先找出並刪除與此訂單綁定的「優惠碼」使用紀錄
        usages = CouponUsage.query.filter_by(order_id=order.id).all()
        for usage in usages:
            # 順便歸還優惠碼的全站使用次數
            coupon = Coupon.query.get(usage.coupon_id)
            if coupon and coupon.used_count > 0:
                coupon.used_count -= 1
            
            # 刪除該筆使用紀錄
            db.session.delete(usage)
            
        # ★★★ 刪除子紀錄後，就可以安全地刪除訂單了
        db.session.delete(order)
        db.session.commit()
    
    return redirect(url_for('admin_orders'))

# --- 聯絡我們頁面 (含表單寄信功能) ---
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message_body = request.form.get('message')
        
        # 寄信給管理員 (您自己)
        try:
            subject_full = f"【官網留言】{subject} - 来自 {name}"
            # 收件人設為您自己的官方信箱
            admin_email = "pdk.salon.office@gmail.com" 
            
            content = f"""
            <html>
            <body>
                <h3>官網收到新留言</h3>
                <p><b>姓名:</b> {name}</p>
                <p><b>信箱:</b> {email}</p>
                <p><b>留言內容:</b><br>{message_body}</p>
            </body>
            </html>
            """
            
            Thread(target=send_via_brevo, args=(admin_email, subject_full, content)).start()
            
            flash('訊息已發送！我們會盡快回覆您。', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            print(f"Contact mail error: {e}")
            flash('發送失敗，請稍後再試。', 'error')
            
    return render_template('contact.html')

# ==============================================================================
# 6. 商品管理路由 (Product Management) ★★★ 新增區塊 ★★★
# ==============================================================================
# --- 靜態資訊頁面 ---
@app.route('/return-policy')
def return_policy():
    return render_template('return_policy.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# 商品列表 (修改版：支援分類篩選，並依 ID 排序)
@app.route('/admin/products')
@login_required
def admin_products():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    # 1. 接收網址傳來的分類參數 (例如 ?category=shampoo)
    cat_filter = request.args.get('category')
    
    # 2. 判斷要抓全部還是抓特定分類，並加上 order_by(Product.id) 進行排序
    if cat_filter:
        # 有選擇分類時：過濾分類後，依 ID 排序
        products = Product.query.filter_by(category=cat_filter).order_by(Product.id).all()
    else:
        # 顯示全部商品時：直接依 ID 排序
        products = Product.query.order_by(Product.id).all()
        
    # 3. 回傳模板 (多傳一個 current_category 給前端做按鈕亮燈判斷)
    return render_template('admin/products.html', products=products, current_category=cat_filter)

@app.route('/admin/product/edit', methods=['GET', 'POST'])
@app.route('/admin/product/edit/<product_id>', methods=['GET', 'POST'])
@login_required
def admin_product_edit(product_id=None):
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    product = None
    if product_id:
        product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        # 1. 取得表單資料
        p_id = request.form.get('id')
        name = request.form.get('name')
        category = request.form.get('category')
        price = request.form.get('price')
        description = request.form.get('description')
        volume = request.form.get('volume') # ★★★ 新增：取得容量欄位

        # --- 處理第一張圖 (主圖) ---
        image_file = request.files.get('image')
        delete_check = request.form.get('delete_image') # 取得是否勾選刪除

        # 預設狀態：如果是編輯模式，先暫存舊圖片路徑；如果是新增，預設為 None
        image_path = product.image if product else None

        if delete_check == 'yes':
            # ★ 情況 A：使用者勾選了「刪除圖片」
            image_path = None
        elif image_file and allowed_file(image_file.filename):
            # ★ 情況 B：使用者上傳了「新圖片」 (這會覆蓋舊圖)
            filename = secure_filename(image_file.filename)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"main_{timestamp}_{filename}" # 加上 main_ 前綴區分

            # 確保上傳資料夾存在
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f"uploads/{filename}"

        # --- ★★★ 新增：處理第二張圖 (標籤介紹圖) ★★★ ---
        tag_image_file = request.files.get('tag_image')
        delete_tag_check = request.form.get('delete_tag_image')

        # 預設狀態：如果是編輯模式，先暫存舊圖片路徑；如果是新增，預設為 None
        tag_image_path = product.tag_image if product else None

        if delete_tag_check == 'yes':
            tag_image_path = None
        elif tag_image_file and allowed_file(tag_image_file.filename):
            filename = secure_filename(tag_image_file.filename)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"tag_{timestamp}_{filename}" # 加上 tag_ 前綴區分

            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            tag_image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            tag_image_path = f"uploads/{filename}"

        # 3. 判斷是新增還是修改
        if product: # 修改模式
            product.name = name
            product.category = category
            product.price = price
            product.description = description
            product.volume = volume # ★★★ 更新這欄
            # 只有在 image_path 有變動 (被刪除或有新上傳) 時才更新
            if delete_check == 'yes' or (image_file and allowed_file(image_file.filename)):
                 product.image = image_path
            
            # 只有在 tag_image_path 有變動 (被刪除或有新上傳) 時才更新
            if delete_tag_check == 'yes' or (tag_image_file and allowed_file(tag_image_file.filename)):
                product.tag_image = tag_image_path

            flash('商品更新成功！')
        else: # 新增模式
            # 檢查 ID 是否重複
            if Product.query.get(p_id):
                return render_template('admin/product_form.html', product=None, error="商品編號已存在")

            new_product = Product(
                id=p_id,
                name=name,
                category=category,
                price=price,
                description=description,
                volume=volume, # ★★★ 寫入這欄
                image=image_path,
                tag_image=tag_image_path
            )
            db.session.add(new_product)
            flash('商品新增成功！')

        db.session.commit()
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', product=product)

# 刪除商品
@app.route('/admin/product/delete', methods=['POST'])
@login_required
def delete_product():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    product_id = request.form.get('product_id')
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash('商品已刪除')
    
    return redirect(url_for('admin_products'))

# -------------------------------------------
# 臨時工具：幫現有會員補發 PDK-ID 推薦碼
# 使用方式：重啟後，瀏覽器輸入網址 /fix_referrals
# -------------------------------------------
@app.route('/fix_referrals')
@login_required
def fix_referrals():
    # 找出所有等級符合 (Pure/Deep/Keep) 的會員
    users = User.query.filter(
        User.member_tier.in_(['Pure', 'Deep', 'Keep'])
    ).all()
    
    count = 0
    for u in users:
        # 強制設定為 PDK-ID 格式 (例如 ID 1 -> PDK-000001)
        correct_code = f"PDK-{u.id:06d}"
        
        # 如果原本沒有，或是格式不對，就更新
        if u.referral_code != correct_code:
            u.referral_code = correct_code
            count += 1
    
    db.session.commit()
    return f"修復完成！已將 {count} 位會員的推薦碼更新為 PDK-XXXXXX 流水號格式。"

# 記得在最上面加入: from sqlalchemy import extract

@app.route('/admin/send_birthday_vouchers')
@login_required
def send_birthday_vouchers():
    # 權限檢查 (可選)
    # if current_user.email != 'admin@gmail.com': return "無權限"

    today = datetime.datetime.now()
    current_month = today.month
    
    # 定義規則
    tier_rewards = {
        'Pure': 150,
        'Deep': 200,
        'Keep': 300
    }
    
    # 1. 準備母本 (確保這 3 張券存在)
    voucher_map = {}
    for tier, amount in tier_rewards.items():
        v_title = f"{tier} 會員生日禮"
        v = Voucher.query.filter_by(title=v_title).first()
        if not v:
            v = Voucher(
                title=v_title,
                discount_value=amount,
                voucher_type='activity', # 生日禮通常不疊加
                min_spend=0,
                valid_days=365,          # ★ 設定效期 1 年
                description=f'祝您生日快樂！{tier} 會員專屬禮金'
            )
            db.session.add(v)
            db.session.flush()
        voucher_map[tier] = v.id

    # 2. 撈出本月壽星
    birthday_users = User.query.filter(
        extract('month', User.birthday) == current_month,
        User.member_tier.in_(['Pure', 'Deep', 'Keep'])
    ).all()
    
    count = 0
    for u in birthday_users:
        vid = voucher_map.get(u.member_tier)
        if vid:
            # 檢查今年是否已經發過 (避免重複按)
            # 邏輯：檢查該用戶過去 300 天內是否有拿過這張券
            recent_v = UserVoucher.query.filter(
                UserVoucher.user_id == u.id,
                UserVoucher.voucher_id == vid,
                UserVoucher.created_at >= today - datetime.timedelta(days=300)
            ).first()
            
            if not recent_v:
                expiry = today + datetime.timedelta(days=365) # 效期一年
                new_uv = UserVoucher(
                    user_id=u.id, 
                    voucher_id=vid, 
                    expiry_date=expiry
                )
                db.session.add(new_uv)
                
                # ★ 3. 寄信通知
                v_obj = Voucher.query.get(vid)
                send_voucher_notification_email(u, v_obj.title, v_obj.discount_value, "一年一度的生日禮金，祝您生日快樂！")
                
                count += 1

    db.session.commit()
    return f"生日禮券發送完畢！本月壽星共 {len(birthday_users)} 人，實際發送 {count} 張，並已寄出通知信。"

# 1. 讓 Render (Gunicorn) 啟動時也能執行資料庫初始化
with app.app_context():
    try:
        # A. 建立資料表 (如果不存在)
        db.create_all()
        
        # B. 初始化資料 (管理員、商品)
        create_initial_data()
        
        # C. 初始化折扣券
        create_default_vouchers()
        
        print("✅ 資料庫與初始資料檢查/建立完成")
    except Exception as e:
        print(f"❌ 初始化資料庫時發生錯誤: {e}")

# 2. 本機開發時的啟動入口
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    