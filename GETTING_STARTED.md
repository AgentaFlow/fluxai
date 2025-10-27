# FluxAI Gateway - Getting Started

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- AWS Account with Bedrock access
- Docker and Docker Compose (optional, for containerized development)

### Option 1: Docker Compose (Recommended for Development)

1. **Clone the repository**
   ```bash
   git clone https://github.com/AgentaFlow/fluxai.git
   cd fluxai
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your AWS credentials
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Access the API**
   - API: http://localhost:8080
   - Docs: http://localhost:8080/docs
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin)

### Option 2: Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/AgentaFlow/fluxai.git
   cd fluxai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and configure:
   # - AWS credentials
   # - Database URL
   # - Redis URL
   ```

5. **Start PostgreSQL and Redis**
   ```bash
   # Using Docker:
   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev_password -e POSTGRES_DB=fluxai postgres:15
   docker run -d -p 6379:6379 redis:7-alpine
   ```

6. **Run the application**
   ```bash
   python -m app.main
   # Or with uvicorn directly:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

7. **Access the API**
   - API: http://localhost:8080
   - Interactive docs: http://localhost:8080/docs
   - Health check: http://localhost:8080/health

## Testing the API

### 1. Health Check
```bash
curl http://localhost:8080/health
```

### 2. Invoke a Model
```bash
curl -X POST http://localhost:8080/v1/bedrock/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "model": "auto",
    "messages": [
      {
        "role": "user",
        "content": "Explain quantum computing in simple terms"
      }
    ],
    "max_tokens": 500,
    "temperature": 0.7
  }'
```

### 3. View Metrics
```bash
curl http://localhost:8080/metrics
```

## Development

### Project Structure
```
fluxai/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── api/                 # API routes
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── bedrock.py
│   │   │   │   ├── analytics.py
│   │   │   │   ├── models.py
│   │   │   │   └── cache.py
│   │   └── dependencies.py
│   ├── core/                # Core configuration
│   │   ├── config.py
│   │   └── logging.py
│   ├── db/                  # Database
│   │   ├── models.py
│   │   └── session.py
│   ├── models/              # Pydantic schemas
│   │   └── schemas.py
│   └── services/            # Business logic
│       ├── bedrock_client.py
│       ├── cost_calculator.py
│       ├── cache.py
│       ├── metrics.py
│       └── analytics.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
ruff check app/
```

### Type Checking
```bash
mypy app/
```

## Next Steps

1. **Set up AWS credentials** in `.env`
2. **Review the [Technical Specification](fluxai-technical-spec.md)** for architecture details
3. **Check the [Implementation Guide](fluxai-implementation-guide.md)** for feature roadmap
4. **Start building** MVP features from the project plan

## Need Help?

- Documentation: See markdown files in the project root
- API Docs: http://localhost:8080/docs (when running)
- Issues: GitHub Issues

## License

See LICENSE file for details.
