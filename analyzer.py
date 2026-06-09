"""analyzer.py - LLM 简历分析模块

职责：调用 LLM 对简历进行多维度评分分析。
对照真实 JD 要求评估，输出结构化分析报告。
"""
import json
from pathlib import Path

from config import get_llm_client, DEEPSEEK_MODEL
from jd_store import search_jds, load_jds

__all__ = ["analyze_resume"]

# ─── 初始化 JD 知识库 ───
_jds_path = Path(__file__).parent / "jds.json"
with open(_jds_path, encoding="utf-8") as f:
    _jd_data = json.load(f)
load_jds(_jd_data)

SYSTEM_PROMPT = """\
你是一个专业的简历分析员。请根据以下维度对简历进行评分，并给出改进建议：
1. 岗位匹配度（40%）
2. 内容组织（25%）
3. 内容质量（25%）
4. 完整性（10%）
请将评分结果和改进建议以 markdown 格式返回。
"""


def analyze_resume(resume_text: str, target_job: str) -> str:
    """
    用 LLM 对简历进行多维度评分分析。

    Args:
        resume_text: 简历文本
        target_job: 目标职位
    Returns:
        LLM 生成的分析报告（markdown 格式）
    Raises:
        RuntimeError: LLM 调用失败时抛出
    """
    client = get_llm_client()
    matched_jds = search_jds(resume_text)

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"请分析以下简历：\n{resume_text}\n\n"
                    f"目标职位：{target_job}\n\n"
                    f"以下是该职位的真实招聘要求：\n{matched_jds}\n\n"
                    "请对照上述岗位要求，从岗位匹配度、内容组织、"
                    "内容质量、完整性四个维度评估简历，并给出具体改进建议。"
                )},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"LLM 分析调用失败: {e}") from e
