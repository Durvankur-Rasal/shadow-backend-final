import os
import shutil
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import CharacterTextSplitter

DB_PATH = "./chroma_db"

# Free local embeddings - no API key needed
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def initialize_vector_db(doc_dir: str):
    """Ingests markdown files from the adrs/ directory."""
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)  # Reset DB for this demo

    loader = DirectoryLoader(doc_dir, glob="**/*.md", loader_cls=TextLoader)
    documents = loader.load()
    
    # Split by header if needed, but for ADRs, keeping them whole is often better
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)

    vectorstore = Chroma.from_documents(
        documents=docs, 
        embedding=embeddings, 
        persist_directory=DB_PATH
    )
    vectorstore.persist()
    print(f"✅ Indexed {len(docs)} ADR documents.")

def get_retriever():
    """Returns a retriever object for the graph to use."""
    vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
    # Search for top 2 most relevant ADRs
    return vectorstore.as_retriever(search_kwargs={"k": 2})

# Function to run manually to seed DB
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    initialize_vector_db("./adrs")