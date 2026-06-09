"""jd_store.py - JD 知识库（混合检索 + Cross-Encoder 重排序）"""
import jieba
import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# ─── 全局状态 ───
client = chromadb.Client()
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-small-zh-v1.5")

# BM25 索引（模块级变量，load_jds 时构建）
_bm25_index: BM25Okapi | None = None
_jd_texts: list[str] = []  # 保存原始文本，用于按索引取回结果

# Cross-Encoder 重排序模型（懒加载，首次调用时初始化）
_reranker: CrossEncoder | None = None
_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"


def _get_collection():
    """获取或创建 ChromaDB collection"""
    return client.get_or_create_collection("job_descriptions", embedding_function=embedding_fn)


def _tokenize(text: str) -> list[str]:
    """
    中文分词（jieba）
    BM25 需要词粒度的输入，不能直接塞整段中文。
    jieba.lcut() 返回分词列表，如 "我喜欢Python" → ["我", "喜欢", "Python"]
    """
    return jieba.lcut(text)


def load_jds(jd_list: list[dict]) -> None:
    """
    把 JD 列表同时存入向量数据库和 BM25 索引。
    Args:
        jd_list: [{"id": "jd_1", "text": "..."}]
    """
    global _bm25_index, _jd_texts

    # 1. 存入 ChromaDB（向量检索用）
    collection = _get_collection()
    texts = [jd["text"] for jd in jd_list]
    ids = [jd["id"] for jd in jd_list]
    collection.upsert(documents=texts, ids=ids)

    # 2. 构建 BM25 索引（关键词检索用）
    _jd_texts = texts
    tokenized_corpus = [_tokenize(t) for t in texts]  # 对每条JD分词
    _bm25_index = BM25Okapi(tokenized_corpus)         # 构建倒排索引


def _vector_search(query: str, top_k: int) -> list[tuple[str, int]]:
    """
    向量语义检索，返回 [(文本, 原始排名), ...]
    ChromaDB 内部会对 query 做 embedding，然后计算余弦相似度。
    """
    collection = _get_collection()
    results = collection.query(query_texts=[query], n_results=top_k)
    docs = results["documents"][0]
    # 返回 (文本, 排名) 元组列表，排名从 0 开始
    return [(doc, rank) for rank, doc in enumerate(docs)]


def _bm25_search(query: str, top_k: int) -> list[tuple[str, int]]:
    """
    BM25 关键词检索，返回 [(文本, 原始排名), ...]
    BM25 通过词频（TF）和逆文档频率（IDF）计算相关性分数。
    """
    if _bm25_index is None:
        return []

    tokenized_query = _tokenize(query)  # 对查询也要分词
    scores = _bm25_index.get_scores(tokenized_query)  # 对每条JD打分

    # argsort 降序取 top_k 的索引
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [(_jd_texts[i], rank) for rank, i in enumerate(top_indices)]


def _rrf_fusion(results_list: list[list[tuple[str, int]]], k: int = 60) -> list[str]:
    """
    RRF（Reciprocal Rank Fusion）融合多路检索结果。

    公式：score(doc) = Σ 1/(k + rank_i)
    - k 是平滑常数（默认60），防止排名第1的文档分数过高
    - 一个文档如果在多路检索中都排名靠前，最终分数就高

    Args:
        results_list: 多路检索结果，每路是 [(文本, 排名), ...]
        k: 平滑常数
    Returns:
        融合排序后的文本列表
    """
    scores: dict[str, float] = {}  # {文本: 累计RRF分数}

    for results in results_list:
        for doc, rank in results:
            if doc not in scores:
                scores[doc] = 0.0
            scores[doc] += 1.0 / (k + rank)  # RRF 核心公式

    # 按分数降序排列，返回文本列表
    sorted_docs = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
    return sorted_docs


def _get_reranker() -> CrossEncoder:
    """
    懒加载 Cross-Encoder 重排序模型。
    
    为什么用懒加载？
    - 模型约 1.1GB，加载需要几秒
    - 如果放在模块顶部，import 时就会加载，拖慢启动
    - 懒加载 = 第一次真正需要时才加载，之后复用
    """
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(_RERANKER_MODEL)
    return _reranker


def _rerank(query: str, candidates: list[str], top_k: int) -> list[str]:
    """
    使用 Cross-Encoder 对候选文档重新精排。
    
    Cross-Encoder 会把 (query, doc) 作为一个整体输入 Transformer，
    输出一个相关性分数。比 Bi-Encoder 更准确，但更慢。
    
    Args:
        query: 用户查询（简历文本）
        candidates: 粗检索得到的候选 JD 列表
        top_k: 精排后返回的数量
    Returns:
        重排后的 Top-K 文档列表
    """
    if not candidates:
        return []
    
    reranker = _get_reranker()
    
    # Cross-Encoder 需要 [(query, doc), ...] 格式的输入
    pairs = [(query, doc) for doc in candidates]
    
    # predict 返回每对的相关性分数
    scores = reranker.predict(pairs)
    
    # 按分数降序排列，取 top_k
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [candidates[i] for i in ranked_indices[:top_k]]


def search_jds(query: str, top_k: int = 3) -> list[str]:
    """
    完整检索流程：混合检索（粗排） → Cross-Encoder（精排）。
    
    Pipeline:
        15条 JD → 向量+BM25 取 Top 6 → Cross-Encoder 精排 → 最终 Top 3
    
    Args:
        query: 简历文本
        top_k: 最终返回的 JD 数量
    Returns:
        匹配的 JD 文本列表
    """
    # 第一阶段：粗检索（快），多取一些候选
    fetch_k = top_k * 2

    vector_results = _vector_search(query, fetch_k)
    bm25_results = _bm25_search(query, fetch_k)

    # RRF 融合
    fused = _rrf_fusion([vector_results, bm25_results])
    
    # 第二阶段：精排序（准），用 Cross-Encoder 重排 Top candidates
    reranked = _rerank(query, fused[:fetch_k], top_k)
    return reranked
