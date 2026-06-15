FROM python:3.12-slim

WORKDIR /app

# System deps for Pillow are already present in slim for JPEG/PNG; install build
# essentials only if a wheel is missing.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persisted via volumes in docker-compose.
ENV FASHION_AI_DB=/app/data/fashion_ai.db
ENV FASHION_AI_UPLOADS=/app/uploads
RUN mkdir -p /app/data /app/uploads

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
