# config.py - AI API 配置
# 支持任何 OpenAI 兼容接口（智谱/DeepSeek/通义/Ollama 等）
# 敏感配置通过环境变量读取，本地开发可在下方填默认值

import os

# === API 配置 ===
# 优先读取环境变量，其次使用下方默认值（本地开发用）
API_KEY = os.environ.get("API_KEY", "")

# API 基础地址（不同提供商的地址不同）
# DeepSeek:     https://api.deepseek.com
# 智谱(GLM):    https://open.bigmodel.cn/api/paas/v4
# 阿里云百炼:    https://dashscope.aliyuncs.com/compatible-mode/v1
# Ollama本地:    http://localhost:11434/v1
API_BASE = os.environ.get("API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# 模型名称
# DeepSeek:  deepseek-chat
# 智谱:      glm-4-flash
# 百炼:      qwen-plus / qwen-turbo / qwen-max
# Ollama:    你本地运行的模型名
MODEL = os.environ.get("MODEL", "qwen3.6-flash-2026-04-16")

# === 服务配置 ===
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"

# === RAG 配置 ===
# 检索知识库时返回的最大段落数
TOP_K = int(os.environ.get("TOP_K", "3"))
# AI 回复最大 token 数
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "1500"))
# 对话历史保留轮数（每轮=用户+助手各1条）
HISTORY_TURNS = int(os.environ.get("HISTORY_TURNS", "5"))

# === Embedding 配置 ===
# 用于知识库向量检索的 Embedding 模型
EMBEDDING_API_BASE = os.environ.get("EMBEDDING_API_BASE", API_BASE)
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-v3")

# === 混合检索权重 ===
# BM25 关键词检索权重（向量检索权重 = 1 - RETRIEVAL_ALPHA）
RETRIEVAL_ALPHA = float(os.environ.get("RETRIEVAL_ALPHA", "0.4"))
