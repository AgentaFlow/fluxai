# FluxAI Observability System

Complete observability solution for FluxAI Gateway with Prometheus metrics, OpenTelemetry tracing, and structured logging.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
  - [Metrics Collection](#metrics-collection)
  - [Distributed Tracing](#distributed-tracing)
  - [Structured Logging](#structured-logging)
- [Metrics Reference](#metrics-reference)
- [Tracing Guide](#tracing-guide)
- [Logging Guide](#logging-guide)
- [Integration Examples](#integration-examples)
- [Grafana Dashboards](#grafana-dashboards)
- [Alerting](#alerting)
- [Troubleshooting](#troubleshooting)

## Overview

The FluxAI observability system provides comprehensive monitoring and debugging capabilities:

- **Metrics**: Real-time performance metrics with Prometheus
- **Tracing**: Distributed tracing with OpenTelemetry
- **Logging**: Structured JSON logs with trace correlation

### Key Benefits

- **99.9% Request Visibility**: Track every request from ingress to completion
- **Sub-Second Query Performance**: Prometheus time-series database
- **Trace Correlation**: Link logs, metrics, and traces with trace IDs
- **Cost Insights**: Track and optimize AWS Bedrock spending
- **Cache Monitoring**: Measure cache hit rates and savings
- **Model Health**: Monitor availability and performance of each model

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FluxAI Gateway                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Metrics    │  │   Tracing    │  │   Logging    │     │
│  │  Collector   │  │  Middleware  │  │  Middleware  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
   ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
   │ Prometheus  │   │ OpenTelemetry│   │  CloudWatch  │
   │   Server    │   │  Collector   │   │     Logs     │
   └──────┬──────┘   └──────┬───────┘   └──────────────┘
          │                  │
          │                  ▼
          │          ┌──────────────┐
          │          │    Jaeger    │
          │          │   Backend    │
          │          └──────────────┘
          │
          ▼
   ┌─────────────┐
   │   Grafana   │
   │  Dashboard  │
   └─────────────┘
```

## Components

### Metrics Collection

**File**: `app/services/metrics.py`

Prometheus-based metrics collection with multi-tenant support.

#### Key Features

- 15+ metrics covering requests, tokens, costs, cache, and model health
- Multi-tenant labeling with `account_id`
- Database persistence for historical analysis
- Thread-safe counters and histograms

#### Initialization

```python
from app.services.metrics import metrics_service

# Initialize on startup
metrics_service.initialize()
```

#### Recording Metrics

```python
await metrics_service.record_request(
    account_id=account.id,
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    input_tokens=1500,
    output_tokens=500,
    cost=0.0125,
    latency_ms=2340,
    cache_hit=False,
    status="success",
    region="us-east-1",
    routing_strategy="cost",
)
```

### Distributed Tracing

**File**: `app/middleware/tracing.py`

OpenTelemetry-based distributed tracing with OTLP export.

#### Key Features

- Automatic trace context propagation
- Span creation for all major operations
- Exception recording with stack traces
- Integration with Jaeger and Zipkin

#### Initialization

```python
from app.middleware.tracing import tracing_middleware

# Initialize on startup
tracing_middleware.initialize()
```

#### Tracing Operations

```python
# Trace a complete request
with tracing_middleware.trace_request(
    operation_name="chat_completion",
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    max_tokens=2000,
    routing_strategy="cost",
) as span:
    # Your request handling code
    response = await handle_request(...)
    
    # Record success
    tracing_middleware.end_span_success(
        span,
        output_tokens=response.output_tokens,
        cost=response.cost,
    )
```

### Structured Logging

**File**: `app/middleware/logging.py`

JSON-formatted structured logging with trace correlation.

#### Key Features

- JSON output format for machine parsing
- Automatic trace ID correlation
- Contextual logging with request/response data
- CloudWatch integration

#### Initialization

```python
from app.middleware.logging import logging_middleware

# Initialize on startup
logging_middleware.initialize()
```

#### Logging Events

```python
# Log request
logging_middleware.log_request(
    client_id=str(account.id),
    request_data={
        "model": "anthropic.claude-3-sonnet-20240229-v1:0",
        "max_tokens": 2000,
        "routing_strategy": "cost",
    },
)

# Log response
logging_middleware.log_response(
    client_id=str(account.id),
    request_data=request_data,
    response_data={
        "model": selected_model,
        "input_tokens": 1500,
        "output_tokens": 500,
        "cost": 0.0125,
        "cache_hit": False,
    },
    latency_ms=2340,
)

# Log error
logging_middleware.log_error(
    client_id=str(account.id),
    error=exception,
    request_data=request_data,
)
```

## Metrics Reference

### Request Metrics

#### `fluxai_requests_total`

Total number of requests processed.

**Type**: Counter  
**Labels**: `account_id`, `model`, `region`, `status`

```promql
# Total requests
sum(fluxai_requests_total)

# Requests per model
sum by(model) (fluxai_requests_total)

# Success rate
sum(rate(fluxai_requests_total{status="success"}[5m])) / 
sum(rate(fluxai_requests_total[5m]))
```

#### `fluxai_request_duration_seconds`

Request latency distribution.

**Type**: Histogram  
**Labels**: `account_id`, `model`, `region`  
**Buckets**: 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0

```promql
# Average latency
histogram_quantile(0.5, sum(rate(fluxai_request_duration_seconds_bucket[5m])) by (le))

# 95th percentile latency
histogram_quantile(0.95, sum(rate(fluxai_request_duration_seconds_bucket[5m])) by (le))

# 99th percentile latency
histogram_quantile(0.99, sum(rate(fluxai_request_duration_seconds_bucket[5m])) by (le))
```

#### `fluxai_request_errors_total`

Total number of errors.

**Type**: Counter  
**Labels**: `model`, `region`, `error_type`

```promql
# Error rate
rate(fluxai_request_errors_total[5m])

# Errors by type
sum by(error_type) (fluxai_request_errors_total)
```

### Token Metrics

#### `fluxai_input_tokens_total`

Total input tokens processed.

**Type**: Counter  
**Labels**: `model`, `region`, `client`

```promql
# Total input tokens
sum(fluxai_input_tokens_total)

# Input tokens per minute
rate(fluxai_input_tokens_total[1m]) * 60
```

#### `fluxai_output_tokens_total`

Total output tokens generated.

**Type**: Counter  
**Labels**: `model`, `region`, `client`

```promql
# Total output tokens
sum(fluxai_output_tokens_total)

# Output tokens per minute
rate(fluxai_output_tokens_total[1m]) * 60
```

### Cost Metrics

#### `fluxai_cost_dollars_total`

Total cost in dollars.

**Type**: Counter  
**Labels**: `account_id`, `model`, `region`

```promql
# Total cost
sum(fluxai_cost_dollars_total)

# Cost by model
sum by(model) (fluxai_cost_dollars_total)

# Daily cost estimate
sum(rate(fluxai_cost_dollars_total[1h])) * 24
```

#### `fluxai_cost_per_request_dollars`

Cost per request distribution.

**Type**: Histogram  
**Labels**: `model`, `region`  
**Buckets**: 0.0001, 0.001, 0.01, 0.1, 1.0, 10.0

```promql
# Average cost per request
histogram_quantile(0.5, sum(rate(fluxai_cost_per_request_dollars_bucket[5m])) by (le, model))

# Most expensive model
topk(1, sum by(model) (rate(fluxai_cost_per_request_dollars_sum[5m])) / 
           sum by(model) (rate(fluxai_cost_per_request_dollars_count[5m])))
```

### Cache Metrics

#### `fluxai_cache_hits_total`

Total cache hits.

**Type**: Counter  
**Labels**: `account_id`, `model`, `cache_type`

```promql
# Total cache hits
sum(fluxai_cache_hits_total)

# Cache hits by type
sum by(cache_type) (fluxai_cache_hits_total)
```

#### `fluxai_cache_misses_total`

Total cache misses.

**Type**: Counter  
**Labels**: `account_id`, `model`

```promql
# Total cache misses
sum(fluxai_cache_misses_total)
```

#### `fluxai_cache_hit_rate`

Current cache hit rate (0-1).

**Type**: Gauge  
**Labels**: `model`

```promql
# Overall cache hit rate
fluxai_cache_hit_rate

# Cache hit rate by model
avg by(model) (fluxai_cache_hit_rate)
```

#### `fluxai_cache_savings_dollars_total`

Total cost savings from cache.

**Type**: Counter  
**Labels**: `model`

```promql
# Total savings
sum(fluxai_cache_savings_dollars_total)

# Savings rate
rate(fluxai_cache_savings_dollars_total[1h])

# Savings percentage
sum(fluxai_cache_savings_dollars_total) / 
(sum(fluxai_cost_dollars_total) + sum(fluxai_cache_savings_dollars_total)) * 100
```

### Model Metrics

#### `fluxai_model_latency_seconds`

Model inference latency.

**Type**: Histogram  
**Labels**: `model`, `region`  
**Buckets**: 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0

```promql
# Median latency by model
histogram_quantile(0.5, sum(rate(fluxai_model_latency_seconds_bucket[5m])) by (le, model))

# Slowest models
topk(5, histogram_quantile(0.95, sum(rate(fluxai_model_latency_seconds_bucket[5m])) by (le, model)))
```

#### `fluxai_model_availability`

Model availability (0-1).

**Type**: Gauge  
**Labels**: `model`, `region`

```promql
# All models availability
fluxai_model_availability

# Models with low availability (<99%)
fluxai_model_availability < 0.99
```

#### `fluxai_model_error_rate`

Model error rate (0-1).

**Type**: Gauge  
**Labels**: `model`, `region`

```promql
# Models with high error rate
fluxai_model_error_rate > 0.05

# Error rate by model
avg by(model) (fluxai_model_error_rate)
```

### System Metrics

#### `fluxai_active_connections`

Current active connections.

**Type**: Gauge

```promql
# Current connections
fluxai_active_connections

# Connection spikes
delta(fluxai_active_connections[1m]) > 100
```

#### `fluxai_queue_depth`

Current request queue depth.

**Type**: Gauge

```promql
# Current queue depth
fluxai_queue_depth

# Queue saturation
fluxai_queue_depth > 1000
```

### Routing Metrics

#### `fluxai_routing_strategy_total`

Requests by routing strategy.

**Type**: Counter  
**Labels**: `strategy`, `model`

```promql
# Requests by strategy
sum by(strategy) (fluxai_routing_strategy_total)

# Most used routing strategy
topk(1, sum by(strategy) (rate(fluxai_routing_strategy_total[5m])))
```

## Tracing Guide

### Trace Structure

Each request generates a trace with multiple spans:

```
Request Trace
├── chat_completion (root span)
│   ├── cache.lookup
│   │   └── embeddings.generate (if semantic cache)
│   ├── routing.decide
│   ├── bedrock.invoke_model
│   └── cost.calculate
```

### Trace Attributes

Standard attributes included in traces:

- `model.id`: Model identifier
- `model.max_tokens`: Maximum tokens requested
- `routing.strategy`: Routing strategy used
- `bedrock.region`: AWS region
- `cache.type`: Cache type (exact/semantic)
- `cost.total`: Total request cost

### Trace Correlation

Traces are correlated with logs using trace IDs:

```json
{
  "event": "request_completed",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "model": "anthropic.claude-3-sonnet-20240229-v1:0",
  "latency_ms": 2340
}
```

### Querying Traces

Use Jaeger UI to query traces:

- By service: `service=fluxai-gateway`
- By operation: `operation=chat_completion`
- By duration: `duration>2s`
- By error: `error=true`
- By tag: `model.id=anthropic.claude-3-sonnet-20240229-v1:0`

## Logging Guide

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for degraded conditions
- **ERROR**: Error messages for failures

### Log Format

All logs are output in JSON format:

```json
{
  "event": "request_completed",
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "client_id": "550e8400-e29b-41d4-a716-446655440000",
  "model": "anthropic.claude-3-sonnet-20240229-v1:0",
  "input_tokens": 1500,
  "output_tokens": 500,
  "cost": 0.0125,
  "cache_hit": false,
  "latency_ms": 2340,
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7"
}
```

### Common Log Events

- `request_received`: Request ingress
- `request_completed`: Successful completion
- `request_error`: Request failure
- `cache_hit`: Cache hit event
- `routing_decision`: Routing selection
- `model_health`: Model health check

### Searching Logs

CloudWatch Insights queries:

```sql
# Find slow requests
fields @timestamp, client_id, model, latency_ms
| filter latency_ms > 5000
| sort latency_ms desc

# Find errors
fields @timestamp, client_id, error_type, error_message
| filter event = "request_error"

# Calculate cache hit rate
stats sum(cache_hit) / count(*) as hit_rate by bin(5m)

# Find expensive requests
fields @timestamp, model, cost
| filter cost > 0.1
| sort cost desc
```

## Integration Examples

### Complete Request Handling

```python
from fastapi import APIRouter, HTTPException
from app.services.metrics import metrics_service
from app.middleware.tracing import tracing_middleware
from app.middleware.logging import logging_middleware

router = APIRouter()

@router.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest, account: Account):
    start_time = time.time()
    
    # Log request
    logging_middleware.log_request(
        client_id=str(account.id),
        request_data={
            "model": request.model,
            "max_tokens": request.max_tokens,
            "routing_strategy": request.routing_strategy or "auto",
        },
    )
    
    # Start trace
    with tracing_middleware.trace_request(
        operation_name="chat_completion",
        model_id=request.model,
        max_tokens=request.max_tokens,
        routing_strategy=request.routing_strategy or "auto",
    ) as request_span:
        try:
            # Increment active connections
            metrics_service.increment_active_connections()
            
            # Check cache
            with tracing_middleware.trace_cache_lookup(
                model_id=request.model,
                cache_type="semantic",
            ) as cache_span:
                cached = await cache_service.get(request.messages)
                
                if cached:
                    # Record cache hit
                    metrics_service.record_cache_hit(
                        account_id=account.id,
                        model_id=request.model,
                        cache_type="semantic",
                    )
                    
                    # Calculate savings
                    savings = cost_calculator.calculate_cache_savings(
                        model_id=request.model,
                        input_tokens=cached.input_tokens,
                        output_tokens=cached.output_tokens,
                    )
                    
                    metrics_service.record_cache_savings(
                        model_id=request.model,
                        savings_dollars=savings.total_savings,
                    )
                    
                    # Log cache hit
                    logging_middleware.log_cache_hit(
                        client_id=str(account.id),
                        model_id=request.model,
                        cache_type="semantic",
                        similarity=cached.similarity,
                        savings_dollars=savings.total_savings,
                    )
                    
                    tracing_middleware.end_span_success(
                        cache_span,
                        cache_hit=True,
                        similarity=cached.similarity,
                    )
                    
                    response_data = {
                        "model": request.model,
                        "input_tokens": cached.input_tokens,
                        "output_tokens": cached.output_tokens,
                        "cost": 0.0,  # Cached, no cost
                        "cache_hit": True,
                        "cache_type": "semantic",
                        "savings_dollars": savings.total_savings,
                    }
                    
                    latency_ms = int((time.time() - start_time) * 1000)
                    
                    # Record metrics
                    await metrics_service.record_request(
                        account_id=account.id,
                        model_id=request.model,
                        input_tokens=cached.input_tokens,
                        output_tokens=cached.output_tokens,
                        cost=0.0,
                        latency_ms=latency_ms,
                        cache_hit=True,
                        status="success",
                        region="us-east-1",
                        routing_strategy=request.routing_strategy or "auto",
                        cache_type="semantic",
                    )
                    
                    # Log response
                    logging_middleware.log_response(
                        client_id=str(account.id),
                        request_data={"model": request.model},
                        response_data=response_data,
                        latency_ms=latency_ms,
                    )
                    
                    tracing_middleware.end_span_success(
                        request_span,
                        cache_hit=True,
                        cost=0.0,
                    )
                    
                    return cached.response
                else:
                    # Record cache miss
                    metrics_service.record_cache_miss(
                        account_id=account.id,
                        model_id=request.model,
                    )
                    
                    tracing_middleware.end_span_success(
                        cache_span,
                        cache_hit=False,
                    )
            
            # Call Bedrock
            with tracing_middleware.trace_bedrock_call(
                model_id=request.model,
                input_tokens=len(request.messages),
                max_tokens=request.max_tokens,
            ) as bedrock_span:
                response = await bedrock.invoke_model(
                    model_id=request.model,
                    messages=request.messages,
                    max_tokens=request.max_tokens,
                )
                
                tracing_middleware.end_span_success(
                    bedrock_span,
                    output_tokens=response.output_tokens,
                )
            
            # Calculate cost
            with tracing_middleware.trace_cost_calculation(
                model_id=request.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
            ) as cost_span:
                cost_breakdown = cost_calculator.calculate_cost(
                    model_id=request.model,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                )
                
                tracing_middleware.end_span_success(
                    cost_span,
                    cost=cost_breakdown.total_cost,
                )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Record metrics
            await metrics_service.record_request(
                account_id=account.id,
                model_id=request.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost=cost_breakdown.total_cost,
                latency_ms=latency_ms,
                cache_hit=False,
                status="success",
                region="us-east-1",
                routing_strategy=request.routing_strategy or "auto",
            )
            
            response_data = {
                "model": request.model,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost": cost_breakdown.total_cost,
                "cache_hit": False,
            }
            
            # Log response
            logging_middleware.log_response(
                client_id=str(account.id),
                request_data={"model": request.model},
                response_data=response_data,
                latency_ms=latency_ms,
            )
            
            tracing_middleware.end_span_success(
                request_span,
                cache_hit=False,
                cost=cost_breakdown.total_cost,
                output_tokens=response.output_tokens,
            )
            
            return response
            
        except Exception as e:
            # Record error
            metrics_service.record_error(
                model_id=request.model,
                region="us-east-1",
                error_type=type(e).__name__,
            )
            
            # Log error
            logging_middleware.log_error(
                client_id=str(account.id),
                error=e,
                request_data={"model": request.model},
            )
            
            # Record in trace
            tracing_middleware.record_exception(request_span, e)
            
            raise HTTPException(status_code=500, detail=str(e))
            
        finally:
            # Decrement active connections
            metrics_service.decrement_active_connections()
```

## Grafana Dashboards

### Dashboard Setup

1. **Add Prometheus Data Source**
   - URL: `http://prometheus:9090`
   - Access: Server (default)

2. **Add Jaeger Data Source**
   - URL: `http://jaeger:16686`
   - Access: Server (default)

### Recommended Dashboards

#### Overview Dashboard

Panels:
- Request rate (requests/sec)
- Average latency (p50, p95, p99)
- Error rate
- Cache hit rate
- Total cost ($/hour)
- Active connections

#### Cost Dashboard

Panels:
- Cost by model (pie chart)
- Cost over time (line chart)
- Cost per request (histogram)
- Cache savings (line chart)
- Daily cost estimate (single stat)
- Most expensive clients (table)

#### Performance Dashboard

Panels:
- Request latency by model (heatmap)
- Throughput by endpoint (bar chart)
- Queue depth (line chart)
- Connection pool usage (gauge)
- Token processing rate (line chart)

#### Cache Dashboard

Panels:
- Cache hit rate (gauge)
- Cache hits vs. misses (stacked area)
- Semantic vs. exact cache hits (pie chart)
- Cache savings over time (line chart)
- Top cached models (table)

#### Model Health Dashboard

Panels:
- Model availability (gauge panel)
- Model error rate (bar chart)
- Model latency comparison (box plot)
- Request distribution by model (pie chart)

## Alerting

### Prometheus Alerts

Create `alerts.yml`:

```yaml
groups:
  - name: fluxai_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(fluxai_request_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
      
      # Low cache hit rate
      - alert: LowCacheHitRate
        expr: fluxai_cache_hit_rate < 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value }}"
      
      # High latency
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(fluxai_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High request latency"
          description: "P95 latency is {{ $value }}s"
      
      # Model unavailable
      - alert: ModelUnavailable
        expr: fluxai_model_availability < 0.9
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Model availability low"
          description: "{{ $labels.model }} availability is {{ $value }}"
      
      # High cost
      - alert: HighHourlyCost
        expr: rate(fluxai_cost_dollars_total[1h]) > 10
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "High hourly cost"
          description: "Cost rate is ${{ $value }}/hour"
```

### Alert Routing

Configure Alertmanager:

```yaml
route:
  receiver: 'slack-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#fluxai-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

## Troubleshooting

### Metrics Not Appearing

**Problem**: Prometheus shows no data

**Solutions**:
1. Check metrics endpoint: `curl http://localhost:8080/metrics`
2. Verify Prometheus configuration:
   ```yaml
   scrape_configs:
     - job_name: 'fluxai'
       static_configs:
         - targets: ['localhost:8080']
   ```
3. Check metrics initialization:
   ```python
   metrics_service.initialize()
   ```

### Traces Not Showing in Jaeger

**Problem**: No traces in Jaeger UI

**Solutions**:
1. Verify OTLP endpoint configuration:
   ```python
   OTLP_ENDPOINT = "localhost:4317"
   ```
2. Check collector status: `curl http://localhost:13133/`
3. Verify trace initialization:
   ```python
   tracing_middleware.initialize()
   ```

### Logs Not Structured

**Problem**: Logs are plain text instead of JSON

**Solutions**:
1. Check logging initialization:
   ```python
   logging_middleware.initialize()
   ```
2. Verify LOG_FORMAT setting: `LOG_FORMAT=json`
3. Check structlog configuration in code

### High Memory Usage

**Problem**: Memory usage growing over time

**Solutions**:
1. Reduce metrics cardinality (limit label values)
2. Adjust Prometheus retention: `--storage.tsdb.retention.time=15d`
3. Enable metric relabeling to drop unused series

### Missing Trace Correlation

**Problem**: Logs don't include trace IDs

**Solutions**:
1. Ensure tracing middleware initialized first
2. Use tracing context managers:
   ```python
   with tracing_middleware.trace_request(...) as span:
       logging_middleware.log_request(...)
   ```
3. Check trace ID extraction:
   ```python
   trace_id = tracing_middleware.get_current_trace_id()
   ```

## Configuration Examples

### Prometheus Configuration

`prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fluxai-gateway'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
```

### OpenTelemetry Collector Configuration

`otel-collector-config.yaml`:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  
  prometheus:
    endpoint: "0.0.0.0:8889"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

### Docker Compose for Observability Stack

`docker-compose.observability.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
  
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "14250:14250"  # gRPC
      - "14268:14268"  # HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true
  
  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    ports:
      - "4317:4317"    # OTLP gRPC
      - "8889:8889"    # Prometheus exporter
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    depends_on:
      - jaeger

volumes:
  prometheus-data:
  grafana-data:
```

---

## Next Steps

1. **Set up Grafana**: Import dashboards and configure alerts
2. **Configure CloudWatch**: Set up log shipping to AWS
3. **Create Custom Dashboards**: Build team-specific views
4. **Set Up Alerts**: Configure PagerDuty or Slack integration
5. **Monitor Costs**: Track and optimize Bedrock spending

For more information, see:
- [FluxAI Technical Specification](fluxai-technical-spec.md)
- [Cost Calculator Documentation](COST_CALCULATOR.md)
- [Semantic Cache Documentation](SEMANTIC_CACHE.md)
