"""main.py - 简历优化器 CLI 入口（完整版 Phase 1-6）

完整 Pipeline：
    PDF 解析 → 分析评分 → 智能改写 → PDF 生成 → Before/After 对比
"""
from pdf_parser import extract_text
from analyzer import analyze_resume
from rewriter import rewrite_resume
from pdf_generator import save_pdf
from diff_highlight import save_diff_report


def main():
    pdf_path = "resume.pdf"
    target_job = "Python 后端开发工程师"

    # ─── Step 1：PDF 解析 ───
    print("📄 正在解析简历 PDF...")
    text = extract_text(pdf_path)
    print(f"   └─ 提取到 {len(text)} 个字符")

    # ─── Step 2：分析评分（Phase 1-4）───
    print("\n" + "="*60)
    print("📊 简历分析报告")
    print("="*60)
    report = analyze_resume(text, target_job)
    print(report)

    # ─── Step 3：智能改写（Phase 5）───
    print("\n" + "="*60)
    print("✏️  正在生成优化简历...")
    print("="*60)
    optimized = rewrite_resume(text, target_job)
    print(optimized)

    # ─── Step 4：生成 PDF（Phase 6）───
    print("\n" + "-"*60)
    print("📑 正在生成 PDF...")
    try:
        pdf_path_out = save_pdf(optimized, "optimized_resume.pdf")
        print(f"   └─ ✅ PDF 已保存: {pdf_path_out}")
    except Exception as e:
        print(f"   └─ ⚠️ PDF 生成失败: {e}")
        print("       已保存 Markdown 版本作为替代")

    # ─── Step 5：Before/After 对比（Phase 6）───
    print("\n" + "-"*60)
    print("🔍 正在生成对比报告...")
    diff_path = save_diff_report(text, optimized, "diff_report.html")
    print(f"   └─ ✅ 对比报告已保存: {diff_path}")

    # ─── 保存 Markdown 版本 ───
    md_path = "optimized_resume.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(optimized)

    # ─── 最终输出 ───
    print("\n" + "="*60)
    print("🎉 全部完成！输出文件：")
    print(f"   ├─ 📝 optimized_resume.md  (优化简历 Markdown)")
    print(f"   ├─ 📑 optimized_resume.pdf  (优化简历 PDF)")
    print(f"   └─ 🔍 diff_report.html      (修改前后对比)")
    print("="*60)


if __name__ == "__main__":
    main()
