# Vibe Search Engine (FAISS + FastAPI)

A local semantic search engine for places, with:
- Sentence-Transformers for embeddings
- FAISS for fast similarity search
- FastAPI for backend
- JavaScript + HTML/CSS for frontend

## Project Structure
```
nyu-corner-datathon-2025/
├── data/                      # All data-related files
│   ├── raw/                  # Original, immutable data
│   │   ├── media.csv
│   │   ├── places.csv
│   │   └── reviews.csv
│   ├── processed/            # Cleaned and processed data
│   │   ├── merged.csv
│   │   └── image_embeddings.csv
│   └── models/              # Trained models and embeddings
│       ├── metadata.index
│       └── reviews.index
│
├── notebooks/               # Jupyter notebooks for development
│   ├── 01_data_preparation.ipynb
│   ├── 02_model_training.ipynb
│   └── 03_hybrid_search.ipynb
│
├── backend/                # FastAPI backend service
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py        # App setup
│   │   ├── core/          # Core functionality
│   │   │   ├── config.py
│   │   │   ├── embeddings.py
│   │   │   ├── hybrid_search.py
│   │   │   └── text_utils.py
│   │   └── api/
│   │       └── routes/
│   │           └── search.py
│   └── requirements.txt
│
├── frontend/              # Static frontend
│   ├── index.html
│   └── static/
│       ├── api.js
│       ├── ui.js
│       └── style.css
│
├── scripts/              # Utility scripts
│   ├── build_index.py   # Build FAISS indices
│   └── run_server.sh    # Launch server
│
└── README.md
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

## License
This project was developed as part of the 2025 Corner-DSC-BAC Datathon.

## Acknowledgements
Built collaboratively by:
- [Tomas Gutierrez](https://github.com/tom4sg)
- Yarden Morad
- [Robin Chen](https://github.com/localhost433)
