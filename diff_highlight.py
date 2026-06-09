"""diff_highlight.py - 简历修改前后对比高亮模块（Phase 6 升级版）

设计思路：
- 旧版：用 difflib.HtmlDiff 做逐行 diff，效果像代码对比工具（不适合简历）
- 新版：按"段落/章节"维度对比，生成卡片式可视化报告

核心改进：
1. 去掉 Markdown 标记后再对比（消除语法噪音）
2. 按段落分块，找出真正有变化的内容
3. 用现代卡片式 HTML 展示，而非朴素的 diff 表格
4. 顶部添加统计摘要（新增/修改/删除了多少内容）
"""
import re
import difflib


def _strip_markdown(text: str) -> str:
    """
    去除 Markdown 格式标记，保留纯文本内容。
    
    知识点：
    - re.sub(pattern, replacement, text) 用正则替换
    - 我们分步去掉：标题标记、粗体、斜体、代码、列表符号、分隔线
    - 这样对比的是"内容变化"而非"格式变化"
    
    Args:
        text: 含 Markdown 标记的文本
    Returns:
        纯文本
    """
    text = re.sub(r"^#{1,3}\s+", "", text, flags=re.MULTILINE)  # # 标题
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)                # **粗体**
    text = re.sub(r"\*(.+?)\*", r"\1", text)                    # *斜体*
    text = re.sub(r"`(.+?)`", r"\1", text)                      # `代码`
    text = re.sub(r"^[-*]\s+", "• ", text, flags=re.MULTILINE)  # - 列表 → •
    text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)      # --- 分隔线
    return text


# ─── 简历章节标题关键词 ───
# 用于识别简历中的"章节分割点"
_SECTION_HEADERS = [
    "教育背景", "项目经历", "比赛经历", "技能证书", "自我评价",
    "专业技能", "工作经历", "个人信息", "基本信息", "求职意向",
    "主修课程", "技术栈",
]


def _is_section_header(line: str) -> bool:
    """
    判断一行是否是简历的章节标题。
    
    知识点：
    - any() + 生成器表达式：短路求值，找到第一个 True 就停止
    - strip() 去除前后空白/特殊字符
    """
    clean = line.strip().strip("#").strip()
    # 短标题（<10字）且包含关键词
    if len(clean) > 15:
        return False
    return any(h in clean for h in _SECTION_HEADERS)


def _split_by_sections(text: str) -> list[tuple[str, str]]:
    """
    用章节标题关键词作为分割点，将简历拆分为逻辑块。
    
    这是解决 PDF 提取文本"全部糊在一起"问题的核心策略：
    - PDF 文本只有单换行 \n，没有双换行 \n\n
    - 但简历有明确的章节结构（教育背景、项目经历、比赛经历...）
    - 我们用这些章节关键词作为"刀"，把文本切成几块
    
    类比：像切蛋糕一样，不是按固定距离切，而是按"层次分界线"切。
    
    流程：
    1. 按单换行拆分为行列表
    2. 遍历每行，遇到章节标题就“切一刀”
    3. 两刀之间的内容合并为一个段落
    """
    lines = text.split("\n")
    sections = []
    current_title = "个人信息"
    current_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        if _is_section_header(stripped):
            # 遇到新章节，保存上一块
            if current_lines:
                content = "\n".join(current_lines)
                sections.append((current_title, content))
            current_title = stripped.strip("#").strip()
            current_lines = []
        else:
            current_lines.append(stripped)

    # 最后一个章节
    if current_lines:
        content = "\n".join(current_lines)
        sections.append((current_title, content))

    return sections


def _split_sections_smart(text: str) -> list[tuple[str, str]]:
    """
    智能分段：先尝试用章节标题分割，如果失败则 fallback 到双换行分割。
    
    知识点：
    - 这是"策略模式"的体现：根据输入特征选择不同的处理策略
    - 对于 PDF 提取的文本：用章节标题分割（因为没有双换行）
    - 对于 Markdown 文本：用双换行分割（因为结构清晰）
    """
    # 尝试章节标题分割
    sections = _split_by_sections(text)
    if len(sections) >= 3:
        return sections
    
    # Fallback: 双换行分割
    paragraphs = re.split(r"\n{2,}", text.strip())
    result = []
    for p in paragraphs:
        p = p.strip()
        if p:
            first_line = p.split("\n")[0][:50]
            result.append((first_line, p))
    return result


