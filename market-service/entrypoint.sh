#!/bin/sh
set -e

echo ""
echo "=============================================="
echo "  Market Service is starting..."
echo "=============================================="
echo "  API:        http://localhost:8001"
echo "  Swagger UI: http://localhost:8001/docs"
echo "  Health:     http://localhost:8001/health"
echo "=============================================="
echo "  (Wait ~30s for Kafka/Postgres healthchecks)"
echo "=============================================="
echo ""

exec uvicorn main:app --host 0.0.0.0 --port 8000
