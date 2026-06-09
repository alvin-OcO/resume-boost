"""rewriter.py - 智能简历改写模块（Phase 5）

职责：结合 JD 匹配 + 范例参考 + LLM 生成，输出优化后的简历。
流程：原始简历 + 匹配 JD + 优秀范例 → LLM → 优化后的简历文本
"""
import json
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from config import get_llm_client, DEEPSEEK_MODEL
from jd_store import search_jds

__all__ = ["rewrite_resume"]

# ─── 范例库（独立的 ChromaDB collection） ───
_example_client = chromadb.Client()
_example_embedding_fn = SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-small-zh-v1.5")

# 标记是否已加载范例
_examples_loaded = False


def _get_example_collection():
    """获取范例库的 ChromaDB collection"""
    return _example_client.get_or_create_collection(
        "resume_examples", embedding_function=_example_embedding_fn
    )


def _load_examples() -> None:
    """
    从 resume_examples.json 加载范例到向量数据库。
    
    使用模块级标志 _examples_loaded 确保只加载一次（幂等性）。
    
    知识点：
    - global 声明让函数内可以修改模块级变量
    - Path(__file__).parent 获取当前文件所在目录（不依赖工作目录）
    """
    global _examples_loaded
    if _examples_loaded:
        return

    examples_path = Path(__file__).parent / "resume_examples.json"
    with open(examples_path, encoding="utf-8") as f:
        examples = json.load(f)

    collection = _get_example_collection()
    collection.upsert(
        documents=[ex["text"] for ex in examples],
        ids=[ex["id"] for ex in examples],
        metadatas=[{"category": ex["category"]} for ex in examples],
    )
    _examples_loaded = True


def _search_examples(query: str, top_k: int = 3) -> list[str]:
    """
    从范例库中检索与简历最相关的优秀范例。
    
    这里只用向量检索（不用 BM25 + RRF），原因：
    - 范例数量少（18条），精确关键词匹配意义不大
    - 向量语义检索足以找到相关范例
    
    Args:
        query: 简历文本（用于语义匹配）
        top_k: 返回的范例数量
    Returns:
        匹配的范例文本列表
    """
    _load_examples()  # 确保范例已加载
    collection = _get_example_collection()
    results = collection.query(query_texts=[query], n_results=top_k)
    return results["documents"][0]


# ─── LLM 改写 Prompt ───
REWRITE_SYSTEM_PROMPT = """\
你是一位资深的简历优化专家，擅长将普通简历改造为高竞争力的求职简历。

## 你的任务
根据【原始简历】、【目标岗位要求】和【优秀简历范例】，重写一份优化后的简历。

## 改写原则
1. **保真性**：不编造经历，只对已有内容进行重新组织和措辞优化
2. **岗位导向**：突出与目标岗位要求匹配的技能和经历
3. **STAR-T 法则**：项目经历遵循 背景→任务→行动→结果→技术亮点 结构
4. **量化成果**：尽可能用数据说话（百分比、人数、时间等）
5. **关键词嵌入**：自然地融入岗位JD中出现的技术关键词
6. **应届生适配**：如果是应届生，不要伪造工作年限，而是强调项目深度和学习能力

## 输出格式
直接输出优化后的简历全文（纯文本，使用 markdown 格式组织），包含：
- 个人信息（精简）
- 专业技能（按目标岗位重组）
- 项目经历（STAR-T 重写）
- 教育背景
- 自我评价（具体化，非套话）

不要输出分析过程，直接输出优化后的简历。
"""


def rewrite_resume(resume_text: str, target_job: str) -> str:
    """
    智能改写简历：结合 JD 匹配 + 范例参考 + LLM 生成。
    
    完整 Pipeline：
        1. search_jds() → 找到最匹配的目标岗位 JD
        2. _search_examples() → 找到相关的优秀简历范例
        3. LLM → 根据三者生成优化后的简历
    
    Args:
        resume_text: 原始简历文本（从 PDF 提取的）
        target_job: 目标职位名称
    Returns:
        优化后的简历文本（markdown 格式）
    """
    # 1. 检索匹配的 JD（系统已有的混合检索 + 重排序）
    matched_jds = search_jds(resume_text, top_k=3)

    # 2. 检索相关的优秀范例
    matched_examples = _search_examples(resume_text, top_k=3)

    # 3. 构建 LLM 输入
    user_prompt = f"""## 原始简历
{resume_text}

## 目标职位
{target_job}

## 该职位的真实招聘要求（供参考）
{chr(10).join(f"【JD {i+1}】{jd}" for i, jd in enumerate(matched_jds))}

## 优秀简历范例（供参考写法和格式）
{chr(10).join(f"【范例 {i+1}】{ex}" for i, ex in enumerate(matched_examples))}

请根据以上信息，重写优化后的简历。"""

    # 4. 调用 LLM
    client = get_llm_client()

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,  # 稍高温度，让改写更有创意
            max_tokens=4000,  # 简历不会太长，4000 token 足够
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"LLM 改写调用失败: {e}") from e
