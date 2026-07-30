# Python 3.12 is used because every dependency ships a prebuilt wheel for it,
# which keeps the container build fast and reliable.
FROM python:3.12-slim

# HOME must point at a writable dir; some hosts run the container as a non-root
# user, and ChromaDB caches its embedding model under $HOME.
ENV HOME=/app
WORKDIR /app

# Install dependencies first so this layer is cached across builds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download the embedding model at build time so the first request is fast
# and no model download happens at runtime.
RUN python -c "import chromadb; c=chromadb.Client(); col=c.create_collection('warmup'); col.add(ids=['1'], documents=['warmup'])"

# Make the data + cache dirs writable no matter which user the host runs as.
RUN mkdir -p /app/data && chmod -R 777 /app/data /app/.cache

# Hosts inject the port via $PORT; default to 8000 for local runs.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
