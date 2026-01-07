# MediChat RAG - System Architecture

## Overview

MediChat RAG is a Retrieval-Augmented Generation (RAG) system that combines document retrieval with large language models to answer medical questions. The system can operate in two modes: document-based retrieval or general knowledge responses.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface (Streamlit)               │
│  - Document Upload  - Chat Interface  - Source Citations    │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer (app.py)               │
│  - Session Management  - UI Logic  - Error Handling         │
└─────────────┬───────────────────────────────┬───────────────┘
              │                               │
              ▼                               ▼
┌──────────────────────┐         ┌──────────────────────┐
│  Document Processor  │         │    Chat Manager      │
│  - PDF Parsing       │         │  - History          │
│  - Text Chunking     │         │  - Context          │
└──────────┬───────────┘         └──────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                      RAG Chain Engine                        │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Embeddings │→ │ Vector Store │→ │    Retriever    │   │
│  │   (OpenAI)  │  │   (FAISS)    │  │  (Similarity)   │   │
│  └─────────────┘  └──────────────┘  └────────┬────────┘   │
│                                               │             │
│                                               ▼             │
│                                    ┌──────────────────┐    │
│                                    │   LLM (GPT-3.5)  │    │
│                                    │  - Generation    │    │
│                                    │  - Synthesis     │    │
│                                    └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. User Interface Layer

**Technology**: Streamlit  
**Location**: `app.py`

**Responsibilities**:
- Document upload interface
- Chat input/output display
- Source citation rendering
- Session state management
- Error message display

**Key Features**:
- File upload with drag-and-drop
- Real-time chat interface
- Expandable source views
- Conversation statistics

### 2. Document Processor

**Location**: `src/document_processor.py`  
**Class**: `DocumentProcessor`

**Responsibilities**:
- Extract text from PDF files
- Split text into semantically meaningful chunks
- Attach metadata to each chunk

**Process Flow**:
```
PDF File → pypdf.PdfReader → Raw Text → RecursiveCharacterTextSplitter → 
Text Chunks → Metadata Addition → Processed Documents
```

**Configuration**:
- Chunk size: 1000 characters
- Chunk overlap: 200 characters
- Separators: Paragraph → Sentence → Word

### 3. RAG Chain Engine

**Location**: `src/rag_chain.py`  
**Class**: `RAGChain`

**Responsibilities**:
- Manage vector store lifecycle
- Perform similarity search
- Generate contextual responses
- Handle special queries (greetings, farewells)

**Process Flow**:

#### Document-Based Query:
```
User Query → Query Classification → Vector Search (FAISS) → 
Top-K Documents → Context Formatting → LLM Prompt → 
Generated Answer + Sources
```

#### General Knowledge Query:
```
User Query → Classification → Direct LLM Call → 
Generated Answer (no sources)
```

**Key Components**:

1. **Embeddings Model**: `text-embedding-ada-002`
   - Converts text to 1536-dimensional vectors
   - Used for both document indexing and query encoding

2. **Vector Store**: FAISS (Facebook AI Similarity Search)
   - In-memory index for fast retrieval
   - Similarity search using cosine distance
   - Retrieves top-K most relevant chunks

3. **Language Model**: GPT-3.5-turbo
   - Generates natural language responses
   - Temperature: 0.3 (balanced creativity/accuracy)
   - Max tokens: 1024

### 4. Chat Manager

**Location**: `src/chat_manager.py`  
**Class**: `ChatManager`

**Responsibilities**:
- Store conversation history
- Manage message metadata
- Provide conversation summaries
- Export chat transcripts

**Data Structure**:
```python
ChatMessage:
  - role: "user" | "assistant"
  - content: str
  - timestamp: datetime
  - metadata: dict (sources, tokens, etc.)
```

**Features**:
- Automatic history trimming (max 20 messages)
- Conversation duration tracking
- Source tracking across conversation
- Export to formatted text

### 5. Utilities

**Location**: `src/utils.py`

**Responsibilities**:
- Logging configuration
- Input sanitization
- Text formatting
- Token estimation
- Error message generation

## Data Flow

### Document Upload Flow

```
1. User uploads PDF via Streamlit
   ↓
2. File passed to DocumentProcessor
   ↓
3. Text extracted using pypdf
   ↓
4. Text split into chunks (1000 chars, 200 overlap)
   ↓
5. Chunks converted to embeddings
   ↓
6. Embeddings stored in FAISS index
   ↓
7. Vector store ready for queries
```

### Query Processing Flow

```
1. User submits question
   ↓
2. Input sanitization
   ↓
3. Query classification (greeting/document/general)
   ↓
4. IF document query AND documents loaded:
   a. Convert query to embedding
   b. Search FAISS for top-5 similar chunks
   c. Format context from retrieved chunks
   d. Create prompt (context + query + instructions)
   e. Send to LLM
   f. Return answer + sources
   ↓
5. ELSE (general query OR no documents):
   a. Create prompt (query + instructions)
   b. Send to LLM
   c. Return answer (no sources)
   ↓
6. Add exchange to chat history
   ↓
7. Display to user
```

