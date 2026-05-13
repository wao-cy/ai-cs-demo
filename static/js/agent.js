// ============ 人工客服工作台 ============

let currentSessionId = null;
let msgOffset = 0;
let pollTimer = null;

// 加载会话列表
async function loadSessions() {
  try {
    const resp = await fetch('/api/agent/sessions');
    const data = await resp.json();
    const sessions = data.sessions || [];

    // 更新统计
    let pending = 0, active = 0;
    sessions.forEach(s => {
      if (s.status === 'pending') pending++;
      else if (s.status === 'active') active++;
    });
    document.getElementById('statPending').textContent = pending;
    document.getElementById('statActive').textContent = active;
    document.getElementById('statTotal').textContent = sessions.length;

    // 渲染列表
    const list = document.getElementById('sessionList');
    if (!sessions.length) {
      list.innerHTML = '<div class="empty-state" style="padding:2rem 0"><div class="ic ic-lg"><i data-lucide="inbox"></i></div><div style="font-size:0.8rem">暂无会话</div><div style="font-size:0.7rem">等待客户转人工请求...</div></div>';
      lucide.createIcons();
      return;
    }

    list.innerHTML = sessions.map(s => {
      const badgeCls = s.status === 'pending' ? 'badge-pending' : s.status === 'active' ? 'badge-active' : 'badge-ai';
      const badgeText = s.status === 'pending' ? '排队中' : s.status === 'active' ? '服务中' : 'AI服务';
      const isActive = s.session_id === currentSessionId ? ' active' : '';
      return `<div class="session-card${isActive}" data-sid="${s.session_id}" onclick="selectSession('${s.session_id}')">
        <div class="name">${s.customer_name} <span class="badge ${badgeCls}">${badgeText}</span></div>
        <div class="preview">${s.last_msg}</div>
        <div class="meta"><span>${s.created_at}</span><span>消息 ${s.msg_count}</span></div>
      </div>`;
    }).join('');
    lucide.createIcons();
  } catch(e) { console.error('加载会话失败', e); }
}

// 选择会话
async function selectSession(sid) {
  currentSessionId = sid;
  msgOffset = 0;

  document.querySelectorAll('.session-card[data-sid]').forEach(el => {
    el.classList.toggle('active', el.dataset.sid === sid);
  });

  try {
    const resp = await fetch(`/api/agent/messages/${sid}`);
    const data = await resp.json();

    document.getElementById('emptyChat').style.display = 'none';
    const chat = document.getElementById('activeChat');
    chat.style.display = 'flex';

    document.getElementById('chatTitle').textContent = data.meta.customer_name || '客户';
    const statusEl = document.getElementById('chatStatus');
    if (data.status === 'pending') {
      statusEl.className = 'badge badge-pending';
      statusEl.textContent = '排队中';
      document.getElementById('acceptBtn').style.display = '';
      document.getElementById('endBtn').style.display = 'none';
      document.getElementById('inputArea').style.display = 'none';
      document.getElementById('quickReplies').style.display = 'none';
    } else if (data.status === 'active') {
      statusEl.className = 'badge badge-active';
      statusEl.textContent = '服务中';
      document.getElementById('acceptBtn').style.display = 'none';
      document.getElementById('endBtn').style.display = '';
      document.getElementById('inputArea').style.display = 'flex';
      document.getElementById('quickReplies').style.display = 'flex';
      document.getElementById('agentInput').focus();
    }

    if (data.meta.ai_summary) {
      document.getElementById('contextPanel').style.display = '';
      document.getElementById('contextSummary').textContent = data.meta.ai_summary;
    } else {
      document.getElementById('contextPanel').style.display = 'none';
    }

    renderMessages(data.customer_msgs, data.agent_msgs);
    lucide.createIcons();
  } catch(e) { console.error('加载消息失败', e); }
}

function renderMessages(customerMsgs, agentMsgs) {
  const container = document.getElementById('chatMessages');
  container.innerHTML = '';

  const all = [
    ...customerMsgs.map(m => ({...m, role: 'customer'})),
    ...agentMsgs.map(m => ({...m, role: 'agent'}))
  ];

  all.sort((a, b) => (a.time || '').localeCompare(b.time || ''));

  all.forEach(m => {
    const row = document.createElement('div');
    row.className = `msg-row ${m.role}`;
    row.innerHTML = `<div>
      <div class="msg-bubble">${escapeHtml(m.content)}</div>
      <div class="msg-time">${m.time}</div>
    </div>`;
    container.appendChild(row);
  });

  msgOffset = agentMsgs.length;
  container.scrollTop = container.scrollHeight;
  lucide.createIcons();
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

// 接入会话
async function acceptSession() {
  if (!currentSessionId) return;
  try {
    await fetch(`/api/agent/accept/${currentSessionId}`, { method: 'POST' });
    await selectSession(currentSessionId);
    loadSessions();
  } catch(e) {}
}

// 结束会话
async function endSession() {
  if (!currentSessionId) return;
  if (!confirm('确定结束本次服务？')) return;
  try {
    await fetch('/api/human/end', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: currentSessionId })
    });
    currentSessionId = null;
    document.getElementById('activeChat').style.display = 'none';
    document.getElementById('emptyChat').style.display = 'flex';
    loadSessions();
  } catch(e) {}
}

// 发送回复
async function sendAgentReply() {
  const input = document.getElementById('agentInput');
  const text = input.value.trim();
  if (!text || !currentSessionId) return;

  input.value = '';

  const container = document.getElementById('chatMessages');
  const row = document.createElement('div');
  row.className = 'msg-row agent';
  row.innerHTML = `<div>
    <div class="msg-bubble">${escapeHtml(text)}</div>
    <div class="msg-time">${new Date().toTimeString().slice(0,8)}</div>
  </div>`;
  container.appendChild(row);
  container.scrollTop = container.scrollHeight;

  try {
    await fetch(`/api/agent/reply/${currentSessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
  } catch(e) {}
}

function quickReply(el) {
  document.getElementById('agentInput').value = el.textContent;
  sendAgentReply();
}

// 轮询：定时刷新
function startPolling() {
  pollTimer = setInterval(async () => {
    await loadSessions();
    if (currentSessionId) {
      try {
        const resp = await fetch(`/api/agent/messages/${currentSessionId}`);
        const data = await resp.json();
        if (data.customer_msgs.length > 0 || data.agent_msgs.length > 0) {
          const container = document.getElementById('chatMessages');
          const currentCount = container.querySelectorAll('.msg-row.customer').length;
          if (data.customer_msgs.length > currentCount) {
            renderMessages(data.customer_msgs, data.agent_msgs);
          }
        }
      } catch(e) {}
    }
  }, 2000);
}

// 初始化
loadSessions();
startPolling();
if (typeof lucide !== 'undefined') lucide.createIcons();
