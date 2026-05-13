// ============ 订单模拟器 ============

const SIM_GAMES = {
  '王者荣耀': {platforms:['QQ','微信'], products:['V10满皮肤 QQ区 李白本命','156皮肤 星耀段位 微信区','国服韩信 89皮肤 QQ区','98皮肤 王者段位 微信区']},
  '和平精英': {platforms:['QQ','微信'], products:['87套装 钻石段位 QQ区','满配号 微信区 65皮肤','荣耀段位 QQ区 53套装']},
  '原神': {platforms:['米哈游','B站'], products:['72级 48角色 米哈游服','满探索 55角色 B站服 68级','90级 42角色 米哈游服']},
  '永劫无间': {platforms:['网易','Steam'], products:['120皮肤 铂金段位 网易版','全角色 Steam版 78皮肤','钻石段位 网易版 95皮肤']},
  '逆水寒': {platforms:['网易'], products:['95级 剑客 网易服','毕业装 奶妈 网易服 88级','满修 战士 网易服']},
  '英雄联盟': {platforms:['QQ','微信'], products:['186皮肤 钻石段位 QQ区','全英雄 142皮肤 微信区','宗师段位 QQ区 98皮肤']},
  '第五人格': {platforms:['网易'], products:['78皮肤 网易服','全角色 56皮肤 网易服','限定金皮号 网易服']},
  'CF穿越火线': {platforms:['QQ'], products:['全英雄级 QQ区','32把英雄武器 QQ区','满V QQ区 钻石段位']},
  'DNF地下城': {platforms:['QQ'], products:['110级 红眼 QQ区','毕业装 QQ区 105级','满级 奶爸 QQ区']},
  '瓦罗兰特': {platforms:['拳头'], products:['67皮肤 钻石段位','全特工 89皮肤','神话段位 45皮肤']},
  'Apex英雄': {platforms:['EA'], products:['3传家宝 EA版','大师段位 EA版 78皮肤','全传家宝 EA版']},
  '梦幻西游': {platforms:['网易'], products:['175级 法师 网易服','无级别 网易服 155级','满修 大唐 网易服']},
  '明日之后': {platforms:['网易'], products:['85级 网易服 庄园16级','毕业装 网易服 78级','满庄园 网易服 92级']},
  'Steam账号': {platforms:['Steam'], products:['168游戏 库值8600元','热门游戏合集 库值4200元','3A大作合集 库值12000元']},
  '神武4': {platforms:['多益'], products:['95级 剑客 多益服','成品号 多益服 88级','满修 法师 多益服']}
};
const SIM_PHONES = ['138****2356','159****7821','186****3345','177****9012','135****6789','188****4523','156****8901','183****1278','176****5634','137****9045'];
const SIM_SELLERS = ['星辰游戏','龙腾账号','优品游戏','极速出号','金牌卖家','风云游戏','盛世账号','传奇出号','皇冠卖家','钻石卖家'];
const SIM_REMARKS = ['买家反馈账号被找回，已启动包赔流程','换绑失败，买家申请售后处理','验号时发现与描述不符','卖家未按时配合换绑','账号存在安全风险，买家申请退款'];

let simOrderData = null;
let simInsertCount = 0;

function initSimulator() {
  // 状态单选按钮交互
  document.querySelectorAll('.sim-status-opt input').forEach(radio => {
    radio.addEventListener('change', () => {
      document.querySelectorAll('.sim-status-opt span').forEach(s => s.style.opacity = '0.5');
      radio.parentElement.querySelector('span').style.opacity = '1';
      document.getElementById('simRemarkWrap').classList.toggle('hidden', radio.value !== '售后中');
    });
    radio.parentElement.querySelector('span').style.opacity = radio.checked ? '1' : '0.5';
  });

  // 输入变化时自动更新预览
  document.querySelectorAll('#simGame,#simPlatform,#simProduct,#simAmount,#simPhone,#simSeller,#simPackage,#simRemark').forEach(el => {
    el.addEventListener('input', updatePreview);
    el.addEventListener('change', updatePreview);
  });

  loadSimCount();
}

function onSimGameChange() {
  const game = document.getElementById('simGame').value;
  const platSel = document.getElementById('simPlatform');
  const platforms = SIM_GAMES[game]?.platforms || ['QQ'];
  platSel.innerHTML = platforms.map(p => `<option value="${p}">${p}</option>`).join('');
}

