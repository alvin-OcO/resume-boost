"""main.py - 简历优化器 CLI 入口"""
from pdf_parser import extract_text
from analyzer import analyze_resume


def main():
    pdf_path = "resume.pdf"
    target_job = "Python 后端开发工程师"

    text = extract_text(pdf_path)
    report = analyze_resume(text, target_job)
    print(report)


if __name__ == "__main__":
    main()
