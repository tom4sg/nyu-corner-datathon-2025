"""
First, Let's load Image Embeddings to a Pinecone Index
"""
#%%

from dotenv import load_dotenv
load_dotenv()

#%%

import os
import pandas as pd
from pinecone.grpc import PineconeGRPC as Pinecone

#%%

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
image_index = pc.Index("corner-clip")

#%%

image_df = pd.read_csv('datasets/image_embeddings_sorted.csv')
merged_df = pd.read_csv('datasets/processed/merged.csv')
full_df = pd.merge(merged_df, image_df, on="place_id", how="inner")
full_df.head()

# %%

embedding_cols = [col for col in full_df.columns if col.startswith('embed_')]

# %%

from tqdm import tqdm

# Batch upload to Pinecone
batch_size = 100
vectors = []

for i, row in tqdm(full_df.iterrows(), total=len(full_df)):

    raw_tags = row.get("tags")
    if isinstance(raw_tags, str) and raw_tags.startswith("{") and raw_tags.endswith("}"):
        tags = [tag.strip() for tag in raw_tags[1:-1].split(",")]
    else:
        tags = []

    metadata_dict = {
    "name": row.get("name"),
    "neighborhood": row.get("neighborhood"),
    "latitude": row.get("latitude"),
    "longitude": row.get("longitude"),
    "tags": tags,
    "description": row.get("short_description"),
    "emoji": row.get("emoji"),
    }

    # Filter out null values, but handle tags (a list) separately
    metadata = {
        k: v for k, v in metadata_dict.items()
        if (isinstance(v, list) and len(v) > 0) or (not isinstance(v, list) and pd.notna(v))
    }
    vectors.append({
        "id": str(row["place_id"]),
        "values": row[embedding_cols].to_numpy(dtype="float32").tolist(),
        "metadata": metadata
    })

    # Upload every `batch_size` entries
    if len(vectors) == batch_size or i == len(full_df) - 1:
        image_index.upsert(vectors=vectors, namespace="images")
        vectors = []

# %%

print(image_index.describe_index_stats())

# %%
"""
Let's test searching the index
"""
from transformers import CLIPProcessor, CLIPModel

# Load the CLIP model and processor
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")

#%%

query = "Day time"

inputs = processor(text=[query], return_tensors="pt", padding=True)
query_embedding = clip_model.get_text_features(**inputs)
query_embedding = query_embedding / query_embedding.norm(p=2, dim=-1, keepdim=True)
query_embedding = query_embedding.detach().cpu().numpy().astype('float32').flatten().tolist()

#%%

results = image_index.query(
    namespace="images", 
    vector=query_embedding, 
    top_k=5,
    include_metadata=True,
    include_values=False
)
# %%

print(results)

# %%
"""
Time to load the metadata index
"""
import ast

merged_df["dense_metadata_embedding"] = merged_df["dense_metadata_embedding"].apply(ast.literal_eval)

#%%

dense_index = pc.Index("corner-metadata-dense")

#%%

batch_size = 100
vectors = []

for i, row in tqdm(merged_df.iterrows(), total=len(merged_df)):

    raw_tags = row.get("tags")
    if isinstance(raw_tags, str) and raw_tags.startswith("{") and raw_tags.endswith("}"):
        tags = [tag.strip() for tag in raw_tags[1:-1].split(",")]
    else:
        tags = []

    metadata_dict = {
    "name": row.get("name"),
    "neighborhood": row.get("neighborhood"),
    "latitude": row.get("latitude"),
    "longitude": row.get("longitude"),
    "tags": tags,
    "description": row.get("short_description"),
    "emoji": row.get("emoji"),
    }

    # Filter out null values, but handle tags (a list) separately
    metadata = {
        k: v for k, v in metadata_dict.items()
        if (isinstance(v, list) and len(v) > 0) or (not isinstance(v, list) and pd.notna(v))
    }
    vectors.append({
        "id": str(row["place_id"]),
        "values": row.get("dense_metadata_embedding"),
        "metadata": metadata
    })

    # Upload every `batch_size` entries
    if len(vectors) == batch_size or i == len(merged_df) - 1:
        dense_index.upsert(vectors=vectors, namespace="metadata")
        vectors = []

#%%

print(dense_index.describe_index_stats())

#%%

from sentence_transformers import SentenceTransformer
metadata_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# %%

query = "pub"
query_embedding = metadata_model.encode([query], normalize_embeddings=True)[0].astype('float32').reshape(1, -1)
query_embedding = query_embedding.flatten().tolist()

print(query_embedding)

#%%

results = dense_index.query(
    namespace="metadata", 
    vector=query_embedding, 
    top_k=5,
    include_metadata=True,
    include_values=False
)
# %%

print(results)

# %%
"""
Let's load metadata sparse embeddings
"""
import re
import ast

def extract_sparse_embedding(sparse_str):
    """Extracts values and indices from a stringified SparseEmbedding object."""
    values_match = re.search(r'values=array\((\[.*?\])', sparse_str, re.DOTALL)
    indices_match = re.search(r"indices=array\((\[.*?\])", sparse_str, re.DOTALL)

    if not values_match or not indices_match:
        raise ValueError("SparseEmbedding string is not in the expected format.")

    values = ast.literal_eval(values_match.group(1))
    indices = ast.literal_eval(indices_match.group(1))

    return {"values": values, "indices": indices}

