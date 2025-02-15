import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document

from api.config import get_settings, OPENAI_API_KEY

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# load settings
settings = get_settings()

# Set the directory for persisting Chroma's index
persist_directory = "./chroma_db"

# Initialize the embedding model using OpenAI's text-embedding-ada-002
embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")

# Create (or load) the Chroma vector store WITH the embedding function
vector_store = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding_model
)


def add_document(doc: Document):
    """
    Adds a single document to the Chroma vector store and persists the changes.
    """
    if not doc.page_content.strip():
        raise ValueError("Document page_content is empty.")

    try:
        # add the document using the embedding function
        vector_store.add_documents([doc])
    except Exception as e:
        print(f"Error adding document to vector store: {e}")
        raise


def search_documents(query: str, k: int = 5):
    """
    Performs a similarity search for the given query.
    Returns a list of (Document, score) tuples.
    """
    return vector_store.similarity_search_with_score(query, k=k)
