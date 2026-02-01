"""
Document Processor Module

This module provides functionality for processing PDF documents and splitting
them into chunks for RAG (Retrieval-Augmented Generation) applications.

Classes:
    DocumentProcessor: Handles PDF processing and text chunking

Author: Muhammad Aqeel
Date: 2024
"""

from typing import List, Dict, Any
import pypdf
from io import BytesIO
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    """
    Handles PDF processing and text chunking for RAG applications.
    
    This class provides methods to extract text from PDF files and split
    the text into manageable chunks with metadata for vector storage.
    
    Attributes:
        chunk_size (int): Maximum size of each text chunk
        chunk_overlap (int): Number of characters to overlap between chunks
        text_splitter (RecursiveCharacterTextSplitter): LangChain text splitter instance
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the DocumentProcessor.
        
        Args:
            chunk_size (int, optional): Size of each text chunk. Defaults to 1000.
            chunk_overlap (int, optional): Overlap between chunks. Defaults to 200.
                Overlap helps maintain context between chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def extract_text_from_pdf(self, file) -> str:
        """
        Extract text content from an uploaded PDF file.
        
        This method reads a PDF file and extracts text from all pages,
        adding page markers to help with source attribution.
        
        Args:
            file: Uploaded file object (from Streamlit file_uploader)
        
        Returns:
            str: Extracted text with page markers
        
        Raises:
            ValueError: If the PDF cannot be read or is corrupted
        
        Example:
            >>> processor = DocumentProcessor()
            >>> text = processor.extract_text_from_pdf(uploaded_file)
        """
        try:
            pdf_reader = pypdf.PdfReader(BytesIO(file.read()))
            text = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n--- Page {page_num + 1} ---\n{page_text}"
            
            return text
        
        except Exception as e:
            raise ValueError(f"Error reading PDF: {str(e)}")
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata.
        
        Uses LangChain's RecursiveCharacterTextSplitter to intelligently
        split text at natural boundaries (paragraphs, sentences, etc.)
        
        Args:
            text (str): Text to split into chunks
            metadata (dict, optional): Metadata to attach to each chunk
        
        Returns:
            List[Dict[str, Any]]: List of chunks with content and metadata
                Each chunk is a dictionary with 'content' and 'metadata' keys
        
        Example:
            >>> chunks = processor.chunk_text("Long text...", {"source": "document.pdf"})
        """
        chunks = self.text_splitter.split_text(text)
        
        # Add metadata to each chunk
        chunked_docs = []
        for i, chunk in enumerate(chunks):
            doc = {
                "content": chunk,
                "metadata": {
                    "chunk_id": i,
                    **(metadata or {})
                }
            }
            chunked_docs.append(doc)
        
        return chunked_docs
    
    def process_pdf(self, file, filename: str) -> List[Dict[str, Any]]:
        """
        Complete pipeline: Extract text from PDF and split into chunks.
        
        This is the main method that combines text extraction and chunking
        into a single convenient operation.
        
        Args:
            file: Uploaded PDF file object
            filename (str): Name of the file (used in metadata)
        
        Returns:
            List[Dict[str, Any]]: Processed chunks with metadata
        
        Raises:
            ValueError: If PDF processing fails
        
        Example:
            >>> processor = DocumentProcessor()
            >>> chunks = processor.process_pdf(uploaded_file, "medical_doc.pdf")
            >>> print(f"Created {len(chunks)} chunks")
        """
        # Extract text
        text = self.extract_text_from_pdf(file)
        
        # Create metadata
        metadata = {
            "source": filename,
            "type": "pdf"
        }
        
        # Chunk text
        chunks = self.chunk_text(text, metadata)
        
        return chunks
