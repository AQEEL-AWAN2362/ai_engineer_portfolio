# 🏥 MediChat RAG - Medical Knowledge Assistant

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.52+-red.svg)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-green.svg)](https://python.langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An AI-powered medical knowledge chatbot that uses Retrieval-Augmented Generation (RAG) to answer questions based on uploaded medical documents or general medical knowledge.

Here is quick demo link: https://aqeel-awan2362-ai-engineer-portfolio-app-hhnsba.streamlit.app/

## ✨ Features

- 📄 **PDF Document Processing**: Upload and process medical PDF documents
- 🔍 **Intelligent Retrieval**: FAISS-based vector search for relevant information
- 🤖 **AI-Powered Responses**: GPT-3.5-turbo powered question answering
- 💬 **Context-Aware Chat**: Maintains conversation history
- 📚 **Source Citations**: Provides references to source documents
- 🎯 **Dual Mode**: Answers from documents or general knowledge
- 🚀 **User-Friendly Interface**: Built with Streamlit

## 🏗️ Architecture

```
MediChat RAG Pipeline:
┌──────────────┐
│  User Query  │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  Document Check  │ → No Documents → General Knowledge Response
└──────┬───────────┘
       │ Has Documents
       ▼
┌──────────────────┐
│ Vector Retrieval │ (FAISS Similarity Search)
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Context + Query  │ → LLM (GPT-3.5) → Answer + Sources
└──────────────────┘
```

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- OpenAI API key
- UV package manager (recommended) or pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AQEEL-AWAN2362/ai_engineer_portfolio.git
   cd "MediChat RAG"
   ```

2. **Set up environment**
   ```bash
   # Using UV (recommended)
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   uv pip install -e .
   ```

3. **Configure environment variables**
   ```bash
   # Create .env file
   cp .env.example .env
   
   # Add your OpenAI API key
   echo "OPENAI_API_KEY=your-api-key-here" >> .env
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

The app will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### Basic Workflow

1. **Upload Documents** (Optional)
   - Click "Choose PDF files" in the sidebar
   - Select one or more medical PDF documents
   - Click "Process Documents"

2. **Ask Questions**
   - Type your question in the chat input
   - Get answers from your documents or general knowledge
   - View source citations for document-based answers

3. **Review Sources**
   - Click "View Sources" to see document excerpts
   - Check which documents were used for the answer

### Example Questions

**Document-specific:**
- "What does my document say about diabetes treatment?"
- "Summarize the key points from my uploaded file"

**General medical:**
- "What are the symptoms of hypertension?"
- "Explain how insulin works"

## 🛠️ Project Structure

```
MediChat RAG/
├── app.py                    # Main Streamlit application
├── config/
│   └── config.yaml          # Configuration settings
├── src/
│   ├── __init__.py
│   ├── document_processor.py  # PDF processing & chunking
│   ├── rag_chain.py          # RAG pipeline orchestration
│   ├── chat_manager.py       # Chat history management
│   └── utils.py              # Utility functions

├── docs/
│   └── USER_GUIDE.md         # Detailed user guide

├── .env                      # Environment variables
├── pyproject.toml           # Project dependencies
└── README.md                # This file
```



## 🔧 Configuration

Edit `config/config.yaml` to customize:

- **Chunk size**: Size of text chunks (default: 1000)
- **Chunk overlap**: Overlap between chunks (default: 200)
- **Model**: LLM model to use (default: gpt-3.5-turbo)
- **Temperature**: Response creativity (default: 0.3)
- **Top K**: Number of documents to retrieve (default: 5)

## 📊 Performance

- **Processing**: ~2-3 seconds per PDF page
- **Query Response**: ~2-5 seconds depending on complexity
- **Memory**: ~500MB for typical usage
- **Concurrent Users**: Designed for single-user deployment


## ⚠️ Disclaimer

**This application is for educational and informational purposes only. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of qualified healthcare providers with any questions regarding medical conditions.**

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Muhammad Aqeel**
- Email: ai.engineer.aqeel@gmail.com
- GitHub: https://github.com/AQEEL-AWAN2362/ai_engineer_portfolio
- streamlit app link: https://aqeel-awan2362-ai-engineer-portfolio-app-hhnsba.streamlit.app/

## 🙏 Acknowledgments

- Built with [LangChain](https://python.langchain.com/)
- Powered by [OpenAI GPT](https://openai.com/)
- UI by [Streamlit](https://streamlit.io/)
- Vector store by [FAISS](https://faiss.ai/)

## 📞 Support

- 📧 Email: ai.engineer.aqeel@gmail.com
- 🐛 Issues: [GitHub Issues](issues-url)
- 📖 Documentation: See `docs/` folder


---

**Made with ❤️ for the medical community**
