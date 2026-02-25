#!/bin/bash

# Startup script for the API service
echo "Starting MyTodo API..."

# Run bootstrap script to initialize database
echo "Running database bootstrap..."
python bootstrap.py

# Start the FastAPI application
echo "Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 8000