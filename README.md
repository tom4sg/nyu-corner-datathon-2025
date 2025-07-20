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

Visit [Vibio](https://nyu-corner-datathon-2025-7yn3.vercel.app/) to experience the intelligent venue search system.

## Architecture

This project consists of:

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python
- **AI Models**: 
  - CLIP for image-text understanding
  - Sentence Transformers for dense embeddings
  - SPLADE for sparse embeddings
  - BGE Reranker for final ranking
- **Vector Database**: Pinecone for efficient similarity search
- **Deployment**: Railway (backend) + Vercel (frontend)

## Tech Stack

### Backend
```python
fastapi
uvicorn
sentence-transformers
fastembed
transformers
pinecone
pydantic
python-dotenv
```

### Frontend
```json
next.js
react
typescript
tailwindcss
```

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Pinecone API key

### Backend Setup

1. **Clone and navigate to backend:**
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
```

4. **Run the server:**
```bash
uvicorn main:app --reload
```

### Frontend Setup

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

## 🔍 How It Works

### Hybrid Search Architecture

The system uses a sophisticated three-tier search approach:

1. **Dense Search**: Uses sentence transformers to capture semantic meaning
2. **Sparse Search**: Uses SPLADE to capture specific keywords and phrases  
3. **Image Search**: Uses CLIP to understand visual context from venue images

### Search Process

```python
# Example of the hybrid search process
query = "romantic dinner with city views"

# 1. Generate embeddings for all three modalities
clip_embedding = clip_model.encode_text(query)
dense_embedding = metadata_model.encode(query)
sparse_embedding = sparse_model.encode(query)

# 2. Search across all indices
image_results = image_index.query(clip_embedding)
dense_results = dense_index.query(dense_embedding)
sparse_results = sparse_index.query(sparse_embedding)

# 3. Merge and rerank results
final_results = rerank(merge_results(image_results, dense_results, sparse_results))
```

## API Endpoints

### Search Places
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
  "places": [
    {
      "place_id": "venue_123",
      "name": "Matcha Bar NYC",
      "neighborhood": "East Village",
      "description": "Cozy matcha cafe with traditional Japanese vibes",
      "emoji": "🍵",
      "score": 0.95
    }
  ],
  "total_results": 15,
  "query": "where to drink a matcha"
}
```

### Health Check
```http
GET /health
```

## Features

- **Natural Language Search**: Search using conversational queries
- **Multi-modal Understanding**: Combines text, image, and metadata analysis
- **Intelligent Ranking**: Advanced reranking using BGE model
- **Real-time Results**: Fast search with sub-second response times
- **Modern UI**: Clean, responsive interface built with Next.js and Tailwind

## 📁 Project Structure

```
corner-datathon/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── Procfile            # Railway deployment config
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js app directory
│   │   ├── components/     # React components
│   │   └── types/          # TypeScript definitions
│   ├── package.json        # Node.js dependencies
│   └── next.config.ts      # Next.js configuration
├── datasets/               # Data files
├── datathon.ipynb         # Original Jupyter notebook
└── README.md              # This file
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
- Advanced ranking algorithms

This web application brings that solution to life with a production-ready interface.

---

## Demo Video

https://github.com/user-attachments/assets/d139b7e4-dce4-49a3-95ab-e7e8c6897689
