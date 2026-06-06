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
    st.caption("📋 检索 | 分析 | 对比 | 综述 | 代码生成")


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

## 📄 文献综述

{result.get('review', '无')}

---

## 📊 方法对比

{result.get('comparison', '无')}

---

## 📚 相关论文

"""
        for i, p in enumerate(result.get('papers', []), 1):
            content += f"\n### {i}. {p.get('title', 'N/A')}\n"
            content += f"- **作者**: {', '.join(p.get('authors', [])[:3])}\n"
            content += f"- **年份**: {p.get('year', 'N/A')}\n"
            content += f"- **摘要**: {p.get('abstract', '')[:300]}...\n"

        if result.get('code'):
            content += f"\n---\n\n## 💻 生成的代码\n\n```python\n{result['code']}\n```\n"

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


# ===== Main =====
st.title("🔬 自动科研助手")
st.caption("输入研究问题，AI 自动检索学术论文、深度分析、方法对比并生成文献综述")

col_input, col_btn = st.columns([5, 1])
with col_input:
    query = st.text_area(
        "研究问题",
        placeholder="例如: Transformer模型的最新进展 / 对比LLaMA和GPT的架构差异 / 扩散模型在图像生成中的应用 ...",
        height=100,
        label_visibility="collapsed",
        key="query_input",
    )
with col_btn:
    st.write("")
    st.write("")
    search_btn = st.button("🔍 开始研究", type="primary", use_container_width=True)

# ===== Pipeline =====
if search_btn and query:
    if "result" not in st.session_state:
        st.session_state.result = None

    llm = DeepSeekClient(Config.DEEPSEEK_API_KEY, Config.DEEPSEEK_BASE_URL)

    # ---- Step 1: Retrieve ----
    with st.status("📚 步骤 1/6: 检索论文...", expanded=True) as status:
        retriever = PaperRetriever()
        retriever.set_llm(llm)
        papers = retriever.search(query, max_results=max_papers)

        if not papers:
            st.error("未找到相关论文，请尝试其他关键词")
            st.stop()

        status.update(label=f"✅ 步骤 1: 检索完成 — 找到 {len(papers)} 篇论文", state="complete")

    st.markdown("#### 📚 检索结果")
    paper_data = []
    for i, p in enumerate(papers, 1):
        paper_data.append({
            "#": i,
            "标题": p.get("title", "N/A")[:80] + ("..." if len(p.get("title", "")) > 80 else ""),
            "作者": ", ".join(p.get("authors", [])[:2]),
            "年份": p.get("year", "N/A"),
        })
    st.dataframe(paper_data, use_container_width=True, hide_index=True)

    # 批量获取PDF链接
    with st.spinner("🔗 正在查找可下载的PDF链接..."):
        pdf_urls = {}
        for p in papers:
            url = retriever.get_pdf_url(p["title"])
            if url:
                pdf_urls[p["title"]] = url

    with st.expander("📋 查看论文摘要"):
        for i, p in enumerate(papers, 1):
            c1, c2 = st.columns([9, 1])
            with c1:
                st.markdown(f"**{i}. {p.get('title', 'N/A')}**")
                st.caption(f"作者: {', '.join(p.get('authors', [])[:3])} | 年份: {p.get('year', 'N/A')}")
                st.write(p.get('abstract', '无摘要')[:500])
            with c2:
                pdf = pdf_urls.get(p["title"])
                if pdf:
                    st.link_button("📥 PDF", pdf, help="在arXiv打开PDF")
                else:
                    st.caption("")
            if i < len(papers):
                st.divider()

    # ---- Quick mode: summary only ----
    if mode == "quick":
        with st.spinner("⚡ 正在生成摘要..."):
            summary = quick_mode(llm, papers, query)

        st.markdown("### 📋 研究摘要")
        st.markdown(summary)

        result = {"query": query, "mode": mode, "papers": papers, "summary": summary}
        st.session_state.result = result

        content, path = save_report(result, "papers")
        st.download_button(
            label="📥 下载论文摘要 (Markdown)",
            data=content,
            file_name=f"papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
        )
        st.stop()

    # ---- Step 2: Filter ----
    with st.status("🔍 步骤 2/6: 筛选最相关论文...", expanded=True) as status2:
        filtered = filter_papers(llm, papers, query)
        status2.update(label=f"✅ 步骤 2: 筛选完成 — 保留 {len(filtered)} 篇", state="complete")

    cols = st.columns(len(filtered))
    for i, (col, p) in enumerate(zip(cols, filtered), 1):
        with col:
            st.markdown(f"**#{i}** {p.get('title', 'N/A')[:50]}...")
            st.caption(f"{p.get('year', 'N/A')} | {', '.join(p.get('authors', [])[:2])}")

    # ---- Step 3: Analyze ----
    with st.status("📖 步骤 3/6: 深度分析论文...", expanded=True) as status3:
        analyses = analyze_papers(llm, filtered)
        status3.update(label=f"✅ 步骤 3: 分析完成 ({len(analyses)} 篇)", state="complete")

    # ---- Step 4: Compare ----
    with st.status("📊 步骤 4/6: 对比方法...", expanded=True) as status4:
        comparison = compare_methods(llm, analyses, query)
        status4.update(label="✅ 步骤 4: 对比完成", state="complete")

    # ---- Step 5: Review ----
    with st.status("✍️ 步骤 5/6: 生成文献综述...", expanded=True) as status5:
        review = generate_review(llm, query, analyses, comparison)
        status5.update(label="✅ 步骤 5: 综述完成", state="complete")

    # ---- Step 6: Code (deep only) ----
    code = None
    if mode == "deep":
        with st.status("💻 步骤 6/6: 生成实验代码...", expanded=True) as status6:
            code = generate_code(llm, analyses)
            code = code.replace("```python", "").replace("```", "").strip()

            code_dir = Path("generated_codes")
            code_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            code_file = code_dir / f"code_{timestamp}.py"
            code_file.write_text(code, encoding="utf-8")

            status6.update(label="✅ 步骤 6: 代码生成完成", state="complete")

    # ===== Display results =====
    result = {
        "query": query, "mode": mode, "papers": filtered,
        "analysis": analyses, "comparison": comparison, "review": review,
    }
    if code:
        result["code"] = code
    st.session_state.result = result

    st.divider()
    st.header("📊 研究结果")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 文献综述", "📊 方法对比", "📖 论文分析", "📚 论文列表"
    ])

    with tab1:
        st.markdown(review)

    with tab2:
        st.markdown(comparison)

    with tab3:
        for i, analysis in enumerate(analyses, 1):
            with st.expander(f"📄 Paper {i}: {analysis.get('title', 'N/A')[:70]}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**核心方法**")
                    st.write(analysis.get("method", "N/A"))
                    st.markdown("**主要贡献**")
                    st.write(analysis.get("contribution", "N/A"))
                with c2:
                    st.markdown("**关键结果**")
                    st.write(analysis.get("result", "N/A"))
                    st.markdown("**局限性**")
                    st.write(analysis.get("limitation", "N/A"))

    with tab4:
        for i, p in enumerate(result.get("papers", []), 1):
            c1, c2 = st.columns([9, 1])
            with c1:
                st.markdown(f"**{i}. {p.get('title', 'N/A')}**")
                st.caption(f"作者: {', '.join(p.get('authors', [])[:3])} | 年份: {p.get('year', 'N/A')}")
                st.write(p.get('abstract', '无摘要')[:500])
                if p.get('url'):
                    st.caption(f"DOI: {p['url']}")
            with c2:
                pdf = pdf_urls.get(p["title"])
                if pdf:
                    st.link_button("📥 PDF", pdf, help="在arXiv打开PDF")
            st.divider()

    if code:
        st.divider()
        st.subheader("💻 生成的代码")
        st.code(code, language="python", line_numbers=True)

    # ---- Downloads ----
    st.divider()
    st.subheader("📥 下载结果")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        full_content, _ = save_report(result, "full")
        st.download_button(
            label="📥 下载完整报告",
            data=full_content,
            file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_dl2:
        papers_content, _ = save_report(result, "papers")
        st.download_button(
            label="📥 下载论文摘要",
            data=papers_content,
            file_name=f"papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.success("✅ 研究完成!")

elif search_btn and not query:
    st.warning("请输入研究问题")
