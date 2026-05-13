// ============ 聊天核心逻辑 ============

let chatOpen = false;
let chatHistory = [];
let isSending = false;
let humanSessionId = null;
let humanMode = false;
let humanPollTimer = null;
let humanMsgOffset = 0;

// 状态映射
const STATUS_MAP = {
  '待付款': {cls:'s-pending', icon:'clock'},
  '交易中': {cls:'s-trading', icon:'arrow-left-right'},
  '验号中': {cls:'s-verifying', icon:'search'},
  '换绑中': {cls:'s-binding', icon:'lock'},
  '已完成': {cls:'s-done', icon:'check-circle'},
  '售后中': {cls:'s-aftersale', icon:'wrench'},
  '已取消': {cls:'s-cancelled', icon:'x-circle'},
};

function initChat() {
  // 渲染场景案例中的 AI 气泡为 markdown
  document.querySelectorAll('.scenario-chat .chat-bubble.ai').forEach(el => {
    el.innerHTML = marked.parse(el.innerHTML.replace(/<br\s*\/?>/gi, '\n'));
  });

  // 页面加载5秒后显示聊天提示
  setTimeout(() => {
    if (!chatOpen) document.getElementById('chatBtn').classList.add('has-new');
  }, 5000);
}

function toggleChat() {
  chatOpen = !chatOpen;
  document.getElementById('chatPanel').classList.toggle('open', chatOpen);
  document.getElementById('chatBtn').classList.remove('has-new');
  if (chatOpen) document.getElementById('chatInput').focus();
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 100) + 'px';
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function sendQuick(btn) {
  const text = btn.textContent;
  document.getElementById('chatInput').value = text;
  sendMessage();
}

function addMessage(role, content, sources, orders) {
  const div = document.createElement('div');
  div.className = 'chat-bubble ' + role;
  if (role === 'ai') {
    div.innerHTML = marked.parse(content);
  } else {
    div.textContent = content;
  }
  if (orders && orders.length) {
    orders.forEach(o => {
      div.appendChild(createOrderCard(o));
    });
  }
  if (sources && sources.length) {
    const srcDiv = document.createElement('div');
    srcDiv.innerHTML = sources.map(s => '<span class="source-tag"><i data-lucide="file-text" class="ic ic-xs"></i> ' + s + '</span>').join(' ');
    div.appendChild(srcDiv);
  }
  document.getElementById('chatMessages').appendChild(div);
  const container = document.getElementById('chatMessages');
  container.scrollTop = container.scrollHeight;
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

function createOrderCard(o) {
  const card = document.createElement('div');
  card.className = 'order-card';
  const st = STATUS_MAP[o.order_status] || {cls:'s-pending', icon:'package'};
  card.innerHTML = `
    <div class="order-card-header">
      <span class="order-id"><i data-lucide="package" class="ic ic-sm"></i> ${o.order_id}</span>
      <span class="order-status ${st.cls}"><i data-lucide="${st.icon}" class="ic ic-xs"></i> ${o.order_status}</span>
    </div>
    <div class="order-card-product">${o.product_name}</div>
    <div class="order-card-divider"></div>
    <div class="order-card-row"><span class="label"><i data-lucide="gamepad-2" class="ic ic-xs"></i> 游戏</span><span class="value">${o.game_name}（${o.account_platform}）</span></div>
    <div class="order-card-row"><span class="label"><i data-lucide="coins" class="ic ic-xs"></i> 金额</span><span class="value amount">¥${o.amount.toFixed(2)}</span></div>
    <div class="order-card-row"><span class="label"><i data-lucide="shield" class="ic ic-xs"></i> 包赔</span><span class="value">${o.package_type}</span></div>
    <div class="order-card-row"><span class="label"><i data-lucide="store" class="ic ic-xs"></i> 卖家</span><span class="value">${o.seller_name}</span></div>
    <div class="order-card-row"><span class="label"><i data-lucide="smartphone" class="ic ic-xs"></i> 手机</span><span class="value">${o.buyer_phone}</span></div>
    <div class="order-card-row"><span class="label"><i data-lucide="clock" class="ic ic-xs"></i> 下单</span><span class="value">${o.create_time}</span></div>
    ${o.remark ? '<div class="order-card-remark"><i data-lucide="alert-triangle" class="ic ic-xs"></i> ' + o.remark + '</div>' : ''}
  `;
  return card;
}

function addTyping() {
  const div = document.createElement('div');
  div.className = 'typing-indicator';
  div.id = 'typingIndicator';
  div.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
  document.getElementById('chatMessages').appendChild(div);
  const container = document.getElementById('chatMessages');
  container.scrollTop = container.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

async function sendMessage() {
  if (isSending) return;
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  input.style.height = 'auto';
  isSending = true;
  document.getElementById('sendBtn').disabled = true;

  addMessage('user', text);

  // 人工客服模式
  if (humanMode && humanSessionId) {
    chatHistory.push({ role: 'user', content: text });
    try {
      await fetch('/api/human/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: humanSessionId, message: text })
      });
    } catch(e) {
      addMessage('ai', '消息发送失败，请重试');
    }
    isSending = false;
    document.getElementById('sendBtn').disabled = false;
    return;
  }

  chatHistory.push({ role: 'user', content: text });

  // 隐藏快捷按钮
  document.getElementById('quickReplies').style.display = 'none';

  addTyping();

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: chatHistory.slice(-10) })
    });
    const data = await resp.json();
    removeTyping();
    addMessage('ai', data.reply, data.sources, data.orders);
    if (data.transfer_to_human) {
      addMessage('system', 'AI 已为您发起转人工请求，正在匹配人工客服...');
      setTimeout(() => transferToHuman(), 800);
    }
    chatHistory.push({ role: 'assistant', content: data.reply });
  } catch (err) {
    removeTyping();
    addMessage('ai', '网络错误，请检查服务是否启动或联系人工客服（9:30-0:30）');
  }

  isSending = false;
  document.getElementById('sendBtn').disabled = false;
}

