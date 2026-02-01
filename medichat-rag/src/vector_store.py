"""
Vector Store Module

This module provides FAISS-based vector storage and retrieval functionality
for storing and searching document embeddings.

Classes:
    VectorStore: Manages FAISS vector store operations
"""

from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


class VectorStore:
    """
    Vector storage and retrieval using FAISS (Facebook AI Similarity Search).
    
    This class manages the creation and querying of a FAISS vector store
    for efficient semantic search over document embeddings.
    
    Attributes:
        vector_store (FAISS): The FAISS vector store instance
        embeddings (OpenAIEmbeddings): OpenAI embedding model
    
    Note:
        This class is currently not actively used in the main RAG pipeline.
        The RAGChain class handles vector store operations directly.
    """
    
    def __init__(self) -> None:
        """
        Initialize the VectorStore with OpenAI embeddings.
        
        Creates an OpenAIEmbeddings instance for converting text to embeddings.
        The vector store is initialized as None and created when needed.
        """
        self.vector_store: FAISS = None
        self.embeddings = OpenAIEmbeddings()
    
    def create_vector_store(self, documents: List[Dict[str, Any]]) -> None:
        """
        Create a FAISS vector store from documents.
        
        Converts document dictionaries to LangChain Document objects and
        creates a FAISS index for similarity searching.
        
        Args:
            documents (List[Dict[str, Any]]): List of document chunks with:
                - 'content' (str): Text content
                - 'metadata' (dict): Associated metadata
        
        Raises:
            ValueError: If documents list is empty or invalid
        
        Example:
            >>> documents = [{"content": "text", "metadata": {}}]
            >>> vector_store = VectorStore()
            >>> vector_store.create_vector_store(documents)
        """
        if not documents:
            raise ValueError("Documents list cannot be empty")
        
        # Convert to LangChain Document objects
        langchain_docs = [
            Document(
                page_content=doc["content"],
                metadata=doc.get("metadata", {})
            )
            for doc in documents
        ]
        
        self.vector_store = FAISS.from_documents(langchain_docs, self.embeddings)
    
    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, str]]:
        """
        Query the vector store for similar documents.
        
        Performs semantic search to find documents most similar to the query.
        
        Args:
            query_text (str): Query text to search for
            top_k (int, optional): Number of top results to return. Defaults to 5.
        
        Returns:
            List[Dict[str, str]]: List of similar documents with content
        
        Raises:
            ValueError: If vector store not initialized
        
        Example:
            >>> results = vector_store.query("medical condition", top_k=3)
        """
        if not self.vector_store:
            raise ValueError("Vector store is not initialized.")
        
        results = self.vector_store.similarity_search(query_text, k=top_k)
        return [{"content": doc.page_content} for doc in results]  