function randomFillOrder() {
  const game = document.getElementById('simGame').value;
  const info = SIM_GAMES[game];
  const platform = info.platforms[Math.floor(Math.random() * info.platforms.length)];
  document.getElementById('simPlatform').innerHTML = info.platforms.map(p => `<option value="${p}" ${p===platform?'selected':''}>${p}</option>`).join('');

  document.getElementById('simProduct').value = info.products[Math.floor(Math.random() * info.products.length)];
  document.getElementById('simAmount').value = (Math.random() * 4500 + 50).toFixed(2);
  document.getElementById('simPhone').value = SIM_PHONES[Math.floor(Math.random() * SIM_PHONES.length)];
  document.getElementById('simSeller').value = SIM_SELLERS[Math.floor(Math.random() * SIM_SELLERS.length)];

  const statuses = document.querySelectorAll('.sim-status-opt input');
  const idx = Math.floor(Math.random() * statuses.length);
  statuses.forEach((r, i) => {
    r.checked = i === idx;
    r.parentElement.querySelector('span').style.opacity = i === idx ? '1' : '0.5';
  });
  document.getElementById('simRemarkWrap').classList.toggle('hidden', statuses[idx].value !== '售后中');
  if (statuses[idx].value === '售后中') {
    document.getElementById('simRemark').value = SIM_REMARKS[Math.floor(Math.random() * SIM_REMARKS.length)];
  } else {
    document.getElementById('simRemark').value = '';
  }

  updatePreview();
}

function getSimFormData() {
  const status = document.querySelector('.sim-status-opt input:checked')?.value || '已完成';
  const now = new Date().toISOString().replace('T',' ').substring(0,19);
  return {
    order_id: 'PZ' + Date.now().toString().slice(-10),
    buyer_phone: document.getElementById('simPhone').value || SIM_PHONES[0],
    game_name: document.getElementById('simGame').value,
    account_platform: document.getElementById('simPlatform').value,
    order_status: status,
    product_name: document.getElementById('simProduct').value || '高级游戏账号',
    amount: parseFloat(document.getElementById('simAmount').value) || 999.99,
    create_time: now,
    seller_name: document.getElementById('simSeller').value || SIM_SELLERS[0],
    package_type: document.getElementById('simPackage').value,
    update_time: now,
    remark: document.getElementById('simRemark').value || ''
  };
}

function updatePreview() {
  simOrderData = getSimFormData();
  const el = document.getElementById('orderPreview');
  const json = JSON.stringify(simOrderData, null, 2);
  const highlighted = json
    .replace(/"([^"]+)":/g, '<span style="color:var(--c1)">"$1"</span>:')
    .replace(/: "([^"]+)"/g, ': <span style="color:var(--c3)">"$1"</span>')
    .replace(/: ([\d.]+)/g, ': <span style="color:var(--c5)">$1</span>');
  el.innerHTML = highlighted;
}

function copyOrderJSON() {
  if (!simOrderData) { randomFillOrder(); }
  const text = JSON.stringify(simOrderData, null, 2);
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById('copyBtn');
    btn.textContent = '已复制';
    setTimeout(() => btn.innerHTML = '<i data-lucide="copy" class="ic ic-xs"></i> 复制 JSON', 2000);
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }).catch(() => {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    const btn = document.getElementById('copyBtn');
    btn.textContent = '已复制';
    setTimeout(() => btn.innerHTML = '<i data-lucide="copy" class="ic ic-xs"></i> 复制 JSON', 2000);
    if (typeof lucide !== 'undefined') lucide.createIcons();
  });
}

async function submitOrder() {
  if (!simOrderData) { randomFillOrder(); }
  const btn = document.getElementById('submitOrderBtn');
  btn.disabled = true;
  btn.textContent = '写入中...';
  try {
    const resp = await fetch('/api/order/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(simOrderData)
    });
    const data = await resp.json();
    if (data.success) {
      btn.textContent = '写入成功';
      simInsertCount++;
      document.getElementById('simCount').textContent = simInsertCount;
    } else {
      btn.textContent = '失败: ' + (data.error || '写入失败');
    }
  } catch (err) {
    btn.textContent = '网络错误';
  }
  setTimeout(() => {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="database" class="ic ic-sm"></i> 写入数据库';
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }, 2000);
}

async function loadSimCount() {
  try {
    const resp = await fetch('/api/order/stats');
    const data = await resp.json();
    document.getElementById('simCount').textContent = data.sim_count || 0;
    simInsertCount = data.sim_count || 0;
  } catch(e) {}
}
