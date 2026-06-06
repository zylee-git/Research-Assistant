from openai import OpenAI
from rich.console import Console
from typing import Dict

console = Console()


class DeepSeekClient:
    """DeepSeek V4 客户端"""
    
    def __init__(self, api_key: str, base_url: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def think(self, prompt: str, effort: str = "high") -> Dict[str, str]:
        """思考模式（用于分析、对比、综述）"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=[{"role": "user", "content": prompt}],
                reasoning_effort=effort,
                extra_body={"thinking": {"type": "enabled"}},
                max_tokens=8192
            )
            return {
                "content": response.choices[0].message.content or "",
                "reasoning": getattr(response.choices[0].message, "reasoning_content", "")
            }
        except Exception as e:
            console.print(f"[red]API错误: {e}[/red]")
            return {"content": "", "reasoning": ""}
    
    def quick(self, prompt: str) -> str:
        """快速模式（用于检索、筛选）"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                extra_body={"thinking": {"type": "disabled"}},
                max_tokens=4096
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            console.print(f"[red]API错误: {e}[/red]")
            return ""