"""app.py - 简历优化器 Web UI"""
import gradio as gr
from pdf_parser import extract_text
from analyzer import analyze_resume


def process(pdf_file, target_job):
    """
    Gradio 回调函数
    Args:
        pdf_file: 上传的 PDF 文件路径
        target_job: 目标岗位
    Returns:
        简历分析报告
    """
    text = extract_text(pdf_file)
    report = analyze_resume(text, target_job)
    return report


gr.Interface(
    fn=process,
    inputs=[
        gr.File(label="上传简历 PDF", file_types=[".pdf"]),
        gr.Textbox(label="目标岗位", placeholder="请输入目标岗位，如 Python 后端开发工程师"),
    ],
    outputs=gr.Markdown(label="简历分析报告"),
    title="ResumeBoost - AI 简历优化器",
    description="上传简历 PDF 并输入目标岗位，基于 RAG 检索真实岗位要求，生成多维度分析报告",
).launch()