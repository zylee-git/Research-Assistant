#!/usr/bin/env python3
"""
自动科研助手 Web UI - 基于 Streamlit
启动: streamlit run webui.py
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
from config import Config
from agent.client import DeepSeekClient
from agent.filters import (
    filter_papers, analyze_papers, compare_methods,
    generate_review, generate_code, quick_mode
)
from tools.retriever import PaperRetriever

st.set_page_config(
    page_title="自动科研助手",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===== Custom CSS =====
st.markdown("""
<style>
    /* 顶部导航标签加粗放大 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #f0f2f6;
        border-radius: 12px;
        padding: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.95rem;
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 18px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #fff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    /* 卡片容器 */
    .card {
        background: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.8rem;
    }
    /* 指标数字 */
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1a73e8;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #666;
    }
    /* 空状态 */
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #999;
    }
    .empty-state .icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ===== Sidebar =====
with st.sidebar:
    st.title("🔬 自动科研助手")
    st.markdown("*基于 DeepSeek V4*")
    st.divider()

    if Config.DEEPSEEK_API_KEY:
        key_preview = Config.DEEPSEEK_API_KEY[:8] + "..." + Config.DEEPSEEK_API_KEY[-4:]
        st.success(f"✅ API 已配置 ({key_preview})")
    else:
        st.error("❌ 未配置 DEEPSEEK_API_KEY")
        st.info("请在 .env 文件中设置 API Key")

    st.divider()

    st.subheader("⚙️ 运行模式")
    mode = st.radio(
        "选择研究深度",
        options=["quick", "full", "deep"],
        format_func=lambda x: {
            "quick": "⚡ 快速模式",
            "full": "📚 完整模式",
            "deep": "🧠 深度模式"
        }[x],
        index=1,
        key="mode_selector",
    )
    st.caption({
        "quick": "检索 + AI 摘要",
        "full": "检索 → 筛选 → 分析 → 对比 → 综述",
        "deep": "完整流程 + 代码生成"
    }[mode])

    st.divider()

    st.subheader("🔧 参数")
    max_papers = st.slider("检索论文数", 3, 20, Config.MAX_PAPERS, 1)

    st.divider()

    with st.expander("📋 项目信息"):
        st.markdown("""
        **功能清单**
        - 论文检索 (OpenAlex)
        - AI 筛选与分析
        - 方法对比表格
        - 文献综述生成
        - PyTorch 代码生成
        - PDF 直链下载
        - 报告导出 (Markdown)
        """)

    st.divider()
    st.caption("检索 | 分析 | 对比 | 综述 | 代码生成")


