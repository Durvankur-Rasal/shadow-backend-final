import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

# Initialize Embeddings (Must match what we used for seeding)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

def get_retriever():
    """
    Connects to the existing Pinecone index.
    """
    print("☁️  Connecting to Pinecone Cloud DB...")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
    return vectorstore.as_retriever()