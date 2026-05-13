# 盼之代售 AI 智能客服系统 Demo

基于 **混合检索 RAG（BM25 + 向量语义）+ 大语言模型 + Function Calling + 人工客服接管** 的游戏账号交易平台智能客服方案。

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端（纯静态）                       │
│  Tailwind CSS + Chart.js + marked.js + Lucide Icons     │
│  index.html ← chat.js / simulator.js / charts.js        │
│  agent.html ← agent.js                                   │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────▼──────────────────────────────────┐
│                   Flask 路由层 (app.py)                   │
│  页面路由 / API 路由 / 请求分发                            │
└───┬──────────┬──────────┬──────────┬────────────────────┘
    │          │          │          │
    ▼          ▼          ▼          ▼
┌────────┐┌────────┐┌────────┐┌────────┐
│kb_svc  ││ai_svc  ││order_  ││chat_   │  ← services/ 业务层
│知识库   ││AI 调用  ││service ││service │
│混合检索 ││FuncCall ││订单操作 ││会话管理 │
└────┬───┘└────┬───┘└────┬───┘└────┬───┘
     │         │         │         │
     ▼         ▼         ▼         ▼
 知识库.md   Dashscope   SQLite   内存字典
 + Embedding  API       orders.db  (Demo用)
```

---

## 核心技术点

### 1. 混合检索 RAG

三阶段检索流程，兼顾精确匹配与语义理解：

```
用户问题
  ├─→ BM25 关键词召回（IDF 加权 + 文档长度归一化 + 标题加权 ×2）
  ├─→ 向量语义召回（Dashscope text-embedding-v3, 1024 维, 余弦相似度）
  └─→ 加权融合（α=0.4 BM25 + 0.6 向量）→ Top-K
```

| 组件 | 算法 | 说明 |
|------|------|------|
| 分词 | 中文 bigram/trigram + 英文单词 | 中文无空格分词，2-3 字滑动窗口 |
| BM25 | k1=1.5, b=0.75 | IDF = log((N-df+0.5)/(df+0.5)+1) |
| 向量 | text-embedding-v3 (1024d) | 启动时批量计算 58 章节 embedding 缓存内存 |
| 融合 | 归一化加权 | BM25 分数 min-max 归一化，向量分数 [-1,1]→[0,1] |

**效果对比：**

| 查询 | 纯 BM25 | 混合检索 |
|------|---------|---------|
| "退钱" | 平台简介（无关） | 交易取消说明、售后场景 |
| "号被找回了" vs "账号找回" | 结果不一致 | 都命中"账号被找回怎么办" |
| "买的游戏号不安全" | 仅关键词匹配 | 扩展命中"遭遇诈骗后怎么办" |

### 2. Function Calling 订单查询

AI 自动识别查询意图 → 引导用户提供信息 → 调用工具查询 → 卡片式展示。

```
用户："查一下我的订单"
  → AI 识别意图，引导提供订单号/手机号/游戏名
用户："手机尾号 2356"
  → AI 调用 query_order(buyer_phone="2356")
  → SQLite 查询，返回匹配订单
  → AI 基于结果生成友好回复 + 前端渲染订单卡片
```

支持：订单号精确匹配、手机号模糊匹配（后4位）、游戏名模糊匹配、组合查询。

### 3. 转人工策略

AI 先引导 → 尝试知识库解决 → 确实无法解决才转人工（非关键词直接转接）。

```
用户："转人工"
  → AI 询问具体问题
用户："号被找回了，要退款！"
  → AI 查订单 + 给包赔方案
用户："不行，就是要转人工"
  → 满足转接条件，Function Calling 触发 transfer_to_human
  → 生成上下文摘要 → 排队 → 客服工作台接入 → 无缝对话
```

### 4. Prompt 管理

System Prompt 从代码中独立为 `prompts/system.md`，按模块管理：
- `prompts/system.md` — 系统提示词（角色设定 + 回答规则 + 订单策略 + 转人工策略 + 对话示例）
- `prompts/tools.py` — Function Calling 工具定义（query_order + transfer_to_human）

---

## 项目结构

```
ai-cs-demo/
├── app.py                  # Flask 路由层（精简，只做请求分发）
├── config.py               # 全部配置（API / 服务 / RAG / Embedding）
├── requirements.txt        # Python 依赖（flask, requests）
├── start.bat               # Windows 一键启动脚本
│
├── prompts/                # Prompt 模板
│   ├── system.md           # 系统提示词
│   └── tools.py            # Function Calling 工具定义
│
├── services/               # 业务逻辑层
│   ├── ai_service.py       # AI API 调用 + tool 执行
│   ├── kb_service.py       # 知识库加载 + BM25 + 向量 + 混合检索
│   ├── order_service.py    # SQLite 订单 CRUD + 模拟数据生成
│   └── chat_service.py     # 人工客服会话管理（内存存储）
│
├── static/                 # 前端静态资源
│   ├── css/
│   │   ├── base.css        # CSS 变量系统 + 重置 + 动画
│   │   ├── components.css  # 卡片/气泡/按钮/徽章等组件
│   │   └── pages.css       # 页面布局（Hero/Section/聊天面板/工作台）
│   └── js/
│       ├── chat.js         # 聊天核心（消息收发/人工模式/订单卡片）
│       ├── agent.js        # 人工客服工作台（会话列表/消息/轮询）
│       ├── simulator.js    # 订单模拟器（随机填充/提交/预览）
│       └── charts.js       # Chart.js 图表初始化
│
├── templates/
│   ├── index.html          # 主展示页（引用 static 文件）
│   └── agent.html          # 人工客服工作台
│
└── data/
    ├── knowledge_base.md   # 知识库原文（9大分类, 58章节, 34KB）
    └── orders.db           # SQLite 订单库（30条模拟数据, 自动生成）
