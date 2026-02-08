from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename # ★★★ 新增：處理檔案上傳的工具 ★★★
from sqlalchemy import or_
import os
import json      # 處理 JSON 資料
import datetime  # 處理時間
import random    # 處理隨機編號

app = Flask(__name__)

# ==============================================================================
# 1. 設定 (Configuration)
# ==============================================================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_super_secret_key_change_this_in_production' 

# ★★★ 新增：設定圖片上傳路徑 ★★★
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 允許上傳的圖片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # 若沒登入，導向的頁面

# ==============================================================================
# 2. 資料庫模型 (Models) - 核心地基
# ==============================================================================

# ★★★ 新增：使用者/會員模型 ★★★
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='customer') # 'admin' or 'customer'
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

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

# ★★★ 升級：訂單模型 (關聯使用者) ★★★
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # 新增：關聯會員 (Nullable 代表訪客也可買)
    customer_name = db.Column(db.String(50), nullable=False)
    customer_email = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    shipping_method = db.Column(db.String(20))
    address = db.Column(db.String(200))
    payment_method = db.Column(db.String(20))
    total_amount = db.Column(db.Integer)
    cart_items = db.Column(db.Text) 
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

# Flask-Login 載入使用者
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

# ==============================================================================
# 4. 前台路由 (Frontend Routes)
# ==============================================================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shampoo')
def shampoo_page():
    products = Product.query.filter_by(category='shampoo').all()
    page_info = {'title_zh': '洗髮精', 'title_en': 'SHAMPOO'}
    return render_template('shampoo.html', products=products, page_info=page_info)

@app.route('/category/<string:cat_name>')
def category_page(cat_name):
    category_data = {
        'shampoo': {'title_zh': '洗髮精', 'title_en': 'SHAMPOO'},
        'conditioner': {'title_zh': '潤髮乳', 'title_en': 'CONDITIONER'},
        'haircare': {'title_zh': '頭髮護理', 'title_en': 'HAIR CARE'},
        'otherproduct': {'title_zh': '其他產品', 'title_en': 'OTHERS'}
    }
    page_info = category_data.get(cat_name, {'title_zh': '精選商品', 'title_en': 'PRODUCTS'})
    products = Product.query.filter_by(category=cat_name).all()
    return render_template('shampoo.html', products=products, page_info=page_info)

@app.route('/product/<product_id>')
def product_page(product_id):
    return render_template(f'product/{product_id}.html')

@app.route('/checkout')
def checkout_page():
    return render_template('checkout.html')

@app.route('/submit_order', methods=['POST'])
def submit_order():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    shipping_method = request.form.get('shipping_method')
    payment_method = request.form.get('payment_method')

    address = ""
    if shipping_method == 'home':
        city = request.form.get('city') or ""
        district = request.form.get('district') or ""
        addr_detail = request.form.get('address') or ""
        address = f"{city}{district}{addr_detail}"
    elif shipping_method == 'store':
        store_name = request.form.get('store_name') or "未指定"
        store_id = request.form.get('store_id')
        address = f"7-11 門市：{store_name}" + (f" ({store_id})" if store_id else "")

    cart_data_str = request.form.get('cart_data')
    try:
        discount = int(request.form.get('discount', 0))
    except:
        discount = 0

    cart_items = []
    total_price = 0
    try:
        if cart_data_str:
            cart_items = json.loads(cart_data_str)
            for item in cart_items:
                p = int(item.get('price', 0))
                q = int(item.get('qty', 0))
                total_price += p * q
    except:
        cart_items = []

    shipping_fee = 100 if shipping_method == 'home' else 40
    total_price += shipping_fee
    total_price -= discount
    if total_price < 0: total_price = 0

    date_str = datetime.datetime.now().strftime("%Y%m%d")
    rand_num = random.randint(1000, 9999)
    order_id = f"PDK-{date_str}-{rand_num}"

    # ★★★ 修改：若有登入會員，記錄 user_id ★★★
    user_id = current_user.id if current_user.is_authenticated else None

    new_order = Order(
        order_no=order_id,
        user_id=user_id,
        customer_name=name,
        customer_email=email,
        customer_phone=phone,
        shipping_method=shipping_method,
        address=address,
        payment_method=payment_method,
        total_amount=total_price,
        cart_items=json.dumps(cart_items, ensure_ascii=False),
        status='pending'
    )
    
    try:
        db.session.add(new_order)
        db.session.commit()
    except Exception as e:
        print(f"存檔失敗: {e}")
        db.session.rollback()

    return render_template('order_success.html', order_id=order_id, name=name, payment_method=payment_method)


