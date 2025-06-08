# NYU Corner - Intelligent Place Discovery

A sophisticated place recommendation system that uses hybrid search combining dense embeddings, sparse embeddings, and image-based search to help NYU students discover places around campus.

## Features

- **Hybrid Search System**:
  - Dense Embeddings (Semantic Search)
  - Sparse Embeddings (Keyword Search)
  - Image-Based Search
  - Configurable weights for each search type

- **Modern Tech Stack**:
  - FastAPI Backend
  - Static Frontend
  - FAISS for Vector Search
  - Sentence Transformers
  - SPLADE for Sparse Embeddings
  - CLIP for Image Understanding

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   └── core/
│   ├── Dockerfile
│   ├── Procfile
│   └── requirements.txt
├── frontend/
│   ├── static/
│   │   ├── api.js
│   │   ├── style.css
│   │   └── ui.js
│   └── index.html
├── data/
│   ├── raw/
│   ├── processed/
│   └── models/
└── scripts/
    └── build_index.py
```

## Local Development

1. **Setup Python Environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt
   ```

2. **Prepare Data**:
   ```bash
   python scripts/build_index.py
   ```

3. **Run Backend**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

4. **Run Frontend**:
   Serve the frontend directory using any static file server

## Deployment

### Backend (Railway)

1. Push code to GitHub
2. Connect repository to Railway
3. Set environment variables:
   - `ALLOWED_ORIGINS`: Comma-separated list of allowed origins
   - `MODEL_CACHE_DIR`: Directory for model storage
   - `PROCESSED_DATA_DIR`: Directory for processed data

### Frontend (Vercel)

1. Push code to GitHub
2. Connect repository to Vercel
3. Set environment variables:
   - `VITE_API_URL`: Your Railway backend URL

## API Documentation

Access the API documentation at `/docs` when running the backend server.

### Search Endpoint

`GET /search`

Parameters:
- `q`: Search query (required)
- `top_k`: Number of results (default: 10)
- `weight_dense`: Weight for dense embeddings (0.0-1.0)
- `weight_sparse`: Weight for sparse embeddings (0.0-1.0)
- `weight_image`: Weight for image embeddings (0.0-1.0)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
