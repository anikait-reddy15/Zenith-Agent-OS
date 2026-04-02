FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (Node.js for MCP, C-compilers for databases)
RUN apt-get update && \
    apt-get install -y nodejs npm gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port Google Cloud expects
EXPOSE 8080

# Run FastAPI in the background (port 8000) AND Streamlit in the foreground (port 8080)
CMD uvicorn api.main:app --host 127.0.0.1 --port 8000 & streamlit run app.py --server.port 8080 --server.address 0.0.0.0