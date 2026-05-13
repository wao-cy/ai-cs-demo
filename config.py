# config.py - AI API 配置
# 支持任何 OpenAI 兼容接口（智谱/DeepSeek/通义/Ollama 等）

# === API 配置 ===
# 填入你的 API Key
API_KEY = ""

# API 基础地址（不同提供商的地址不同）
# DeepSeek:     https://api.deepseek.com
# 智谱(GLM):    https://open.bigmodel.cn/api/paas/v4
# 阿里云百炼:    https://dashscope.aliyuncs.com/compatible-mode/v1
# Ollama本地:    http://localhost:11434/v1
API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 模型名称
# DeepSeek:  deepseek-chat
# 智谱:      glm-4-flash
# 百炼:      qwen-plus / qwen-turbo / qwen-max
# Ollama:    你本地运行的模型名
MODEL = "qwen3.6-flash-2026-04-16"

# === 服务配置 ===
HOST = "127.0.0.1"
PORT = 5000
DEBUG = True

# === RAG 配置 ===
# 检索知识库时返回的最大段落数
TOP_K = 3
# AI 回复最大 token 数
MAX_TOKENS = 1500
# 对话历史保留轮数（每轮=用户+助手各1条）
HISTORY_TURNS = 5

# === Embedding 配置 ===
# 用于知识库向量检索的 Embedding 模型
EMBEDDING_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
EMBEDDING_MODEL = "text-embedding-v3"

# === 混合检索权重 ===
# BM25 关键词检索权重（向量检索权重 = 1 - RETRIEVAL_ALPHA）
RETRIEVAL_ALPHA = 0.4
