# scripts/build_index.py

import pandas as pd
import numpy as np
from tqdm import tqdm
tqdm.pandas()
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import torch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.core.text_utils import combining_text, concat_reviews
from app.core.embeddings import load_model, encode_texts, embed_and_pool, chunk_by_tokens
from app.core.faiss_io import build_faiss_index, save_faiss_index
from app.core.config import settings

# Import new embedding models
from fastembed import SparseTextEmbedding
from transformers import CLIPProcessor, CLIPModel
from sentence_transformers import SentenceTransformer

# Paths
RAW_MEDIA = settings.RAW_MEDIA_PATH
RAW_PLACES = settings.RAW_PLACES_PATH
RAW_REVIEWS = settings.RAW_REVIEWS_PATH
PROCESSED_CSV = settings.PROCESSED_CSV_PATH
DENSE_INDEX_PATH = Path(__file__).resolve().parents[1] / "data/indices/dense.index"
SPARSE_INDEX_PATH = Path(__file__).resolve().parents[1] / "data/indices/sparse.index"
IMAGE_INDEX_PATH = Path(__file__).resolve().parents[1] / "data/indices/image.index"

# Initialize models
def init_models(device='cuda' if torch.cuda.is_available() else 'cpu'):
    print("Initializing models...")
    dense_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device=device)
    sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    return dense_model, sparse_model, clip_processor, clip_model

# Helpers
def parallel_apply(df, func, workers=4):
    """Apply a function in parallel to each row of the DataFrame."""
    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(func, [row for _, row in df.iterrows()]))
    return results

def load_data():
    """Load datasets from CSV files."""
    print("Loading datasets...")
    media_df = pd.read_csv(RAW_MEDIA)
    places_df = pd.read_csv(RAW_PLACES)
    reviews_df = pd.read_csv(RAW_REVIEWS)
    
    # Also load image embeddings if available
    image_embeddings_path = Path(__file__).resolve().parents[1] / "data/processed/image_embeddings_sorted.csv"
    image_df = pd.read_csv(image_embeddings_path) if image_embeddings_path.exists() else None
    
    return media_df, places_df, reviews_df, image_df

def prepare_merge_df(media_df, places_df, reviews_df):
    """Prepare the merged DataFrame."""
    print("Processing datasets...")
    reviews_df = reviews_df.drop_duplicates(subset=['place_id', 'review_text'])
    media_df = media_df.drop_duplicates(subset=['place_id', 'media_url'])

    # Aggregate reviews and media
    reviews_agg = reviews_df.groupby('place_id')['review_text'].apply(list).reset_index()
    media_agg = media_df.groupby('place_id')['media_url'].apply(list).reset_index()

    # Merge everything
    merge_df = places_df.merge(media_agg, on='place_id', how='inner')
    merge_df = merge_df.merge(reviews_agg, on='place_id', how='inner')
    
    # Add concatenated reviews
    agg_reviews = reviews_df.groupby('place_id')['review_text'].apply(concat_reviews).reset_index(name='concat_reviews')
    merge_df = merge_df.merge(agg_reviews, on='place_id', how='left')
    
    merge_df = merge_df.drop_duplicates(subset='place_id').reset_index(drop=True)
    
    # Combine text fields
    print("Combining text fields...")
    merge_df['combined_text'] = merge_df.apply(combining_text, axis=1)
    
    return merge_df

def generate_embeddings(merge_df, dense_model, sparse_model, image_df=None):
    """Generate all types of embeddings."""
    print("Generating embeddings...")
    batch_size = 32
    
    # Dense embeddings
    print("Generating dense embeddings...")
    dense_embeddings = []
    for i in tqdm(range(0, len(merge_df), batch_size), desc="Dense embeddings"):
        batch = merge_df['combined_text'].iloc[i:i + batch_size].tolist()
        batch_embeddings = dense_model.encode(batch, normalize_embeddings=True)
        dense_embeddings.append(batch_embeddings)
    dense_embeddings = np.vstack(dense_embeddings)
    merge_df['dense_metadata_embedding'] = dense_embeddings.tolist()

    # Sparse embeddings
    print("Generating sparse embeddings...")
    sparse_embeddings = []
    for i in tqdm(range(0, len(merge_df), batch_size), desc="Sparse embeddings"):
        batch = merge_df['combined_text'].iloc[i:i + batch_size].tolist()
        batch_embeddings = list(sparse_model.embed(batch))
        sparse_embeddings.extend(batch_embeddings)
    merge_df['sparse_metadata_embedding'] = sparse_embeddings

    # Add image embeddings if available
    if image_df is not None:
        print("Adding image embeddings...")
        merge_df = merge_df.merge(
            image_df[['place_id', 'image_embedding']], 
            on='place_id', 
            how='left'
        )
    
    return merge_df

def build_and_save_indices(merge_df):
    """Build and save all FAISS indices."""
    print("Building and saving indices...")
    
    # Dense index
    dense_embeddings = np.array(merge_df['dense_metadata_embedding'].tolist(), dtype='float32')
    dense_index = build_faiss_index(dense_embeddings)
    save_faiss_index(dense_index, DENSE_INDEX_PATH)
    
    # Sparse index (convert sparse to dense for FAISS)
    sparse_embeddings = np.array([
        sparse_to_dense(emb, dim=30315) for emb in merge_df['sparse_metadata_embedding']
    ], dtype='float32')
    sparse_index = build_faiss_index(sparse_embeddings)
    save_faiss_index(sparse_index, SPARSE_INDEX_PATH)
    
    # Image index if available
    if 'image_embedding' in merge_df.columns:
        image_embeddings = np.array(merge_df['image_embedding'].tolist(), dtype='float32')
        image_index = build_faiss_index(image_embeddings)
        save_faiss_index(image_index, IMAGE_INDEX_PATH)

def sparse_to_dense(sparse_embedding, dim=30315):
    """Convert sparse embedding to dense vector."""
    dense_vec = np.zeros(dim, dtype=np.float32)
    dense_vec[sparse_embedding.indices] = sparse_embedding.values
    return dense_vec

def save_processed_csv(merge_df):
    """Save the processed DataFrame."""
    print(f"Saving processed CSV at {PROCESSED_CSV}...")
    PROCESSED_CSV.parent.mkdir(exist_ok=True, parents=True)
    merge_df.to_csv(PROCESSED_CSV, index=False)

def main():
    # Initialize models
    dense_model, sparse_model, clip_processor, clip_model = init_models()
    
    # Load datasets
    media_df, places_df, reviews_df, image_df = load_data()
    
    # Prepare merged DataFrame
    merge_df = prepare_merge_df(media_df, places_df, reviews_df)
    
    # Generate all embeddings
    merge_df = generate_embeddings(merge_df, dense_model, sparse_model, image_df)
    
    # Build and save indices
    build_and_save_indices(merge_df)
    
    # Save processed CSV
    save_processed_csv(merge_df)
    
    print("Index building completed successfully.")

if __name__ == "__main__":
    main()
