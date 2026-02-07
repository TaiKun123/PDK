from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# ============================================
# 1. 資料庫配置 (Configuration)
# ============================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ============================================
# 2. 定義資料表模型 (Model)
# ============================================
class Product(db.Model):
    # ★★★ 修改 2：ID 必須是 String (文字)，才能存 "sh_001"
    id = db.Column(db.String(50), primary_key=True)
    
    # 商品基本資訊
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)

# ============================================
# 3. 資料庫初始化與建立預設資料 (Seeds)
# ============================================
with app.app_context():
    db.create_all() # 建立資料表結構
    
    # 檢查是否已經有第一個商品 (sh_001)
    if not Product.query.get("sh_001"):
        
        # --- 洗髮精系列 (Shampoo) ---
        sh_001 = Product(id="sh_001", name="淨屑舒活洗髮精", category="shampoo", price=700, description="1.清除油脂 2.滋養髮根 3.強韌成長")
        sh_002 = Product(id="sh_002", name="輕柔活力洗髮精", category="shampoo", price=700, description="1.深層控油 2.強健髮根 3.蓬鬆清爽")
        sh_003 = Product(id="sh_003", name="翅藻植翠洗髮精", category="shampoo", price=700, description="1.平衡油脂 2.鎖水保濕 3.輕盈蓬鬆")
        sh_004 = Product(id="sh_004", name="淨化控油調理洗髮精", category="shampoo", price=850, description="1.油脂平衡 2.植萃淨化 3.賦活蓬鬆")
        sh_005 = Product(id="sh_005", name="極致燙染修復洗髮精", category="shampoo", price=850, description="1.賦活修復 2.鎖水護色 3.極致補水")
        
        # --- 潤髮乳系列 (Conditioner) ---
        co_001 = Product(id="co_001", name="翅藻植翠極致乳", category="conditioner", price=700, description="1.深層滋養 2.強韌髮芯 3.護色彈力")
        co_002 = Product(id="co_002", name="極致燙染修復護理素", category="conditioner", price=850, description="1.深層修復 2.強韌彈性 3.高效保濕")
        
        # --- 保養品系列 (Hair care) ---
        hc_001 = Product(id="hc_001", name="摩洛哥Q10精華修復液", category="haircare", price=500, description="1.抗氧防護 2.強韌養分 3.瞬效柔滑")
        hc_002 = Product(id="hc_002", name="黃金堅果E油", category="haircare", price=500, description="1.雙重防禦 2.鎖色持久 3.撫平毛躁")
        hc_003 = Product(id="hc_003", name="芳香質感精華乳", category="haircare", price=350, description="1.平衡調理 2.修補水分 3.護色功能")
        hc_004 = Product(id="hc_004", name="彈力亮澤修復液", category="haircare", price=350, description="1.護色修復 2.減少毛躁 3.閃亮健康")
        
        # --- 其他產品系列 (Other product) ---
        op_001 = Product(id="op_001", name="PLASTIC WAX", category="otherproduct", price=400, description="1.強力造型 2.造型再現")
        
        db.session.add_all([sh_001, sh_002, sh_003, sh_004, sh_005, co_001,co_002,hc_001,hc_002,hc_003,hc_004,op_001])
        db.session.commit()
        print("資料庫建立成功！已寫入預設商品資料。")

# ============================================
# 4. 路由設定 (Routes)
# ============================================

# --- 首頁 ---
@app.route('/')
def home():
    return render_template('index.html')

# --- 洗髮精專區 ---
@app.route('/shampoo')
def shampoo_page():
    products = Product.query.filter_by(category='shampoo').all()
    return render_template('shampoo.html', products=products)

# --- 通用分類頁面 ---
@app.route('/category/<string:cat_name>')
def category_page(cat_name):
    # 1. 定義每個分類對應的標題資料
    category_data = {
        'shampoo': {
            'title_zh': '洗髮精', 
            'title_en': 'SHAMPOO', 
        },
        'conditioner': {
            'title_zh': '潤髮乳', 
            'title_en': 'CONDITIONER', 
        },
        'haircare': {
            'title_zh': '頭髮護理', 
            'title_en': 'HAIR CARE', 
        },
        'otherproduct': {
            'title_zh': '其他產品', 
            'title_en': 'OTHERS', 
        }
    }

    page_info = category_data.get(cat_name, {
        'title_zh': '精選商品', 
        'title_en': 'PRODUCTS', 
    })

    products = Product.query.filter_by(category=cat_name).all()
    
    return render_template('shampoo.html', products=products, page_info=page_info)

# --- 商品詳情頁 (單一商品) ---
# ★★★ 修改 3：網址參數必須改為 string，才能接收 "sh_001"
@app.route('/product/<product_id>')
def product_page(product_id):
    # 這裡的邏輯是：直接去 templates/product/ 資料夾找對應的 HTML 檔
    # 例如 product_id 是 sh_001，就會去找 templates/product/sh_001.html
    return render_template(f'product/{product_id}.html')

# --- 結帳畫面 ---

@app.route('/checkout')
def checkout_page():
    return render_template('checkout.html')

# ============================================
# 5. 啟動程式 (Main)
# ============================================
if __name__ == '__main__':
    # host='0.0.0.0' 允許手機或外部裝置透過 IP 連線
    app.run(host='0.0.0.0', port=5000, debug=True)