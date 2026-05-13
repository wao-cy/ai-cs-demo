# -*- coding: utf-8 -*-
"""知识库加载与检索服务 — 混合检索（BM25 + 向量语义 + 加权融合）"""

import os
import re
import math
import requests
import config

KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'knowledge_base.md')

kb_sections = []        # 章节列表 [{title, content, keywords, tokens, tf}]
kb_embeddings = None    # numpy 数组 (n_sections, dim)，启动时计算
_idf = {}               # 词 -> IDF 值
_avg_dl = 0.0           # 平均文档长度（token 数）


# ============ 文本分词 ============

_STOPWORDS = {
    '的', '了', '是', '在', '有', '和', '与', '或', '等', '为', '中',
    '对', '可', '将', '由', '从', '到', '被', '及', '以', '之', '不',
    '也', '都', '会', '能', '要', '请', '如', '若', '则', '该', '其',
    '什么', '怎么', '如何', '可以', '一个', '这个', '那个', '哪些',
    '需要', '进行', '操作', '处理', '情况', '问题', '用户', '买家', '卖家',
}


def _tokenize(text):
    """中英文混合分词：中文 bigram/trigram + 英文单词"""
    text = re.sub(r'[#|*\-\[\]()>{}]', ' ', text)
    text = re.sub(r'[，。！？、；：""''（）\n\r\t]', ' ', text)
    tokens = []
    cn_segments = re.findall(r'[一-鿿]+', text)
    for seg in cn_segments:
        if len(seg) >= 2:
            tokens.append(seg)
        for n in range(2, min(4, len(seg) + 1)):
            for i in range(len(seg) - n + 1):
                gram = seg[i:i + n]
                if len(gram) >= 2:
                    tokens.append(gram)
    en_words = re.findall(r'[a-zA-Z0-9]{2,}', text)
    tokens.extend(w.lower() for w in en_words)
    return [t for t in tokens if t not in _STOPWORDS]


def _term_freq(tokens):
    """计算词频 dict"""
    tf = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1
    return tf


# ============ BM25 ============

_K1 = 1.5
_B = 0.75


def _build_bm25_index():
    """预计算 BM25 所需的 IDF 和文档统计"""
    global _idf, _avg_dl

    n = len(kb_sections)
    if n == 0:
        return

    # 计算每个词出现在多少个文档中
    doc_freq = {}
    total_dl = 0
    for sec in kb_sections:
        unique_tokens = set(sec['tokens'])
        for t in unique_tokens:
            doc_freq[t] = doc_freq.get(t, 0) + 1
        total_dl += len(sec['tokens'])

    _avg_dl = total_dl / n if n > 0 else 1

    # IDF: log((N - n_t + 0.5) / (n_t + 0.5) + 1)
    for term, df in doc_freq.items():
        _idf[term] = math.log((n - df + 0.5) / (df + 0.5) + 1.0)


def _bm25_score(query_tokens, section):
    """计算单个文档的 BM25 分数"""
    tf = section['tf']
    dl = len(section['tokens'])
    score = 0.0
    for qt in query_tokens:
        if qt not in tf:
            continue
        term_f = tf[qt]
        idf = _idf.get(qt, 0)
        numerator = term_f * (_K1 + 1)
        denominator = term_f + _K1 * (1 - _B + _B * dl / _avg_dl)
        score += idf * numerator / denominator
    return score


def _bm25_retrieve(query, top_k):
    """BM25 关键词检索，返回 [(score, section), ...]"""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return [(0.0, s) for s in kb_sections[:top_k]]

    scored = []
    for sec in kb_sections:
        s = _bm25_score(query_tokens, sec)
        # 标题匹配加权
        title_tokens = set(_tokenize(sec['title']))
        title_overlap = len(set(query_tokens) & title_tokens)
        s += title_overlap * 2.0
        scored.append((s, sec))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k * 3]  # 多召回一些给融合用


# ============ 向量检索 ============

def _get_embeddings(texts):
    """调用 Dashscope Embedding API 获取向量"""
    headers = {
        'Authorization': f'Bearer {config.API_KEY}',
        'Content-Type': 'application/json'
    }
    # text-embedding-v3 单次最多 10 条
    all_embeddings = []
    batch_size = 10
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        payload = {
            'model': config.EMBEDDING_MODEL,
            'input': batch,
            'encoding_format': 'float'
        }
        url = f'{config.EMBEDDING_API_BASE.rstrip("/")}/embeddings'
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # 按 index 排序确保顺序正确
        sorted_data = sorted(data['data'], key=lambda x: x['index'])
        for item in sorted_data:
            all_embeddings.append(item['embedding'])
    return all_embeddings


