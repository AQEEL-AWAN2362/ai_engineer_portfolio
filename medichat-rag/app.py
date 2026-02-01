"""
MediChat RAG - Medical Knowledge Assistant

A Streamlit-based web application for querying medical knowledge through
a Retrieval-Augmented Generation (RAG) system. Users can upload PDF documents
and ask questions, which are answered using either the uploaded documents
or general medical knowledge from the LLM.

Main Components:
- Document processing and chunking
- Vector store creation and retrieval
- LLM-based response generation
- Chat history management
- Multi-modal Q&A (documents + general knowledge)

Author: Muhammad Aqeel
Version: 0.1.0
"""

import streamlit as st
from dotenv import load_dotenv
import os
from src.document_processor import DocumentProcessor
from src.rag_chain import RAGChain
from src.chat_manager import ChatManager
from src.utils import get_logger, sanitize_input, format_document_metadata

logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Streamlit page configuration
st.set_page_config(
    page_title="MediChat RAG",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_session_state() -> None:
    """Initialize Streamlit session state variables."""
    state_defaults = {
        'processed_docs': [],
        'doc_processor': DocumentProcessor(),
        'rag_chain': RAGChain(),
        'chat_manager': ChatManager(),
        'all_chunks': []
    }
    
    for key, default_value in state_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def render_sidebar() -> None:
    """Render the sidebar with document upload and stats."""
    with st.sidebar:
        st.header("📤 Document Upload")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload medical PDF documents to query"
        )
        
        # Process documents button
        if uploaded_files and st.button("Process Documents", type="primary"):
            process_documents(uploaded_files)
        
        # Display processed documents
        if st.session_state.processed_docs:
            st.success(f"✅ {len(st.session_state.processed_docs)} document(s) processed")
            
            with st.expander("View Uploaded Documents"):
                for doc in st.session_state.processed_docs:
                    st.write(f"📄 {doc['filename']}")
                    st.caption(f"Chunks: {doc['num_chunks']}")
        
        # Display conversation statistics
        if st.session_state.chat_manager.messages:
            st.divider()
            st.subheader("📊 Conversation Stats")
            summary = st.session_state.chat_manager.get_summary()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Messages", summary['message_count'])
            with col2:
                st.metric("Duration", summary.get('duration', 'N/A'))


def render_chat_interface() -> None:
    """Render the main chat interface."""
    st.subheader("💬 Chat Interface")
    
    # Info message based on document status
    if not st.session_state.processed_docs:
        st.info("💡 Upload documents in the sidebar to ask questions about them, "
                "or chat about general medical topics")
    else:
        st.info("✅ Documents loaded! Ask questions about them or general medical topics")
        
        # Display chat history
        for message in st.session_state.chat_manager.messages:
            with st.chat_message(message.role):
                st.write(message.content)
                
                # Show sources for assistant messages
                if message.metadata and message.metadata.get('sources'):
                    with st.expander("📚 View Sources"):
                        for source in message.metadata.get('sources', []):
                            st.caption(format_document_metadata(source.get('metadata', {})))


def handle_user_query(prompt: str) -> None:
    """
    Handle user query and generate response.
    
    Args:
        prompt (str): User's question
    """
    clean_prompt = sanitize_input(prompt)
    
    # Add user message to history
    st.session_state.chat_manager.add_user_message(clean_prompt)
    
    # Display user message
    with st.chat_message("user"):
        st.write(clean_prompt)
    
    # Generate and display response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Thinking..."):
            try:
                rag_chain = st.session_state.rag_chain
                
                # Determine response source based on document availability
                if st.session_state.processed_docs:
                    answer, context = rag_chain.answer_question(
                        clean_prompt, 
                        top_k=5, 
                        use_documents_only=False
                    )
                else:
                    # No documents: use general knowledge
                    answer = rag_chain.generate_response_without_context(clean_prompt)
                    context = []
                
                # Add assistant message to history
                st.session_state.chat_manager.add_assistant_message(
                    answer,
                    metadata={"sources": context}
                )
                
                # Display response
                st.write(answer)
                
                # Show document sources if retrieved
                if context:
                    with st.expander("📚 View Sources"):
                        for i, source in enumerate(context, 1):
                            metadata_text = format_document_metadata(
                                source.get('metadata', {})
                            )
                            st.caption(f"**Document {i}:** {metadata_text}")
                            
                            with st.expander(f"Source {i} content"):
                                st.text(source['content'][:500] + "...")
            
            except ValueError as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error(f"RAG error: {str(e)}")
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                st.error(f"❌ {error_msg}")
                logger.error(error_msg)


def process_documents(uploaded_files: list) -> None:
    """
    Process uploaded PDF files and create vector store.
    
    Args:
        uploaded_files (list): List of uploaded file objects from Streamlit
    """
    processor = st.session_state.doc_processor
    rag_chain = st.session_state.rag_chain
    
    with st.spinner("Processing documents..."):
        for file in uploaded_files:
            try:
                # Extract and chunk PDF
                chunks = processor.process_pdf(file, file.name)
                
                # Accumulate chunks
                st.session_state.all_chunks.extend(chunks)
                
                # Track processed document
                st.session_state.processed_docs.append({
                    'filename': file.name,
                    'chunks': chunks,
                    'num_chunks': len(chunks)
                })
                
                st.success(f"✅ Processed: {file.name}")
            
            except Exception as e:
                logger.error(f"Error processing {file.name}: {str(e)}")
                st.error(f"❌ Error processing {file.name}: {str(e)}")
        
        # Create vector store from all accumulated chunks
        if st.session_state.all_chunks:
            try:
                rag_chain.create_vector_store(st.session_state.all_chunks)
                st.success(
                    f"✅ Vector store created with {len(st.session_state.all_chunks)} chunks"
                )
            except Exception as e:
                logger.error(f"Error creating vector store: {str(e)}")
                st.error(f"❌ Error creating vector store: {str(e)}")


def main() -> None:
    """Main application entry point."""
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error(
            "⚠️ **Missing Configuration**\n\n"
            "Please set `OPENAI_API_KEY` in your `.env` file to use this application."
        )
        return
    
    # Initialize session state
    initialize_session_state()
    
    # Render page header
    st.title("🏥 MediChat RAG - Medical Knowledge Assistant")
    st.markdown("---")
    
    # Render components
    render_sidebar()
    render_chat_interface()
    
    # Handle user input
    if prompt := st.chat_input("Ask a question..."):
        handle_user_query(prompt)
    
    # Render footer
    st.markdown("---")
    st.caption(
        "⚠️ **Disclaimer:** This tool is for informational purposes only. "
        "It is not a substitute for professional medical advice. "
        "Always consult qualified healthcare professionals."
    )


if __name__ == "__main__":
    main()
