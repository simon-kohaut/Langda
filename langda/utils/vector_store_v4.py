import json
from typing import List
from pathlib import Path
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings

import logging
logger = logging.getLogger(__name__)

# ======================================================================== #
#                                Retriever                                 #
# ======================================================================== #
class LangdaVectorStore:
    """
    Creates and manages a FAISS vector store from JSON data
    """
    def __init__(self):
        self.json_dir = Path(__file__).parent
        self.vs_dir = self.json_dir / "vector_store"

        self.vs_dir.mkdir(parents=True, exist_ok=True)

        self.index_name = "problog_docs"
        self.json_file_path = self.json_dir / f"{self.index_name}.json"

        self.vs_index_name = self.index_name
        self.vector_store_path = self.vs_dir / f"{self.vs_index_name}.faiss"
        self.embedding_function = OllamaEmbeddings(model="nomic-embed-text")

    def create_documents(self) -> List[Document]:
        """
        convert JSON data to LangChain Documents
        returns: 
            List of Document objects ready for vectorization
        """
        documents: List[Document] = []
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                json_file: List[dict] = json.load(f)
            logger.info(f"Successfully loaded {len(json_file)} items from {self.json_file_path}")

            for item in json_file:

                content = item.get('embedding_text', item.get('content', ''))

                if not content:
                    logger.warning(f"Warning: No content found for item with id: {item.get('id', 'unknown')}")
                    continue

                # Create metadata from other fields
                metadata = {
                    'id': item.get('id', ''),
                    'title': item.get('title', ''),
                    'actual_content': item.get('content', ''),  # 添加真正的内容
                    'tags': item.get('tags', []),
                    'keywords': item.get('keywords', []),
                }

                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                documents.append(doc)

            logger.info(f"Created {len(documents)} documents from JSON data")
            return documents
        
        except Exception as e:
            logger.error(f"Error creating Documents file: {e}")
            raise

    def create_faiss_vector_store(self) -> FAISS:
        """
        Create and save FAISS vector store
        returns:
            FAISS vector store object
        """
        logger.info("Creating FAISS vector store...")
        documents = self.create_documents()
        
        if not documents:
            raise ValueError("No documents found to create vector store")
        
        vector_store = FAISS.from_documents(documents, self.embedding_function)
        vector_store.save_local(self.vs_dir, index_name=self.vs_index_name)
        logger.info(f"Vector store saved to {self.vs_dir}/{self.vs_index_name}")
        return vector_store

    @property
    def vs(self) -> FAISS:
        """
        Get or create the vector storage object
        returns:
            FAISS vector store object
        """
        if not self.vector_store_path.exists():
            logger.info("Vector store not found, creating new one...")
            return self.create_faiss_vector_store()

        logger.info("Loading existing vector store...")
        return FAISS.load_local(
            self.vs_dir, 
            self.embedding_function, 
            index_name=self.vs_index_name,
            allow_dangerous_deserialization=True
        )

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Perform similarity search on the local vector library.
        args:
            query: search query text
            k: number of results to return
        returns:
            document list
        """
        return self.vs.similarity_search(query, k=k)

    def similarity_search_with_scores(self, query: str, k: int = 5) -> List[tuple]:
        """
        Perform similarity search with similarity scores
        args:
            query: Search query text
            k: Number of results to return
            
        returns:
            List of (document, score) tuples
        """
        return self.vs.similarity_search_with_score(query, k=k)