## Technical Decisions

### Why FAISS?

- **Speed**: In-memory index provides sub-millisecond retrieval
- **Scalability**: Handles thousands of documents efficiently
- **Simplicity**: No database setup required
- **Accuracy**: Highly optimized similarity search

**Trade-offs**:
- No persistence (index rebuilt each session)
- Limited to single machine
- No distributed search

### Why GPT-3.5-turbo?

- **Cost-effective**: 10x cheaper than GPT-4
- **Fast**: Lower latency for better UX
- **Sufficient quality**: Adequate for medical Q&A
- **Token efficiency**: Good for longer contexts

### Why Streamlit?

- **Rapid development**: Quick UI prototyping
- **Python-native**: No frontend framework needed
- **Built-in features**: File upload, chat interface
- **Easy deployment**: Simple hosting options

## Security Considerations

### Data Privacy

- **No persistent storage**: Documents removed after session
- **Local processing**: Only API calls to OpenAI
- **API key protection**: Stored in `.env` (not committed)

### Input Sanitization

- **XSS prevention**: Harmful characters removed
- **Length limits**: Queries capped at 1000 characters
- **File type validation**: Only PDF files accepted

### Error Handling

- **Graceful degradation**: Errors don't crash app
- **User-friendly messages**: Technical details hidden
- **Logging**: All errors logged for debugging

## Performance Optimization

### Embeddings

- **Batch processing**: Multiple chunks embedded at once
- **Caching**: Reuse embeddings when possible

### Vector Search

- **Top-K limiting**: Only retrieve necessary documents
- **Early termination**: Stop if threshold met

### LLM Calls

- **Temperature tuning**: Lower = faster, more predictable
- **Token limits**: Cap response length
- **Streaming**: (Future) Stream responses to user

## Scalability Considerations

### Current Limitations

- **Single-user**: Session-based state management
- **In-memory storage**: Limited by RAM
- **No caching**: Repeat queries re-processed

### Future Improvements

- **Multi-user**: Implement user authentication
- **Persistent storage**: Save vector stores to disk
- **Distributed processing**: Scale horizontally
- **Query caching**: Cache frequent queries
- **Async processing**: Non-blocking operations

## Monitoring & Observability

### Logging

- **Structured logs**: JSON format for parsing
- **Log levels**: DEBUG → INFO → WARNING → ERROR
- **Log rotation**: Automatic file management

### Metrics (Future)

- Query latency
- Retrieval accuracy
- User satisfaction scores
- Error rates
- Token usage

## Testing Strategy

### Unit Tests

- `test_document_processor.py`: PDF processing, chunking
- `test_rag_chain.py`: Retrieval, generation
- `test_vector_store.py`: Vector operations

### Integration Tests

- End-to-end query flow
- Document upload → query → response
- Error handling paths

### Future Testing

- Performance benchmarks
- Accuracy evaluation
- Load testing
- User acceptance testing

## Deployment Architecture

### Development

```
Local Machine
├── Python 3.12+ environment
├── Streamlit dev server
├── OpenAI API (cloud)
└── Logs (local disk)
```

### Production (Future)

```
Cloud Platform (AWS/GCP/Azure)
├── Container (Docker)
├── Load Balancer
├── App Servers (horizontal scaling)
├── Persistent Storage (S3/GCS/Blob)
├── Logging Service (CloudWatch/Stackdriver)
└── Monitoring (Prometheus/Grafana)
```

## API Integration

### OpenAI API

**Endpoints Used**:
1. `/v1/embeddings` - Text embedding generation
2. `/v1/chat/completions` - Response generation

**Rate Limits**:
- Embeddings: 3000 requests/min
- Chat: 90,000 tokens/min

**Error Handling**:
- Retry with exponential backoff
- Fallback to cached responses (future)
- User notification on persistent failures

## Configuration Management

**File**: `config/config.yaml`

**Categories**:
- Document processing parameters
- RAG chain settings
- Chat management
- UI customization
- Safety limits

**Environment Variables**:
- `OPENAI_API_KEY`: Required for API access
- Other secrets in `.env` file

## Future Enhancements

1. **Multi-modal Support**: Images, tables in PDFs
2. **Advanced Retrieval**: Hybrid search (keyword + semantic)
3. **Fine-tuning**: Custom medical LLM
4. **Evaluation Framework**: Automated quality assessment
5. **Real-time Collaboration**: Multi-user document annotation
6. **Voice Interface**: Speech-to-text and text-to-speech
7. **Mobile App**: Native iOS/Android applications

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Author**: Muhammad Aqeel
