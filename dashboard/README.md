# FluxAI Observability Dashboard

Interactive real-time dashboard for monitoring FluxAI Gateway performance, costs, and health.

## 🎯 Features

- **📈 Real-time Metrics**: Live monitoring of requests, latency, and throughput
- **💰 Cost Analytics**: Detailed cost tracking and forecasting
- **🗄️ Cache Performance**: Cache hit rates and savings analysis
- **🤖 Model Health**: Model availability and performance monitoring
- **🔍 Distributed Tracing**: Request trace visualization

## 🚀 Quick Start

### Installation

```bash
# Install dashboard dependencies
pip install streamlit plotly pandas sqlalchemy requests

# Or install all FluxAI dependencies
pip install -r requirements.txt
```

### Running the Dashboard

```bash
# From the fluxai root directory
streamlit run dashboard/app.py

# Or with custom port
streamlit run dashboard/app.py --server.port 8501
```

The dashboard will open automatically in your browser at `http://localhost:8501`.

## 📊 Dashboard Pages

### 1. Overview

Real-time system overview with:
- Total requests and throughput
- Average latency (P50, P95, P99)
- Total cost and cost per request
- Error rate
- Request rate chart
- Latency distribution
- Token usage trends

### 2. Cost Analytics

Comprehensive cost tracking:
- Total cost and cost per request
- Cache savings
- Cost distribution by model (pie chart)
- Cumulative cost over time
- Cost forecast (daily/monthly projections)
- Most expensive requests table

### 3. Cache Performance

Cache effectiveness monitoring:
- Cache hit rate
- Total hits and cost saved
- Tokens saved
- Hit rate timeline
- Cache type distribution (exact vs semantic)
- Cumulative savings chart
- Cache performance by model

### 4. Model Health

Model monitoring and comparison:
- Model status cards (healthy/degraded/unhealthy)
- Availability and error rates
- Latency comparison (P50/P95/P99)
- Model usage over time
- Detailed health metrics table

### 5. Distributed Tracing

Request trace exploration:
- Recent traces list
- Trace search by ID
- Filter by duration and errors
- Span timeline visualization
- Detailed span information

## ⚙️ Configuration

### Environment Variables

```bash
# Prometheus endpoint
PROMETHEUS_URL=http://localhost:9090

# Database connection
DATABASE_URL=postgresql://fluxai:your_password@localhost:5432/fluxai

# Auto-refresh settings
AUTO_REFRESH=true
REFRESH_INTERVAL=30

# Jaeger endpoint (for tracing)
JAEGER_URL=http://localhost:16686
```

### Dashboard Settings

Configure via the sidebar:
- **Time Range**: 5m, 15m, 1h, 6h, 24h, 7d, 30d
- **Auto-Refresh**: Enable/disable with custom interval
- **Filters**: Filter by account, model, region

## 📈 Metrics Data Sources

### Prometheus Metrics

The dashboard queries Prometheus for real-time metrics:

```promql
# Request rate
sum(rate(fluxai_requests_total[5m]))

# Latency percentiles
histogram_quantile(0.95, sum(rate(fluxai_request_duration_seconds_bucket[5m])) by (le))

# Cost tracking
sum(increase(fluxai_cost_dollars_total[1h]))

# Cache hit rate
sum(rate(fluxai_cache_hits_total[5m])) / 
(sum(rate(fluxai_cache_hits_total[5m])) + sum(rate(fluxai_cache_misses_total[5m])))
```

### PostgreSQL Data

Historical data from PostgreSQL:
- Request metrics (detailed request logs)
- Cost analytics (aggregated cost data)
- Trace information (request traces)
- Account information

## 🎨 Customization

### Adding Custom Charts

Edit `dashboard/app.py`:

```python
def render_custom_view(self, time_range: str):
    """Render custom dashboard view."""
    st.header("Custom Metrics")
    
    # Fetch data
    data = self.metrics_client.get_custom_metrics(time_range)
    
    # Create chart
    fig = px.line(data, x="timestamp", y="value", title="Custom Metric")
    st.plotly_chart(fig, use_container_width=True)
```

### Adding New Metrics Queries

Edit `dashboard/metrics_client.py`:

