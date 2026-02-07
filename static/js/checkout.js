/* static/js/checkout.js */

// ==========================================
// 0. 台灣行政區資料庫 (完整版)
// ==========================================
const taiwanDistricts = {
    "台北市": ["中正區", "大同區", "中山區", "松山區", "大安區", "萬華區", "信義區", "士林區", "北投區", "內湖區", "南港區", "文山區"],
    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "新店區", "樹林區", "鶯歌區", "三峽區", "淡水區", "汐止區", "瑞芳區", "土城區", "蘆洲區", "五股區", "泰山區", "林口區", "深坑區", "石碇區", "坪林區", "三芝區", "石門區", "八里區", "平溪區", "雙溪區", "貢寮區", "金山區", "萬里區", "烏來區"],
    "基隆市": ["仁愛區", "信義區", "中正區", "中山區", "安樂區", "暖暖區", "七堵區"],
    "桃園市": ["桃園區", "中壢區", "大溪區", "楊梅區", "蘆竹區", "大園區", "龜山區", "八德區", "龍潭區", "平鎮區", "新屋區", "觀音區", "復興區"],
    "新竹市": ["東區", "北區", "香山區"],
    "新竹縣": ["竹北市", "竹東鎮", "新埔鎮", "關西鎮", "湖口鄉", "新豐鄉", "芎林鄉", "橫山鄉", "北埔鄉", "寶山鄉", "峨眉鄉", "尖石鄉", "五峰鄉"],
    "苗栗縣": ["苗栗市", "頭份市", "苑裡鎮", "通霄鎮", "竹南鎮", "後龍鎮", "卓蘭鎮", "大湖鄉", "公館鄉", "銅鑼鄉", "南庄鄉", "頭屋鄉", "三義鄉", "西湖鄉", "造橋鄉", "三灣鄉", "獅潭鄉", "泰安鄉"],
    "台中市": ["中區", "東區", "南區", "西區", "北區", "西屯區", "南屯區", "北屯區", "豐原區", "東勢區", "大甲區", "清水區", "沙鹿區", "梧棲區", "后里區", "神岡區", "潭子區", "大雅區", "新社區", "石岡區", "外埔區", "大安區", "烏日區", "大肚區", "龍井區", "霧峰區", "太平區", "大里區", "和平區"],
    "彰化縣": ["彰化市", "鹿港鎮", "和美鎮", "線西鄉", "伸港鄉", "福興鄉", "秀水鄉", "花壇鄉", "芬園鄉", "員林市", "溪湖鎮", "田中鎮", "大村鄉", "埔鹽鄉", "埔心鄉", "永靖鄉", "社頭鄉", "二水鄉", "北斗鎮", "二林鎮", "田尾鄉", "埤頭鄉", "芳苑鄉", "大城鄉", "竹塘鄉", "溪州鄉"],
    "南投縣": ["南投市", "埔里鎮", "草屯鎮", "竹山鎮", "集集鎮", "名間鄉", "鹿谷鄉", "中寮鄉", "魚池鄉", "國姓鄉", "水里鄉", "信義鄉", "仁愛鄉"],
    "雲林縣": ["斗六市", "斗南鎮", "虎尾鎮", "西螺鎮", "土庫鎮", "北港鎮", "古坑鄉", "大埤鄉", "莿桐鄉", "林內鄉", "二崙鄉", "崙背鄉", "麥寮鄉", "東勢鄉", "褒忠鄉", "臺西鄉", "元長鄉", "四湖鄉", "口湖鄉", "水林鄉"],
    "嘉義市": ["東區", "西區"],
    "嘉義縣": ["太保市", "朴子市", "布袋鎮", "大林鎮", "民雄鄉", "溪口鄉", "新港鄉", "六腳鄉", "東石鄉", "義竹鄉", "鹿草鄉", "水上鄉", "中埔鄉", "竹崎鄉", "梅山鄉", "番路鄉", "大埔鄉", "阿里山鄉"],
    "台南市": ["中西區", "東區", "南區", "北區", "安平區", "安南區", "永康區", "歸仁區", "新化區", "左鎮區", "玉井區", "楠西區", "南化區", "仁德區", "關廟區", "龍崎區", "官田區", "麻豆區", "佳里區", "西港區", "七股區", "將軍區", "學甲區", "北門區", "新營區", "後壁區", "白河區", "東山區", "六甲區", "下營區", "柳營區", "鹽水區", "善化區", "大內區", "山上區", "新市區", "安定區"],
    "高雄市": ["楠梓區", "左營區", "鼓山區", "三民區", "鹽埕區", "前金區", "新興區", "苓雅區", "前鎮區", "旗津區", "小港區", "鳳山區", "林園區", "大寮區", "大樹區", "大社區", "仁武區", "鳥松區", "岡山區", "橋頭區", "燕巢區", "田寮區", "阿蓮區", "路竹區", "湖內區", "茄萣區", "永安區", "彌陀區", "梓官區", "旗山區", "美濃區", "六龜區", "甲仙區", "杉林區", "內門區", "茂林區", "桃源區", "那瑪夏區"],
    "屏東縣": ["屏東市", "潮州鎮", "東港鎮", "恆春鎮", "萬丹鄉", "長治鄉", "麟洛鄉", "九如鄉", "里港鄉", "鹽埔鄉", "高樹鄉", "萬巒鄉", "內埔鄉", "竹田鄉", "新埤鄉", "枋寮鄉", "新園鄉", "崁頂鄉", "林邊鄉", "南州鄉", "佳冬鄉", "琉球鄉", "車城鄉", "滿州鄉", "枋山鄉", "三地門鄉", "霧台鄉", "瑪家鄉", "泰武鄉", "來義鄉", "春日鄉", "獅子鄉", "牡丹鄉"],
    "宜蘭縣": ["宜蘭市", "羅東鎮", "蘇澳鎮", "頭城鎮", "礁溪鄉", "壯圍鄉", "員山鄉", "冬山鄉", "五結鄉", "三星鄉", "大同鄉", "南澳鄉"],
    "花蓮縣": ["花蓮市", "鳳林鎮", "玉里鎮", "新城鄉", "吉安鄉", "壽豐鄉", "光復鄉", "豐濱鄉", "瑞穗鄉", "富里鄉", "秀林鄉", "萬榮鄉", "卓溪鄉"],
    "台東縣": ["台東市", "成功鎮", "關山鎮", "卑南鄉", "鹿野鄉", "池上鄉", "東河鄉", "長濱鄉", "太麻里鄉", "大武鄉", "綠島鄉", "海端鄉", "延平鄉", "金峰鄉", "達仁鄉", "蘭嶼鄉"],
    "澎湖縣": ["馬公市", "湖西鄉", "白沙鄉", "西嶼鄉", "望安鄉", "七美鄉"],
    "金門縣": ["金城鎮", "金湖鎮", "金沙鎮", "金寧鄉", "烈嶼鄉", "烏坵鄉"],
    "連江縣": ["南竿鄉", "北竿鄉", "莒光鄉", "東引鄉"]
};

