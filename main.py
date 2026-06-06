#!/usr/bin/env python3
"""
自动科研助手 - 基于DeepSeek V4
"""

import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel

from config import Config
from agent.agent import ResearchAgent

console = Console()

def truncate(text: str, max_len: int = 60) -> str:
    return text[:max_len] + "..." if len(text) > max_len else text

def print_banner():
    banner = """
╔═══════════════════════════════════════════════════════╗
║   🔬 自动科研助手 - Auto Research Assistant          ║
║   基于 DeepSeek V4                                    ║
║   功能: 检索 | 分析 | 对比 | 综述 | 代码生成         ║
╚═══════════════════════════════════════════════════════╝
"""
    console.print(Panel(banner, style="bold blue"))


def check_config():
    if not Config.DEEPSEEK_API_KEY:
        console.print("[red]❌ 错误: 未配置 DEEPSEEK_API_KEY[/red]")
        console.print("[yellow]请在 .env 文件中设置: DEEPSEEK_API_KEY=your_key[/yellow]")
        return False
    console.print("[green]✅ 配置正常[/green]")
    return True


def save_full_report(result: dict) -> str:
    """保存完整报告（综述+对比+论文+代码）"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = Path(f"reports/report_{timestamp}.md")
    save_path.parent.mkdir(exist_ok=True)
    
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
        content += f"\n---\n\n## 💻 生成的代码\n\n```python\n{result.get('code')}\n```\n"

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(save_path)


def display_result(result: dict):
    """显示结果"""
    
    if result.get("review"):
        console.print("\n[bold cyan]📄 文献综述[/bold cyan]")
        console.print("─" * 50)
        md = Markdown(result["review"][:2000])
        console.print(md)
    
    if result.get("comparison"):
        console.print("\n[bold cyan]📊 方法对比[/bold cyan]")
        console.print("─" * 50)
        md = Markdown(result["comparison"][:1500])
        console.print(md)
    
    if result.get("code"):
        console.print("\n[bold cyan]💻 生成代码[/bold cyan]")
        console.print("─" * 50)
        syntax = Syntax(result["code"], "python", theme="monokai", line_numbers=True)
        console.print(syntax)
    
    if result.get("papers"):
        console.print("\n[bold cyan]📚 相关论文[/bold cyan]")
        table = Table()
        table.add_column("#", style="dim")
        table.add_column("标题", style="green")
        table.add_column("年份", style="blue")
        for i, p in enumerate(result["papers"][:8], 1):
            table.add_row(str(i), truncate(p["title"], 60), p.get("year", ""))
        console.print(table)


def save_papers_only(result: dict) -> str:
    """仅保存论文列表和摘要"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = Path(f"reports/papers_{timestamp}.md")
    save_path.parent.mkdir(exist_ok=True)
    
    content = f"""# 论文摘要汇总

**研究问题**: {result['query']}
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

"""
    for i, p in enumerate(result.get('papers', []), 1):
        content += f"\n## {i}. {p.get('title', 'N/A')}\n\n"
        content += f"- **作者**: {', '.join(p.get('authors', [])[:3])}\n"
        content += f"- **年份**: {p.get('year', 'N/A')}\n\n"
        content += f"**摘要**:\n{p.get('abstract', '无')}\n\n"
        content += "---\n"

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(save_path)


def main():
    print_banner()
    
    if not check_config():
        sys.exit(1)
    
    console.print("\n[green]使用示例:[/green]")
    console.print("  - \"Transformer模型的最新进展\"")
    console.print("  - \"对比LLaMA和GPT的架构\"")
    console.print("  - /deep \"扩散模型在图像生成中的应用\" (深度模式)")
    console.print("  - /quick \"多模态大模型\" (快速模式)")
    console.print("  - /full \"对比CNN和Transformer\" (完整模式)\n")
    
    agent = ResearchAgent(Config)
    
    while True:
        user_input = Prompt.ask("\n[bold cyan]🔍 研究问题[/bold cyan]")
        
        if user_input.lower() in ["quit", "exit", "q"]:
            console.print("[yellow]再见！👋[/yellow]")
            break
        
        mode = "full"
        query = user_input
        
        if user_input.startswith("/"):
            parts = user_input.split(" ", 1)
            if len(parts) == 2:
                cmd = parts[0][1:]
                if cmd in ["quick", "full", "deep"]:
                    mode = cmd
                    query = parts[1]
        
        try:
            result = agent.run(query, mode=mode)
            display_result(result)
            
            # 询问保存选项
            console.print("\n[bold]保存选项:[/bold]")
            console.print("  1. 保存完整报告（综述+对比+论文）")
            console.print("  2. 仅保存论文摘要")
            console.print("  3. 全部保存")
            console.print("  4. 不保存")
            
            choice = Prompt.ask("请选择", choices=["1", "2", "3", "4"], default="1")
            
            if choice in ["1", "3"]:
                path = save_full_report(result)
                console.print(f"[green]✅ 完整报告: {path}[/green]")
            
            if choice in ["2", "3"]:
                path = save_papers_only(result)
                console.print(f"[green]✅ 论文摘要: {path}[/green]")
            
            if choice == "4":
                console.print("[dim]未保存[/dim]")
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]用户中断[/yellow]")
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")


if __name__ == "__main__":
    main()