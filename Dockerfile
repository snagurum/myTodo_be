# 1. Use the official Python 3.12 slim image
FROM python:3.12-slim

# 2. Set environment variables to prevent Python from writing .pyc files & buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set work directory
WORKDIR /app

# 4. Install system dependencies (if your mysql driver needs compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the project files
COPY . .

# 7. Make the startup script executable
RUN chmod +x startup.sh

# 8. Expose the FastAPI port
EXPOSE 8000 8001

# 9. Run the startup script
CMD ["./startup.sh"]