def _build_vector_index():
    """计算所有章节的 embedding 并缓存"""
    global kb_embeddings
    try:
        texts = [sec['title'] + ' ' + sec['content'][:1000] for sec in kb_sections]
        embeddings = _get_embeddings(texts)
        # 转为简单的 list of lists（避免 numpy 依赖）
        kb_embeddings = embeddings
        print(f"[向量索引] 已计算 {len(embeddings)} 个章节的 embedding (dim={len(embeddings[0])})")
    except Exception as e:
        print(f"[向量索引] 计算失败，将仅使用 BM25 检索: {e}")
        kb_embeddings = None


def _cosine_similarity(vec_a, vec_b):
    """计算两个向量的余弦相似度（纯 Python）"""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _vector_retrieve(query, top_k):
    """向量语义检索，返回 [(similarity, section), ...]"""
    if kb_embeddings is None:
        return []

    try:
        query_vecs = _get_embeddings([query])
        if not query_vecs:
            return []
        query_vec = query_vecs[0]
    except Exception as e:
        print(f"[向量检索] 查询 embedding 失败: {e}")
        return []

    scored = []
    for i, sec in enumerate(kb_sections):
        sim = _cosine_similarity(query_vec, kb_embeddings[i])
        scored.append((sim, sec))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k * 3]


# ============ 知识库加载 ============

def load_knowledge_base():
    """加载知识库，构建 BM25 索引 + 向量索引"""
    global kb_sections

    with open(KB_PATH, 'r', encoding='utf-8') as f:
        text = f.read()

    sections = []
    parts = re.split(r'^### ', text, flags=re.MULTILINE)
    for part in parts[1:]:
        lines = part.split('\n', 1)
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""
        if content and len(content) > 50:
            tokens = _tokenize(title + ' ' + content[:800])
            sections.append({
                'title': title,
                'content': content,
                'tokens': tokens,
                'tf': _term_freq(tokens),
            })

    if len(sections) < 5:
        sections = []
        parts = re.split(r'^## ', text, flags=re.MULTILINE)
        for part in parts[1:]:
            lines = part.split('\n', 1)
            title = lines[0].strip()
            content = lines[1].strip() if len(lines) > 1 else ""
            if content:
                tokens = _tokenize(title + ' ' + content[:500])
                sections.append({
                    'title': title,
                    'content': content,
                    'tokens': tokens,
                    'tf': _term_freq(tokens),
                })

    kb_sections = sections
    print(f"[知识库] 已加载 {len(sections)} 个章节")

    # 构建 BM25 索引
    _build_bm25_index()
    print(f"[BM25] 索引构建完成 (词汇量={len(_idf)}, 平均文档长度={_avg_dl:.0f})")

    # 构建向量索引
    _build_vector_index()


# ============ 混合检索 ============

def retrieve_sections(query, top_k=None):
    """混合检索：BM25 + 向量语义 + 加权融合"""
    if top_k is None:
        top_k = config.TOP_K

    alpha = config.RETRIEVAL_ALPHA  # BM25 权重

    # BM25 召回
    bm25_results = _bm25_retrieve(query, top_k)
    # 向量召回
    vec_results = _vector_retrieve(query, top_k)

    # 归一化 BM25 分数到 [0, 1]
    bm25_scores = {id(s): sc for sc, s in bm25_results}
    bm25_max = max(bm25_scores.values()) if bm25_scores else 1.0
    bm25_min = min(bm25_scores.values()) if bm25_scores else 0.0
    bm25_range = bm25_max - bm25_min if bm25_max != bm25_min else 1.0

    # 向量分数（余弦相似度本身在 [-1,1]，归一化到 [0,1]）
    vec_scores = {id(s): sc for sc, s in vec_results}

    # 合并所有候选文档
    all_sections = {}
    for _, s in bm25_results:
        all_sections[id(s)] = s
    for _, s in vec_results:
        all_sections[id(s)] = s

    # 加权融合
    fused = []
    for sid, sec in all_sections.items():
        bm25_norm = (bm25_scores.get(sid, 0) - bm25_min) / bm25_range
        vec_norm = (vec_scores.get(sid, 0) + 1) / 2  # [-1,1] -> [0,1]
        final_score = alpha * bm25_norm + (1 - alpha) * vec_norm
        fused.append((final_score, sec))

    fused.sort(key=lambda x: x[0], reverse=True)

    if not fused:
        return kb_sections[:top_k]

    return [s for _, s in fused[:top_k]]