```

---

## 快速启动

### 1. 配置 AI 接口

编辑 `config.py`，填入你的 API Key：

```python
API_KEY = "你的API密钥"
API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 通义千问
MODEL = "qwen-plus"
```

支持的提供商：

| 提供商 | API_BASE | MODEL |
|--------|----------|-------|
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | qwen-plus / qwen-turbo / qwen-max |
| DeepSeek | `https://api.deepseek.com` | deepseek-chat |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | glm-4-flash |
| Ollama 本地 | `http://localhost:11434/v1` | 你本地运行的模型名 |

> Embedding 模型使用同一 API Key 调用 `text-embedding-v3`，无需额外配置。

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python app.py       # 或双击 start.bat
```

启动后访问 **http://127.0.0.1:5000**

人工客服工作台：**http://127.0.0.1:5000/agent**（建议新标签页打开）

---

## 配置说明（config.py）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `API_KEY` | — | AI API 密钥（必填） |
| `API_BASE` | 通义千问 | API 基础地址 |
| `MODEL` | qwen3.6-flash-2026-04-16 | 对话模型名称 |
| `HOST` | 127.0.0.1 | 服务监听地址 |
| `PORT` | 5000 | 服务端口 |
| `DEBUG` | True | 调试模式 |
| `TOP_K` | 3 | RAG 检索返回的最大段落数 |
| `MAX_TOKENS` | 1500 | AI 回复最大 token 数 |
| `HISTORY_TURNS` | 5 | 对话历史保留轮数 |
| `EMBEDDING_API_BASE` | 通义千问 | Embedding API 地址 |
| `EMBEDDING_MODEL` | text-embedding-v3 | Embedding 模型名称 |
| `RETRIEVAL_ALPHA` | 0.4 | BM25 权重（向量权重 = 1 - alpha） |

---

## API 接口

### AI 对话

#### POST `/api/chat`

```json
// 请求
{ "message": "我的订单怎么样了", "history": [{"role":"user","content":"..."}] }

// 响应
{
  "reply": "AI 回复（Markdown）",
  "sources": ["来源章节标题"],
  "orders": [{ "order_id": "PZ...", "order_status": "已完成", "amount": 999.99 }],
  "transfer_to_human": false,
  "retrieve_time": 12,
  "ai_time": 2340,
  "status": "success"
}
```

### 订单操作

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/order/add` | POST | 写入一条订单（模拟器用） |
| `/api/order/stats` | GET | 订单统计（总数/状态分布/模拟器写入数） |

### 人工客服 — 客户侧

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/human/transfer` | POST | 请求转人工，返回 session_id |
| `/api/human/status` | GET | 查询会话状态（pending/active/closed） |
| `/api/human/send` | POST | 客户发送消息 |
| `/api/human/poll` | GET | 轮询客服回复（`after` 参数指定偏移） |
| `/api/human/end` | POST | 结束会话 |

### 人工客服 — 工作台侧

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/agent/sessions` | GET | 获取未关闭会话列表 |
| `/api/agent/messages/<id>` | GET | 获取会话详情（消息 + AI 摘要） |
| `/api/agent/accept/<id>` | POST | 客服接入会话 |
| `/api/agent/reply/<id>` | POST | 客服发送回复 |

---

## 设计风格

- **深色科技风**，主色调青色 (#06b6d4) + 蓝色 (#3b82f6)
- **CSS 变量系统**：色彩梯度、间距（4px 基准）、圆角、阴影、响应式断点
- **Lucide SVG 图标**，不使用 emoji
- **Chart.js** 图表（月度对话量趋势 + 问题分类分布）
- **marked.js** Markdown 渲染（AI 回复支持加粗/列表/表格/代码/引用）
- **滚动入场动画**（IntersectionObserver）
- **响应式**：桌面端完整适配，移动端基本可用

---

## 注意事项

- 本项目为 **面试展示用途**，知识库数据来源于盼之代售官网帮助中心
- 订单数据为 **模拟生成**，不代表真实交易信息
- Function Calling 依赖模型对 tools API 的支持，推荐 qwen-plus 及以上
- 启动时会自动计算 58 个章节的 embedding（约 6 次 API 调用），之后检索全程本地
- 人工客服会话存储在 **内存** 中，重启丢失（Demo 用，生产环境应使用 Redis）
- 消息同步采用 **轮询**（2秒间隔），生产环境建议 WebSocket
- 如需重新生成订单数据：`python -c "from services.order_service import init_db; init_db(force=True)"`

---

## 许可

仅供学习展示使用。
