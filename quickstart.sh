#!/bin/bash

# OCR Microservice Quick Start Script

set -e

echo "=========================================="
echo "OCR Microservice - Quick Start"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Check if .env exists, if not copy from .env.example
if [ ! -f .env ]; then
    echo "📋 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
fi

# Create network if it doesn't exist
if ! docker network ls | grep -q seguramiga-network; then
    echo "🌐 Creating Docker network: seguramiga-network..."
    docker network create seguramiga-network
    echo "✓ Network created"
    echo ""
else
    echo "✓ Docker network already exists"
    echo ""
fi

# Build and start the service
echo "🔨 Building OCR microservice..."
echo ""
docker-compose build

echo ""
echo "🚀 Starting OCR microservice..."
echo ""
docker-compose up -d

echo ""
echo "⏳ Waiting for service to be ready (this may take 15-30 seconds)..."
echo ""

# Wait for service to be healthy
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose ps | grep -q "healthy"; then
        echo "✓ Service is healthy!"
        break
    fi

    if curl -s http://localhost:8080/api/v1/health > /dev/null 2>&1; then
        echo "✓ Service is responding!"
        break
    fi

    echo "  Attempt $((attempt + 1))/$max_attempts - waiting..."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Service failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ OCR Microservice is ready!"
echo "=========================================="
echo ""
echo "📍 Service URLs:"
echo "   - Health Check: http://localhost:8080/api/v1/health"
echo "   - API Docs: http://localhost:8080/docs"
echo "   - ReDoc: http://localhost:8080/redoc"
echo ""
echo "📝 Quick Commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop service: docker-compose down"
echo "   - Restart service: docker-compose restart"
echo "   - Check status: docker-compose ps"
echo ""
echo "📖 Example usage:"
echo "   python example_usage.py"
echo ""
echo "🧪 Run tests:"
echo "   docker-compose exec ocr-service pytest"
echo ""
echo "=========================================="
