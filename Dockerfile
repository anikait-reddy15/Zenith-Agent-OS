# Use the official Python 3.10 slim image to match your local environment
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install critical system dependencies:
# 1. nodejs & npm: Required for the MCP Memory server to run 'npx'
# 2. gcc & libpq-dev: Required for psycopg2 (PostgreSQL) and SQLAlchemy to compile correctly
RUN apt-get update && \
    apt-get install -y nodejs npm gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose port 8080 (The default port Google Cloud Run expects)
EXPOSE 8080

# Command to run the FastAPI server when the container starts
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]