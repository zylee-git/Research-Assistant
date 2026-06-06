# test_retriever.py
from tools.retriever import PaperRetriever

r = PaperRetriever()
papers = r.search("transformer attention", 3)

for p in papers:
    print(f"标题: {p['title'][:50]}")
    print(f"摘要: {p['abstract'][:100] if p['abstract'] else '无'}")
    print(f"年份: {p['year']}")
    print("-" * 40)