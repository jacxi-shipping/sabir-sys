# Dockerfile for Egg Farm Management System
# This creates a containerized version of the application

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libxi6 \
    libxrender1 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY egg_farm_system/ ./egg_farm_system/
COPY run.py .

# Create data directory
RUN mkdir -p /data

# Set environment variables
ENV DISPLAY=:0
ENV QT_QPA_PLATFORM=xcb
ENV DATA_DIR=/data

# Volume for persistent data
VOLUME ["/data"]

# Run the application
CMD ["python", "run.py"]
