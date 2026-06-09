"""main.py - 简历优化器 CLI 入口（完整版 Phase 1-6）

完整 Pipeline：
    PDF 解析 → 分析评分 → 智能改写 → PDF 生成 → Before/After 对比

用法：
    uv run python main.py                    # 默认 resume.pdf + Python后端
    uv run python main.py my.pdf 算法工程师   # 指定文件和岗位
"""
import sys
from pathlib import Path

from pdf_parser import extract_text
from analyzer import analyze_resume
from rewriter import rewrite_resume
from pdf_generator import save_pdf
from diff_highlight import save_diff_report


def main():
    """
    CLI 入口，支持两种调用方式：
    - 无参数：使用默认值（resume.pdf + Python 后端开发工程师）
    - 有参数：main.py <pdf路径> [目标岗位]

    知识点：
    - sys.argv[0] 是脚本名，sys.argv[1:] 是用户传的参数
    - Path.exists() 检查文件是否存在，防止运行时才报 FileNotFoundError
    """
    # ─── 解析 CLI 参数 ───
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "resume.pdf"
    target_job = sys.argv[2] if len(sys.argv) > 2 else "Python 后端开发工程师"

    # ─── 输入校验 ───
    if not Path(pdf_path).exists():
        print(f"❌ 文件不存在: {pdf_path}")
        print("   用法: uv run python main.py <简历PDF路径> [目标岗位]")
        sys.exit(1)

    print(f"🎯 目标岗位: {target_job}")
    print(f"📄 简历文件: {pdf_path}")

    # ─── Step 1：PDF 解析 ───
    print("\n📄 正在解析简历 PDF...")
    text = extract_text(pdf_path)
    if not text.strip():
        print("❌ PDF 文本为空，请检查文件是否为扫描件（需要 OCR）")
        sys.exit(1)
    print(f"   └─ 提取到 {len(text)} 个字符")

    # ─── Step 2：分析评分（Phase 1-4）───
    print("\n" + "=" * 60)
    print("📊 简历分析报告")
    print("=" * 60)
    try:
        report = analyze_resume(text, target_job)
        print(report)
    except RuntimeError as e:
        print(f"⚠️  分析失败: {e}")
        print("    继续执行改写步骤...")
        report = None

    # ─── Step 3：智能改写（Phase 5）───
    print("\n" + "=" * 60)
    print("✏️  正在生成优化简历...")
    print("=" * 60)
    try:
        optimized = rewrite_resume(text, target_job)
        print(optimized)
    except RuntimeError as e:
        print(f"❌ 改写失败: {e}")
        sys.exit(1)

    # ─── Step 4：保存 Markdown ───
    md_path = "optimized_resume.md"
    Path(md_path).write_text(optimized, encoding="utf-8")

    # ─── Step 5：生成 PDF（Phase 6）───
    print("\n" + "-" * 60)
    print("📑 正在生成 PDF...")
    try:
        pdf_path_out = save_pdf(optimized, "optimized_resume.pdf")
        print(f"   └─ ✅ PDF 已保存: {pdf_path_out}")
    except Exception as e:
        print(f"   └─ ⚠️ PDF 生成失败: {e}")
        print("       已保存 Markdown 版本作为替代")

    # ─── Step 6：Before/After 对比（Phase 6）───
    print("\n" + "-" * 60)
    print("🔍 正在生成对比报告...")
    diff_path = save_diff_report(text, optimized, "diff_report.html")
    print(f"   └─ ✅ 对比报告已保存: {diff_path}")

    # ─── 最终输出 ───
    print("\n" + "=" * 60)
    print("🎉 全部完成！输出文件：")
    print(f"   ├─ 📝 {md_path}  (优化简历 Markdown)")
    print(f"   ├─ 📑 optimized_resume.pdf  (优化简历 PDF)")
    print(f"   └─ 🔍 {diff_path}      (修改前后对比)")
    print("=" * 60)


if __name__ == "__main__":
    main()