```python
def get_custom_metrics(self, time_range: str) -> pd.DataFrame:
    """Get custom metrics from Prometheus."""
    query = "your_prometheus_query_here"
    result = self._query_prometheus_range(query, time_range)
    
    # Process and return data
    return pd.DataFrame(...)
```

## 🔧 Troubleshooting

### Dashboard Won't Start

```bash
# Check if port 8501 is available
netstat -ano | findstr :8501

# Use different port
streamlit run dashboard/app.py --server.port 8502
```

### No Data Showing

1. **Check Prometheus connection**:
   ```bash
   curl http://localhost:9090/-/healthy
   ```

2. **Check database connection**:
   ```bash
   psql postgresql://fluxai:dev_password@localhost:5432/fluxai
   ```

3. **Verify metrics are being collected**:
   ```bash
   curl http://localhost:8080/metrics
   ```

### Slow Performance

1. **Reduce time range**: Use shorter time ranges (5m, 15m) instead of 7d, 30d
2. **Disable auto-refresh**: Turn off auto-refresh when not needed
3. **Filter data**: Use account/model/region filters to reduce data volume

## 📱 Deployment

### Docker Deployment

Create `Dockerfile.dashboard`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy dashboard files
COPY dashboard/ /app/dashboard/
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir streamlit plotly pandas sqlalchemy requests

# Expose Streamlit port
EXPOSE 8501

# Run dashboard
CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:

1. Create a `.env` file with your environment variables:

   ```env
   PROMETHEUS_URL=http://prometheus:9090
   DATABASE_URL=postgresql://fluxai:yourpassword@db:5432/fluxai
### Kubernetes Deployment

Create `k8s/dashboard-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fluxai-dashboard
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fluxai-dashboard
  template:
    metadata:
      labels:
        app: fluxai-dashboard
    spec:
      containers:
      - name: dashboard
        image: fluxai-dashboard:latest
        ports:
        - containerPort: 8501
        env:
        - name: PROMETHEUS_URL
          value: "http://prometheus-service:9090"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: fluxai-secrets
              key: database-url
---
apiVersion: v1
kind: Service
metadata:
  name: fluxai-dashboard
spec:
  selector:
    app: fluxai-dashboard
  ports:
  - port: 8501
    targetPort: 8501
  type: LoadBalancer
```

## 🎯 Best Practices

### 1. Time Range Selection

- **Real-time monitoring**: Use 5m or 15m
- **Recent analysis**: Use 1h or 6h
- **Daily review**: Use 24h
- **Trend analysis**: Use 7d or 30d

### 2. Auto-Refresh

- Enable for real-time monitoring
- Set interval to 30-60 seconds for production
- Disable when analyzing historical data

### 3. Filters

- Use account filters for multi-tenant monitoring
- Filter by model for specific model analysis
- Use region filters for geo-specific analysis

### 4. Performance

- Cache Prometheus queries (built-in)
- Use materialized views for database queries
- Limit time ranges for large datasets
- Use sampling for high-cardinality metrics

## 🔐 Security

### Authentication

Add basic authentication:

```python
# In dashboard/app.py
import streamlit as st

def check_password():
    """Returns True if password is correct."""
    def password_entered():
        if st.session_state["password"] == "your_password_here":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("Password incorrect")
        return False
    else:
        return True

# At the start of main()
if not check_password():
    st.stop()
```

### Role-Based Access

Integrate with your auth system:

```python
from app.auth import get_current_user

user = get_current_user()
if not user.has_permission("view_dashboard"):
    st.error("Access denied")
    st.stop()
```

## 📚 Additional Resources

- **Streamlit Documentation**: https://docs.streamlit.io/
- **Plotly Charts**: https://plotly.com/python/
- **Prometheus Queries**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **FluxAI Documentation**: [../README.md](../README.md)

## 🤝 Contributing

To add new dashboard features:

1. Create new view method in `ObservabilityDashboard` class
2. Add data fetching method in `MetricsClient` class
3. Add tab in main dashboard
4. Update this documentation

## 📝 License

Same license as FluxAI Gateway. See [LICENSE](../LICENSE).

---

**Need Help?** Check the [Troubleshooting](#troubleshooting) section or open an issue on GitHub.