// ============ 人工客服转接 ============

function openChatAndTransfer() {
  if (!chatOpen) toggleChat();
}

async function transferToHuman() {
  if (humanMode) return;

  const summary = chatHistory.slice(-6).map(h => `${h.role === 'user' ? '客户' : 'AI'}: ${h.content}`).join('\n');

  try {
    const resp = await fetch('/api/human/transfer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: null,
        summary: summary || '客户主动转人工',
        customer_name: '客户'
      })
    });
    const data = await resp.json();

    if (data.success) {
      humanSessionId = data.session_id;
      humanMode = true;

      document.getElementById('chatTitle').textContent = '排队中 · 等待人工客服';
      document.getElementById('chatOnline').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block"></span><span style="color:#f59e0b">等待接入</span>';
      document.getElementById('chatPanel').querySelector('.chat-panel-header').classList.add('human-mode');
      addMessage('system', '已为您发起转人工请求，正在为您匹配人工客服，请稍候...');

      const waitDiv = document.createElement('div');
      waitDiv.className = 'human-waiting';
      waitDiv.id = 'humanWait';
      waitDiv.innerHTML = '<div class="spinner"></div>正在匹配人工客服...';
      document.getElementById('chatMessages').appendChild(waitDiv);

      startHumanPoll();
    }
  } catch(e) {
    addMessage('ai', '转人工请求发送失败，请稍后再试或拨打人工客服热线：020-22959716');
  }
}

async function pollHumanStatus() {
  if (!humanSessionId) return;
  try {
    const statusResp = await fetch(`/api/human/status?session_id=${humanSessionId}`);
    const statusData = await statusResp.json();

    if (statusData.status === 'active' && !document.getElementById('humanConnected')) {
      const waitEl = document.getElementById('humanWait');
      if (waitEl) waitEl.remove();

      document.getElementById('chatTitle').textContent = '人工客服 · 小张';
      document.getElementById('chatOnline').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-green-400 inline-block"></span><span style="color:#10b981">服务中</span>';

      addMessage('system', '人工客服「小张」已为您服务，您可以直接描述问题。');

      const connected = document.createElement('div');
      connected.id = 'humanConnected';
      connected.style.display = 'none';
      document.getElementById('chatMessages').appendChild(connected);

      document.getElementById('sendBtn').style.background = 'linear-gradient(135deg, #3b82f6, #6366f1)';
    }

    if (statusData.status === 'closed') {
      stopHumanPoll();
      humanMode = false;
      humanSessionId = null;

      document.getElementById('chatTitle').textContent = '小盼 · AI 客服';
      document.getElementById('chatOnline').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-green-400 inline-block"></span>在线';
      document.getElementById('chatPanel').querySelector('.chat-panel-header').classList.remove('human-mode');
      document.getElementById('sendBtn').style.background = '';

      addMessage('system', '人工客服已结束服务，后续问题可以继续咨询小盼~');
      return;
    }

    if (statusData.status === 'active') {
      const msgResp = await fetch(`/api/human/poll?session_id=${humanSessionId}&after=${humanMsgOffset}`);
      const msgData = await msgResp.json();

      if (msgData.messages && msgData.messages.length > 0) {
        msgData.messages.forEach(m => {
          addMessage('human', m.content);
        });
        humanMsgOffset = msgData.total;
      }
    }
  } catch(e) {}
}

function startHumanPoll() {
  if (humanPollTimer) clearInterval(humanPollTimer);
  pollHumanStatus();
  humanPollTimer = setInterval(pollHumanStatus, 2000);
}

function stopHumanPoll() {
  if (humanPollTimer) {
    clearInterval(humanPollTimer);
    humanPollTimer = null;
  }
}
