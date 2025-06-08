import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
import faiss
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from transformers import CLIPProcessor, CLIPModel

def normalize_scores(scores):
    """Normalize scores between 0 and 1"""
    scores = np.array(scores).reshape(-1, 1)
    scaler = MinMaxScaler()
    return scaler.fit_transform(scores).flatten()

def sparse_to_dense(sparse_embedding, dim=30315):
    """Convert sparse embedding to dense vector"""
    dense_vec = np.zeros(dim, dtype=np.float32)
    dense_vec[sparse_embedding.indices] = sparse_embedding.values
    return dense_vec

class HybridSearchEngine:
    def __init__(self, metadata_df):
        self.metadata_df = metadata_df
        
        # Initialize models
        self.metadata_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        
        # Initialize indices and embeddings
        self._initialize_indices()
    
    def _initialize_indices(self):
        """Initialize FAISS indices and embeddings"""
        # Dense metadata embeddings
        dense_embeddings = []
        batch_size = 32
        for i in range(0, len(self.metadata_df), batch_size):
            batch = self.metadata_df['combined_text'].iloc[i:i + batch_size].tolist()
            batch_embeddings = self.metadata_model.encode(batch, normalize_embeddings=True)
            dense_embeddings.append(batch_embeddings)
        self.dense_embeddings = np.vstack(dense_embeddings)
        
        # Create dense FAISS index
        d = self.dense_embeddings.shape[1]
        self.dense_index = faiss.IndexFlatL2(d)
        self.dense_index.add(self.dense_embeddings.astype('float32'))
        
        # Sparse embeddings
        sparse_embeddings = []
        for i in range(0, len(self.metadata_df), batch_size):
            batch = self.metadata_df['combined_text'].iloc[i:i + batch_size].tolist()
            batch_embeddings = list(self.sparse_model.embed(batch))
            sparse_embeddings.extend(batch_embeddings)
        
        # Convert sparse to dense for faster similarity computation
        self.sparse_embeddings_dense = np.vstack([
            sparse_to_dense(embedding, dim=30315)
            for embedding in sparse_embeddings
        ])
        
        # Image embeddings (assuming they're already in the DataFrame)
        if 'image_embedding' in self.metadata_df.columns:
            image_embeddings = np.array(self.metadata_df['image_embedding'].tolist(), dtype='float32')
            d_img = image_embeddings.shape[1]
            self.image_index = faiss.IndexFlatL2(d_img)
            self.image_index.add(image_embeddings)
        else:
            self.image_index = None
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        weight_dense: float = 0.4,
        weight_sparse: float = 0.3,
        weight_image: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search using dense, sparse, and image embeddings
        """
        # Dense metadata search
        query_dense = self.metadata_model.encode([query], normalize_embeddings=True)[0].astype('float32').reshape(1, -1)
        distances_dense, indices_dense = self.dense_index.search(query_dense, top_k)
        scores_dense = -distances_dense[0]  # Negative L2 distance → higher is better
        
        # Sparse search
        query_sparse = list(self.sparse_model.embed([query]))[0]
        query_sparse_dense = sparse_to_dense(query_sparse, dim=30315).reshape(1, -1)
        similarities_sparse = cosine_similarity(query_sparse_dense, self.sparse_embeddings_dense)[0]
        top_indices_sparse = np.argpartition(-similarities_sparse, top_k)[:top_k]
        top_indices_sparse = top_indices_sparse[np.argsort(similarities_sparse[top_indices_sparse])[::-1]]
        scores_sparse = similarities_sparse[top_indices_sparse]
        
        # Image search (if available)
        if self.image_index is not None:
            inputs = self.clip_processor(text=[query], return_tensors="pt", padding=True)
            query_image_embedding = self.clip_model.get_text_features(**inputs)
            query_image_embedding = query_image_embedding / query_image_embedding.norm(p=2, dim=-1, keepdim=True)
            query_image_embedding = query_image_embedding.detach().cpu().numpy().astype('float32').reshape(1, -1)
            distances_image, indices_image = self.image_index.search(query_image_embedding, top_k)
            scores_image = -distances_image[0]
            norm_image = normalize_scores(scores_image)
        else:
            norm_image = np.zeros(top_k)
            weight_image = 0
            # Redistribute weights
            total = weight_dense + weight_sparse
            weight_dense = weight_dense / total
            weight_sparse = weight_sparse / total
        
        # Normalize scores
        norm_dense = normalize_scores(scores_dense)
        norm_sparse = normalize_scores(scores_sparse)
        
        # Compute hybrid scores
        hybrid_scores = (
            weight_dense * norm_dense[:top_k] +
            weight_sparse * norm_sparse[:top_k] +
            weight_image * norm_image[:top_k]
        )
        
        # Gather results
        results = []
        for i in range(top_k):
            idx = indices_dense[0][i]
            row = self.metadata_df.iloc[idx]
            result = {
                'name': row['name'],
                'neighborhood': row['neighborhood'],
                'tags': row['tags'],
                'description': row['short_description'],
                'hybrid_score': float(hybrid_scores[i]),
                'dense_score': float(norm_dense[i]),
                'sparse_score': float(norm_sparse[i])
            }
            if self.image_index is not None:
                result['image_score'] = float(norm_image[i])
            results.append(result)
        
        # Filter and sort results
        results = [res for res in results if res['hybrid_score'] > 0.1]
        results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return results 