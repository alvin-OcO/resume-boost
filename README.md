# 📄 ResumeBoost — AI 简历优化系统

> 基于 RAG（检索增强生成）的端到端简历优化 Pipeline：分析评分 → 智能改写 → PDF 生成 → 修改对比。

## ✨ 核心功能

| 功能模块 | 说明 |
|---|---|
| **多维度评分** | 对照真实 JD，从岗位匹配度/内容组织/内容质量/完整性四维度打分 |
| **混合检索** | 向量语义检索 + BM25 关键词检索 + RRF 融合，精准匹配 JD |
| **Cross-Encoder 重排序** | 粗排后用 Cross-Encoder 精排，提升匹配准确性 |
| **范例库参考** | 18 条优秀简历范例辅助 LLM 改写，输出 STAR-T 结构 |
| **智能改写** | LLM 结合 JD + 范例，生成岗位导向的优化简历 |
| **PDF 生成** | Markdown → PDF，使用系统中文字体，排版精美 |
| **Before/After 对比** | 语义级段落对比，卡片式 HTML 报告，高亮差异 |

## 🏗️ 系统架构

```
用户上传 PDF + 输入目标岗位
        │
        ▼
┌──────────────┐
│  PDF Parser  │ ← PyMuPDF 文本提取
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│               RAG 检索 Pipeline                       │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ Vector      │  │ BM25        │  │ RRF Fusion  │  │
│  │ (ChromaDB)  │  │ (jieba)     │  │ (k=60)      │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         └────────────────┼────────────────┘          │
│                          ▼                           │
│              ┌─────────────────────┐                 │
│              │ Cross-Encoder Rerank│                  │
│              │ (bge-reranker-v2-m3)│                  │
│              └──────────┬──────────┘                 │
└─────────────────────────┼────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
     ┌──────────┐  ┌──────────┐  ┌──────────┐
     │ Analyzer │  │ Rewriter │  │ Examples │
     │(评分分析)│  │(智能改写)│  │ (范例库) │
     └────┬─────┘  └────┬─────┘  └──────────┘
          │              │
          ▼              ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ 分析报告    │  │ PDF 生成   │  │ Diff 对比  │
   │ (Markdown) │  │ (fpdf2)    │  │ (HTML)     │
   └────────────┘  └────────────┘  └────────────┘
```

## 🚀 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 配置 API Key
echo "DEEPSEEK_API_KEY=你的key" > .env

# 3. 放入简历 PDF
cp your_resume.pdf resume.pdf

# 4. 运行（完整 Pipeline）
uv run python main.py
```

### 输出文件

| 文件 | 用途 |
|---|---|
| `optimized_resume.md` | 优化后简历（Markdown，可编辑） |
| `optimized_resume.pdf` | 优化后简历（PDF，可直接投递） |
| `diff_report.html` | 修改前后对比报告（浏览器打开） |

## 📂 项目结构

```
resume-boost/
├── main.py              # CLI 入口（完整 Pipeline）
├── app.py               # Web UI（Gradio）
├── pdf_parser.py        # PDF 文本提取（PyMuPDF）
├── jd_store.py          # JD 混合检索 + Cross-Encoder 重排序
├── analyzer.py          # LLM 多维度评分分析
├── rewriter.py          # 智能改写（JD + 范例 → LLM → 优化简历）
├── pdf_generator.py     # Markdown → PDF（fpdf2 + 中文字体）
├── diff_highlight.py    # Before/After 语义对比报告
├── jds.json             # 15 条真实大厂 JD 数据库
├── resume_examples.json # 18 条优秀简历范例库
├── pyproject.toml       # 项目依赖配置
└── .env                 # API Key（不上传）
```

## 🛠️ 技术栈

| 类别 | 技术 |
|---|---|
| PDF 解析 | PyMuPDF (`pymupdf`) |
| 向量数据库 | ChromaDB（内存模式） |
| 中文 Embedding | `BAAI/bge-small-zh-v1.5` |
| 中文分词 | jieba |
| 关键词检索 | BM25 (`rank-bm25`) |
| 重排序模型 | `BAAI/bge-reranker-v2-m3` (Cross-Encoder) |
| LLM | DeepSeek (OpenAI SDK 兼容) |
| PDF 生成 | fpdf2 + 微软雅黑字体 |
| 文本对比 | difflib (标准库) |
| Web UI | Gradio |
| 包管理 | uv |

## 🔬 RAG Pipeline 详解

```
Phase 1: 中文 Embedding
    └─ BAAI/bge-small-zh-v1.5（无需认证，768维）

Phase 2: 知识库
    ├─ 15 条真实大厂 JD（含 category 分类）
    └─ 18 条优秀简历范例（资深级 + 应届生级）

Phase 3: 混合检索
    ├─ 向量语义检索（ChromaDB）
    ├─ BM25 关键词检索（jieba 分词）
    └─ RRF 融合排序（Reciprocal Rank Fusion, k=60）

Phase 4: 精排
    └─ Cross-Encoder 重排序（bge-reranker-v2-m3）

Phase 5: 智能改写
    ├─ 范例库向量检索（匹配相关优秀简历）
    └─ LLM 三源输入：原始简历 + 匹配JD + 匹配范例 → 优化简历

Phase 6: 输出
    ├─ PDF 生成（Markdown → fpdf2 → A4 PDF）
    └─ Diff 对比（章节语义匹配 + Jaccard + 行内高亮）
```

## 📊 评分维度

| 维度 | 权重 | 评估内容 |
|---|---|---|
| 岗位匹配度 | 40% | 对照真实 JD 要求评估技能/经历匹配 |
| 内容组织 | 25% | 模块划分是否清晰、时间线是否有序 |
| 内容质量 | 25% | 量化表达、STAR-T 法则、具体成果 |
| 完整性 | 10% | 基本信息、技能、链接是否齐全 |

## 📜 License

MIT
