# FluxAI

**Optimize the flow of AI**

FluxAI is a cost optimization and observability platform for AWS Bedrock that helps companies reduce their LLM expenses by 30-50% through intelligent caching, smart routing, and real-time analytics.

[![Status](https://img.shields.io/badge/Status-Active%20Development-green)]()
[![Python](https://img.shields.io/badge/Python-3.11+-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal)]()
[![License](https://img.shields.io/badge/License-See%20LICENSE-lightgrey)](LICENSE)

---

## 📊 Project Status

### ✅ Implemented Components

| Component | Status | Documentation |
|-----------|--------|---------------|
| **API Gateway** | ✅ Complete | [Technical Spec](fluxai-technical-spec.md) |
| **Semantic Cache** | ✅ Complete | [Implementation Guide](SEMANTIC_CACHE.md) |
| **Cost Calculator** | ✅ Complete | [Calculator Guide](COST_CALCULATOR.md) |
| **Observability** | ✅ Complete | [Observability Guide](OBSERVABILITY.md) |
| **Dashboard** | ✅ Complete | [Dashboard Guide](dashboard/README.md) |
| **Multi-Model Router** | 📋 Documented | [Router Implementation](ROUTER_IMPLEMENTATION.md) |

### Implementation Summaries

- **[SEMANTIC_CACHE_SUMMARY.md](SEMANTIC_CACHE_SUMMARY.md)** - Complete summary of semantic cache implementation
- **[COST_CALCULATOR_IMPLEMENTATION.md](COST_CALCULATOR_IMPLEMENTATION.md)** - Cost calculator implementation details
- **[OBSERVABILITY_IMPLEMENTATION.md](OBSERVABILITY_IMPLEMENTATION.md)** - Observability system implementation summary

---

## 🎥 Demo Video

[![FluxAI Demo](https://img.youtube.com/vi/U8jHmLgnpkw/maxresdefault.jpg)](https://youtu.be/U8jHmLgnpkw)

*Click the image above to watch our 3-minute demo showing FluxAI in action*

## 🎯 Overview

FluxAI is a drop-in optimization layer that sits between your applications and AWS Bedrock, providing intelligent cost reduction, performance optimization, and complete observability for your LLM operations.

### Key Benefits

- **💰 Reduce Costs by 30-50%**: Semantic caching and smart routing automatically optimize your Bedrock spending
- **📊 Complete Visibility**: Real-time cost tracking, model performance metrics, and usage analytics
- **⚡ Improve Performance**: Intelligent model selection and request optimization
- **🔒 Enterprise Ready**: SOC 2 compliance roadmap, RBAC, audit logs, and SSO integration

---

## 💡 How It Works

```
┌─────────────────────────────────────┐
│      Customer Applications          │
│   (APIs, Chatbots, AI Agents)      │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│          FluxAI Gateway             │
│  Auth | Rate Limit | Cost Track     │
└─────────────┬───────────────────────┘
              │
     ┌────────┼────────┐
     ↓        ↓        ↓
┌────────┐ ┌──────┐ ┌──────────┐
│Semantic│ │Smart │ │Dashboard │
│ Cache  │ │Router│ │Analytics │
└────────┘ └──────┘ └──────────┘
     │        │        │
     └────────┼────────┘
              ↓
┌─────────────────────────────────────┐
│         AWS Bedrock API             │
│  (Claude, Llama, Titan, Mistral)   │
└─────────────────────────────────────┘
```

### Core Features

1. **🎯 API Gateway**: Drop-in replacement for Bedrock API with authentication and rate limiting
2. **💰 Cost Tracking**: Real-time cost calculation per request with detailed analytics
3. **🧠 Semantic Caching**: 30-50% cost reduction through intelligent response caching using AWS Bedrock Titan Embeddings
4. **🔀 Smart Routing**: Cost, latency, or capability-based model selection
5. **📊 Analytics Dashboard**: Beautiful real-time metrics and cost insights with Streamlit
6. **🔔 Cost Alerts**: Threshold notifications and anomaly detection
7. **🔍 Observability**: Complete monitoring with Prometheus, OpenTelemetry, and distributed tracing

---

## 📚 Documentation

### Getting Started

- **[Quick Start Guide](fluxai-quick-start.md)** - Get up and running in 5 minutes
- **[Technical Specification](fluxai-technical-spec.md)** - Complete system architecture and design
- **[Implementation Guide](fluxai-implementation-guide.md)** - Development roadmap and code examples
- **[Getting Started (Detailed)](GETTING_STARTED.md)** - Step-by-step setup instructions
- **[Docker Deployment](DOCKER_DEPLOYMENT.md)** - Complete Docker and Docker Compose guide

### Deep Dives & Implementation Guides

**Core Features:**

- **[Semantic Cache Implementation](SEMANTIC_CACHE.md)** - How the semantic caching system works, performance characteristics, and cost savings analysis
- **[Cost Calculator Guide](COST_CALCULATOR.md)** - Real-time cost tracking, savings analysis, and optimization recommendations
- **[Multi-Model Router](ROUTER_IMPLEMENTATION.md)** - Intelligent model selection based on cost, latency, or capabilities
- **[Observability System](OBSERVABILITY.md)** - Comprehensive monitoring with Prometheus metrics, OpenTelemetry tracing, and structured logging
- **[Dashboard Guide](dashboard/README.md)** - Interactive Streamlit dashboard for real-time monitoring and analytics
- **[Dashboard Quick Reference](dashboard/QUICK_REFERENCE.md)** - Quick reference guide for daily dashboard usage

**Implementation Summaries:**

- **[Semantic Cache Summary](SEMANTIC_CACHE_SUMMARY.md)** - Complete implementation summary with files created and testing checklist
- **[Cost Calculator Summary](COST_CALCULATOR_IMPLEMENTATION.md)** - Implementation details, features, and next steps
- **[Observability Summary](OBSERVABILITY_IMPLEMENTATION.md)** - Full observability system implementation with metrics, tracing, and logging

### API Reference

- **OpenAPI Documentation**: Available at `/docs` when running the server
- **Cache API**: `GET /v1/cache/stats`, `DELETE /v1/cache`
- **Bedrock API**: `POST /v1/bedrock/invoke`, `POST /v1/bedrock/invoke/stream`
- **Analytics API**: `GET /v1/analytics/cost`
- **Metrics API**: `GET /metrics` (Prometheus format)

### Testing & Validation

- **[Testing Checklist](TESTING_CHECKLIST.md)** - Comprehensive testing guide to verify all components are working correctly

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for Redis, Prometheus, PostgreSQL)
- AWS Account with Bedrock access
- AWS credentials configured

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/fluxai.git
cd fluxai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your AWS credentials and settings

# 4. Start infrastructure services (Redis, Prometheus, PostgreSQL)
docker-compose up -d

# 5. Run the FluxAI Gateway
uvicorn app.main:app --reload

# 6. View API documentation
# Open http://localhost:8000/docs in your browser

# 7. Launch observability dashboard (optional)
# Windows PowerShell:
.\start-dashboard.ps1

# Linux/macOS:
./start-dashboard.sh

# Or manually:
streamlit run dashboard/app.py
```

See [GETTING_STARTED.md](GETTING_STARTED.md) for detailed setup instructions.

---

## 💰 Cost Savings Example

### Without FluxAI (Direct Bedrock)

```
100,000 requests/month × $0.0165 per request = $1,650/month
```

### With FluxAI (40% cache hit rate)

```
60,000 Bedrock requests × $0.0165 = $990
40,000 cache hits × $0.00005 = $2
Total: $992/month

Savings: $658/month (40% reduction)
Annual Savings: $7,896
```

The semantic cache uses AWS Bedrock Titan Embeddings to identify similar queries and return cached responses, providing massive cost savings with minimal latency impact.

Learn more in [SEMANTIC_CACHE.md](SEMANTIC_CACHE.md).

---

## 📄 License

See [LICENSE](LICENSE) file for details.
