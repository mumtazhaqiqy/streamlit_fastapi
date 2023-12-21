# Dockerfile
FROM python:3.8-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY fastapi/app.py  /app/fastapi/
COPY streamlit/streamlit_app.py /app/streamlit/

# Expose ports (not strictly necessary with Docker Compose, but good practice)
EXPOSE 8000
EXPOSE 8501
