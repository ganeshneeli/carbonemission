# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Build args / env
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose Streamlit default port
EXPOSE 8080

# Cloud Run requires $PORT; Streamlit honours STREAMLIT_SERVER_PORT
ENV STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

CMD ["streamlit", "run", "app.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0"]
