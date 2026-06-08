import gradio as gr
from pdf_parser import extract_text
from analyzer import analyze_resume

def process(pdf_file,target_job):
    """
    Gradio 回调函数
    Args:
        pdf_file: PDF文件
        target_job: 目标岗位
    Returns:
        简历分析报告
    """
    # 1. extract_text(pdf_file) 提取文本
    text = extract_text(pdf_file)
    # 2. analyze_resume(text, target_job) 获取报告
    report = analyze_resume(text, target_job)
    # 3. return 报告
    return report
    
gr.Interface(
    fn = process,
    inputs = [
        gr.File(label = "上传简历 PDF ",file_types = [".pdf"]),
        gr.Textbox(label = "目标岗位",placeholder = "请输入目标岗位,如软件工程师")
    ],
    outputs = gr.Markdown(label = "简历分析报告"),
    title = "简历优化器",
    description = "上传简历 PDF 文件并输入目标岗位，获取简历分析报告"
).launch()