/* static/js/checkout.js - 完整合併版 */

// ==========================================
// 0. 台灣行政區資料庫 (保留原樣)
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
// 1. 初始化變數
// ==========================================
// ★ 接收後端傳來的折扣券資料 (防呆: 若沒定義則為空陣列)
let availableVouchers = (typeof SERVER_VOUCHERS !== 'undefined') ? SERVER_VOUCHERS : [];

let cart = JSON.parse(localStorage.getItem('pdk_cart')) || [];
let currentSubtotal = 0;
let shippingFee = 100;
let totalDiscount = 0;

// 常數定義
const PROMO_THRESHOLD = 1000;         // 滿額贈門檻
const FREE_SHIPPING_THRESHOLD = 2000; // 免運門檻

let state = {
    promoCode: null, 
    referralCode: null, 
    referralDiscount: 0, // ★ 必須要有這個
    selectedTypeA: null, 
    selectedTypeB: {} 
};

// ==========================================
// 2. 啟動 (DOM Ready)
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    renderPage(); // 渲染購物車
    initCitySelector(); // 初始化縣市選單
    
    // --- UI 事件綁定 (舊功能) ---
    const shippingSelect = document.getElementById('shippingSelect');
    if (shippingSelect) shippingSelect.addEventListener('change', () => {
        updateShippingUI(); 
        recalcTotal();
    });

    const confirmationHeader = document.getElementById('confirmationHeader');
    if (confirmationHeader) confirmationHeader.addEventListener('click', toggleConfirmation);
    
    const btnSubmitOrder = document.getElementById('btnSubmitOrder');
    if (btnSubmitOrder) btnSubmitOrder.addEventListener('click', submitOrder);

    // --- 輸入驗證 (舊功能) ---
    const nameInput = document.getElementById('inputName');
    if(nameInput) nameInput.addEventListener('blur', checkName);

    const phoneInput = document.getElementById('inputPhone');
    if(phoneInput) phoneInput.addEventListener('blur', checkPhone);

    const emailInput = document.getElementById('inputEmail');
    if(emailInput) emailInput.addEventListener('blur', checkEmail);

    const addressInput = document.getElementById('addressInput');
    if(addressInput) {
        addressInput.addEventListener('blur', () => {
            if(document.getElementById('shippingSelect').value === 'home') checkDeliveryInfo();
        });
    }

    const storeInput = document.getElementById('storeNameInput');
    if(storeInput) {
        storeInput.addEventListener('blur', () => {
            if(document.getElementById('shippingSelect').value === 'store') checkDeliveryInfo();
        });
    }

    // --- ★ 新增：折扣專區 UI 事件 ---
    const header = document.getElementById('discountHeader');
    const body = document.getElementById('discountBody');
    if(header && body) {
        header.addEventListener('click', () => {
            header.classList.toggle('active');
            body.style.display = (body.style.display === 'none') ? 'block' : 'none';
        });
    }

    // 優惠碼按鈕 (改用新的 applyPromoCode)
    const btnPromo = document.getElementById('btnApplyPromo');
    if(btnPromo) btnPromo.addEventListener('click', applyPromoCode);

    // 推薦碼按鈕
    const btnRef = document.getElementById('btnApplyReferral');
    if(btnRef) btnRef.addEventListener('click', applyReferralCode);

    // 折扣券 Modal 相關
    const btnModal = document.getElementById('btnOpenVoucherModal');
    const modal = document.getElementById('voucherModal');
    const close = document.querySelector('.close-modal');
    const confirm = document.getElementById('btnConfirmVouchers');

    if(btnModal) btnModal.addEventListener('click', openVoucherModal);
    if(close) close.addEventListener('click', () => modal.style.display = 'none');
    if(confirm) confirm.addEventListener('click', confirmVoucherSelection);
    
    // 點擊視窗外關閉 Modal
    window.onclick = function(event) {
        if (event.target == modal) modal.style.display = "none";
    }

    // 初始化狀態
    updateShippingUI();
});

