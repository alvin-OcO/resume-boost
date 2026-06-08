import fitz
def extract_text(pdf_path: str) -> str:
    """
    从 PDF 文件中提取全部文本。
    
    Args:
        pdf_path: PDF 文件路径
    Returns:
        提取出的纯文本字符串
    """
    # 1. fitz.open(pdf_path)
    doc = fitz.open(pdf_path)
    # 2. 遍历所有页面（doc 可以用 for 循环迭代）
    text=""
    for page in doc:
    # 3. 每页 page.get_text() 拼接起来
        text += page.get_text()
    # 4. 返回完整文本
    return text