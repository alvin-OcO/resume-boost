"""pdf_parser.py - PDF 文本提取模块"""
import pymupdf as fitz  # PyMuPDF >= 1.24 需要用 pymupdf 导入


def extract_text(pdf_path: str) -> str:
    """
    从 PDF 文件中提取全部文本。
    Args:
        pdf_path: PDF 文件路径
    Returns:
        提取出的纯文本字符串
    """
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text