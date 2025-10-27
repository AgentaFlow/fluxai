# FluxAI - Docker Deployment Guide

This guide covers deploying FluxAI using Docker and Docker Compose for development and production environments.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Services Overview](#services-overview)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Service Management](#service-management)
- [Monitoring & Debugging](#monitoring--debugging)
- [Scaling & Performance](#scaling--performance)

---

## 🚀 Quick Start

### Prerequisites

- Docker 24.0+ and Docker Compose 2.0+
- AWS credentials configured
- At least 4GB RAM available
- Ports 3000, 4317, 5432, 6379, 8080, 8501, 9090, 16686 available

### Launch All Services

```bash
# Start the complete stack
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Access Points

- **API Gateway**: http://localhost:8080/docs
- **Dashboard**: http://localhost:8501
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Jaeger UI**: http://localhost:16686

---

## 🏗️ Services Overview

### Core Services

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| **API** | fluxai-api | 8080 | Main FastAPI gateway with semantic cache, cost tracking |
| **Dashboard** | fluxai-dashboard | 8501 | Streamlit observability dashboard |
| **PostgreSQL** | fluxai-postgres | 5432 | Request history, cost data, traces |
| **Redis** | fluxai-redis | 6379 | Semantic cache storage, session data |
| **Prometheus** | fluxai-prometheus | 9090 | Metrics collection and querying |
| **Grafana** | fluxai-grafana | 3000 | Metrics visualization and alerting |
| **Jaeger** | fluxai-jaeger | 16686 | Distributed tracing and debugging |

### Network Architecture

```
┌─────────────────────────────────────────────────────┐
│              Docker Network: fluxai-network         │
│                                                     │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐        │
│  │   API   │  │Dashboard │  │ Prometheus │        │
│  │  :8080  │  │  :8501   │  │   :9090    │        │
│  └────┬────┘  └─────┬────┘  └──────┬─────┘        │
│       │            │               │               │
│  ┌────┴────┐  ┌────┴────┐     ┌───┴────┐          │
│  │PostgreSQL│  │  Redis  │     │ Jaeger │          │
│  │  :5432   │  │  :6379  │     │ :16686 │          │
│  └──────────┘  └─────────┘     └────────┘          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Development Deployment

### Environment Configuration

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure AWS credentials:**
   ```bash
   # Edit .env file
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   ```

3. **Optional configurations:**
   ```bash
   # Database
   DATABASE_URL=postgresql+asyncpg://fluxai:dev_password@postgres:5432/fluxai
   
   # Redis
   REDIS_URL=redis://redis:6379/0
   
   # Observability
   OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
   PROMETHEUS_URL=http://prometheus:9090
   
   # Dashboard
   AUTO_REFRESH=true
   REFRESH_INTERVAL=30
   ```

### Start Development Environment

```bash
# Start all services
docker-compose up -d

# View startup logs
docker-compose logs -f api

# Wait for services to be healthy
docker-compose ps
```

### Hot Reload Development

The API service is configured with hot reload for development:

```yaml
volumes:
  - ./app:/app/app  # Code changes auto-reload
```

**To develop:**
1. Edit files in `./app/` directory
2. Changes are automatically detected
3. Server reloads automatically

---

## 🚢 Production Deployment

### Build Production Images

```bash
# Build API image
docker build -t fluxai-api:latest -f Dockerfile .

# Build Dashboard image
docker build -t fluxai-dashboard:latest -f Dockerfile.dashboard .

# Tag for registry
docker tag fluxai-api:latest your-registry/fluxai-api:1.0.0
docker tag fluxai-dashboard:latest your-registry/fluxai-dashboard:1.0.0

# Push to registry
docker push your-registry/fluxai-api:1.0.0
docker push your-registry/fluxai-dashboard:1.0.0
```

### Production docker-compose.prod.yml

Create a production-specific compose file:

```yaml
version: '3.8'

services:
  api:
    image: your-registry/fluxai-api:1.0.0
    restart: always
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=WARNING
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
  
  dashboard:
    image: your-registry/fluxai-dashboard:1.0.0
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

### Launch Production Stack

```bash
# Start with production config
docker-compose -f docker-compose.prod.yml up -d

# Verify all services are running
docker-compose -f docker-compose.prod.yml ps

# Check health status
docker-compose -f docker-compose.prod.yml exec api curl http://localhost:8080/health
```

---

## 🔧 Service Management

### Individual Service Control

```bash
# Start specific service
docker-compose up -d api

# Stop specific service
docker-compose stop dashboard

# Restart service
docker-compose restart prometheus

# View service logs
docker-compose logs -f api

# Execute commands in container
docker-compose exec api python -c "import sys; print(sys.version)"
```

### Database Management

```bash
# Run database migrations
docker-compose exec api alembic upgrade head

# Access PostgreSQL shell
docker-compose exec postgres psql -U fluxai -d fluxai

# Backup database
docker-compose exec postgres pg_dump -U fluxai fluxai > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U fluxai -d fluxai
```

### Redis Cache Management

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Check cache statistics
docker-compose exec redis redis-cli INFO stats

# Clear cache
docker-compose exec redis redis-cli FLUSHALL

# Monitor cache in real-time
docker-compose exec redis redis-cli MONITOR
```

---

## 📊 Monitoring & Debugging

### Health Checks

All services include health checks:

```bash
# Check all service health
docker-compose ps

# API health
curl http://localhost:8080/health

# Dashboard health
curl http://localhost:8501/_stcore/health

# Prometheus health
curl http://localhost:9090/-/healthy

# Redis health
docker-compose exec redis redis-cli ping
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# Since timestamp
docker-compose logs --since 2024-01-01T10:00:00 api

# Follow with timestamps
docker-compose logs -f -t api
```

### Resource Usage

```bash
# View container stats
docker stats

# Specific containers
docker stats fluxai-api fluxai-dashboard

# Memory usage
docker-compose exec api ps aux --sort=-%mem | head

# Disk usage
docker system df
```

### Debugging

```bash
# Enter container shell
docker-compose exec api /bin/bash

# Check environment variables
docker-compose exec api env

# Test network connectivity
docker-compose exec api ping postgres
docker-compose exec api curl http://prometheus:9090

# View container details
docker inspect fluxai-api
```

---

## ⚡ Scaling & Performance

### Horizontal Scaling

```bash
# Scale API service
docker-compose up -d --scale api=3

# With load balancer (requires nginx/traefik)
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d
```

### Resource Limits

Configure in docker-compose.yml:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Redis Performance

```bash
# Increase Redis memory
docker-compose exec redis redis-cli CONFIG SET maxmemory 512mb

# Change eviction policy
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### PostgreSQL Performance

```bash
# Increase connections
docker-compose exec postgres psql -U fluxai -c "ALTER SYSTEM SET max_connections = 200;"

# Increase shared buffers
docker-compose exec postgres psql -U fluxai -c "ALTER SYSTEM SET shared_buffers = '256MB';"

# Restart to apply
docker-compose restart postgres
```

---

## 🧹 Cleanup

### Stop All Services

```bash
# Stop containers (keeps data)
docker-compose down

# Stop and remove volumes (destroys data)
docker-compose down -v

# Remove images too
docker-compose down --rmi all -v
```

### Clean Up Docker

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Remove everything unused
docker system prune -a --volumes
```

---

## 🆘 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find what's using port 8080
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Change port in docker-compose.yml
ports:
  - "8081:8080"  # Use different host port
```

**Service won't start:**
```bash
# Check logs
docker-compose logs service_name

# Rebuild image
docker-compose build --no-cache service_name

# Remove and recreate
docker-compose rm -f service_name
docker-compose up -d service_name
```

**Out of memory:**
```bash
# Increase Docker memory limit (Docker Desktop settings)
# Or reduce service resource usage

# Check memory usage
docker stats
```

**Network issues:**
```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

---

## 📚 Additional Resources

- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FluxAI Documentation](../README.md)
- [Observability Guide](../OBSERVABILITY.md)
- [Dashboard Guide](../dashboard/README.md)

---

**Need Help?**
- Check service logs: `docker-compose logs -f`
- Verify health: `docker-compose ps`
- Review [OBSERVABILITY.md](../OBSERVABILITY.md) for debugging
