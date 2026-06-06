import json
import re
from typing import List, Dict


def filter_papers(llm, papers: list, query: str) -> list:
    """使用LLM筛选论文"""
    if len(papers) <= 3:
        return papers
    
    prompt = f"""查询: {query}

论文列表:
{chr(10).join([f"{i+1}. {p['title']}" for i, p in enumerate(papers)])}

返回最相关的3篇论文的编号（JSON数组，如[1,2,3]）:"""
    
    try:
        resp = llm.quick(prompt)
        indices = eval(re.search(r'\[.*?\]', resp).group())
        return [papers[i-1] for i in indices if 1 <= i <= len(papers)]
    except:
        return papers[:3]


def analyze_papers(llm, papers: list) -> list:
    """深度分析论文"""
    analyses = []
    for paper in papers[:5]:
        prompt = f"""分析以下论文，提取关键信息（JSON格式）：

标题: {paper['title']}
年份: {paper['year']}
摘要: {paper['abstract']}

返回JSON:
{{"method": "核心方法", "contribution": "主要贡献", "result": "关键结果", "limitation": "局限性"}}"""
        
        resp = llm.think(prompt, effort="high")
        try:
            json_match = re.search(r'\{.*\}', resp["content"], re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                analysis["title"] = paper["title"]
                analyses.append(analysis)
            else:
                analyses.append({"title": paper["title"], "method": "N/A", "contribution": "N/A"})
        except:
            analyses.append({"title": paper["title"], "method": "N/A"})
    return analyses


def compare_methods(llm, analyses: list, query: str) -> str:
    """对比方法"""
    if not analyses:
        return "无足够论文进行对比"
    
    prompt = f"""研究主题: {query}

论文分析结果:
{json.dumps(analyses, ensure_ascii=False, indent=2)}

请对比这些论文的方法，生成Markdown格式的对比表格，包含：论文、核心方法、主要贡献、局限性。"""
    
    return llm.think(prompt, effort="max")["content"]


def generate_review(llm, query: str, analyses: list, comparison: str) -> str:
    """生成综述"""
    prompt = f"""请撰写关于"{query}"的文献综述（500-800字）。

论文分析:
{json.dumps([{"title": a.get("title"), "method": a.get("method"), "contribution": a.get("contribution")} for a in analyses], ensure_ascii=False, indent=2)}

对比结果:
{comparison[:1000]}

结构:
1. 引言
2. 主流方法分类
3. 对比分析
4. 挑战与展望"""
    
    return llm.think(prompt, effort="high")["content"]


def generate_code(llm, analyses: list) -> str:
    """生成实验代码"""
    method = analyses[0].get("method", "transformer") if analyses else "attention mechanism"
    
    prompt = f"""根据以下方法描述生成PyTorch实现代码：

方法: {method}

要求: 包含import、核心类定义、前向传播、简单测试。
只输出代码。"""
    
    return llm.quick(prompt)


def quick_mode(llm, papers: list, query: str) -> str:
    """快速模式总结"""
    summaries = []
    for paper in papers[:5]:
        summaries.append(f"**{paper['title']}** ({paper['year']})\n{paper['abstract'][:300]}...")
    
    prompt = f"""根据以下论文摘要，总结关于"{query}"的研究现状（200字以内）：

{chr(10).join(summaries)}"""
    
    return llm.quick(prompt)