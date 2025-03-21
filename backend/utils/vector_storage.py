import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_DB_PATH

# Initialize ChromaDB and embedding model
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def store_in_chromadb(text_data, doc_id):
    try:
        vector = embedding_model.encode(text_data).tolist()
        chroma_client.get_or_create_collection("financial_statements").add(
            ids=[doc_id],
            embeddings=[vector],
            metadatas=[{"document_id": doc_id, "text": text_data}]
        )
    except Exception as e:
        # Add error handling for embedding and storage issues
        print(f"Error storing document {doc_id} in ChromaDB: {str(e)}")
