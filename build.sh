#!/usr/bin/env bash
# Build script for Render deployment
set -e

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Building FAISS index..."
python -m app.rag.vector_store

echo "Build complete!"