# ==============================================================================
# 5. 會員與後台路由 (Auth & Admin Routes)
# ==============================================================================

# 登入頁面 (前台會員 & 後台管理員共用)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('username') # 前端 input name 若是 username
        password = request.form.get('password')
        
        # ★★★ 新邏輯：去資料庫查使用者 ★★★
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user) # 登入成功，寫入 session
            if user.role == 'admin':
                return redirect(url_for('admin_orders'))
            else:
                return redirect(url_for('home')) # 一般會員回首頁 (之後改成會員中心)
        else:
            return render_template('admin/login.html', error="帳號或密碼錯誤")
            
    return render_template('admin/login.html')

@app.route('/logout')
@app.route('/admin/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

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

    query = Order.query
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

    return render_template('admin/order_detail.html', order=order, items=items)

@app.route('/admin/order/update_status', methods=['POST'])
@login_required
def update_order_status():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    order_id = request.form.get('order_id')
    new_status = request.form.get('status')
    source_page = request.form.get('source_page', 'detail') 
    
    order = Order.query.get(order_id)
    if order:
        order.status = new_status
        db.session.commit()
    
    if source_page == 'list':
        return redirect(url_for('admin_orders'))
    else:
        return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/order/delete', methods=['POST'])
@login_required
def delete_order():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    order_id = request.form.get('order_id')
    order = Order.query.get(order_id)
    if order:
        db.session.delete(order)
        db.session.commit()
    
    return redirect(url_for('admin_orders'))

# ==============================================================================
# 6. 商品管理路由 (Product Management) ★★★ 新增區塊 ★★★
# ==============================================================================

# 商品列表
# 商品列表 (修改版：支援分類篩選)
@app.route('/admin/products')
@login_required
def admin_products():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    # 1. 接收網址傳來的分類參數 (例如 ?category=shampoo)
    cat_filter = request.args.get('category')
    
    # 2. 判斷要抓全部還是抓特定分類
    if cat_filter:
        products = Product.query.filter_by(category=cat_filter).all()
    else:
        products = Product.query.all()
        
    # 3. 回傳模板 (多傳一個 current_category 給前端做按鈕亮燈判斷)
    return render_template('admin/products.html', products=products, current_category=cat_filter)

# 新增/編輯商品 (共用一個視圖)
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
        
        # 2. 處理圖片上傳與刪除 (★ 修改過的部分 ★)
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
            filename = f"{timestamp}_{filename}"
            
            # 確保上傳資料夾存在
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
                
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f"uploads/{filename}"
            
        # ★ 情況 C：沒刪除也沒上傳 -> 保持原樣 (image_path 維持舊路徑)

        # 3. 判斷是新增還是修改
        if product: # 修改模式
            product.name = name
            product.category = category
            product.price = price
            product.description = description
            
            # ★ 關鍵：只有當 image_path 有被變更 (變成 None 或 新路徑) 時才寫入
            # 但因為我們上面邏輯已經處理好了 image_path，直接賦值即可
            product.image = image_path
            
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
                image=image_path
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

if __name__ == '__main__':
    with app.app_context():
        create_initial_data() # 啟動時自動檢查並建立資料
    app.run(host='0.0.0.0', port=5000, debug=True)