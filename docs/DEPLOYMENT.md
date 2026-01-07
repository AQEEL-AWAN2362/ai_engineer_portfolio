# MediChat RAG - Deployment Guide

This guide covers various deployment options for the MediChat RAG application, from local development to cloud production environments.

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Environment Configuration](#environment-configuration)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Production Considerations](#production-considerations)
6. [Troubleshooting](#troubleshooting)

---

## Local Development Setup

### Prerequisites

- Python 3.12 or higher
- Git
- OpenAI API key
- UV package manager (recommended) or pip

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd "MediChat RAG"
   ```

2. **Create Virtual Environment**
   
   Using UV (recommended):
   ```bash
   uv venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```
   
   Using venv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   
   Using UV:
   ```bash
   uv pip install -e .
   ```
   
   Using pip:
   ```bash
   pip install -e .
   ```

4. **Configure Environment Variables**
   ```bash
   # Create .env file
   cp .env.example .env
   
   # Edit .env and add your OpenAI API key
   OPENAI_API_KEY=your-api-key-here
   ```

5. **Run the Application**
   ```bash
   streamlit run app.py
   ```

6. **Access the Application**
   - Open browser to: `http://localhost:8501`
   - The app should load with the upload interface

### Development Mode

For development with auto-reload:
```bash
streamlit run app.py --server.runOnSave true
```

---

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root:

```env
# Required
OPENAI_API_KEY=sk-...

# Optional
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
LOG_LEVEL=INFO
```

### Configuration File

Edit `config/config.yaml` to customize:

```yaml
# Example configuration
document_processing:
  chunk_size: 1000
  chunk_overlap: 200

rag:
  model_name: "gpt-3.5-turbo"
  temperature: 0.3
  top_k: 5
```

---

## Docker Deployment

### Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache .

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  medichat:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Build and Run

```bash
# Build image
docker build -t medichat-rag .

# Run container
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=your-api-key \
  medichat-rag

# Or use docker-compose
docker-compose up -d
```

---

## Cloud Deployment

### AWS Deployment (ECS Fargate)

#### Prerequisites
- AWS Account
- AWS CLI configured
- Docker installed

#### Steps

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name medichat-rag
   ```

2. **Build and Push Docker Image**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Build image
   docker build -t medichat-rag .
   
   # Tag image
   docker tag medichat-rag:latest \
     <account-id>.dkr.ecr.us-east-1.amazonaws.com/medichat-rag:latest
   
   # Push image
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/medichat-rag:latest
   ```

3. **Create ECS Task Definition**
   
   Create `task-definition.json`:
   ```json
   {
     "family": "medichat-rag",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "containerDefinitions": [
       {
         "name": "medichat-rag",
         "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/medichat-rag:latest",
         "portMappings": [
           {
             "containerPort": 8501,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "OPENAI_API_KEY",
             "value": "your-api-key"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/medichat-rag",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

4. **Create ECS Service**
   ```bash
   aws ecs create-service \
     --cluster default \
     --service-name medichat-rag \
     --task-definition medichat-rag \
     --desired-count 1 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
   ```

### Google Cloud Platform (Cloud Run)

#### Prerequisites
- GCP Account
- gcloud CLI installed

#### Steps

1. **Build and Push to Container Registry**
   ```bash
   # Set project
   gcloud config set project your-project-id
   
   # Build image
   gcloud builds submit --tag gcr.io/your-project-id/medichat-rag
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy medichat-rag \
     --image gcr.io/your-project-id/medichat-rag \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars OPENAI_API_KEY=your-api-key \
     --memory 1Gi \
     --cpu 1
   ```

3. **Access Application**
   ```bash
   # Get service URL
   gcloud run services describe medichat-rag --platform managed --region us-central1 --format 'value(status.url)'
   ```

### Azure (Container Instances)

#### Prerequisites
- Azure Account
- Azure CLI installed

#### Steps

1. **Create Resource Group**
   ```bash
   az group create --name medichat-rg --location eastus
   ```

2. **Create Container Registry**
   ```bash
   az acr create --resource-group medichat-rg \
     --name medichatregistry --sku Basic
   ```

3. **Build and Push Image**
   ```bash
   # Login to ACR
   az acr login --name medichatregistry
   
   # Build and push
   az acr build --registry medichatregistry \
     --image medichat-rag:latest .
   ```

4. **Deploy Container Instance**
   ```bash
   az container create \
     --resource-group medichat-rg \
     --name medichat-rag \
     --image medichatregistry.azurecr.io/medichat-rag:latest \
     --cpu 1 --memory 1 \
     --registry-login-server medichatregistry.azurecr.io \
     --registry-username <username> \
     --registry-password <password> \
     --dns-name-label medichat-rag \
     --ports 8501 \
     --environment-variables OPENAI_API_KEY=your-api-key
   ```

### Streamlit Community Cloud

1. **Push code to GitHub**
   ```bash
   git push origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect GitHub repository
   - Select repository and branch
   - Add secrets in Streamlit Cloud settings:
     ```
     OPENAI_API_KEY = "your-api-key"
     ```
   - Click "Deploy"

---

## Production Considerations

### Security

1. **API Key Management**
   - Use secret management services (AWS Secrets Manager, Azure Key Vault)
   - Rotate keys regularly
   - Never commit keys to version control

2. **HTTPS**
   - Always use HTTPS in production
   - Use SSL/TLS certificates
   - Enable HSTS headers

3. **Authentication**
   - Implement user authentication (OAuth, SAML)
   - Use Streamlit authentication decorators
   - Consider API key authentication for programmatic access

4. **Rate Limiting**
   - Implement rate limiting to prevent abuse
   - Monitor API usage
   - Set quotas per user

### Monitoring

1. **Application Monitoring**
   ```python
   # Add monitoring to app.py
   import sentry_sdk
   from sentry_sdk.integrations.streamlit import StreamlitIntegration
   
   sentry_sdk.init(
       dsn="your-sentry-dsn",
       integrations=[StreamlitIntegration()],
   )
   ```

2. **Logging**
   - Use structured logging (JSON format)
   - Centralize logs (CloudWatch, Stackdriver, Azure Monitor)
   - Set up alerts for errors

3. **Metrics**
   - Track query latency
   - Monitor OpenAI API usage
   - Track error rates
   - User engagement metrics

### Performance

1. **Caching**
   - Enable Streamlit caching:
     ```python
     @st.cache_resource
     def load_model():
         return RAGChain()
     ```

2. **Resource Limits**
   - Set memory limits (1-2GB recommended)
   - Limit concurrent users
   - Implement request queuing

3. **Scaling**
   - Use load balancer for multiple instances
   - Implement session stickiness
   - Consider stateless design

### Backup and Recovery

1. **Data Backup**
   - Backup logs regularly
   - Export conversation histories
   - Snapshot configurations

2. **Disaster Recovery**
   - Document recovery procedures
   - Test backup restoration
   - Maintain runbooks

---

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port 8501
lsof -i :8501  # Mac/Linux
netstat -ano | findstr :8501  # Windows

# Kill process or use different port
streamlit run app.py --server.port 8502
```

#### OpenAI API Errors
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check rate limits
# Implement exponential backoff
```

#### Memory Issues
```bash
# Increase Docker memory limit
docker run -m 2g ...

# Or adjust chunk size in config
document_processing:
  chunk_size: 500  # Reduce from 1000
```

#### Slow Performance
- Reduce `top_k` retrieval count
- Lower chunk size
- Use caching
- Upgrade to faster OpenAI model

### Debug Mode

Run in debug mode:
```bash
streamlit run app.py --logger.level=debug
```

### Logs Location

- Development: `logs/medichat.log`
- Docker: `/app/logs/medichat.log`
- Cloud: Check cloud provider's logging service

---

## Maintenance

### Update Dependencies

```bash
# Update all packages
uv pip compile --upgrade pyproject.toml

# Update specific package
uv pip install --upgrade langchain
```

### Health Checks

Implement health check endpoint:
```python
# Add to app.py
@st.cache_resource
def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}
```

### Monitoring Checklist

- [ ] API key valid and not expired
- [ ] OpenAI API accessible
- [ ] Sufficient compute resources
- [ ] Logs being written
- [ ] No memory leaks
- [ ] Response times acceptable
- [ ] Error rate below threshold

---

## Support

For deployment issues:
- 📧 Email: ai.engineer.aqeel@gmail.com
- 🐛 GitHub Issues: [repository-url]/issues
- 📖 Documentation: See other docs in `/docs` folder

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Author**: Muhammad Aqeel