def _compute_similarity(a: str, b: str) -> float:
    """
    计算两个文本的综合相似度（0.0 ~ 1.0）。
    
    使用双重策略：
    1. SequenceMatcher（字符级别 LCS 相似度）
    2. 关键词重叠度（Jaccard 系数）
    
    为什么需要双重策略？
    - 原始简历："负责系统架构设计及核心模块开发，集成RAG技术"（短）
    - 优化简历："负责系统整体架构设计与核心模块开发，采用Flask搭建后端服务...集成RAG..."（长）
    - SequenceMatcher 对长度差异敏感，短文本被长文本"稀释"导致 ratio 很低
    - 关键词重叠度则不受长度影响，只看"是否包含相同关键词"
    
    最终取两者的加权平均：60% 关键词 + 40% 序列匹配
    """
    # 策略 1：序列相似度
    seq_sim = difflib.SequenceMatcher(None, a, b).ratio()
    
    # 策略 2：关键词重叠度（Jaccard 系数）
    # 提取长度 >= 2 的词（过滤单字符噪音）
    words_a = set(w for w in re.findall(r'[\w]+', a) if len(w) >= 2)
    words_b = set(w for w in re.findall(r'[\w]+', b) if len(w) >= 2)
    
    if not words_a or not words_b:
        return seq_sim
    
    # Jaccard = 交集 / 并集
    intersection = words_a & words_b
    union = words_a | words_b
    jaccard = len(intersection) / len(union) if union else 0.0
    
    # 加权融合
    return 0.4 * seq_sim + 0.6 * jaccard


def _inline_diff(old: str, new: str) -> str:
    """
    生成行内差异高亮 HTML。
    
    对比两段文本，标记出具体哪些词/字变了：
    - 绿色背景：新增的内容
    - 红色删除线：被删除的内容
    
    知识点：
    - SequenceMatcher.get_opcodes() 返回操作码列表
    - 每个操作码是 (tag, i1, i2, j1, j2)
    - tag: 'equal'(不变) / 'replace'(替换) / 'insert'(插入) / 'delete'(删除)
    """
    sm = difflib.SequenceMatcher(None, old, new)
    output = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            output.append(_escape_html(old[i1:i2]))
        elif tag == "replace":
            output.append(f'<del class="removed">{_escape_html(old[i1:i2])}</del>')
            output.append(f'<ins class="added">{_escape_html(new[j1:j2])}</ins>')
        elif tag == "insert":
            output.append(f'<ins class="added">{_escape_html(new[j1:j2])}</ins>')
        elif tag == "delete":
            output.append(f'<del class="removed">{_escape_html(old[i1:i2])}</del>')
    return "".join(output)


