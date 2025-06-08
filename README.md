# Vibe Search Engine (FAISS + FastAPI)

A local semantic search engine for places, with:
- Sentence-Transformers for embeddings
- FAISS for fast similarity search
- FastAPI for backend
- JavaScript + HTML/CSS for frontend

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

## Setup Instructions

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Data Preparation
1. Place raw data files in `data/raw/`
2. Run the data preparation notebook:
```bash
jupyter notebook notebooks/01_data_preparation.ipynb
```

### Model Training
1. Run the model training notebook:
```bash
jupyter notebook notebooks/02_model_training.ipynb
```

### Running the Application

1. Start the backend server:
```bash
./scripts/run_server.sh
```

2. Start the frontend server:
```bash
cd frontend
python -m http.server 5500
```

3. Visit `http://localhost:5500` in your browser

## Features

### Hybrid Search
The application uses a sophisticated hybrid search combining:
1. Dense Semantic Search (Sentence-Transformers)
   - Understands context and meaning
   - Good for natural language queries

2. Sparse Text Search (SPLADE)
   - Excellent for keyword matching
   - Preserves important terms

3. Image Search (CLIP)
   - Visual similarity search
   - Multimodal understanding

### Configurable Weights
You can adjust search weights through the API:
- `weight_dense`: Semantic understanding (default: 0.4)
- `weight_sparse`: Keyword matching (default: 0.3)
- `weight_image`: Visual similarity (default: 0.3)

## Development

### Notebooks
The notebooks directory contains the research and development process:
1. `01_data_preparation.ipynb`: Data cleaning and preprocessing
2. `02_model_training.ipynb`: Model training and evaluation
3. `03_hybrid_search.ipynb`: Hybrid search implementation

### Adding New Features
1. Develop and test in notebooks
2. Implement in the backend
3. Update the frontend
4. Document in README

### Deployment

#### Backend (Railway)
1. Push code to GitHub
2. Connect repository to Railway
3. Set environment variables:
   - `ALLOWED_ORIGINS`: Comma-separated list of allowed origins
   - `MODEL_CACHE_DIR`: Directory for model storage
   - `PROCESSED_DATA_DIR`: Directory for processed data

#### Frontend (Vercel)
1. Push code to GitHub
2. Connect repository to Vercel
3. Set environment variables:
   - `VITE_API_URL`: Your Railway backend URL

## License
This project was developed as part of the 2025 Corner-DSC-BAC Datathon.

## Acknowledgements
Built collaboratively by:
- [Tomas Gutierrez](https://github.com/tom4sg)
- Yarden Morad
- [Robin Chen](https://github.com/localhost433)
