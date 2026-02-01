FROM python:3.12-slim

# Prevents Python from writing .pyc files and enables stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps (build tools) and streamlit dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
       ca-certificates \
       gcc \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# copy dependency files first for caching
COPY requirements.txt pyproject.toml ./

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh || true

# Expose API and Streamlit ports
EXPOSE 8000 8501

ENTRYPOINT ["/app/docker-entrypoint.sh"]