// ==========================================
// 1. 初始化資料
// ==========================================
let cart = JSON.parse(localStorage.getItem('pdk_cart')) || [];
let shippingFee = 100; // 預設黑貓
let discount = 0;
const PROMO_THRESHOLD = 1000;

// ==========================================
// 2. 渲染頁面
// ==========================================
function renderPage() {
    const listEl = document.getElementById('checkoutItemsList');
    if (!listEl) return;

    let subtotal = 0;
    let html = '';

    if (cart.length === 0) {
        listEl.innerHTML = '<p style="text-align:center; color:#666; padding:20px;">購物車是空的</p>';
        updateValues(0);
        return;
    }

    cart.forEach(item => {
        let itemTotal = item.price * item.qty;
        subtotal += itemTotal;

        html += `
        <div class="checkout-item">
            <div class="checkout-img product-bg-${item.id}"></div>
            
            <div style="flex:1;">
                <div style="font-size:0.95rem; margin-bottom:5px;">${item.name}</div>
                <div style="font-size:0.85rem; color:#888;">NT$ ${item.price}</div>
                
                <div class="mini-qty-control">
                    <div class="mini-qty-btn" onclick="changeQty('${item.id}', -1)">-</div>
                    <div class="mini-qty-num">${item.qty}</div>
                    <div class="mini-qty-btn" onclick="changeQty('${item.id}', 1)">+</div>
                </div>
            </div>
            
            <div style="font-family:'Times New Roman'; font-size:1rem;">NT$ ${itemTotal.toLocaleString()}</div>
        </div>
        `;
    });

    listEl.innerHTML = html;
    updateValues(subtotal);
}

