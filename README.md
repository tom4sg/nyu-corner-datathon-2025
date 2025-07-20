# NYU x Corner Datathon 2025 Solution
Won 1st place in NYU DSC 2025 Datathon - This notebook implements the solution: A RAG recommendation system in Python to match open-ended user queries with NYC
venues using structured tags, reviews, and image data.
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

---

### Usage Examples

```python
# Basic dense search
results = search_places_dense_metadata("where to drink a matcha", top_k=5)

# Sparse search for specific terms
results = search_places_sparse_metadata("dance-y bars that have disco balls", top_k=5)

# Full hybrid search
results = hybrid_search(
    query="what should I do this weekend",
    metadata_index=index_dense_metadata,
    image_index=index_image,
    sparse_embeddings=sparse_embeddings_dense,
    metadata_model=metadata_model,
    sparse_model=sparse_model,
    processor=processor,
    clip_model=clip_model,
    weight_dense=0.4,
    weight_sparse=0.3,
    weight_image=0.3
)
```

### Dependencies

```python
sentence_transformers
fastembed
transformers
faiss-cpu
scikit-learn
pandas
numpy
tqdm
spacy
joblib
pathlib
```
---
https://github.com/user-attachments/assets/d139b7e4-dce4-49a3-95ab-e7e8c6897689
