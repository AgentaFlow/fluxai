# FluxAI

**Optimize the flow of AI**

FluxAI is a cost optimization and observability platform for AWS Bedrock that helps companies reduce their LLM expenses by 30-50% through intelligent caching, smart routing, and real-time analytics.

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
5. **📊 Analytics Dashboard**: Beautiful real-time metrics and cost insights
6. **🔔 Cost Alerts**: Threshold notifications and anomaly detection

---

## 📚 Documentation

### Getting Started

- **[Quick Start Guide](fluxai-quick-start.md)** - Get up and running in 5 minutes
- **[Technical Specification](fluxai-technical-spec.md)** - Complete system architecture and design
- **[Implementation Guide](fluxai-implementation-guide.md)** - Development roadmap and code examples
- **[Getting Started (Detailed)](GETTING_STARTED.md)** - Step-by-step setup instructions

### Deep Dives

- **[Semantic Cache Implementation](SEMANTIC_CACHE.md)** - How the semantic caching system works, performance characteristics, and cost savings analysis
- **[Cost Calculator Guide](COST_CALCULATOR.md)** - Real-time cost tracking, savings analysis, and optimization recommendations
- **[Multi-Model Router](ROUTER_IMPLEMENTATION.md)** - Intelligent model selection based on cost, latency, or capabilities

### API Reference

- **OpenAPI Documentation**: Available at `/docs` when running the server
- **Cache API**: `GET /v1/cache/stats`, `DELETE /v1/cache`
- **Bedrock API**: `POST /v1/bedrock/invoke`, `POST /v1/bedrock/invoke/stream`
- **Analytics API**: `GET /v1/analytics/cost`

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/fluxai.git
cd fluxai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your AWS credentials

# 4. Start services with Docker
docker-compose up -d

# 5. Run the application
uvicorn app.main:app --reload

# 6. Open the dashboard
open http://localhost:8080/docs
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