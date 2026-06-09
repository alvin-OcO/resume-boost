"""pdf_generator.py - 简历 PDF 生成模块（Phase 6）

将 Markdown 格式的优化简历转为精美 PDF 文件。

技术路线：Markdown → 逐行解析 → fpdf2 渲染 → PDF
- fpdf2：纯 Python PDF 生成库，零系统依赖
- 使用 Windows 自带的微软雅黑字体（msyh.ttc）支持中文

为什么最终选了 fpdf2？
- weasyprint 依赖 GTK/Pango 系统库，Windows 安装困难（已踩坑）
- xhtml2pdf 中文支持差
- fpdf2 纯 Python + 支持 TrueType 字体 = 最适合 Windows 环境

知识点：
- fpdf2 的核心思路是"手动排版"——你告诉它每行写什么字、多大、什么颜色
- 相比 weasyprint 的"自动排版"（HTML+CSS），fpdf2 需要我们自己解析 Markdown
- 但好处是：零依赖、跨平台、可控性强
"""
import re
from pathlib import Path

from fpdf import FPDF

__all__ = ["save_pdf"]


# ─── 字体路径（Windows 系统字体） ───
# Windows 自带微软雅黑，路径固定在 C:\Windows\Fonts\
_FONT_DIR = Path("C:/Windows/Fonts")
_FONT_REGULAR = _FONT_DIR / "msyh.ttc"  # 微软雅黑 常规
_FONT_BOLD = _FONT_DIR / "msyhbd.ttc"   # 微软雅黑 粗体


class ResumePDF(FPDF):
    """
    自定义 PDF 类，继承 fpdf2 的 FPDF。
    
    知识点：
    - FPDF 是 fpdf2 的核心类，代表一个 PDF 文档
    - 通过继承它可以自定义页眉、页脚等行为
    - header()/footer() 是钩子方法，每页自动调用
    """

    def header(self):
        """页眉（这里留空，简历不需要页眉）"""
        pass

    def footer(self):
        """
        页脚：显示页码。
        
        知识点：
        - self.page_no() 返回当前页码
        - self.set_y(-15) 将光标移到底部 15mm 处
        - {nb} 是 fpdf2 的特殊占位符，会被替换为总页数
        """
        self.set_y(-15)
        self.set_font("msyh", size=8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"- {self.page_no()} -", align="C")


def _parse_markdown_line(line: str) -> dict:
    """
    解析单行 Markdown，返回结构化信息。
    
    这是一个简易 Markdown 解析器，只处理简历中常见的语法：
    - # 一级标题
    - ## 二级标题
    - ### 三级标题
    - - 无序列表
    - --- 分隔线
    - 普通段落
    
    知识点：
    - 用正则表达式匹配 Markdown 语法
    - 返回字典方便后续统一处理
    
    Args:
        line: 单行 Markdown 文本
    Returns:
        {"type": "h1"|"h2"|"h3"|"bullet"|"hr"|"text", "content": "..."}
    """
    stripped = line.strip()

    if not stripped:
        return {"type": "blank", "content": ""}
    if re.match(r"^---+$", stripped):
        return {"type": "hr", "content": ""}
    if stripped.startswith("### "):
        return {"type": "h3", "content": stripped[4:]}
    if stripped.startswith("## "):
        return {"type": "h2", "content": stripped[3:]}
    if stripped.startswith("# "):
        return {"type": "h1", "content": stripped[2:]}
    if stripped.startswith("- ") or stripped.startswith("* "):
        return {"type": "bullet", "content": stripped[2:]}
    return {"type": "text", "content": stripped}


def _clean_inline_markdown(text: str) -> str:
    """
    清除行内 Markdown 标记（**粗体**、*斜体*、`代码`）。
    
    fpdf2 不支持混合样式的 cell，所以我们把标记去掉，保留纯文本。
    后续可以用 write_html() 支持混合样式，但对简历来说纯文本足够清晰。
    
    Args:
        text: 含 Markdown 标记的文本
    Returns:
        纯文本
    """
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **bold** → bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)       # *italic* → italic
    text = re.sub(r"`(.+?)`", r"\1", text)         # `code` → code
    return text


def save_pdf(md_text: str, output_path: str = "optimized_resume.pdf") -> str:
    """
    将 Markdown 简历生成 PDF 文件。
    
    Pipeline:
        Markdown文本 → 逐行解析 → fpdf2绘制 → 输出PDF
    
    知识点：
    - FPDF.add_page()：添加新页
    - FPDF.add_font()：注册自定义字体（支持中文的关键！）
    - FPDF.cell()：输出一行文本
    - FPDF.multi_cell()：输出可自动换行的多行文本
    - FPDF.output()：保存 PDF 到文件
    
    Args:
        md_text: Markdown 格式的简历文本
        output_path: PDF 输出路径
    Returns:
        保存的文件路径
    """
    pdf = ResumePDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ─── 注册中文字体 ───
    # fpdf2 默认只有 Helvetica 等西文字体，中文会变成方块
    # 必须注册 TrueType 字体才能显示中文
    # uni=True 表示启用 Unicode 支持
    pdf.add_font("msyh", style="", fname=str(_FONT_REGULAR), uni=True)
    pdf.add_font("msyh", style="B", fname=str(_FONT_BOLD), uni=True)

    pdf.add_page()
    pdf.set_font("msyh", size=11)

    # ─── 逐行解析并渲染 ───
    for line in md_text.split("\n"):
        parsed = _parse_markdown_line(line)
        content = _clean_inline_markdown(parsed["content"])

        if parsed["type"] == "blank":
            pdf.ln(4)  # 空行：留 4mm 间距

        elif parsed["type"] == "hr":
            # 分隔线：画一条灰色横线
            y = pdf.get_y()
            pdf.set_draw_color(180, 180, 180)
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.ln(6)

        elif parsed["type"] == "h1":
            # 一级标题：居中、大字、底部横线
            pdf.set_font("msyh", style="B", size=16)
            pdf.cell(0, 12, content, align="C", new_x="LMARGIN", new_y="NEXT")
            # 标题下方加横线
            y = pdf.get_y()
            pdf.set_draw_color(50, 50, 50)
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.ln(6)
            pdf.set_font("msyh", size=11)

        elif parsed["type"] == "h2":
            # 二级标题：左侧蓝色竖条 + 粗体
            pdf.ln(4)
            y = pdf.get_y()
            pdf.set_fill_color(52, 152, 219)  # 蓝色
            pdf.rect(pdf.l_margin, y, 2, 7, style="F")  # 竖条
            pdf.set_x(pdf.l_margin + 5)
            pdf.set_font("msyh", style="B", size=13)
            pdf.cell(0, 7, content, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
            pdf.set_font("msyh", size=11)

        elif parsed["type"] == "h3":
            # 三级标题：粗体稍大
            pdf.ln(2)
            pdf.set_font("msyh", style="B", size=11)
            pdf.cell(0, 7, content, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("msyh", size=11)

        elif parsed["type"] == "bullet":
            # 列表项：缩进 + 圆点
            pdf.set_x(pdf.l_margin + 5)
            pdf.cell(4, 6, "•")
            pdf.multi_cell(0, 6, content)

        else:
            # 普通文本
            if content:
                pdf.multi_cell(0, 6, content)

    # ─── 输出 PDF ───
    pdf.output(output_path)
    return output_path
