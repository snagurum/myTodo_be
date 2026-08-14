# 1. Use the official Python 3.12 slim image
FROM python:3.12-slim

# 2. Set environment variables to prevent Python from writing .pyc files & buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Create a non-root system user and group early while still root
RUN groupadd -r appuser && useradd -r -g appuser -s /sbin/nologin appuser

# 4. Set work directory and ensure the non-root user has access to it
WORKDIR /app

# 5. Install system dependencies (if your mysql driver needs compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 6. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy the project files and change ownership to the non-root user
COPY --chown=appuser:appuser . .

# 8. Make the startup script executable
RUN chmod +x startup.sh

# 9. Switch to the non-root user for all subsequent operations and runtime
USER appuser

# 10. Expose the FastAPI port
EXPOSE 8000 8001

# 11. Run the startup script
CMD ["./startup.sh"]
