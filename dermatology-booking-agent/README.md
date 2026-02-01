# Dermatology Clinic AI Booking Agent

## Executive Summary

A production-ready, enterprise-grade AI-powered appointment booking system designed for dermatology clinics. The system automates patient consultations, availability checking, and appointment scheduling using conversational AI, with integrated email confirmations and comprehensive patient management.

**Built with**: Python 3.12 • Ollama • FastAPI • Langchain • LangGraph • PostgreSQL • Streamlit • Gmail API 

---

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Booking Workflow](#booking-workflow)
- [Email Configuration](#email-configuration)
- [Troubleshooting](#troubleshooting)


---

## Features

### Core Functionality

- **Intelligent Conversation Management**: Multi-turn dialogues with context retention using LangGraph state management
- **Real-time Availability Checking**: Database-driven appointment slot availability with configurable doctor schedules
- **Automated Confirmations**: HTML email confirmations via Gmail API with full conversation history
- **Patient Management**: Persistent patient records with appointment history
- **Stateless Backend Architecture**: Designed for horizontal scaling and cloud deployment
- **Professional Chat Interface**: Responsive Streamlit UI with session management

### AI & Conversational

- **Natural Language Understanding**: Extracts booking details from conversational input
- **Medical Safeguards**: Prevents medical diagnoses or clinical advice
- **Context-Aware Responses**: Remembers patient information within conversation session
- **Graceful Fallbacks**: Mock responses when LLM unavailable, ensuring service continuity

### Integration & Reliability

- **OAuth2 Gmail Integration**: Secure email confirmations with automatic token management
- **Database Persistence**: All appointments and conversations stored in PostgreSQL
- **Error Handling**: Comprehensive logging and error recovery mechanisms
- **Modular Architecture**: Separated concerns for easy maintenance and testing

---

## System Architecture

### High-Level Flow

```
┌─────────────────┐
│  Streamlit UI   │ (React-like chat interface)
└────────┬────────┘
         │ HTTP/JSON
         ↓
┌──────────────────────────┐
│  FastAPI Backend         │
│  (Orchestration Layer)   │
└────────┬─────────────────┘
         │
    ┌────┴───────────┬─────────────┐
    ↓                ↓             ↓
┌─────────┐   ┌────────────┐   ┌──────────┐
│LangGraph │   │PostgreSQL  │   │Gmail API │
│  Agent   │   │ Database   │   │Emails    │
└─────────┘   └────────────┘   └──────────┘
    │
    └──→ Ollama LLM (Language Model)
```

### Component Responsibilities

| Component | Purpose |
|-----------|---------|
| **Streamlit UI** | Patient-facing chat interface with session management |
| **FastAPI Server** | HTTP API for agent communication and message routing |
| **LangGraph Workflow** | Conversational state machine and booking logic |
| **PostgreSQL** | Persistent storage for patients, appointments, conversations |
| **Gmail Service** | OAuth2-based email confirmations |
| **Ollama LLM** | Natural language understanding and response generation |

---

## Project Structure

```
dermatology-clinic-ai-agent/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── __init__.py
│   │
│   ├── agent/
│   │   ├── graph.py            # LangGraph workflow definition
│   │   ├── tools.py            # Agent tools (availability check, booking)
│   │   └── __init__.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── agent_routes.py # Chat endpoint
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── core/
│   │   ├── config.py           # Environment configuration
│   │   └── __init__.py
│   │
│   ├── db/
│   │   ├── engine.py           # SQLModel connection
│   │   ├── models.py           # ORM models (Patient, Doctor, Appointment)
│   │   └── __init__.py
│   │
│   └── services/
│       ├── booking_service.py  # Appointment creation and persistence
│       ├── gmail_service.py    # Email sending via Gmail API
│       └── __init__.py
│
├── ui/
│   └── app.py                  # Streamlit chat interface
│
├── scripts/
│   └── init_db.py              # Database initialization and seeding
│
├── .env                        # Environment variables (local)
├── .env.example                # Template for environment variables
├── credentials.json            # Gmail OAuth2 credentials
├── token.json                  # Gmail OAuth2 token (auto-generated)
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
└── README.md                   # This file
```

---

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **PostgreSQL**: 12 or higher (local or cloud-hosted)
- **RAM**: Minimum 4GB (8GB+ recommended)
- **Storage**: 500MB+ available

### External Services

1. **PostgreSQL Database**
   - Local installation or Supabase (cloud PostgreSQL)
   - Database credentials for connection string

2. **Ollama Language Model**
   - Local Ollama instance or cloud API
   - Supported models: deepseek-v3.1, mistral, llama2
   - For cloud: Ollama API endpoint + API key

3. **Gmail Account** (Optional but recommended)
   - For booking confirmation emails
   - Requires Google Cloud Console OAuth2 setup
   - Project with Gmail API enabled

---

## Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd dermatology-clinic-ai-agent
```

### Step 2: Create Python Environment

```bash
# Using venv
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or using UV (faster):
```bash
uv pip install -r requirements.txt
```

### Step 4: Database Setup

#### Option A: PostgreSQL Locally

```bash
# Initialize database schema and seed data
python scripts/init_db.py
```

#### Option B: Supabase Cloud

1. Create account at https://supabase.com
2. Create new project and copy connection string
3. Update DATABASE_URL in .env
4. Run: `python scripts/init_db.py`

---

## Configuration

### Environment Variables

Create `.env` file in project root (copy from `.env.example`):

```bash
# ============================================
# DATABASE CONFIGURATION (REQUIRED)
# ============================================
DATABASE_URL=postgresql://user:password@localhost:5432/dermatology_clinic

# ============================================
# LANGUAGE MODEL CONFIGURATION (REQUIRED)
# ============================================
# Local Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-v3.1:671b-cloud

# For cloud Ollama (optional)
# OLLAMA_API_KEY=your_api_key_here

# ============================================
# GMAIL CONFIGURATION (RECOMMENDED)
# ============================================
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
GMAIL_SENDER_EMAIL=clinic@gmail.com

# ============================================
# APPLICATION CONFIGURATION (OPTIONAL)
# ============================================
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=False
```

### Detailed Configuration

| Variable | Required | Type | Description | Example |
|----------|----------|------|-------------|---------|
| `DATABASE_URL` | Yes | String | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `OLLAMA_BASE_URL` | Yes | String | Ollama API endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | Yes | String | Model identifier | `deepseek-v3.1:671b-cloud` |
| `OLLAMA_API_KEY` | No | String | Cloud Ollama API key | (if using cloud) |
| `GMAIL_CREDENTIALS_FILE` | No | String | Path to credentials.json | `credentials.json` |
| `GMAIL_TOKEN_FILE` | No | String | OAuth token storage | `token.json` |
| `GMAIL_SENDER_EMAIL` | No | String | Sender email address | `clinic@gmail.com` |
| `API_HOST` | No | String | FastAPI host | `127.0.0.1` |
| `API_PORT` | No | Integer | FastAPI port | `8000` |
| `DEBUG` | No | Boolean | Enable debug logging | `False` |

---

## Quick Start

### Terminal 1: Start API Server

```bash
cd /path/to/project
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Terminal 2: Start Streamlit UI

```bash
cd /path/to/project
streamlit run ui/app.py --server.port 8501
```

Expected output:
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

### Terminal 3: (Optional) Enable Gmail Confirmations

```bash
cd /path/to/project
python -c "from app.services.gmail_service import GmailService; GmailService().authorize()"
```

Follow the browser OAuth flow to authorize the app.

### Access the Application

1. **Chat Interface**: http://localhost:8501
2. **API Health Check**: http://localhost:8000/health
3. **API Documentation**: http://localhost:8000/docs (Swagger UI)

---

## API Documentation

### Chat Endpoint

**POST** `/agent/chat`

Send a message to the booking agent.

**Request Body**:
```json
{
  "message": "I'd like to book an appointment for acne treatment",
  "session_id": "patient-unique-id",
  "booking_details": {
    "name": "John Doe",
    "phone": "03001234567",
    "email": "john@example.com",
    "concern": "acne",
    "date": "2026-02-05",
    "time": "14:00"
  }
}
```

**Response**:
```json
{
  "response": "Great! I've confirmed your appointment for February 5, 2026 at 2:00 PM. A confirmation email has been sent to john@example.com."
}
```

**Status Codes**:
- `200 OK` - Message processed successfully
- `422 Unprocessable Entity` - Invalid request format
- `500 Internal Server Error` - Server error (check logs)

### Health Check Endpoint

**GET** `/health`

Returns server status.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-01T10:30:00Z"
}
```

---


## Booking Workflow

### Multi-Step Conversation Flow

```
Step 1: USER INITIATES
  ├─ "I'd like to book an appointment"
  └─ Agent: "Great! What concerns would you like to address?"

Step 2: DETAIL EXTRACTION
  ├─ User provides: Name, Phone, Email, Medical Concern
  ├─ Agent parses user input
  └─ Agent: "When would you prefer to come in?"

Step 3: AVAILABILITY CHECK
  ├─ User specifies: Date and Time
  ├─ Agent queries available slots
  └─ Agent: "I have slots at 10 AM, 2 PM, or 4 PM on February 5"

Step 4: CONFIRMATION
  ├─ User: "2 PM works for me"
  ├─ Agent shows summary with all details
  └─ Agent: "Shall I proceed with booking?"

Step 5: EXECUTION & CONFIRMATION
  ├─ User: "Yes, confirm"
  ├─ Agent saves appointment to database
  ├─ Email confirmation sent to patient
  └─ Agent: "✅ APPOINTMENT CONFIRMED!"
```


## Email Configuration

### Gmail OAuth2 Setup

#### 1. Google Cloud Console Configuration

1. Visit https://console.cloud.google.com
2. Create new project or select existing
3. Enable Gmail API:
   - Search "Gmail API" → Click Enable
4. Create OAuth2 Credentials:
   - Type: Desktop Application
   - Authorized Redirect URIs add:
     - `http://localhost:8888/`
     - `http://localhost:8888`
     - `http://127.0.0.1:8888/`
5. Download credentials → Save as `credentials.json`

#### 2. Application Setup

```bash
# Place credentials.json in project root
# Update .env:
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_SENDER_EMAIL=your-email@gmail.com
```

#### 3. First-Time Authorization

```bash
python -c "from app.services.gmail_service import GmailService; GmailService().authorize()"
```

- Browser opens to Google login
- Sign in with your Gmail account
- Click "Allow" to authorize email sending
- Token saved to `token.json` (auto-generated)

### Email Content

Confirmation emails include:

- ✓ Appointment date, time, and doctor
- ✓ Patient medical concern
- ✓ Full conversation history
- ✓ Pre-appointment instructions
- ✓ Clinic contact information
- ✓ Cancellation/rescheduling instructions

**Template Format**: HTML with clinic branding

---

## Troubleshooting

### Database Issues

**Error: "Connection refused"**
```
Cause: PostgreSQL not running or wrong connection string
Fix:
  1. Ensure PostgreSQL service is running
  2. Check DATABASE_URL in .env
  3. Verify credentials are correct
  4. Test connection: psql <DATABASE_URL>
```

**Error: "Relation does not exist"**
```
Cause: Database tables not created
Fix:
  python scripts/init_db.py
```

### LLM/Ollama Issues

**Error: "Cannot connect to Ollama"**
```
Cause: Ollama service not running
Fix:
  1. Start Ollama: ollama serve
  2. Check OLLAMA_BASE_URL in .env (default: http://localhost:11434)
  3. Verify model installed: ollama list
```

**Error: "Model not found"**
```
Cause: Specified model not available
Fix:
  ollama pull deepseek-v3.1
  # Or other supported model
```

**Timeout/Slow Response**
```
Cause: LLM overloaded or slow connection
Fix:
  1. Wait for previous requests to complete
  2. Restart Ollama service
  3. Check network connectivity
  4. Use smaller model if available
```

### Gmail Issues

**Error: "Credentials file not found"**
```
Cause: Missing credentials.json
Fix:
  1. Download from Google Cloud Console
  2. Place in project root
  3. Verify GMAIL_CREDENTIALS_FILE in .env
```

**Error: "Invalid OAuth token"**
```
Cause: Token expired or permissions revoked
Fix:
  1. Delete token.json
  2. Re-run authorization:
     python -c "from app.services.gmail_service import GmailService; GmailService().authorize()"
```

**Error: "Emails not sending but booking succeeded"**
```
Cause: Email service failed
Fix:
  1. Check application logs for email errors
  2. Verify Gmail account isn't in restricted mode
  3. Check email sending quota
  4. Ensure 2FA is enabled on Gmail
```

### Application Issues

**Error: "Address already in use"**
```
Cause: Port 8000 or 8501 already in use
Fix:
  # Use different port
  python -m uvicorn app.main:app --port 8001
  streamlit run ui/app.py --server.port 8502
```

**Streamlit: "ModuleNotFoundError"**
```
Cause: Dependencies not installed or wrong environment
Fix:
  1. Activate virtual environment
  2. pip install -r requirements.txt
  3. Restart Streamlit
```

---

## Support & Documentation

### Useful Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Gmail API Guide](https://developers.google.com/gmail/api)

---

## License

Proprietary software for Dr. AQEEL Skin Clinic.

---

**Last Updated**: February 2026  
**Version**: 1.0.0 (Production)  


