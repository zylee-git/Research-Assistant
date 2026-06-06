from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .client import DeepSeekClient
from .filters import (
    filter_papers, analyze_papers, compare_methods,
    generate_review, generate_code, quick_mode
)

console = Console()


class ResearchAgent:
    """科研助手Agent"""
    
    def __init__(self, config):
        self.config = config
        self.llm = DeepSeekClient(config.DEEPSEEK_API_KEY, config.DEEPSEEK_BASE_URL)
        self.papers = []
    
    def run(self, query: str, mode: str = "full") -> Dict[str, Any]:
        """运行Agent"""
        console.print(f"\n[bold cyan]🔬 科研助手启动[/bold cyan]")
        console.print(f"[green]问题: {query}[/green]")
        console.print(f"[dim]模式: {mode}[/dim]\n")
        
        # 1. 检索
        console.print("[yellow]📚 步骤1: 检索论文...[/yellow]")
        from tools.retriever import PaperRetriever
        retriever = PaperRetriever()
        retriever.set_llm(self.llm)
        self.papers = retriever.search(query, max_results=self.config.MAX_PAPERS)
        console.print(f"[green]找到 {len(self.papers)} 篇论文[/green]")
        
        if mode == "quick":
            summary = quick_mode(self.llm, self.papers, query)
            return {"query": query, "summary": summary, "papers": self.papers[:5]}
        
        # 2. 筛选
        console.print("[yellow]🔍 步骤2: 筛选论文...[/yellow]")
        filtered = filter_papers(self.llm, self.papers, query)
        
        # 3. 分析
        console.print("[yellow]📖 步骤3: 分析论文...[/yellow]")
        analyses = analyze_papers(self.llm, filtered)
        
        # 4. 对比
        console.print("[yellow]📊 步骤4: 对比方法...[/yellow]")
        comparison = compare_methods(self.llm, analyses, query)
        
        # 5. 综述
        console.print("[yellow]✍️ 步骤5: 生成综述...[/yellow]")
        review = generate_review(self.llm, query, analyses, comparison)
        
        result = {
            "query": query,
            "mode": mode,
            "papers": self.papers[:5],
            "analysis": analyses,
            "comparison": comparison,
            "review": review,
        }
        
        # 6. 代码（深度模式）
        if mode == "deep":
            console.print("[yellow]💻 步骤6: 生成代码...[/yellow]")
            code = generate_code(self.llm, analyses)

            # 清理 markdown 标记
            code = code.replace("```python", "").replace("```", "").strip()
            
            result["code"] = code
            
            # 保存代码到文件
            code_dir = Path("generated_codes")
            code_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            code_file = code_dir / f"code_{timestamp}.py"
            code_file.write_text(code, encoding="utf-8")
            console.print(f"[green]✅ 代码已保存: {code_file}[/green]")
        
        return result