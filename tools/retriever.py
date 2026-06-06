import requests
import time
import re
from typing import List, Dict


class PaperRetriever:
    def __init__(self, llm=None):
        self.last_request = 0
        self.llm = llm  # 可选的LLM用于翻译
    
    def set_llm(self, llm):
        """设置LLM用于翻译"""
        self.llm = llm
    
    def translate_query(self, query: str) -> str:
        """将中文查询转换为英文关键词"""
        # 如果已经是纯英文，直接返回
        if re.match(r'^[A-Za-z\s]+$', query.strip()):
            return query.strip()
        
        # 如果有LLM，用LLM翻译
        if self.llm:
            try:
                prompt = f"""将以下中文研究问题转换为英文关键词（只输出英文，不要解释）：

中文: {query}
英文关键词:"""
                result = self.llm.quick(prompt)
                # 清理结果
                result = result.strip().strip('"').strip("'")
                if result and len(result) > 3:
                    print(f"[翻译] {query} -> {result}")
                    return result
            except:
                pass
        
        # 常见中英文映射（备用）
        mapping = {
            "大语言模型": "large language model",
            "语言模型": "language model",
            "神经网络": "neural network",
            "深度学习": "deep learning",
            "机器学习": "machine learning",
            "计算机视觉": "computer vision",
            "图像分类": "image classification",
            "目标检测": "object detection",
            "图像分割": "image segmentation",
            "自然语言处理": "natural language processing",
            "情感分析": "sentiment analysis",
            "文本分类": "text classification",
            "注意力机制": "attention mechanism",
            "Transformer": "Transformer",
            "注意力": "attention",
            "对比": "comparison",
            "最新进展": "recent advances",
            "综述": "survey",
            "实现": "",
            "Vision Transformer": "Vision Transformer",
            "ViT": "Vision Transformer",
            "ResNet": "ResNet",
            "CNN": "CNN",
            "卷积神经网络": "convolutional neural network",
            "循环神经网络": "recurrent neural network",
            "生成对抗网络": "generative adversarial network",
            "扩散模型": "diffusion model",
            "强化学习": "reinforcement learning",
            "图神经网络": "graph neural network",
        }
        
        result = query
        for cn, en in mapping.items():
            if cn in result:
                if en:
                    result = result.replace(cn, en)
                else:
                    result = result.replace(cn, "")
        
        # 移除多余空格和标点
        result = re.sub(r'[^\w\s]', '', result)
        result = re.sub(r'\s+', ' ', result).strip()
        
        # 如果结果太短或没有英文单词，返回默认
        if len(result) < 3 or not re.search(r'[A-Za-z]', result):
            return "machine learning"
        
        print(f"[翻译] {query} -> {result}")
        return result
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        # 翻译查询
        english_query = self.translate_query(query)
        print(f"[检索] 使用关键词: {english_query}")
        
        now = time.time()
        if now - self.last_request < 1:
            time.sleep(1)
        self.last_request = now
        
        url = "https://api.openalex.org/works"
        params = {
            "search": english_query.replace(" ", "+"),
            "per-page": max_results
        }
        
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code != 200:
                print(f"[错误] HTTP {resp.status_code}")
                return []
            
            papers = []
            for work in resp.json().get("results", []):
                authors = []
                for auth in work.get("authorships", [])[:3]:
                    name = auth.get("author", {}).get("display_name")
                    if name:
                        authors.append(name)
                
                # 提取摘要
                abstract = ""
                abstract_index = work.get("abstract_inverted_index")
                if abstract_index:
                    words_positions = []
                    for word, positions in abstract_index.items():
                        for pos in positions:
                            words_positions.append((pos, word))
                    words_positions.sort()
                    abstract = " ".join([word for _, word in words_positions])
                
                papers.append({
                    "title": work.get("title", ""),
                    "authors": authors,
                    "abstract": abstract[:500] if abstract else "",
                    "year": (work.get("publication_date") or "")[:4],
                    "url": work.get("doi", ""),
                })
            print(f"[检索] 找到 {len(papers)} 篇论文")
            return papers
        except Exception as e:
            print(f"检索错误: {e}")
            return []