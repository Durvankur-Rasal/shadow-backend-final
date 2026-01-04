import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

# Load keys
load_dotenv()

def seed_db():
    print("🚀 Connecting to Pinecone...")
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME")
    
    # 1. Load ADRs
    print("📂 Loading ADR documents...")
    loader = DirectoryLoader("./adrs", glob="**/*.md", loader_cls=TextLoader)
    docs = loader.load()
    print(f"   Found {len(docs)} documents.")

    # 2. Embed & Upload
    print("⚡ Generating embeddings and uploading...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    PineconeVectorStore.from_documents(
        docs, 
        embeddings, 
        index_name=index_name
    )
    print("✅ Upload Complete! Your knowledge is now in the cloud.")

if __name__ == "__main__":
    seed_db()