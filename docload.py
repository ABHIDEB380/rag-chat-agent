import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_docling.loader import DoclingLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

load_dotenv()

# Resolve from this file's directory so debug/run cwd does not matter.
FILE_PATH = Path(__file__).resolve().parent / "Tutorial_EDIT.pdf"

load = DoclingLoader(file_path=str(FILE_PATH))

docs = load.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

texts = text_splitter.split_documents(docs)
print(len(texts))
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2",
    #001output_dimensionality=512
    )

client = QdrantClient(url=os.getenv("QDRANTCLIENT_HOST_URL"))

client.create_collection(
    collection_name="beginner_python",
    vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
)

vector_store = QdrantVectorStore(
    client=client,
    collection_name="beginner_python",
    embedding=embeddings,
)

vector_store.add_documents(texts)

print("Indexing is done.")