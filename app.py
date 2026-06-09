"""app.py - 简历优化器 Web UI（Gradio）

完整 Pipeline 的可视化版本：
- 上传 PDF + 输入目标岗位
- 输出：分析报告 + 优化简历 + PDF 文件 + 对比报告

知识点：
- Gradio 的 File 组件上传后返回临时文件路径
- 多输出用列表返回，对应 outputs 列表中的各组件
- gr.DownloadButton 不适用于动态文件，用 gr.File 作为输出替代
"""
import tempfile
from pathlib import Path

import gradio as gr

from pdf_parser import extract_text
from analyzer import analyze_resume
from rewriter import rewrite_resume
from pdf_generator import save_pdf
from diff_highlight import save_diff_report


def process(pdf_file, target_job: str):
    """
    完整 Pipeline 回调函数。

    Args:
        pdf_file: Gradio 上传的 PDF 文件路径
        target_job: 目标岗位名称
    Returns:
        (分析报告, 优化简历MD, PDF路径, 对比报告路径)
    """
    if not pdf_file:
        return "❌ 请上传简历 PDF", "", None, None

    if not target_job or not target_job.strip():
        return "❌ 请输入目标岗位", "", None, None

    # ─── Step 1: PDF 解析 ───
    text = extract_text(pdf_file)
    if not text.strip():
        return "❌ PDF 文本为空，可能是扫描件", "", None, None

    # ─── Step 2: 分析评分 ───
    try:
        report = analyze_resume(text, target_job)
    except RuntimeError as e:
        report = f"⚠️ 分析失败: {e}"

    # ─── Step 3: 智能改写 ───
    try:
        optimized = rewrite_resume(text, target_job)
    except RuntimeError as e:
        return report, f"❌ 改写失败: {e}", None, None

    # ─── Step 4: 生成 PDF ───
    output_dir = Path(tempfile.mkdtemp())
    pdf_out_path = str(output_dir / "optimized_resume.pdf")
    try:
        save_pdf(optimized, pdf_out_path)
    except Exception:
        pdf_out_path = None

    # ─── Step 5: 生成对比报告 ───
    diff_path = str(output_dir / "diff_report.html")
    save_diff_report(text, optimized, diff_path)

    return report, optimized, pdf_out_path, diff_path


# ─── Gradio UI 构建 ───
demo = gr.Interface(
    fn=process,
    inputs=[
        gr.File(label="上传简历 PDF", file_types=[".pdf"]),
        gr.Textbox(
            label="目标岗位",
            placeholder="如：Python 后端开发工程师",
            value="Python 后端开发工程师",
        ),
    ],
    outputs=[
        gr.Markdown(label="📊 分析报告"),
        gr.Markdown(label="✏️ 优化后简历"),
        gr.File(label="📑 优化 PDF 下载"),
        gr.File(label="🔍 对比报告下载"),
    ],
    title="ResumeBoost - AI 简历优化系统",
    description="上传简历 PDF + 输入目标岗位 → 多维评分 + 智能改写 + PDF生成 + 修改对比",
    flagging_mode="never",
)

if __name__ == "__main__":
    demo.launch()
