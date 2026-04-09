
from knowledge_manager import KnowledgeManager

km = KnowledgeManager()

queries = [
    "Hero's Odyssey",
    "RPG mechanics",
    "GamiCore version",
    "Taremwa Studios history"
]

for q in queries:
    print(f"\nQuery: {q}")
    results = km.search(q)
    if results:
        for r in results:
            print(f"  [Found in {r['source']}] Topic: {r['topic']}")
            print(f"  Content snippet: {r['content'][:100]}...")
    else:
        print("  No results found.")

