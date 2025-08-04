import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pydantic import BaseModel
from transformers import CLIPProcessor, CLIPModel
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from pinecone import Pinecone
from langchain_anthropic import ChatAnthropic
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import ast
import re

# Load environment variables
load_dotenv()

# Let's first define the pydantic models for searching and returning

class SearchRequest(BaseModel):
    query: str

class Place(BaseModel):
    place_id: str
    name: str
    neighborhood: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    reviews: Optional[str] = None
    emoji: Optional[str] = None
    score: float

class SearchResponse(BaseModel):
    llm_response: str
    places: List[Place]
    total_results: int
    query: str

# Let's load the LLM with LangChain

llm = ChatAnthropic(
    model="claude-3-5-sonnet-20240620",
    anthropic_api_key=os.getenv("PERSONAL_ANTHROPIC")
)

# Now define the API with FastAPI

app = FastAPI(
    title="Vibe Search System",
    description="A place to find the best NYU venues",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get access to the specific indices in pinecone
try:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    image_index = pc.Index("corner-clip")
    dense_index = pc.Index("corner-metadata-dense")
    sparse_index = pc.Index("corner-metadata-sparse")
except Exception as e:
    print(f"Warning: Could not initialize Pinecone: {e}")

# Load the models
try:
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    metadata_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")
except Exception as e:
    print(f"Warning: Could not load models: {e}")



def merge_matches(dense_result, sparse_result, image_result) -> List[Dict]:
    """
    Merges matches from all three indexes into a single deduplicated list.
    Keeps only the highest scoring version of each unique 'id',
    but defers ranking to a reranker.
    """

    all_matches = (
        dense_result.get("matches", []) +
        sparse_result.get("matches", []) +
        image_result.get("matches", [])
    )

    # Deduplicate by id, keeping highest-score version
    merged = {}
    for match in all_matches:
        match_id = match["id"]
        if match_id not in merged or match["score"] > merged[match_id]["score"]:
            merged[match_id] = match

    # No sorting, will use reranker for final order
    formatted_results = []
    for match in merged.values():
        meta = match.get("metadata", {})
        formatted_results.append({
            "id": match["id"],
            "name": meta.get("name"),
            "neighborhood": meta.get("neighborhood"),
            "description": meta.get("description"),
            "reviews": meta.get("reviews"),
            "emoji": meta.get("emoji"),
            "score": match["score"]
        })

    return formatted_results

def format_place_strings(places: List[Dict]) -> List[str]:
    rerank_map = {}
    for place in places:
        name = place.get("name", "Unknown")
        emoji = place.get("emoji", "")
        neighborhood = place.get("neighborhood", "Unknown area")
        desc = place.get("description", "No description")

        key = f"{emoji} {name} ({neighborhood}) — {desc}"
        rerank_map[key] = place
    return rerank_map

# Define Async Pinecone query functions per index
executor = ThreadPoolExecutor()

async def pinecone_image_query(clip_embedding):
    return await asyncio.get_event_loop().run_in_executor(executor, lambda: (
        image_index.query(
            namespace="images", 
            vector=clip_embedding, 
            top_k=20,
            include_metadata=True,
            include_values=False
        )
    ))

async def pinecone_sparse_query(values, indices):
    return await asyncio.get_event_loop().run_in_executor(executor, lambda: (
        sparse_index.query(
            namespace="metadata", 
            sparse_vector={"values": values, "indices": indices},
            top_k=20,
            include_metadata=True,
            include_values=False
        )
    ))

async def pinecone_dense_query(dense_embedding):
    return await asyncio.get_event_loop().run_in_executor(executor, lambda: (
        dense_index.query(
            namespace="metadata", 
            vector=dense_embedding, 
            top_k=20,
            include_metadata=True,
            include_values=False
        )
    ))


@app.get("/")
async def root():
    return {
        "message": "Vibe Search API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/search": "Search for places",
            "/health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.post("/search", response_model=SearchResponse)
async def search_places(request: SearchRequest):
    """
    Search places function which does hybrid search -> reranker
    """
    try:
        query = request.query

        # Get CLIP (image) embedding
        inputs = processor(text=[query], return_tensors="pt", padding=True)
        clip_embedding = clip_model.get_text_features(**inputs)
        clip_embedding = clip_embedding / clip_embedding.norm(p=2, dim=-1, keepdim=True)
        clip_embedding = clip_embedding.detach().cpu().numpy().astype('float32').flatten().tolist()

        # Get SPLADE (sparse) embedding
        sparse_embedding = list(sparse_model.embed(query))
        values = sparse_embedding[0].values.tolist()
        indices = sparse_embedding[0].indices.tolist()

        # Get dense embedding
        dense_embedding = metadata_model.encode([query], normalize_embeddings=True)[0].astype('float32').tolist()

        # Async Pinecone queries
        image_q = pinecone_image_query(clip_embedding)
        sparse_q = pinecone_sparse_query(values, indices)
        dense_q = pinecone_dense_query(dense_embedding)

        image_results, sparse_results, dense_results = await asyncio.gather(image_q, sparse_q, dense_q)

        # Merge all results
        hybrid_results = merge_matches(dense_results, sparse_results, image_results)
        formatted_results = format_place_strings(hybrid_results)

        # Rerank with BGE
        reranked = pc.inference.rerank(
            model="bge-reranker-v2-m3",
            query=query,
            documents=list(formatted_results.keys()),
            top_n=15,
            return_documents=True,
        )

        # Add reranked score to places and format for LLM input
        top_places = []
        llm_input = ""

        for doc in reranked.data:
            key = doc.document.text
            original_place = formatted_results[key].copy()
            original_place["score"] = round(doc.score, 6)
            top_places.append(original_place)
            reviews = ast.literal_eval(original_place["reviews"])
            
            llm_input += f"{key}\n reviews:\n\n"

            for review in reviews[:5]:  # only first 5
                llm_input += f"- {review}\n"

            llm_input += "\n\n"
        
        # Transform into response model
        places = []
        for doc in top_places:
            place = Place(
                place_id=doc["id"],
                name=doc["name"],
                neighborhood=doc.get("neighborhood"),
                latitude=None,
                longitude=None,
                tags=None,
                description=doc.get("description"),
                reviews=doc.get("reviews"),
                emoji=doc.get("emoji"),
                score=doc.get("score")
            )
            places.append(place)
        
        prompt = (f"Summarize the following results"
          f"\nsearch_engine_results: {llm_input}"
          f"\nas if you were responding to this query:{query}"
          f"\nStart with something like 'I think you'd like the following:'"
          f"\nOnly include the top 4 results"
        )

        llm_response = llm.invoke(prompt)

        return SearchResponse(
            llm_response=llm_response.content,
            places=places,
            total_results=len(places),
            query=query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
