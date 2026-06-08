import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def analyze_resume(resume_text: str, target_job: str) -> str:
    """
    用LLM对简历进行多维度评分分析
    Args:
        resume_text: 简历文本
        target_job: 目标职位
    returns:
        LLM生成的分析报告（markdown格式）
    """
    # 1. 创建 client
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )
    # 2. 构造 system prompt（告诉 LLM 评分维度和输出格式）
    system_prompt = """
    你是一个专业的简历分析员。请根据以下维度对简历进行评分，并给出改进建议：
    1. 岗位匹配度（40%）
    2. 内容组织（25%）
    3. 内容质量（25%）
    4. 完整性（10%）
    请将评分结果和改进建议以 markdown 格式返回，例如：
    # 简历分析报告
    ## 个人信息
    评分：10/10
    改进建议：无
    ## 教育背景
    评分：10/10
    改进建议：无
    """
    # 3. 调用 client.chat.completions.create(...)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请分析以下简历，并给出评分和改进建议：\n{resume_text}\n目标职位是：{target_job}"},
        ],
    )
    # 4. 返回 response 内容
    return response.choices[0].message.content
