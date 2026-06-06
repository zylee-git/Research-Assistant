class CodeGenerator:
    """实验代码生成器"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def generate(self, method_desc: str, framework: str = "pytorch") -> str:
        prompt = f"""根据以下方法描述生成{framework}代码。只输出代码，不要解释。

方法: {method_desc[:800]}

要求: 包含import、核心类/函数、测试示例。

代码:"""
        
        return self.llm.generate_quick(prompt, max_tokens=2000)