# %%

sparse_index = pc.Index("corner-metadata-sparse")

#%%

batch_size = 100
vectors = []

for i, row in tqdm(merged_df.iterrows(), total=len(merged_df)):

    raw_tags = row.get("tags")
    if isinstance(raw_tags, str) and raw_tags.startswith("{") and raw_tags.endswith("}"):
        tags = [tag.strip() for tag in raw_tags[1:-1].split(",")]
    else:
        tags = []

    metadata_dict = {
    "name": row.get("name"),
    "neighborhood": row.get("neighborhood"),
    "latitude": row.get("latitude"),
    "longitude": row.get("longitude"),
    "tags": tags,
    "description": row.get("short_description"),
    "emoji": row.get("emoji"),
    }

    # Filter out null values, but handle tags (a list) separately
    metadata = {
        k: v for k, v in metadata_dict.items()
        if (isinstance(v, list) and len(v) > 0) or (not isinstance(v, list) and pd.notna(v))
    }

    sparse = extract_sparse_embedding(row.get("sparse_metadata_embedding"))

    vectors.append({
        "id": str(row["place_id"]),
       "sparse_values": {
                "values": sparse["values"],
                "indices": sparse["indices"]
            },
        "metadata": metadata
    })

    # Upload every `batch_size` entries
    if len(vectors) == batch_size or i == len(merged_df) - 1:
        sparse_index.upsert(vectors=vectors, namespace="metadata")
        vectors = []

#%%

print(sparse_index.describe_index_stats())

# %%

from fastembed import SparseTextEmbedding
sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")

# %%

query = "sports bar"
sparse_embedding = list(sparse_model.embed(query))
values = sparse_embedding[0].values.tolist()
indices = sparse_embedding[0].indices.tolist()

#%%

results = sparse_index.query(
    namespace="metadata",
    sparse_vector={
      "values": values,
      "indices": indices
    }, 
    top_k=5,
    include_metadata=True,
    include_values=False
)
# %%

print(results)

#%%

from typing import List, Dict

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

    # Deduplicate by 'id', keeping highest-score version (optional, still helpful)
    merged = {}
    for match in all_matches:
        match_id = match["id"]
        if match_id not in merged or match["score"] > merged[match_id]["score"]:
            merged[match_id] = match

    # No sorting here — reranker decides final order
    formatted_results = []
    for match in merged.values():
        meta = match.get("metadata", {})
        formatted_results.append({
            "id": match["id"],
            "name": meta.get("name"),
            "neighborhood": meta.get("neighborhood"),
            "description": meta.get("description"),
            "emoji": meta.get("emoji"),
            "score": match["score"]  # Keep original for context if needed
        })

    return formatted_results

# %%
"""
We have loaded all the indices! Let's try to figure out a hybrid search methodology
"""

query = "coffee upper west side"

inputs = processor(text=[query], return_tensors="pt", padding=True)
query_embedding = clip_model.get_text_features(**inputs)
query_embedding = query_embedding / query_embedding.norm(p=2, dim=-1, keepdim=True)
query_embedding = query_embedding.detach().cpu().numpy().astype('float32').flatten().tolist()

image_results = image_index.query(
    namespace="images", 
    vector=query_embedding, 
    top_k=20,
    include_metadata=True,
    include_values=False
)

sparse_embedding = list(sparse_model.embed(query))
values = sparse_embedding[0].values.tolist()
indices = sparse_embedding[0].indices.tolist()


sparse_results = sparse_index.query(
    namespace="metadata",
    sparse_vector={
      "values": values,
      "indices": indices
    }, 
    top_k=20,
    include_metadata=True,
    include_values=False
)

query_embedding = metadata_model.encode([query], normalize_embeddings=True)[0].astype('float32').reshape(1, -1)
query_embedding = query_embedding.flatten().tolist()

dense_results = dense_index.query(
    namespace="metadata", 
    vector=query_embedding, 
    top_k=20,
    include_metadata=True,
    include_values=False
)
# %%

hybrid_results = merge_matches(dense_results, sparse_results, image_results)
print(hybrid_results)

#%%

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

# Example usage
formatted_results = format_place_strings(hybrid_results)
print(formatted_results.keys())

# %%

reranked_results = pc.inference.rerank(
    model="bge-reranker-v2-m3",
    query=query,
    documents=list(formatted_results.keys()),
    top_n=10,
    return_documents=True,
)

print(reranked_results)
# %%
from pprint import pprint

top_places = [] 
for doc in reranked_results.data:
    key = doc.document.text
    original_place = formatted_results[key].copy()  # Avoid mutating original dict
    original_place["score"] = round(doc.score, 6)  # Replace with rerank score
    top_places.append(original_place)


#%%




top_places = [formatted_results[doc.document.text] for doc in reranked_results.data]
pprint(top_places)
# %%
