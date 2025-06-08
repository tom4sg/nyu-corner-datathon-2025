from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parents[3]
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    MODELS_DIR: Path = DATA_DIR / "models"

    # Raw data paths
    RAW_MEDIA_PATH: Path = RAW_DATA_DIR / "media.csv"
    RAW_PLACES_PATH: Path = RAW_DATA_DIR / "places.csv"
    RAW_REVIEWS_PATH: Path = RAW_DATA_DIR / "reviews.csv"

    # Processed data paths
    PROCESSED_CSV_PATH: Path = PROCESSED_DIR / "merged.csv"
    IMAGE_EMBEDDINGS_PATH: Path = PROCESSED_DIR / "image_embeddings.csv"

    # Model paths
    METADATA_INDEX_PATH: Path = MODELS_DIR / "metadata.index"
    REVIEWS_INDEX_PATH: Path = MODELS_DIR / "reviews.index"

    # Model settings
    DENSE_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    SPARSE_MODEL_NAME: str = "prithivida/Splade_PP_en_v1"
    CLIP_MODEL_NAME: str = "openai/clip-vit-base-patch32"

settings = Settings()
