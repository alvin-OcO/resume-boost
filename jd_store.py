import chromadb

# 全局 client
client = chromadb.Client()

def _get_collection():
    """获取或创建 collection"""
    return client.get_or_create_collection("job_descriptions")

def load_jds(jd_list: list[dict]) -> None:
    """
    把JD列表存入向量数据库
    Args:
        jd_list:[{"id":"jd_1", "text":"..."}]
    """
    collection = _get_collection()
    collection.upsert(documents=[jd["text"] for jd in jd_list], ids=[jd["id"] for jd in jd_list])

def search_jds(query: str, top_k: int = 3) -> list[str]:
    """
    检索与query最匹配的top_k个JD
    Args:
        query: 简历文本
        top_k: 返回的JD数量
    Returns:
        匹配的JD文本列表
    """
    collection = _get_collection()
    results = collection.query(query_texts=[query], n_results=top_k)
    return results["documents"][0]
