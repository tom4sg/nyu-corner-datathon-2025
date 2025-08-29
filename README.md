# Vibio - NYC Venue Recommendation System

**NYU x Corner Datathon 2025 - 1st Place Winner** 

A full-stack web application that provides venue recommendations for NYC using RAG with Hybrid Search & Reranking. 

<p align="center">
  <img
    src="https://github.com/user-attachments/assets/e4768aea-1311-4684-a876-a28d3377b311"
    alt="Announcement"
    width="49%"
  />
  <img
    src="https://github.com/user-attachments/assets/cdb89808-0866-4279-b391-6ca31ad25df3"
    alt="Winners"
    width="49%"
  />
</p>

Visit [Vibio](https://www.vibio.space/) to use it yourself!

## Overview

This project consists of:

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python
- **Embedding and Reranking**: 
  - CLIP for image-text embeddings
  - Sentence Transformers for dense embeddings
  - SPLADE for sparse embeddings
  - BGE Reranker for final ranking against user query
- **LLM Output**: Claude 3.5 Sonnet for natural language
- **Vector DB**: Pinecone Dense and Sparse indices
- **Deployment**: Railway (backend) + Vercel (frontend)

### Pseudocode: Hybrid Search Function
```python3
# 1. Generate embeddings
clip_embedding   = clip_model.encode_text(query)       # CLIP (image/text)
sparse_embedding = sparse_model.embed(query)           # SPLADE (sparse)
dense_embedding  = metadata_model.encode(query)        # SentenceTransformer (dense)

# 2. Query Pinecone indexes (async)
image_q  = pinecone_image_query(clip_embedding)
sparse_q = pinecone_sparse_query(sparse_embedding)
dense_q  = pinecone_dense_query(dense_embedding)

image_results, sparse_results, dense_results = await asyncio.gather(
    image_q, sparse_q, dense_q
)

# 3. Merge hybrid search results
hybrid_results = merge_matches(dense_results, sparse_results, image_results)

# 4. Rerank with BGE
reranked = pc.inference.rerank(
    model="bge-reranker-v2-m3",
    query=query,
    documents=list(hybrid_results.keys()),
    top_n=8
)
```


## Local Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- Pinecone API key
- Anthropic API key

### Backend

1. **Navigate to backend:**
```bash
cd backend
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set environment variables:**
```bash
PINECONE_API_KEY=your_pinecone_api_key
PERSONAL_ANTHROPIC=your_anthropic_api_key
```

4. **Run the server:**
```bash
uvicorn main:app --reload
```

### Frontend

1. **Navigate to frontend:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Set environment variables:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. **Run the development server:**
```bash
npm run dev
```

## API Endpoints

### Search
```http
POST /search
Content-Type: application/json

{
  "query": "where to drink a matcha"
}
```

**Response:**
```json
{
  "llm_response": "I think you'd like the following:\n\n1. Matcha Bar NYC in East Village: This cozy matcha cafe offers traditional Japanese vibes with excellent matcha drinks and a serene atmosphere perfect for relaxing or studying.\n\n2. Cha Cha Matcha in SoHo: Known for their Instagram-worthy matcha creations and trendy atmosphere.\n\n3. Matchaful in West Village: Offers high-quality ceremonial grade matcha with a minimalist aesthetic.\n\nThese spots all offer authentic matcha experiences with different vibes - from traditional to trendy. Perfect for matcha enthusiasts!",
  "places": [
    {
      "place_id": "venue_123",
      "name": "Matcha Bar NYC",
      "neighborhood": "East Village",
      "description": "Cozy matcha cafe with traditional Japanese vibes",
      "reviews": "['Amazing matcha quality', 'Great atmosphere for studying', 'Authentic Japanese experience']",
      "emoji": "🍵",
      "score": 0.95
    }
  ],
  "total_results": 15,
  "query": "where to drink a matcha"
}
```

### Health
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "API is running"
}
```

## Deployment

### Backend (Railway)
The backend is automatically deployed to Railway with the configuration in `railway.json`.

### Frontend (Vercel)
The frontend can be deployed to Vercel with the configuration in `vercel.json`.

## Original Solution

The original datathon solution was implemented in Jupyter Notebook (`datathon.ipynb`) and demonstrated:

- RAG recommendation system for NYC venues
- Hybrid dense and sparse search
- Image-text understanding with CLIP
- FAISS index for vector storage and retrieval

### Demo Video

https://github.com/user-attachments/assets/d139b7e4-dce4-49a3-95ab-e7e8c6897689
