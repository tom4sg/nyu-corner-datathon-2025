import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pydantic import BaseModel, Field
from places_data import (
    Recommendation,
    build_place_fields,
    markdown_response,
    message_text,
    review_snippet,
    split_recommendations,
)
from transformers import CLIPProcessor, CLIPModel
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from pinecone import Pinecone
from langchain_anthropic import ChatAnthropic
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import ast

import logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Let's first define the pydantic models for searching and returning

class SearchRequest(BaseModel):
    query: str
    mode: str
    exclude_ids: List[str] = Field(default_factory=list)

class Place(BaseModel):
    place_id: str
    name: str
    neighborhood: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    reviews: Optional[str] = None
    review_snippet: Optional[str] = None
    emoji: Optional[str] = None
    score: float
    image_urls: List[str] = Field(default_factory=list)
    maps_url: Optional[str] = None
    reviews_url: Optional[str] = None
    google_rating: Optional[float] = None
    google_review_count: Optional[int] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    hours_today: Optional[str] = None
    open_now: Optional[bool] = None

class SearchResponse(BaseModel):
    llm_response: str
    intro: Optional[str] = None
    outro: Optional[str] = None
    recommendations: List[Recommendation] = Field(default_factory=list)
    places: List[Place]
    total_results: int
    query: str

# Let's load the LLM with LangChain

llm = ChatAnthropic(
    model="claude-sonnet-4-5-20250929",
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
    allow_origins=[
        "https://www.vibio.space",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get access to the specific indices in pinecone
try:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    logging.info("Image index initializing...")
    image_index = pc.Index("corner-clip")
    
    logging.info("Dense index initializing...")
    dense_index = pc.Index("corner-metadata-dense")
    
    logging.info("Sparse index initializing...")
    sparse_index = pc.Index("corner-metadata-sparse")
    
    logging.info("All indexes initialized.")
    
except Exception:
    logging.exception("Could not initialize Pinecone")
    raise

# Load the models
try:
    logging.info("Loading CLIP processor...")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    logging.info("Loading CLIP model...")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")

    logging.info("Loading dense model...")
    metadata_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    logging.info("Loading sparse model...")
    sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")

    logging.info("All models loaded.")

except Exception:
    logging.exception("Could not load models")
    raise


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
            "latitude": meta.get("latitude"),
            "longitude": meta.get("longitude"),
            "tags": meta.get("tags"),
            "score": match["score"]
        })

    return formatted_results

def format_place_strings_deep(places: List[Dict]) -> Dict[str, Dict]:
    rerank_map = {}
    for place in places:
        name = place.get("name", "Unknown")
        emoji = place.get("emoji", "")
        neighborhood = place.get("neighborhood", "Unknown area")
        desc = place.get("description", "No description")

        key = f"{emoji} {name} ({neighborhood}) — {desc}"
        rerank_map[key] = place
    return rerank_map

def format_place_strings_quick(places: List[Dict]) -> Dict[str, Dict]:
    rerank_map = {}
    for place in places.matches:
        name = place["metadata"].get("name", "Unknown")
        emoji = place["metadata"].get("emoji", "")
        neighborhood = place["metadata"].get("neighborhood", "Unknown area")
        desc = place["metadata"].get("description", "No description")

        key = f"{emoji} {name} ({neighborhood}) — {desc}"
        rerank_map[key] = place
    return rerank_map


# Define Async Pinecone query functions per index
executor = ThreadPoolExecutor()

def candidate_count(exclude_ids: List[str]) -> int:
    if not exclude_ids:
        return 10
    return min(len(exclude_ids) + 16, 100)


def result_id(value) -> str:
    if isinstance(value, dict):
        return str(value.get("id") or "")
    return str(getattr(value, "id", "") or "")


def without_excluded(results: Dict[str, Dict], exclude_ids: List[str]) -> Dict[str, Dict]:
    excluded = set(exclude_ids)
    if not excluded:
        return results
    return {key: value for key, value in results.items() if result_id(value) not in excluded}


