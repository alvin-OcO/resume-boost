# 📄 ResumeBoost

> AI 简历优化器——上传 PDF + 输入目标岗位，基于 RAG 检索真实招聘要求，自动生成多维度评分与改进建议。

## ✨ 亮点

- **RAG 增强分析**：向量检索最匹配的岗位 JD，让 LLM 对照真实要求评分
- **多维度评分体系**：岗位匹配度(40%) + 内容组织(25%) + 内容质量(25%) + 完整性(10%)
- **模块化架构**：PDF 解析 → 向量检索 → LLM 分析，职责单一、易扩展
- **双模式运行**：CLI 快速验证 + Gradio Web UI 可视化交互
- **隐私安全**：简历 PDF 本地处理，不上传云端

## 🏗️ 架构

```
用户上传 PDF + 输入目标岗位
    │
    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ PDF Parser   │ ──→ │ JD Store     │ ──→ │ LLM Analyzer │
│ (PyMuPDF)    │     │ (ChromaDB)   │     │ (DeepSeek)   │
└──────────────┘     └──────────────┘     └──────────────┘
                                                    │
                                                    ▼
                                          ┌──────────────┐
                                          │ 分析报告      │
                                          │ (Markdown)   │
                                          └──────────────┘
```

## 🚀 快速开始

```bash
# 安装依赖
uv sync

# 配置 API Key
echo "DEEPSEEK_API_KEY=你的key" > .env
```

### CLI 模式

```bash
uv run main.py
```

### Web UI 模式

```bash
uv run app.py
# 浏览器打开 http://127.0.0.1:7860
```

## 📊 评分维度

| 维度 | 权重 | 评估内容 |
|---|---|---|
| 岗位匹配度 | 40% | 对照真实 JD 要求评估关键词匹配度 |
| 内容组织 | 25% | 模块划分是否清晰、时间线是否有序 |
| 内容质量 | 25% | 量化表达、STAR 法则、具体成果 |
| 完整性 | 10% | 基本信息、技能、链接是否齐全 |

## 📂 项目结构

```
├── app.py           # Web UI（Gradio）
├── main.py          # CLI 入口
├── pdf_parser.py    # PDF 文本提取模块
├── analyzer.py      # LLM 多维分析模块
├── jd_store.py      # 向量检索模块（ChromaDB）
├── jds.json         # 岗位 JD 数据库
├── .env             # API Key（不上传）
└── .gitignore
```

## 🛠️ 技术栈

- **PDF 解析**：PyMuPDF (fitz)
- **向量检索**：ChromaDB（内置 Embedding，本地运行）
- **LLM**：DeepSeek (OpenAI SDK 兼容)
- **Web UI**：Gradio
- **包管理**：uv

## 💡 RAG 工作流程

1. **Retrieve**：用简历文本作为查询，从向量数据库中检索最匹配的岗位 JD
2. **Augment**：将检索到的 JD 注入 LLM 的 prompt 中
3. **Generate**：LLM 对照真实岗位要求生成有据可依的分析报告
