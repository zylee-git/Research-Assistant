# 🔬 自动科研助手 (Auto Research Assistant)

基于 DeepSeek V4 的智能学术论文检索与分析系统。输入研究问题，AI 自动检索论文、深度分析、方法对比并生成文献综述。

## 功能

- **📚 论文检索** — 通过 OpenAlex API 检索 2.5 亿+ 学术作品，支持中英文混合查询（LLM 自动翻译）
- **🔍 智能筛选** — LLM 从检索结果中筛选最相关的 3 篇论文
- **📖 深度分析** — 提取每篇论文的方法、贡献、结果、局限性（结构化 JSON）
- **📊 方法对比** — 生成 Markdown 对比表格
- **✍️ 文献综述** — 自动撰写 500-800 字结构化综述
- **💻 代码生成** — 基于论文方法生成 PyTorch 实现代码
- **📥 PDF 下载** — 通过 arXiv API 查找并提供 PDF 直链
- **📄 报告导出** — 一键下载 Markdown 格式完整报告

## 安装

```bash
git clone <repo-url>
cd research-assistant
pip install -r requirements.txt
```

## 配置

在项目根目录创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=sk-your-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

也可以启动 Web UI 后在侧边栏直接输入 Key（支持永久保存或仅本次会话）。

## 使用

### Web UI（推荐）

```bash
streamlit run webui.py
```

浏览器打开 http://localhost:8501 ，顶部 6 个标签页：

| 标签 | 内容 |
|------|------|
| 🏠 主界面 | 输入问题 + 执行流水线 + 下载报告 |
| 📚 文献检索 | 论文列表、摘要、PDF 下载 |
| 📊 方法对比 | LLM 生成的方法对比表格 |
| 📄 文献综述 | 完整结构化综述 |
| 📝 快速摘要 | 快速模式 AI 摘要 |
| 💻 代码生成 | 深度模式生成的 PyTorch 代码 |

三种运行模式：

| 模式 | 流程 | 适用场景 |
|------|------|----------|
| ⚡ 快速 | 检索 + AI 摘要 | 快速了解领域 |
| 📚 完整 | 检索→筛选→分析→对比→综述 | 深入文献调研 |
| 🧠 深度 | 完整 + PyTorch 代码生成 | 复现实验 |

### CLI

```bash
python main.py
```

交互式命令：
- `Transformer 最新进展` — 默认完整模式
- `/quick 多模态大模型` — 快速模式
- `/full 对比 CNN 和 Transformer` — 完整模式
- `/deep 扩散模型在图像生成中的应用` — 深度模式

## 项目结构

```
research-assistant/
├── main.py              # CLI 入口（Rich 终端 UI）
├── webui.py             # Web UI（Streamlit）
├── config.py            # 配置加载
├── requirements.txt     # 依赖
├── .env                 # API Key（不纳入版本控制）
│
├── agent/               # AI 代理层
│   ├── agent.py         # ResearchAgent 编排器（6 步流水线）
│   ├── client.py        # DeepSeek V4 API 客户端
│   └── filters.py       # LLM 处理函数（筛选/分析/对比/综述/代码）
│
├── tools/               # 基础工具
│   ├── retriever.py     # OpenAlex 检索 + arXiv PDF 查找 + 中英翻译
│   └── code_gen.py      # 代码生成器
│
├── data/                # 数据目录
├── reports/             # 输出的 Markdown 报告
└── generated_codes/     # 生成的 Python 代码
```

## 技术栈

| 层 | 技术 |
|----|------|
| LLM | DeepSeek V4 Pro + DeepSeek V4 Flash |
| 论文检索 | OpenAlex API |
| PDF 获取 | arXiv API |
| 前端 | Streamlit + Rich |
| 语言 | Python 3.10+ |

## 依赖

```
openai>=1.0.0
python-dotenv>=1.0.0
rich>=13.0.0
requests>=2.28.0
streamlit>=1.28.0
```
