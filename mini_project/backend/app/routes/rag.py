from fastapi import APIRouter, Query, HTTPException
from app.rag.retriever import retrieve

router = APIRouter(prefix="/api/rag", tags=["RAG Knowledge Base"])

@router.get("/search")
def search_knowledge_base(
    q: str = Query(..., description="Query string to search in the knowledge base"),
    top_k: int = Query(5, ge=1, le=10, description="Number of results to retrieve")
):
    try:
        results = retrieve(query=q, top_k=top_k)
        return {
            "query": q,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")