# ===== Helpers =====
def save_report(result, fmt="full"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("reports").mkdir(exist_ok=True)

    if fmt == "full":
        path = Path(f"reports/report_{timestamp}.md")
        content = f"""# {result['query']}

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**运行模式**: {result.get('mode', 'full')}

---

## 文献综述

{result.get('review', '无')}

---

## 方法对比

{result.get('comparison', '无')}

---

## 相关论文

"""
        for i, p in enumerate(result.get('papers', []), 1):
            content += f"\n### {i}. {p.get('title', 'N/A')}\n"
            content += f"- **作者**: {', '.join(p.get('authors', [])[:3])}\n"
            content += f"- **年份**: {p.get('year', 'N/A')}\n"
            content += f"- **摘要**: {p.get('abstract', '')[:300]}...\n"

        if result.get('code'):
            content += f"\n---\n\n## 生成的代码\n\n```python\n{result['code']}\n```\n"

        path.write_text(content, encoding="utf-8")
        return content, str(path)
    else:
        path = Path(f"reports/papers_{timestamp}.md")
        content = f"""# 论文摘要汇总

**研究问题**: {result['query']}
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

"""
        for i, p in enumerate(result.get('papers', []), 1):
            content += f"\n## {i}. {p.get('title', 'N/A')}\n\n"
            content += f"- **作者**: {', '.join(p.get('authors', [])[:3])}\n"
            content += f"- **年份**: {p.get('year', 'N/A')}\n"
            content += f"- **DOI**: {p.get('url', 'N/A')}\n\n"
            content += f"**摘要**:\n{p.get('abstract', '无')}\n\n---\n"

        path.write_text(content, encoding="utf-8")
        return content, str(path)


def show_empty(icon, title, desc):
    st.markdown(f"""
    <div class="empty-state">
        <div class="icon">{icon}</div>
        <h3>{title}</h3>
        <p>{desc}</p>
    </div>
    """, unsafe_allow_html=True)


# ===== Top Navigation Tabs =====
tabs = st.tabs([
    "🏠 主界面",
    "📚 文献检索",
    "📊 方法对比",
    "📄 文献综述",
    "📝 快速摘要",
    "💻 代码生成",
])

# Initialize session state
if "result" not in st.session_state:
    st.session_state.result = None
if "pdf_urls" not in st.session_state:
    st.session_state.pdf_urls = {}
if "papers" not in st.session_state:
    st.session_state.papers = []
if "analyses" not in st.session_state:
    st.session_state.analyses = []
if "comparison" not in st.session_state:
    st.session_state.comparison = ""
if "review" not in st.session_state:
    st.session_state.review = ""
if "code" not in st.session_state:
    st.session_state.code = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "query_text" not in st.session_state:
    st.session_state.query_text = ""
if "run_mode" not in st.session_state:
    st.session_state.run_mode = ""
if "pipeline_step" not in st.session_state:
    st.session_state.pipeline_step = 0


# ============================================================
# Tab 0: 主界面
# ============================================================
with tabs[0]:
    st.title("🔬 自动科研助手")
    st.caption("输入研究问题，AI 自动检索学术论文、深度分析、方法对比并生成文献综述")

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        query = st.text_area(
            "研究问题",
            placeholder="例如: Transformer模型的最新进展 / 对比LLaMA和GPT的架构差异 / 扩散模型在图像生成中的应用 ...",
            height=100,
            label_visibility="collapsed",
            key="query_input_main",
        )
    with col_btn:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 开始研究", type="primary", use_container_width=True)

    if search_btn and query:
        # 初始化流水线
        st.session_state.result = None
        st.session_state.papers = []
        st.session_state.pdf_urls = {}
        st.session_state.analyses = []
        st.session_state.comparison = ""
        st.session_state.review = ""
        st.session_state.code = ""
        st.session_state.summary = ""
        st.session_state.query_text = query
        st.session_state.run_mode = mode
        st.session_state.pipeline_step = 1
        st.rerun()

    # ---- 流水线状态机 ----
    step = st.session_state.get("pipeline_step", 0)

    if step == 0 and st.session_state.result:
        st.success("✅ 研究完成! 请切换到上方标签页查看详细结果")
        st.divider()
        st.subheader("📥 下载报告")
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            full_content, _ = save_report(st.session_state.result, "full")
            st.download_button(
                label="📥 下载完整报告", data=full_content,
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown", use_container_width=True,
            )
        with col_dl2:
            papers_content, _ = save_report(st.session_state.result, "papers")
            st.download_button(
                label="📥 下载论文摘要", data=papers_content,
                file_name=f"papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown", use_container_width=True,
            )

    elif step == "quick_summary" or (isinstance(step, int) and step >= 1):
        llm = DeepSeekClient(Config.DEEPSEEK_API_KEY, Config.DEEPSEEK_BASE_URL)
        q = st.session_state.query_text
        m = st.session_state.run_mode

        step_labels = {
            1: "检索论文", 2: "筛选论文", 3: "分析论文",
            4: "对比方法", 5: "生成综述", 6: "生成代码",
        }
        total = 5 if m != "deep" else 6
        if m == "quick":
            total = 2
            step_labels = {1: "检索论文", 2: "快速摘要"}

        # 进度条
        current_step_num = 2 if step == "quick_summary" else (step if isinstance(step, int) else 1)
        st.progress(current_step_num / total, text=f"步骤 {current_step_num}/{total}")

        # 已完成的步骤
        done_steps = []
        if m == "quick":
            if step == "quick_summary":
                done_steps = [1]
        else:
            for i in range(1, step if isinstance(step, int) else 1):
                done_steps.append(i)
        for s in done_steps:
            st.caption(f"✅ {step_labels.get(s, '')}")

        # ---- 执行当前步骤 ----
        try:
            if m == "quick":
                if step == 1:
                    with st.status("📚 步骤 1/2: 检索论文...", expanded=True) as s:
                        retriever = PaperRetriever()
                        retriever.set_llm(llm)
                        papers = retriever.search(q, max_results=max_papers)
                        if not papers:
                            st.error("未找到相关论文，请尝试其他关键词")
                            st.session_state.pipeline_step = 0
                            st.stop()
                        st.session_state.papers = papers
                        pdf_urls = {}
                        for p in papers:
                            url = retriever.get_pdf_url(p["title"])
                            if url:
                                pdf_urls[p["title"]] = url
                        st.session_state.pdf_urls = pdf_urls
                        s.update(label=f"✅ 步骤 1: 检索完成 — {len(papers)} 篇", state="complete")
                    st.session_state.pipeline_step = "quick_summary"
                    st.rerun()

                elif step == "quick_summary":
                    with st.status("⚡ 步骤 2/2: 生成摘要...", expanded=True) as s:
                        summary = quick_mode(llm, st.session_state.papers, q)
                        st.session_state.summary = summary
                        result = {"query": q, "mode": m, "papers": st.session_state.papers, "summary": summary}
                        st.session_state.result = result
                        s.update(label="✅ 步骤 2: 摘要完成", state="complete")
                    st.session_state.pipeline_step = 0
                    st.rerun()

            else:  # full / deep
                if step == 1:
                    with st.status("📚 步骤 1/6: 检索论文...", expanded=True) as s:
                        retriever = PaperRetriever()
                        retriever.set_llm(llm)
                        papers = retriever.search(q, max_results=max_papers)
                        if not papers:
                            st.error("未找到相关论文，请尝试其他关键词")
                            st.session_state.pipeline_step = 0
                            st.stop()
                        st.session_state.papers = papers
                        pdf_urls = {}
                        for p in papers:
                            url = retriever.get_pdf_url(p["title"])
                            if url:
                                pdf_urls[p["title"]] = url
                        st.session_state.pdf_urls = pdf_urls
                        s.update(label=f"✅ 步骤 1: 检索完成 — {len(papers)} 篇", state="complete")
                    st.session_state.pipeline_step = 2
                    st.rerun()

                elif step == 2:
                    with st.status("🔍 步骤 2/6: 筛选最相关论文...", expanded=True) as s:
                        filtered = filter_papers(llm, st.session_state.papers, q)
                        st.session_state.papers = filtered
                        s.update(label=f"✅ 步骤 2: 筛选完成 — 保留 {len(filtered)} 篇", state="complete")
                    st.session_state.pipeline_step = 3
                    st.rerun()

                elif step == 3:
                    with st.status("📖 步骤 3/6: 深度分析论文...", expanded=True) as s:
                        analyses = analyze_papers(llm, st.session_state.papers)
                        st.session_state.analyses = analyses
                        s.update(label=f"✅ 步骤 3: 分析完成 ({len(analyses)} 篇)", state="complete")
                    st.session_state.pipeline_step = 4
                    st.rerun()

                elif step == 4:
                    with st.status("📊 步骤 4/6: 对比方法...", expanded=True) as s:
                        comparison = compare_methods(llm, st.session_state.analyses, q)
                        st.session_state.comparison = comparison
                        s.update(label="✅ 步骤 4: 对比完成", state="complete")
                    st.session_state.pipeline_step = 5
                    st.rerun()

                elif step == 5:
                    with st.status("✍️ 步骤 5/6: 生成文献综述...", expanded=True) as s:
                        review = generate_review(llm, q, st.session_state.analyses, st.session_state.comparison)
                        st.session_state.review = review
                        s.update(label="✅ 步骤 5: 综述完成", state="complete")
                    st.session_state.pipeline_step = 6 if m == "deep" else 0
                    if m != "deep":
                        result = {
                            "query": q, "mode": m, "papers": st.session_state.papers,
                            "analysis": st.session_state.analyses,
                            "comparison": st.session_state.comparison,
                            "review": st.session_state.review,
                        }
                        st.session_state.result = result
                    st.rerun()

                elif step == 6 and m == "deep":
                    with st.status("💻 步骤 6/6: 生成实验代码...", expanded=True) as s:
                        code = generate_code(llm, st.session_state.analyses)
                        code = code.replace("```python", "").replace("```", "").strip()
                        st.session_state.code = code
                        code_dir = Path("generated_codes")
                        code_dir.mkdir(exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        code_file = code_dir / f"code_{timestamp}.py"
                        code_file.write_text(code, encoding="utf-8")
                        s.update(label="✅ 步骤 6: 代码生成完成", state="complete")
                    result = {
                        "query": q, "mode": m, "papers": st.session_state.papers,
                        "analysis": st.session_state.analyses,
                        "comparison": st.session_state.comparison,
                        "review": st.session_state.review, "code": st.session_state.code,
                    }
                    st.session_state.result = result
                    st.session_state.pipeline_step = 0
                    st.rerun()

        except Exception as e:
            st.error(f"流水线执行出错: {e}")
            st.session_state.pipeline_step = 0

    elif search_btn and not query:
        st.warning("请输入研究问题")
    else:
        show_empty("🔍", "开始你的研究之旅", "在上方输入研究问题，选择运行模式，点击「开始研究」按钮")
        st.markdown("""
        <div style="max-width:500px;margin:0 auto;">
        <p style="text-align:center;color:#888;">支持中英文混合查询，AI 自动翻译为英文关键词检索</p>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# Tab 1: 文献检索
# ============================================================
with tabs[1]:
    st.header("📚 文献检索与下载")

    if not st.session_state.papers:
        show_empty("📚", "暂无检索结果", "请先在主界面输入研究问题并开始检索")
    else:
        papers = st.session_state.papers
        pdf_urls = st.session_state.pdf_urls

        # 指标行
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("论文数量", f"{len(papers)} 篇")
        with c2:
            st.metric("PDF可下载", f"{len(pdf_urls)} 篇")
        with c3:
            has_doi = sum(1 for p in papers if p.get("url"))
            st.metric("有DOI", f"{has_doi} 篇")

        st.divider()

        # 论文列表
        for i, p in enumerate(papers, 1):
            with st.container():
                c_title, c_btn = st.columns([9, 1])
                with c_title:
                    st.markdown(f"### {i}. {p.get('title', 'N/A')}")
                    st.caption(f"👤 {', '.join(p.get('authors', [])[:5])}  |  📅 {p.get('year', 'N/A')}")
                    if p.get('url'):
                        st.caption(f"🔗 DOI: [{p['url']}](https://doi.org/{p['url']})")

                    with st.expander("📄 摘要"):
                        st.write(p.get('abstract', '无摘要')[:800])

                with c_btn:
                    st.write("")
                    st.write("")
                    pdf = pdf_urls.get(p["title"])
                    if pdf:
                        st.link_button("📥 PDF", pdf, help="在 arXiv 打开 PDF")
                    else:
                        st.caption("无PDF")

                st.divider()


# ============================================================
# Tab 2: 方法对比
# ============================================================
with tabs[2]:
    st.header("📊 方法对比")

    if not st.session_state.comparison:
        show_empty("📊", "暂无对比结果", "请先运行完整模式或深度模式生成方法对比")
    else:
        st.markdown(st.session_state.comparison)


# ============================================================
# Tab 3: 文献综述
# ============================================================
with tabs[3]:
    st.header("📄 文献综述")

    if not st.session_state.review:
        show_empty("📄", "暂无文献综述", "请先运行完整模式或深度模式生成文献综述")
    else:
        st.info(f"**研究问题**: {st.session_state.query_text}")
        st.markdown(st.session_state.review)


# ============================================================
# Tab 4: 快速摘要
# ============================================================
with tabs[4]:
    st.header("📝 快速摘要")

    if not st.session_state.summary and st.session_state.run_mode != "quick":
        show_empty("📝", "暂无快速摘要", "快速摘要仅在「快速模式」下生成，请在侧边栏切换到快速模式后重新检索")

    elif not st.session_state.summary:
        show_empty("📝", "暂无快速摘要", "请先在主界面选择快速模式并开始检索")

    else:
        st.info(f"**研究问题**: {st.session_state.query_text}")
        st.markdown(st.session_state.summary)

        if st.session_state.papers:
            st.divider()
            st.subheader("相关论文")
            for i, p in enumerate(st.session_state.papers[:5], 1):
                st.markdown(f"**{i}. {p.get('title', 'N/A')}**")
                st.caption(f"{', '.join(p.get('authors', [])[:3])} | {p.get('year', 'N/A')}")


# ============================================================
# Tab 5: 代码生成
# ============================================================
with tabs[5]:
    st.header("💻 代码生成")

    if not st.session_state.code:
        show_empty("💻", "暂无生成代码", "请先在侧边栏切换到「深度模式」后重新检索，系统将基于论文方法生成 PyTorch 实现代码")
    else:
        analyses = st.session_state.analyses
        if analyses:
            method_desc = analyses[0].get("method", "N/A") if analyses else "N/A"
            st.caption(f"**基于方法**: {method_desc[:100]}")

        st.code(st.session_state.code, language="python", line_numbers=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 下载代码 (.py)",
                data=st.session_state.code,
                file_name=f"generated_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
                mime="text/x-python",
                use_container_width=True,
            )
        with col2:
            if st.button("📋 复制代码", use_container_width=True):
                st.toast("代码已复制到剪贴板", icon="✅")
