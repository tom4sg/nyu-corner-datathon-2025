# app/api/routes/search.py

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from app.core.hybrid_search import HybridSearchEngine
from app.core.config import settings
import pandas as pd

router = APIRouter()

# Load metadata and initialize search engine
metadata_df = pd.read_csv(settings.PROCESSED_CSV_PATH)
search_engine = HybridSearchEngine(metadata_df)

@router.get("/search")
async def search(
    q: str = Query(..., description="Search query"),
    top_k: int = 10,
    weight_dense: float = Query(0.4, ge=0.0, le=1.0),
    weight_sparse: float = Query(0.3, ge=0.0, le=1.0),
    weight_image: float = Query(0.3, ge=0.0, le=1.0)
):
    """
    Hybrid search combining dense, sparse, and image embeddings
    """
    try:
        # Normalize weights to sum to 1
        total_weight = weight_dense + weight_sparse + weight_image
        if total_weight != 1.0:
            weight_dense = weight_dense / total_weight
            weight_sparse = weight_sparse / total_weight
            weight_image = weight_image / total_weight

        # Perform hybrid search
        results = await run_in_threadpool(
            search_engine.search,
            query=q,
            top_k=top_k,
            weight_dense=weight_dense,
            weight_sparse=weight_sparse,
            weight_image=weight_image
        )

        if not results:
            return JSONResponse(
                status_code=200,
                content={"results": [], "message": "No valid results found for your query."}
            )

        return {"results": results}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Search failed: {str(e)}"}
        )
