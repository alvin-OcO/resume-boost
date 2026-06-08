# main.py - 简历优化器主入口

from pdf_parser import extract_text
from analyzer import analyze_resume


def main():
    # 1. 定义 PDF 路径和目标岗位
    pdf_path = "resume.pdf"
    target_job = "软件工程师"
    # 2. 调用 extract_text() 提取文本
    text = extract_text(pdf_path)
    # 3. 调用 analyze_resume() 获取报告
    report = analyze_resume(text, target_job)
    # 4. print 报告
    print(report)

if __name__ == "__main__":
    main()