def _escape_html(text: str) -> str:
    """转义 HTML 特殊字符，防止 XSS 和渲染错误。"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )


def generate_diff_html(original: str, optimized: str) -> str:
    """
    生成现代化的简历对比报告 HTML。
    
    流程：
    1. 去掉 Markdown 标记（对比"内容"而非"格式"）
    2. 按段落分块
    3. 用相似度匹配找出对应段落
    4. 分类为：保留/修改/新增/删除
    5. 生成卡片式 HTML 报告
    
    Args:
        original: 原始简历文本（PDF 提取的）
        optimized: 优化后简历文本（Markdown 格式）
    Returns:
        完整 HTML 字符串
    """
    # 1. 预处理：去掉 Markdown 标记
    clean_optimized = _strip_markdown(optimized)

    # 2. 智能分段
    # 原始文本（PDF）：用章节标题分割
    # 优化文本（Markdown）：用双换行分割
    orig_sections = _split_sections_smart(original)
    opt_sections = _split_sections_smart(clean_optimized)

    # 3. 段落匹配：为优化版的每个段落找到原版中最相似的段落
    changes = []  # [(type, orig_text, opt_text), ...]
    matched_orig = set()

    for opt_title, opt_text in opt_sections:
        best_match = -1
        best_sim = 0.0
        for i, (_, orig_text) in enumerate(orig_sections):
            if i in matched_orig:
                continue
            sim = _compute_similarity(orig_text, opt_text)
            if sim > best_sim:
                best_sim = sim
                best_match = i

        # 阈值：0.25 即可认为是"同一段内容的改写"
        # 因为 STAR-T 改写后长度会扩展 3-5 倍，相似度天然偏低
        if best_sim > 0.25:
            matched_orig.add(best_match)
            if best_sim > 0.85:
                changes.append(("unchanged", orig_sections[best_match][1], opt_text))
            else:
                changes.append(("modified", orig_sections[best_match][1], opt_text))
        else:
            # 全新段落
            changes.append(("added", "", opt_text))

    # 原版中没被匹配到的段落 = 被删除
    for i, (_, orig_text) in enumerate(orig_sections):
        if i not in matched_orig:
            changes.append(("deleted", orig_text, ""))

    # 4. 统计
    n_unchanged = sum(1 for t, _, _ in changes if t == "unchanged")
    n_modified = sum(1 for t, _, _ in changes if t == "modified")
    n_added = sum(1 for t, _, _ in changes if t == "added")
    n_deleted = sum(1 for t, _, _ in changes if t == "deleted")

    # 5. 生成 HTML
    cards_html = ""
    for change_type, orig_text, opt_text in changes:
        if change_type == "unchanged":
            cards_html += f'''
            <div class="card unchanged">
                <div class="card-badge badge-keep">保留</div>
                <div class="card-content">{_escape_html(opt_text)}</div>
            </div>'''
        elif change_type == "modified":
            diff_html = _inline_diff(orig_text, opt_text)
            cards_html += f'''
            <div class="card modified">
                <div class="card-badge badge-modify">优化</div>
                <div class="card-label">修改前：</div>
                <div class="card-old">{_escape_html(orig_text)}</div>
                <div class="card-label">修改后：</div>
                <div class="card-new">{diff_html}</div>
            </div>'''
        elif change_type == "added":
            cards_html += f'''
            <div class="card added">
                <div class="card-badge badge-add">新增</div>
                <div class="card-content">{_escape_html(opt_text)}</div>
            </div>'''
        elif change_type == "deleted":
            cards_html += f'''
            <div class="card deleted">
                <div class="card-badge badge-del">删除</div>
                <div class="card-content">{_escape_html(orig_text)}</div>
            </div>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <title>简历优化对比报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            background: #f5f7fa;
            padding: 30px;
            color: #333;
            line-height: 1.7;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            font-size: 24px;
            margin-bottom: 8px;
            color: #1a1a2e;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-bottom: 24px;
        }}
        /* 统计摘要 */
        .summary {{
            display: flex;
            gap: 12px;
            justify-content: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        .stat {{
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
        }}
        .stat-keep {{ background: #e8f4fd; color: #1971c2; }}
        .stat-modify {{ background: #fff3cd; color: #856404; }}
        .stat-add {{ background: #d4edda; color: #155724; }}
        .stat-del {{ background: #f8d7da; color: #721c24; }}
        /* 卡片 */
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border-left: 4px solid #ccc;
            position: relative;
        }}
        .card.unchanged {{ border-left-color: #74b9ff; opacity: 0.7; }}
        .card.modified {{ border-left-color: #fdcb6e; }}
        .card.added {{ border-left-color: #00b894; }}
        .card.deleted {{ border-left-color: #e17055; }}
        .card-badge {{
            position: absolute;
            top: 12px;
            right: 12px;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-keep {{ background: #e8f4fd; color: #1971c2; }}
        .badge-modify {{ background: #fff3cd; color: #856404; }}
        .badge-add {{ background: #d4edda; color: #155724; }}
        .badge-del {{ background: #f8d7da; color: #721c24; }}
        .card-label {{
            font-size: 12px;
            color: #888;
            margin: 8px 0 4px;
            font-weight: 600;
        }}
        .card-old {{
            background: #fff5f5;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 13px;
            color: #666;
            text-decoration: line-through;
            text-decoration-color: #e17055;
        }}
        .card-new {{
            background: #f0fff4;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 13px;
        }}
        .card-content {{
            font-size: 13px;
            white-space: pre-wrap;
        }}
        ins.added {{
            background: #c8f7c5;
            text-decoration: none;
            padding: 1px 2px;
            border-radius: 2px;
        }}
        del.removed {{
            background: #ffc9c9;
            text-decoration: line-through;
            padding: 1px 2px;
            border-radius: 2px;
            color: #999;
        }}
        .legend {{
            text-align: center;
            margin-top: 24px;
            font-size: 12px;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 简历优化对比报告</h1>
        <p class="subtitle">以下展示了优化前后的内容变化，按段落对比</p>
        <div class="summary">
            <span class="stat stat-keep">📌 保留 {n_unchanged} 段</span>
            <span class="stat stat-modify">✏️ 优化 {n_modified} 段</span>
            <span class="stat stat-add">✅ 新增 {n_added} 段</span>
            <span class="stat stat-del">🗑️ 删除 {n_deleted} 段</span>
        </div>
        {cards_html}
        <div class="legend">
            <span style="color:#00b894">■</span> 绿色背景 = 新增内容 &nbsp;
            <span style="color:#e17055">■</span> 红色删除线 = 被删内容 &nbsp;
            <span style="color:#fdcb6e">■</span> 黄色卡片 = 优化改写
        </div>
    </div>
</body>
</html>'''

    return html


def save_diff_report(original: str, optimized: str, output_path: str = "diff_report.html") -> str:
    """
    生成并保存对比报告为 HTML 文件。

    Args:
        original: 原始简历文本
        optimized: 优化后简历文本
        output_path: 输出文件路径
    Returns:
        保存的文件路径
    """
    html = generate_diff_html(original, optimized)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
