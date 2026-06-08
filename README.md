# 📄 ResumeBoost

> AI 简历优化器——上传 PDF + 输入目标岗位，自动生成多维度评分与改进建议。

## ✨ 亮点

- **多维度评分体系**：岗位匹配度(40%) + 内容组织(25%) + 内容质量(25%) + 完整性(10%)
- **模块化三层架构**：PDF 解析 → LLM 分析 → 结果展示，职责单一、易扩展
- **双模式运行**：CLI 快速验证 + Gradio Web UI 可视化交互
- **隐私安全**：简历 PDF 本地处理，不上传云端

## 🏗️ 架构

```
用户上传 PDF + 输入目标岗位
    │
    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ PDF Parser   │ ──→ │ LLM Analyzer │ ──→ │ 分析报告      │
│ (PyMuPDF)    │     │ (DeepSeek)   │     │ (Markdown)   │
└──────────────┘     └──────────────┘     └──────────────┘
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
| 岗位匹配度 | 40% | 简历关键词与目标岗位的重合度 |
| 内容组织 | 25% | 模块划分是否清晰、时间线是否有序 |
| 内容质量 | 25% | 量化表达、STAR 法则、具体成果 |
| 完整性 | 10% | 基本信息是否齐全 |

## 📂 项目结构

```
├── app.py           # Web UI（Gradio）
├── main.py          # CLI 入口
├── pdf_parser.py    # PDF 文本提取模块
├── analyzer.py      # LLM 多维分析模块
├── .env             # API Key（不上传）
└── .gitignore
```

## 🛠️ 技术栈

- **PDF 解析**：PyMuPDF (fitz)
- **LLM**：DeepSeek (OpenAI SDK 兼容)
- **Web UI**：Gradio
- **包管理**：uv
