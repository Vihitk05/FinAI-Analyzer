import os

# Storage Paths
DATA_FOLDER = "data"
TEMP_IMAGE_FOLDER = "temp_images"
CHROMA_DB_PATH = "chroma_db"

# Create necessary folders
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(TEMP_IMAGE_FOLDER, exist_ok=True)
os.makedirs(CHROMA_DB_PATH, exist_ok=True)