// ==========================================
// 3. 數值更新核心 (小計、運費、總額、贈品)
// ==========================================
function updateValues(subtotal) {
    // 讀取運費
    const select = document.getElementById('shippingSelect');
    if (select) {
        shippingFee = parseInt(select.options[select.selectedIndex].dataset.price);
    }

    // 計算合計
    let total = subtotal + shippingFee - discount;
    if (total < 0) total = 0;

    // DOM 更新
    const headerSubtotal = document.getElementById('headerSubtotal');
    if(headerSubtotal) headerSubtotal.innerText = subtotal.toLocaleString();
    
    const rightSubtotal = document.getElementById('rightSubtotal');
    if(rightSubtotal) rightSubtotal.innerText = subtotal.toLocaleString();
    
    const summarySubtotal = document.getElementById('summarySubtotal');
    if(summarySubtotal) summarySubtotal.innerText = subtotal.toLocaleString();

    const summaryShipping = document.getElementById('summaryShipping');
    if(summaryShipping) summaryShipping.innerText = shippingFee;

    const summaryDiscount = document.getElementById('summaryDiscount');
    if(summaryDiscount) summaryDiscount.innerText = discount;

    const summaryTotal = document.getElementById('summaryTotal');
    if(summaryTotal) summaryTotal.innerText = total.toLocaleString();

    // 優惠券顯示控制
    const discRow = document.getElementById('discountRow');
    if(discRow) discRow.style.display = discount > 0 ? 'flex' : 'none';

    // 滿額贈邏輯
    const promoEl = document.getElementById('promoTask');
    const promoText = document.getElementById('promoText');
    
    if (promoEl && promoText) {
        const icon = promoEl.querySelector('.task-icon');

        if (subtotal >= PROMO_THRESHOLD) {
            promoEl.className = 'promo-task-bar task-success';
            icon.innerText = '✓';
            promoText.innerText = '已達成！贈送旅行分裝小瓶';
        } else {
            let diff = PROMO_THRESHOLD - subtotal;
            promoEl.className = 'promo-task-bar task-fail';
            icon.innerText = '✕';
            promoText.innerText = `還差 NT$ ${diff} 送旅行分裝小瓶`;
        }
    }
}

// ==========================================
// 4. 修改數量功能
// ==========================================
function changeQty(id, delta) {
    let item = cart.find(i => i.id === id);
    if (item) {
        item.qty += delta;
        if (item.qty <= 0) {
            cart = cart.filter(i => i.id !== id);
        }
        localStorage.setItem('pdk_cart', JSON.stringify(cart));
        renderPage();
    }
}

// ==========================================
// 5. 變更運費
// ==========================================
function updateShipping() {
    let subtotal = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
    updateValues(subtotal);
}

// ==========================================
// 6. 套用優惠碼
// ==========================================
function applyPromo() {
    const input = document.getElementById('promoInput');
    const msg = document.getElementById('promoMsg');
    
    if (!input) return;

    const code = input.value.trim().toUpperCase();

    if (code === 'VIP50') {
        discount = 50;
        if(msg) {
            msg.style.color = '#4caf50';
            msg.innerText = '優惠碼套用成功！折抵 NT$50';
        }
    } else {
        discount = 0;
        if(msg) {
            msg.style.color = '#ff5252';
            msg.innerText = '無效的優惠碼';
        }
    }
    updateShipping();
}

// ==========================================
// 7. 手機版收合切換
// ==========================================
function toggleConfirmation() {
    if (window.innerWidth >= 992) return;
    const content = document.getElementById('confirmationContent');
    const icon = document.querySelector('.toggle-icon');
    
    if (content) {
        if (content.classList.contains('open')) {
            content.classList.remove('open');
            if(icon) icon.classList.remove('rotate');
        } else {
            content.classList.add('open');
            if(icon) icon.classList.add('rotate');
        }
    }
}

// ==========================================
// 8. 縣市區域連動邏輯 (新增部分)
// ==========================================
function initCitySelector() {
    const citySelect = document.getElementById('citySelect');
    const districtSelect = document.getElementById('districtSelect');

    if (!citySelect || !districtSelect) return;

    // 填入所有縣市
    for (let city in taiwanDistricts) {
        let option = document.createElement('option');
        option.value = city;
        option.text = city;
        citySelect.appendChild(option);
    }

    // 監聽變更
    citySelect.addEventListener('change', function() {
        const selectedCity = this.value;
        const districts = taiwanDistricts[selectedCity];

        // 清空區域選單
        districtSelect.innerHTML = '<option value="" disabled selected>請選擇區域</option>';

        // 填入對應區域
        if (districts) {
            districts.forEach(district => {
                let option = document.createElement('option');
                option.value = district;
                option.text = district;
                districtSelect.appendChild(option);
            });
        }
    });
}

// ==========================================
// 9. 啟動 (DOM Ready)
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    renderPage();
    initCitySelector(); // 啟動縣市選單
});