def places_only(query: str, top_places: List[dict]) -> SearchResponse:
    places = [place_from_doc(doc, query) for doc in top_places]
    return SearchResponse(
        llm_response="",
        places=places,
        total_results=len(places),
        query=query,
    )


async def pinecone_image_query(clip_embedding, top_k=10):
    return await asyncio.get_event_loop().run_in_executor(executor, lambda: (
        image_index.query(
            namespace="images", 
            vector=clip_embedding, 
            top_k=top_k,
            include_metadata=True,
            include_values=False
        )
    ))

async def pinecone_sparse_query(values, indices, top_k=10):
    return await asyncio.get_event_loop().run_in_executor(executor, lambda: (
        sparse_index.query(
            namespace="metadata", 
            sparse_vector={"values": values, "indices": indices},
            top_k=top_k,
            include_metadata=True,
            include_values=False
        )
    ))

async def pinecone_dense_query(dense_embedding, top_k=10):
    return await asyncio.get_event_loop().run_in_executor(executor, lambda: (
        dense_index.query(
            namespace="metadata", 
            vector=dense_embedding, 
            top_k=top_k,
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

        exclude_ids = request.exclude_ids or []
        summarize = not exclude_ids
        if request.mode == "deep":
            return await run_hybrid_search(query, exclude_ids, summarize)
        elif request.mode == "quick":
            return await run_quick_search(query, exclude_ids, summarize)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid mode: {request.mode}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

def place_from_doc(doc: dict, query: str) -> Place:
    fields = build_place_fields(doc)
    snippet = review_snippet(review_lines(fields.get("reviews")), query)
    return Place(**fields, review_snippet=snippet)


def review_lines(raw) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(review) for review in raw]
    try:
        parsed = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return []
    if isinstance(parsed, list):
        return [str(review) for review in parsed]
    return []


async def summarize_places(query: str, top_places: List[dict]):
    llm_input = ""
    for place in top_places:
        name = place.get("name", "Unknown")
        emoji = place.get("emoji", "")
        neighborhood = place.get("neighborhood", "Unknown area")
        desc = place.get("description", "No description")
        llm_input += f"{emoji} {name} ({neighborhood}) — {desc}\n reviews:\n\n"

        for review in review_lines(place.get("reviews"))[:3]:  # only first 3
            llm_input += f"- {review}\n"

        llm_input += "\n\n"

    prompt = (f"Summarize the following results"
        f"\nsearch_engine_results: {llm_input}"
        f"\nas if you were responding to this query:{query}"
        f"\nStart with something like 'I think you'd like the following:'"
        f"\nOnly talk about the top 3 results"
        f"\nBegin the part about each place on its own line with just the place's name in double square brackets, like [[Name]]"
        f"\nIf you add any closing remarks, put them after a final [[end]]"
    )

    message = await asyncio.get_event_loop().run_in_executor(executor, lambda: llm.invoke(prompt))
    content = message_text(message)
    intro, picks, outro = split_recommendations(content, top_places)
    if not picks:
        logging.warning("Could not split the LLM response by place")
        return content, content, [], ""
    if not intro:
        intro = "I think you'd like the following:"
    names = {place.get("id"): place.get("name") or place.get("id") for place in top_places}
    recommendations = [Recommendation(**pick) for pick in picks]
    return intro, markdown_response(intro, picks, names, outro), recommendations, outro


async def respond_with_places(query: str, top_places: List[dict]) -> SearchResponse:
    places = [place_from_doc(doc, query) for doc in top_places]
    intro, llm_text, recommendations, outro = await summarize_places(query, top_places)

    shown_intro = None if not recommendations else intro
    return SearchResponse(
        llm_response=llm_text,
        intro=shown_intro,
        outro=outro or None,
        recommendations=recommendations,
        places=places,
        total_results=len(places),
        query=query,
    )


def reranked_document_text(doc) -> str:
    document = doc.get("document") if isinstance(doc, dict) else getattr(doc, "document", None)
    if isinstance(document, dict):
        return document.get("text") or ""
    if isinstance(document, str):
        return document
    return getattr(document, "text", "") or ""


def reranked_score(doc) -> float:
    score = doc.get("score") if isinstance(doc, dict) else getattr(doc, "score", 0)
    return round(float(score or 0), 6)


async def run_hybrid_search(query: str, exclude_ids: Optional[List[str]] = None, summarize: bool = True):
    """
    Run the deep/hybrid search with CLIP, SPLADE, and dense embeddings
    """
    try:
        # Get CLIP (image) embedding
        inputs = processor(text=[query], return_tensors="pt", padding=True)
        clip_output = clip_model.get_text_features(**inputs)
        
        # Extract tensor from output if it's a BaseModelOutputWithPooling object
        if hasattr(clip_output, 'pooler_output') and clip_output.pooler_output is not None:
            clip_embedding = clip_output.pooler_output
        elif hasattr(clip_output, 'last_hidden_state'):
            # Use mean pooling if we only have last_hidden_state
            clip_embedding = clip_output.last_hidden_state.mean(dim=1)
        else:
            # Assume it's already a tensor (older behavior)
            clip_embedding = clip_output
        
        clip_embedding = clip_embedding / clip_embedding.norm(p=2, dim=-1, keepdim=True)
        clip_embedding = clip_embedding.detach().cpu().numpy().astype('float32').flatten().tolist()

        # Get SPLADE (sparse) embedding
        sparse_embedding = list(sparse_model.embed(query))
        values = sparse_embedding[0].values.tolist()
        indices = sparse_embedding[0].indices.tolist()

        # Get dense embedding
        dense_embedding = metadata_model.encode([query], normalize_embeddings=True)[0].astype('float32').tolist()
        top_k = candidate_count(exclude_ids or [])

        # Async Pinecone queries
        image_q = pinecone_image_query(clip_embedding, top_k)
        sparse_q = pinecone_sparse_query(values, indices, top_k)
        dense_q = pinecone_dense_query(dense_embedding, top_k)

        image_results, sparse_results, dense_results = await asyncio.gather(image_q, sparse_q, dense_q)

        # Merge all results
        hybrid_results = merge_matches(dense_results, sparse_results, image_results)
        formatted_results = without_excluded(format_place_strings_deep(hybrid_results), exclude_ids or [])
        if not formatted_results:
            return places_only(query, [])

        # Rerank with BGE
        reranked = pc.inference.rerank(
            model="bge-reranker-v2-m3",
            query=query,
            documents=list(formatted_results.keys()),
            top_n=min(8, len(formatted_results)),
            return_documents=True,
        )

        top_places = []
        for doc in reranked.data:
            key = reranked_document_text(doc)
            original_place = formatted_results[key].copy()
            original_place["score"] = reranked_score(doc)
            top_places.append(original_place)

        if not summarize:
            return places_only(query, top_places)
        return await respond_with_places(query, top_places)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deep Search failed: {str(e)}")
    
    

async def run_quick_search(query: str, exclude_ids: Optional[List[str]] = None, summarize: bool = True):
    """
    Run quick search - placeholder for you to fill in
    """
    try:
        dense_embedding = metadata_model.encode([query], normalize_embeddings=True)[0].astype('float32').tolist()
        dense_q = await pinecone_dense_query(dense_embedding, candidate_count(exclude_ids or []))
        formatted_results = without_excluded(format_place_strings_quick(dense_q), exclude_ids or [])
        if not formatted_results:
            return places_only(query, [])

        reranked = pc.inference.rerank(
            model="bge-reranker-v2-m3",
            query=query,
            documents=list(formatted_results.keys()),
            top_n=min(8, len(formatted_results)),
            return_documents=True,
        )

        top_places = []
        for doc in reranked.data:
            key = reranked_document_text(doc)
            original_place = formatted_results[key]["metadata"].copy()
            original_place["id"] = formatted_results[key]["id"]
            original_place["score"] = reranked_score(doc)
            top_places.append(original_place)

        if not summarize:
            return places_only(query, top_places)
        return await respond_with_places(query, top_places)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick Search failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
