"""
RAG Chain Module

This module implements the Retrieval-Augmented Generation (RAG) pipeline
for the MediChat application, combining document retrieval with LLM generation.

Classes:
    RAGChain: Main RAG pipeline orchestrator

Author: Muhammad Aqeel
Date: 2024
"""

import random
from typing import List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from src.utils import get_logger

logger = get_logger(__name__)


class RAGChain:
    """
    Retrieval-Augmented Generation pipeline for question answering.
    
    This class combines vector store retrieval with LLM generation to answer
    questions based on uploaded documents or general knowledge.
    
    Attributes:
        model_name (str): OpenAI model identifier
        temperature (float): LLM temperature for response generation
        llm (ChatOpenAI): LangChain ChatOpenAI instance
        embeddings (OpenAIEmbeddings): Embeddings model for vector store
        vector_store (FAISS): FAISS vector store for document retrieval
        retriever: LangChain retriever instance
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.3):
        """
        Initialize the RAG Chain.
        
        Args:
            model_name (str, optional): OpenAI model to use. Defaults to "gpt-3.5-turbo".
            temperature (float, optional): Temperature for response generation (0-1).
                Lower values = more focused, higher = more creative. Defaults to 0.3.
        """
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=1024
        )
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self.retriever = None
    
    def create_vector_store(self, documents: List[Dict[str, Any]]) -> None:
        """
        Create FAISS vector store from processed documents.
        
        Converts document chunks to embeddings and stores them in a FAISS
        index for efficient similarity search.
        
        Args:
            documents (List[Dict[str, Any]]): List of document chunks with
                'content' and 'metadata' keys
        
        Raises:
            Exception: If vector store creation fails
        
        Example:
            >>> rag_chain = RAGChain()
            >>> rag_chain.create_vector_store(processed_chunks)
        """
        try:
            # Convert document dicts to LangChain Document objects
            langchain_docs = [
                Document(
                    page_content=doc["content"],
                    metadata=doc.get("metadata", {})
                )
                for doc in documents
            ]
            
            # Create FAISS vector store
            self.vector_store = FAISS.from_documents(
                langchain_docs,
                self.embeddings
            )
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            logger.info(f"✅ Vector store created with {len(langchain_docs)} documents")
        
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise
    
    def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from vector store.
        
        Uses similarity search to find the most relevant document chunks
        for the given query.
        
        Args:
            query (str): User's question
            top_k (int, optional): Number of results to retrieve. Defaults to 5.
        
        Returns:
            List[Dict[str, Any]]: Relevant documents with content and metadata
        
        Raises:
            ValueError: If vector store is not initialized
        
        Example:
            >>> context = rag_chain.retrieve_context("What is diabetes?", top_k=3)
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Process documents first.")
        
        try:
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": top_k}
            )
            retrieved_docs = retriever.invoke(query)
            
            results = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": None  # FAISS doesn't return scores directly
                }
                for doc in retrieved_docs
            ]
            
            logger.info(f"Retrieved {len(results)} documents for query: {query[:50]}...")
            return results
        
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            raise
    
    def generate_response(self, query: str, context: List[Dict[str, Any]]) -> str:
        """
        Generate answer using LLM with retrieved context.
        
        Creates a prompt combining the user's question and relevant documents,
        then generates a response using the LLM.
        
        Args:
            query (str): User's question
            context (List[Dict[str, Any]]): Retrieved documents
        
        Returns:
            str: Generated answer from LLM
        
        Raises:
            Exception: If response generation fails
        """
        try:
            # Format context for prompt
            context_text = self._format_context(context)
            
            # Build prompt
            prompt = self._build_prompt(query, context_text)
            
            # Get response from LLM
            response = self.llm.invoke(prompt)
            answer = response.content
            
            logger.info(f"Generated response for query: {query[:50]}...")
            return answer
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def answer_question(
        self, 
        query: str, 
        top_k: int = 5, 
        use_documents_only: bool = False
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Complete RAG pipeline: retrieve relevant docs → generate answer.
        
        This is the main method that orchestrates the entire RAG process,
        intelligently deciding whether to use documents or general knowledge.
        
        Args:
            query (str): User's question
            top_k (int, optional): Number of documents to retrieve. Defaults to 5.
            use_documents_only (bool, optional): If True, only answer from documents.
                Defaults to False.
        
        Returns:
            Tuple[str, List[Dict[str, Any]]]: Generated answer and retrieved context
        
        Raises:
            Exception: If RAG pipeline fails
        
        Example:
            >>> answer, sources = rag_chain.answer_question("What is hypertension?")
        """
        try:
            # Handle special cases
            if self._is_greeting(query):
                answer = self.generate_response_without_context(query)
                return answer, []
            
            if self._is_farewell(query):
                answer = self._generate_farewell_message()
                return answer, []
            
            if self._is_unclear_query(query):
                answer = self._generate_clarification_message()
                return answer, []
            
            # Check if document-specific question
            is_document_question = self._is_document_question(query)
            
            # No vector store - use general knowledge
            if not self.vector_store:
                answer = self.generate_response_without_context(query)
                return answer, []
            
            # Retrieve relevant documents
            context = self.retrieve_context(query, top_k)
            
            # Generate response based on query type
            if is_document_question and context:
                answer = self.generate_response(query, context)
                return answer, context
            elif is_document_question:
                answer = "I don't have enough information in the documents to answer that question."
                return answer, []
            else:
                # General question - use LLM knowledge
                answer = self.generate_response_without_context(query)
                return answer, []
        
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {str(e)}")
            raise
    
    def generate_response_without_context(self, query: str) -> str:
        """
        Generate answer using LLM without document context (general knowledge).
        
        Args:
            query (str): User's question
        
        Returns:
            str: Generated answer from LLM
        
        Raises:
            Exception: If response generation fails
        """
        try:
            prompt = f"""You are a helpful medical knowledge assistant. Answer the user's question based on your general knowledge.

USER QUESTION:
{query}

INSTRUCTIONS:
- Answer naturally and conversationally
- Be accurate and helpful
- If it's a greeting, respond warmly
- For medical questions, provide general information responsibly
- Include disclaimers where appropriate

ANSWER:"""
            
            response = self.llm.invoke(prompt)
            answer = response.content
            
            logger.info(f"Generated response from general knowledge: {query[:50]}...")
            return answer
        
        except Exception as e:
            logger.error(f"Error generating response without context: {str(e)}")
            raise
    
    # Private helper methods
    
    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting."""
        greetings = {
            'hi', 'hello', 'hey', 'greetings', 'good morning', 
            'good afternoon', 'good evening', 'howdy', 'sup', 
            'what\'s up', 'how are you', 'how\'s it going'
        }
        
        query_lower = query.lower().strip()
        
        # Exact match
        if query_lower in greetings:
            return True
        
        # Check if starts with greeting
        for greeting in greetings:
            if query_lower.startswith(greeting):
                remaining = query_lower[len(greeting):].strip()
                if not remaining or len(remaining.split()) <= 2:
                    return True
        
        return False
    
    def _is_farewell(self, query: str) -> bool:
        """Check if query is a farewell."""
        farewells = {
            'bye', 'goodbye', 'see you', 'take care', 'farewell',
            'adios', 'cya', 'see ya', 'cheerio', 'gotta go',
            'have to go', 'talk later', 'ttyl'
        }
        
        query_lower = query.lower().strip()
        return any(farewell in query_lower for farewell in farewells)
    
    def _is_unclear_query(self, query: str) -> bool:
        """Check if query is unclear or too vague."""
        unclear_keywords = {'nothing', 'nope', 'nah', 'whatever', 'dunno', 'idk'}
        query_lower = query.lower().strip()
        
        return (len(query_lower.split()) == 1 and query_lower in unclear_keywords)
    
    def _is_document_question(self, query: str) -> bool:
        """Detect if query is specifically about uploaded documents."""
        document_keywords = {
            'document', 'documents', 'file', 'pdf', 'mention', 'mentioned',
            'in the document', 'from the document', 'uploaded', 'your document',
            'my document', 'about the file', 'does the document'
        }
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in document_keywords)
    
    def _generate_farewell_message(self) -> str:
        """Generate a friendly farewell message."""
        messages = [
            "Goodbye! Feel free to come back anytime you have questions.",
            "See you later! Take care!",
            "Bye! I'm here whenever you need help.",
            "Have a great day! Come back if you need more information.",
            "Take care! See you soon!"
        ]
        return random.choice(messages)
    
    def _generate_clarification_message(self) -> str:
        """Generate a clarification request for unclear input."""
        messages = [
            "I'm not sure what you mean. Could you ask me a question about medical topics or your uploaded documents?",
            "Please provide more details. What would you like to know about?",
            "I'd be happy to help! Could you please rephrase your question?",
            "Can you ask me a specific question about medical topics or your documents?"
        ]
        return random.choice(messages)
    
    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Format retrieved documents for the prompt."""
        formatted = []
        for i, doc in enumerate(context, 1):
            source = doc.get("metadata", {}).get("source", "Unknown")
            formatted.append(f"[Document {i} - {source}]\n{doc['content']}\n")
        
        return "\n---\n".join(formatted)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the final prompt for the LLM."""
        return f"""You are a helpful medical knowledge assistant. Use the provided context to answer the user's question accurately and concisely.

CONTEXT:
{context}

USER QUESTION:
{query}

INSTRUCTIONS:
- Answer based only on the provided context
- If the context doesn't contain relevant information, say "I don't have enough information to answer that"
- Be concise and clear
- Provide medical information responsibly
- Include relevant citations from source documents

ANSWER:"""
