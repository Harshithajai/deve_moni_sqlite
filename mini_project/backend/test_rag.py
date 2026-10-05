# backend/test_rag.py
from app.rag.retriever import retrieve

def test_query(query_text: str):
    print(f"\n--- Query: '{query_text}' ---")
    results = retrieve(query_text, top_k=3)
    
    if not results:
        print("No results found.")
        return

    for i, item in enumerate(results, 1):
        print(f"\nResult {i} (Score: {item.get('similarity_score', 0):.4f}):")
        print(f"Document: {item.get('title', 'Unknown')} ({item.get('source', 'N/A')})")
        print(f"Page: {item.get('page_number', 'N/A')}")
        
        # Safely extract text field
        chunk_text = item.get('text') or item.get('chunk_text', 'No text available')
        print(f"Excerpt: {chunk_text[:200]}...")

if __name__ == "__main__":
    test_query("What activities support turn-taking and social interaction?")
    test_query("How to monitor developmental milestones in young children?")