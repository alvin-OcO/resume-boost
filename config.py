"""config.py - 全局配置中心

统一管理：
- 环境变量加载（.env 只加载一次）
- LLM 客户端单例（避免每次调用重复创建）
- 模型/API 配置常量

知识点：
- 所有模块 import config 后直接使用 config.get_llm_client()
- 用模块级变量 + 函数封装实现"惰性单例"
- 比起在每个文件里写 load_dotenv() + OpenAI(...)，集中管理更好维护
"""
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

# ─── 加载 .env（整个进程只需一次） ───
load_dotenv()

# ─── LLM 配置常量 ───
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# ─── LLM 客户端（惰性单例） ───
_llm_client: Optional[OpenAI] = None


def get_llm_client() -> OpenAI:
    """
    获取 LLM 客户端（单例模式）。

    知识点：
    - global 让函数内可修改模块级变量
    - 第一次调用时创建，后续复用同一个实例
    - OpenAI SDK 的 client 是线程安全的，可以全局共享

    Raises:
        ValueError: 未配置 DEEPSEEK_API_KEY 时抛出，提示用户检查 .env
    """
    global _llm_client
    if _llm_client is None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError(
                "❌ 未找到 DEEPSEEK_API_KEY！\n"
                "   请在项目根目录创建 .env 文件并添加：\n"
                "   DEEPSEEK_API_KEY=你的密钥"
            )
        _llm_client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    return _llm_client
