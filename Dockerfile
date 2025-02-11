# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables to prevent writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy project files to the container
COPY . /app

# Install dependencies with best practices
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 7860

# Use Gunicorn to serve the application efficiently
CMD ["gunicorn", "-w", "4", "-k", "sync", "--max-requests", "1000", "--max-requests-jitter", "50", "-b", "0.0.0.0:7860", "app:app"]