// ==========================================
// 3. 渲染頁面
// ==========================================
function renderPage() {
    const listEl = document.getElementById('checkoutItemsList');
    if (!listEl) return;

    currentSubtotal = 0; // 重置小計
    let html = '';

    if (cart.length === 0) {
        listEl.innerHTML = '<p style="text-align:center; color:#666; padding:20px;">購物車是空的</p>';
        recalcTotal();
        return;
    }

    cart.forEach(item => {
        let itemTotal = item.price * item.qty;
        currentSubtotal += itemTotal;

        // 判斷圖片來源
        let imgStyle = '';
        let bgClass = '';
        if (item.img && item.img.trim() !== '') {
            imgStyle = `background-image: url('${item.img}'); background-size: cover; background-position: center;`;
        } else {
            bgClass = `product-bg-${item.id}`;
        }

        html += `
        <div class="checkout-item">
            <div class="checkout-img ${bgClass}" style="${imgStyle}"></div>
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
    recalcTotal(); // ★ 渲染完立刻算一次錢
}

function recalcTotal() {
    // 1. 運費 & 免運
    const select = document.getElementById('shippingSelect');
    let baseShippingFee = 100; 
    if (select && select.options[select.selectedIndex]) {
        baseShippingFee = parseInt(select.options[select.selectedIndex].dataset.price);
    }
    
    // ★★★ 這裡順便幫您修正會員免運邏輯，確保變數能讀到 ★★★
    const tierElem = document.getElementById('userTier');
    const tier = tierElem ? tierElem.value : 'Pure';
    const quotaElem = document.getElementById('shippingQuota');
    const quota = quotaElem ? parseInt(quotaElem.value) : 0;

    if (currentSubtotal >= FREE_SHIPPING_THRESHOLD) {
        shippingFee = 0; 
    } else {
        shippingFee = baseShippingFee;
        // 補上會員免運判斷
        if (tier === 'Deep' && select.value === 'store') shippingFee = 0;
        else if (tier === 'Keep' && quota > 0) shippingFee = 0;
    }

    // ===================================
    // A. 優惠碼
    // ===================================
    let promoDiscount = 0;
    if (state.promoCode) {
        promoDiscount = state.promoCode.discount;
    }

    // ===================================
    // ★★★ B-0. 新增：讀取推薦碼折扣 ★★★
    // ===================================
    // 如果驗證成功，state.referralDiscount 會是 50，否則為 0
    let referralDiscount = state.referralDiscount || 0;


    // ===================================
    // B. 折扣券 (計算原始總額 vs 上限)
    // ===================================
    let rawVoucherDiscount = 0;

    // Type A
    if (state.selectedTypeA) {
        const v = availableVouchers.find(v => v.id == state.selectedTypeA);
        if (v && currentSubtotal >= v.voucher.min_spend) {
            rawVoucherDiscount += v.voucher.discount_value;
        }
    }
    // Type B
    for (const [vid, count] of Object.entries(state.selectedTypeB)) {
        const v = availableVouchers.find(v => v.id == vid);
        if (v && count > 0 && currentSubtotal >= v.voucher.min_spend) {
            rawVoucherDiscount += (v.voucher.discount_value * count);
        }
    }

    // 折扣券上限邏輯
    let voucherCap = (currentSubtotal >= 1500) ? 600 : 300;
    let actualVoucherDiscount = Math.min(rawVoucherDiscount, voucherCap);

    // UI 提示文字
    const successMsg = document.getElementById('voucherSuccessMsg');
    const warningMsg = document.getElementById('voucherWarningMsg');

    if (actualVoucherDiscount > 0) {
        successMsg.style.display = 'block';
        successMsg.innerText = `折扣券已套用！折抵 NT$${actualVoucherDiscount}`;
        
        if (rawVoucherDiscount > voucherCap) {
            warningMsg.style.display = 'block';
            warningMsg.innerText = `超出折抵上限 (本單上限 $${voucherCap})，請檢查使用的優惠券，超出不退還`;
        } else {
            warningMsg.style.display = 'none';
        }
    } else {
        successMsg.style.display = 'none';
        warningMsg.style.display = 'none';
    }

    // ===================================
    // C. 總折扣 = 優惠碼 + 折扣券 + ★★★ 推薦碼 ★★★
    // ===================================
    // 修改這裡：把 referralDiscount 加進去
    totalDiscount = promoDiscount + actualVoucherDiscount + referralDiscount;

    // 安全防護 (折扣不能超過商品總額)
    if (totalDiscount > currentSubtotal) totalDiscount = currentSubtotal;

    // 3. 計算總金額
    let total = currentSubtotal + shippingFee - totalDiscount;
    if (total < 0) total = 0;

    // 4. 更新 UI 數字
    safeSetText('headerSubtotal', currentSubtotal.toLocaleString());
    safeSetText('rightSubtotal', currentSubtotal.toLocaleString());
    safeSetText('summarySubtotal', currentSubtotal.toLocaleString());
    
    const feeEl = document.getElementById('summaryShipping');
    if(feeEl) {
        if (shippingFee === 0 && currentSubtotal < FREE_SHIPPING_THRESHOLD) {
             // 顯示綠色 (會員免運)
             feeEl.innerHTML = '<span style="color:#4caf50; font-weight:bold;"> 0 (會員免運)</span>';
        } else if (shippingFee === 0) {
             feeEl.innerHTML = '<span style="color:#4caf50; font-weight:bold;"> 0 </span>';
        } else {
             feeEl.innerText = shippingFee;
             feeEl.style.color = '#fff';
        }
    }

    // ★ 這裡會自動更新「折扣專區總額」和「下方折扣明細」
    safeSetText('summaryDiscount', totalDiscount);
    safeSetText('zoneTotalDiscount', totalDiscount);
    safeSetText('summaryTotal', total.toLocaleString());

    const zoneSummarySpan = document.getElementById('zoneTotalDiscountSummary');
    if (zoneSummarySpan) {
        if (totalDiscount > 0) zoneSummarySpan.classList.add('dh-summary-green');
        else zoneSummarySpan.classList.remove('dh-summary-green');
    }

    const discRow = document.getElementById('discountRow');
    if (discRow) discRow.style.display = totalDiscount > 0 ? 'flex' : 'none';

    // Modal 內的提示
    const modalSub = document.getElementById('modalSubtotalInfo');
    const modalLim = document.getElementById('modalLimitInfo');
    if(modalSub) modalSub.innerText = `$${currentSubtotal}`;
    if(modalLim) modalLim.innerText = `$${voucherCap}`;

    updateHiddenInputs();
    updatePromoTaskBar();
}

function updatePromoTaskBar() {
    const promoEl = document.getElementById('promoTask');
    const promoText = document.getElementById('promoText');
    
    if (promoEl && promoText) {
        const icon = promoEl.querySelector('.task-icon');
        
        if (currentSubtotal >= PROMO_THRESHOLD) {
            promoEl.className = 'promo-task-bar task-success';
            icon.innerText = '✓';
            
            if (currentSubtotal >= FREE_SHIPPING_THRESHOLD) {
                promoText.innerText = '已達成免運！且贈送旅行分裝小瓶';
            } else {
                let diffShip = FREE_SHIPPING_THRESHOLD - currentSubtotal;
                promoText.innerText = `已送小瓶！再買 NT$ ${diffShip} 享免運`;
            }

        } else {
            let diff = PROMO_THRESHOLD - currentSubtotal;
            promoEl.className = 'promo-task-bar task-fail';
            icon.innerText = '✕';
            promoText.innerText = `還差 NT$ ${diff} 送旅行分裝小瓶`;
        }
    }
}

function updateHiddenInputs() {
    // 1. 優惠碼
    const hiddenPromo = document.getElementById('hiddenPromoCode');
    if(hiddenPromo) hiddenPromo.value = state.promoCode ? state.promoCode.code : '';
    
    // 2. 推薦碼
    const hiddenRef = document.getElementById('hiddenReferralCode');
    if(hiddenRef) hiddenRef.value = state.referralCode || '';

    // 3. 折扣券 IDs (轉換為 "1,5,5" 格式)
    let ids = [];
    if (state.selectedTypeA) ids.push(state.selectedTypeA);
    for (const [vid, count] of Object.entries(state.selectedTypeB)) {
        for(let i=0; i<count; i++) ids.push(vid);
    }
    const hiddenVouchers = document.getElementById('hiddenVouchers');
    if(hiddenVouchers) hiddenVouchers.value = ids.join(',');
    
    // 4. 購物車資料
    const hiddenCart = document.getElementById('hiddenCartInput');
    if(hiddenCart) hiddenCart.value = JSON.stringify(cart);
}

// ==========================================
// 5. 折扣券 Modal 邏輯 (★ 新增)
// ==========================================
function openVoucherModal() {
    const modal = document.getElementById('voucherModal');
    modal.style.display = 'flex';
    renderVoucherList();
}

function renderVoucherList() {
    const listA = document.getElementById('voucherListActivity');
    const listB = document.getElementById('voucherListReward');
    
    listA.innerHTML = '';
    listB.innerHTML = '';

    // Type B 分組
    let groupB = {};

    availableVouchers.forEach(uv => {
        // 低消判斷
        const disabled = currentSubtotal < uv.voucher.min_spend;
        const disabledStyle = disabled ? 'opacity:0.5; pointer-events:none;' : '';
        const hint = disabled ? `<span style="color:#ff5252; font-size:0.75rem;">(滿$${uv.voucher.min_spend}可用)</span>` : '';

        // 日期格式化
        const dateStr = uv.expiry_date ? `時限: ${uv.expiry_date}` : '永久有效';

        if (uv.voucher.voucher_type === 'activity') {
            // --- ★ Type A (單選): 圓圈打勾樣式 ---
            const isSelected = (state.selectedTypeA == uv.id);
            const activeClass = isSelected ? 'active' : '';
            
            const html = `
                <div class="voucher-item ${activeClass}" style="${disabledStyle}" onclick="tempSelectA('${uv.id}')">
                    <div class="v-info">
                        <div class="v-title">${uv.voucher.title} ${hint}</div>
                        <span class="v-desc">折抵 NT$${uv.voucher.discount_value}</span>
                        <span class="v-date">${dateStr}</span>
                    </div>
                    <div class="v-check-circle"></div>
                </div>
            `;
            listA.innerHTML += html;

        } else {
            // Group Type B (準備資料)
            const key = uv.voucher.title;
            if (!groupB[key]) groupB[key] = { ids: [], def: uv.voucher, expiry: dateStr };
            groupB[key].ids.push(uv.id);
        }
    });

    if (listA.innerHTML === '') listA.innerHTML = '<div style="color:#666; padding:10px;">無可用活動券</div>';

    // --- Type B (可疊加): 維持計數器 ---
    if (Object.keys(groupB).length === 0) {
        listB.innerHTML = '<div style="color:#666; text-align:center; padding:10px;">無可用獎勵券</div>';
    }

    for (const [title, data] of Object.entries(groupB)) {
        let usedCount = 0;
        data.ids.forEach(id => { if (state.selectedTypeB[id]) usedCount++; });

        const totalOwn = data.ids.length;
        const disabled = currentSubtotal < data.def.min_spend;
        const disabledStyle = disabled ? 'opacity:0.5;' : '';
        const hint = disabled ? `<span style="color:#ff5252;">(未達門檻)</span>` : `持有: ${totalOwn}`;

        const html = `
            <div class="voucher-item" style="${disabledStyle}; cursor:default;">
                <div class="v-info">
                    <div class="v-title">${title}</div>
                    <span class="v-desc">單張折抵 $${data.def.discount_value} | ${hint}</span>
                </div>
                <div class="qty-control">
                    <div class="qty-btn" onclick="tempChangeB('${title}', -1)">-</div>
                    <div class="qty-val" id="qty_${title}">${usedCount}</div>
                    <div class="qty-btn" onclick="tempChangeB('${title}', 1)">+</div>
                </div>
            </div>
        `;
        listB.innerHTML += html;
    }
}
// 暫存選擇 A
function tempSelectA(id) {
    if (state.selectedTypeA == id) {
        state.selectedTypeA = null; // 再次點擊 -> 取消選取
    } else {
        state.selectedTypeA = id; // 選取
    }
    renderVoucherList(); // ★ 重繪列表：這是讓綠色框框顯示的關鍵
    updateModalEstimate(); // 更新預估金額
}

// 暫存選擇 B (計數器邏輯)
function tempChangeB(title, delta) {
    let allIds = [];
    let def = null;
    availableVouchers.forEach(v => {
        if (v.voucher.title === title && v.voucher.voucher_type !== 'activity') {
            allIds.push(v.id);
            def = v.voucher;
        }
    });

    if (!def) return;
    if (currentSubtotal < def.min_spend) return;

    let currentSelectedIds = [];
    allIds.forEach(id => {
        if (state.selectedTypeB[id]) currentSelectedIds.push(id);
    });
    let count = currentSelectedIds.length;

    // 檢查總上限
    let totalBCount = 0;
    for (let c of Object.values(state.selectedTypeB)) totalBCount += c;

    if (delta > 0) {
        // 增加
        const limit = (currentSubtotal >= 1000) ? 5 : 3;
        if (totalBCount >= limit) { alert(`消費金額對應的特殊券上限為 ${limit} 張`); return; }
        if (count >= allIds.length) return; // 不能超過持有數

        // 找一個沒被選的 ID 加進去
        const freeId = allIds.find(id => !state.selectedTypeB[id]);
        if (freeId) state.selectedTypeB[freeId] = 1;

    } else {
        // 減少
        if (count <= 0) return;
        const removeId = currentSelectedIds[currentSelectedIds.length - 1];
        delete state.selectedTypeB[removeId];
    }
    renderVoucherList();
}

function updateModalEstimate() {
    let rawEst = 0; // 原始折扣總和 (未受限)

    // 1. 計算 Type A (活動券)
    if (state.selectedTypeA) {
        // 使用寬鬆比對 (==) 避免 ID 型別問題
        const v = availableVouchers.find(i => i.id == state.selectedTypeA);
        if (v) rawEst += v.voucher.discount_value;
    }

    // 2. 計算 Type B (獎勵券) - ★ 改用跟 recalcTotal 一樣的寫法
    for (const [vid, count] of Object.entries(state.selectedTypeB)) {
        const v = availableVouchers.find(i => i.id == vid);
        if (v && count > 0) {
            rawEst += (v.voucher.discount_value * count);
        }
    }

    // 3. 套用上限邏輯 ($1500 / $300 / $600)
    let discountCap = (currentSubtotal >= 1500) ? 600 : 300;
    
    // 最終預估 = 取 (原始總和, 上限, 商品總額) 的最小值
    let finalEst = Math.min(rawEst, discountCap, currentSubtotal);

    // 4. 更新 UI 顯示
    const el = document.getElementById('modalEstDiscount');
    if (el) {
        // 如果原始折扣 > 上限，顯示紅字提示
        if (rawEst > discountCap) {
            el.innerHTML = `${finalEst} <span style="font-size:0.8rem; color:#ff5252; margin-left:5px;">(已達折扣券上限)</span>`;
        } else {
            el.innerText = finalEst;
        }
    }
}

function confirmVoucherSelection() {
    // 更新外部 UI 文字
    let count = 0;
    if (state.selectedTypeA) count++;
    count += Object.keys(state.selectedTypeB).length;

    const badge = document.getElementById('voucherCountBadge');
    const text = document.getElementById('voucherSelectText');
    
    if (count > 0) {
        badge.innerText = count;
        badge.style.display = 'inline-block';
        text.innerText = `已選擇 ${count} 張券`;
        text.style.fontWeight = 'bold';
        text.style.color = '#333';
    } else {
        badge.style.display = 'none';
        text.innerText = '選擇您的折扣券';
        text.style.fontWeight = 'normal';
        text.style.color = '#666';
    }

    document.getElementById('voucherModal').style.display = 'none';
    recalcTotal();
}

// ==========================================
// 6. 優惠碼與推薦碼 (★ 整合舊 API)
// ==========================================
function applyPromoCode() {
    const input = document.getElementById('promoInput');
    const msg = document.getElementById('promoMsg');
    const code = input.value.trim();

    if (!code) return;
    
    if(msg) { msg.innerText = "檢查中..."; msg.style.color = "#666"; }

    // 使用您原本寫好的 API
    fetch('/api/check_coupon', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code, amount: currentSubtotal })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // ★ 成功後存入 state，而不是直接改 total
            state.promoCode = { code: code, discount: data.discount_amount };
            
            if(msg) { 
                msg.style.color = '#4caf50'; 
                msg.innerText = data.message; 
            }
            input.disabled = true;
            // 鎖定按鈕
            const btn = document.getElementById('btnApplyPromo');
            if(btn) { btn.innerText = "已套用"; btn.disabled = true; }
            
            recalcTotal(); // 重算
        } else {
            state.promoCode = null;
            if(msg) { 
                msg.style.color = '#ff5252'; 
                msg.innerText = data.message; 
            }
            recalcTotal();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if(msg) { msg.style.color = '#ff5252'; msg.innerText = '系統錯誤，請稍後再試'; }
    });
}

function applyReferralCode() {
    const input = document.getElementById('referralInput');
    const msg = document.getElementById('referralMsg');
    const btn = document.getElementById('btnApplyReferral');
    const code = input.value.trim();
    
    // 1. 基本檢查
    if(!code) {
        if(msg) { 
            msg.innerText = "請輸入代碼"; 
            msg.className = "dz-msg error"; 
        }
        return;
    }

    // 2. 鎖定按鈕，顯示檢查中
    if(btn) { 
        btn.innerText = "檢查中..."; 
        btn.disabled = true; 
    }

    // 3. ★★★ 關鍵：發送 AJAX 問後端這個碼對不對 ★★★
    fetch('/api/check_referral', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code })
    })
    .then(res => res.json())
    .then(data => {
        if (data.valid) {
            // --- 驗證成功 ---
            state.referralCode = code;
            state.referralDiscount = 50; // ★ 設定折扣金額為 50
            
            // 顯示綠色成功訊息
            if(msg) {
                msg.innerHTML = '<span style="color:#4caf50;">✔ ' + data.msg + '</span>';
                msg.className = "dz-msg success";
            }
            
            // 鎖定輸入框
            input.disabled = true;
            if(btn) btn.innerText = "已套用";
            
            // 更新隱藏欄位 (讓送出訂單時後端收得到)
            const hiddenRef = document.getElementById('hiddenReferralCode');
            if(hiddenRef) hiddenRef.value = code;

            // ★ 立即重算金額 (這會讓折扣專區馬上顯示金額)
            recalcTotal(); 
        } else {
            // --- 驗證失敗 ---
            state.referralCode = null;
            state.referralDiscount = 0; // 歸零
            
            // 顯示紅色錯誤訊息
            if(msg) {
                msg.innerText = data.msg; // 例如：無效的推薦碼
                msg.className = "dz-msg error";
            }
            
            if(btn) { 
                btn.innerText = "驗證"; 
                btn.disabled = false; 
            }
            
            const hiddenRef = document.getElementById('hiddenReferralCode');
            if(hiddenRef) hiddenRef.value = "";
            
            recalcTotal(); // 重算 (把可能原本有的扣掉)
        }
    })
    .catch(err => {
        console.error(err);
        if(msg) { 
            msg.innerText = "系統忙碌中，請稍後再試"; 
            msg.className = "dz-msg error"; 
        }
        if(btn) { 
            btn.innerText = "驗證"; 
            btn.disabled = false; 
        }
    });
}

// ==========================================
// 7. 輔助函式與驗證 (保留舊功能)
// ==========================================
function safeSetText(id, text) {
    const el = document.getElementById(id);
    if(el) el.innerText = text;
}

function updateShippingUI() {
    const select = document.getElementById('shippingSelect');
    if (!select) return;

    const method = select.value;
    const homeGroup = document.getElementById('homeDeliveryGroup');
    const storeGroup = document.getElementById('storePickupGroup');
    
    const citySelect = document.getElementById('citySelect');
    const districtSelect = document.getElementById('districtSelect');
    const addressInput = document.getElementById('addressInput');
    const storeInput = document.getElementById('storeNameInput');

    if (method === 'home') {
        if(homeGroup) homeGroup.style.display = 'block';
        if(storeGroup) storeGroup.style.display = 'none';
        
        if(citySelect) citySelect.setAttribute('required', 'required');
        if(districtSelect) districtSelect.setAttribute('required', 'required');
        if(addressInput) addressInput.setAttribute('required', 'required');
        if(storeInput) storeInput.removeAttribute('required');

    } else {
        if(homeGroup) homeGroup.style.display = 'none';
        if(storeGroup) storeGroup.style.display = 'block';
        
        if(citySelect) citySelect.removeAttribute('required');
        if(districtSelect) districtSelect.removeAttribute('required');
        if(addressInput) addressInput.removeAttribute('required');
        if(storeInput) storeInput.setAttribute('required', 'required');
    }
}

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

window.changeQty = function(id, delta) {
    let item = cart.find(i => i.id === id);
    if (item) {
        item.qty += delta;
        if (item.qty <= 0) {
            cart = cart.filter(i => i.id !== id);
        }
        localStorage.setItem('pdk_cart', JSON.stringify(cart));
        renderPage();
    }
};

function initCitySelector() {
    const citySelect = document.getElementById('citySelect');
    const districtSelect = document.getElementById('districtSelect');
    if (!citySelect || !districtSelect) return;

    for (let city in taiwanDistricts) {
        let option = document.createElement('option');
        option.value = city;
        option.text = city;
        citySelect.appendChild(option);
    }

    citySelect.addEventListener('change', function() {
        const selectedCity = this.value;
        const districts = taiwanDistricts[selectedCity];
        districtSelect.innerHTML = '<option value="" disabled selected>請選擇區域</option>';
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

// 驗證邏輯 (Regex)
const patterns = {
    name: /^[\u4e00-\u9fa5a-zA-Z\s]+$/, 
    email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ 
};

function showError(input, errorMsgDiv) {
    input.classList.add('error');
    if (errorMsgDiv) errorMsgDiv.classList.add('show');
}
function showSuccess(input, errorMsgDiv) {
    input.classList.remove('error');
    if (errorMsgDiv) errorMsgDiv.classList.remove('show');
}

function checkName() {
    const input = document.getElementById('inputName');
    if(!input) return false;
    const error = input.parentElement.querySelector('.error-msg');
    const val = input.value.trim();

    if (patterns.name.test(val) && val.length >= 2) {
        showSuccess(input, error);
        return true;
    } else {
        showError(input, error);
        return false;
    }
}

function checkPhone() {
    const input = document.getElementById('inputPhone');
    if(!input) return false;
    const error = input.parentElement.querySelector('.error-msg');
    let val = input.value;

    val = val.replace(/\D/g, '');
    if (val.length === 9 && val.startsWith('9')) {
        val = '0' + val;
    }

    if (val.length === 10 && val.startsWith('09')) {
        input.value = val; 
        showSuccess(input, error);
        return true;
    } else {
        showError(input, error);
        return false;
    }
}

function checkEmail() {
    const input = document.getElementById('inputEmail');
    if(!input) return false;
    const error = input.parentElement.querySelector('.error-msg');
    const suggestion = document.getElementById('emailSuggestion');
    let val = input.value.trim().toLowerCase();

    const typos = ['@ggmail.', '@gamil.', '@gmal.', '@gnail.', '@gmai.'];
    let autoFixed = false;

    typos.forEach(typo => {
        if (val.includes(typo)) {
            val = val.replace(typo, '@gmail.');
            input.value = val;
            autoFixed = true;
        }
    });

    if (autoFixed && suggestion) {
        suggestion.innerText = "已為您修正為 @gmail.com";
        suggestion.style.display = 'block';
        setTimeout(() => { suggestion.style.display = 'none'; }, 3000);
    } else if (suggestion) {
        suggestion.style.display = 'none';
    }

    if (patterns.email.test(val)) {
        showSuccess(input, error);
        return true;
    } else {
        showError(input, error);
        return false;
    }
}

function checkDeliveryInfo() {
    const methodSelect = document.getElementById('shippingSelect');
    if(!methodSelect) return false;
    const method = methodSelect.value;
    
    if (method === 'home') {
        const city = document.getElementById('citySelect');
        const district = document.getElementById('districtSelect');
        const addr = document.getElementById('addressInput');
        const addrError = addr ? addr.parentElement.querySelector('.error-msg') : null;
        
        let isCityOk = city && city.value !== "";
        let isDistOk = district && district.value !== "";
        
        if (city) { isCityOk ? city.classList.remove('error') : city.classList.add('error'); }
        if (district) { isDistOk ? district.classList.remove('error') : district.classList.add('error'); }

        let isAddrOk = false;
        if (addr && addr.value.trim().length >= 8) {
            showSuccess(addr, addrError);
            isAddrOk = true;
        } else if (addr) {
            showError(addr, addrError);
        }

        return isCityOk && isDistOk && isAddrOk;

    } else {
        const store = document.getElementById('storeNameInput');
        const storeError = store ? store.parentElement.querySelector('.error-msg') : null;
        
        if (store && store.value.trim().length >= 2) {
            showSuccess(store, storeError);
            return true;
        } else if (store) {
            showError(store, storeError);
            return false;
        }
        return false;
    }
}

function submitOrder() {
    cart = JSON.parse(localStorage.getItem('pdk_cart')) || [];

    if (cart.length === 0) {
        alert("購物車是空的，無法結帳！");
        return;
    }
    
    // 進行驗證
    const vEmail = checkEmail();
    const vName = checkName();
    const vPhone = checkPhone();
    const vDelivery = checkDeliveryInfo();
    
    if (vEmail && vName && vPhone && vDelivery) {
        if(confirm("確定要送出訂單嗎？")) {
            // ★ 關鍵：送出前，把折扣資料同步到 Hidden Input
            updateHiddenInputs();

            const form = document.getElementById('checkoutForm');
            form.action = "/submit_order";
            form.method = "POST";
            form.submit();
        }
    } else {
        alert("請檢查紅色標示的欄位是否填寫正確。");
        const firstError = document.querySelector('.error');
        if(firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
}