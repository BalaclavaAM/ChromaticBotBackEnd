# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for image processing and PDM
RUN apt-get update && apt-get install -y \
    libgl1-mesa-dri \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install PDM
RUN pip install --no-cache-dir pdm

# Copy dependency files first for better caching
COPY pyproject.toml pdm.lock* ./

# Install dependencies using PDM
# --prod flag installs only production dependencies
# --no-lock skips lock file update
# --no-editable installs packages in non-editable mode
RUN pdm install --prod --no-lock --no-editableadsasdas

# Add PDM's bin directory to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY . .

# Create imageCache directory
RUN mkdir -p imageCache

# Expose port 8080
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PDM_PYTHON=/usr/local/bin/python

# Run the application with Uvicorn directly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
