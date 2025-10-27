# FluxAI Dashboard - Quick Reference

## 🚀 Start Dashboard

### Windows (PowerShell)
```powershell
.\start-dashboard.ps1
```

### Linux/Mac
```bash
chmod +x start-dashboard.sh
./start-dashboard.sh
```

### Manual Start
```bash
streamlit run dashboard/app.py
```

Dashboard opens at: **http://localhost:8501**

---

## 📊 Dashboard Tabs

| Tab | Purpose | Key Metrics |
|-----|---------|-------------|
| **📈 Overview** | System health at a glance | Requests, Latency, Cost, Errors |
| **💰 Cost Analytics** | Cost tracking & forecasting | Total cost, Cost/request, Savings, Forecast |
| **🗄️ Cache Performance** | Cache effectiveness | Hit rate, Savings, Tokens saved |
| **🤖 Model Health** | Model monitoring | Availability, Error rate, Latency |
| **🔍 Tracing** | Request debugging | Trace search, Span timeline |

---

## ⚙️ Sidebar Controls

### Time Range
- **5m, 15m** - Real-time monitoring
- **1h, 6h** - Recent activity
- **24h, 7d, 30d** - Historical analysis

### Auto-Refresh
- Enable for live monitoring
- Set interval (5-60 seconds)
- Disable for historical analysis

### Filters
- **Account** - Multi-tenant filtering
- **Models** - Specific model analysis
- **Regions** - Geographic filtering

---

## 🔍 Key Features

### Overview Page
- **Request Rate Chart** - Requests/second over time
- **Latency Distribution** - P50, P95, P99 percentiles
- **Token Usage** - Input/output token trends

### Cost Analytics
- **Cost by Model** - Pie chart of model costs
- **Cost Timeline** - Cumulative cost tracking
- **Expensive Requests** - Top 10 costly requests
- **Forecast** - Daily/monthly cost projections

### Cache Performance
- **Hit Rate Timeline** - Cache effectiveness over time
- **Cache Type Distribution** - Exact vs Semantic hits
- **Savings Chart** - Cumulative cost savings
- **Per-Model Stats** - Cache performance by model

### Model Health
- **Status Cards** - Visual health indicators
  - 🟢 Healthy (≥99% availability)
  - 🟡 Degraded (95-99% availability)
  - 🔴 Unhealthy (<95% availability)
- **Latency Comparison** - Bar chart of model latencies
- **Usage Timeline** - Model request distribution

### Tracing
- **Trace Search** - Find specific request traces
- **Filter Options**:
  - By Trace ID
  - Minimum duration
  - Errors only
- **Span Timeline** - Visual trace breakdown
- **Detailed View** - Complete span information

---

## 📈 Prometheus Queries Used

### Request Rate
```promql
sum(rate(fluxai_requests_total[5m]))
```

### P95 Latency
```promql
histogram_quantile(0.95, sum(rate(fluxai_request_duration_seconds_bucket[5m])) by (le)) * 1000
```

### Cache Hit Rate
```promql
sum(rate(fluxai_cache_hits_total[5m])) / 
(sum(rate(fluxai_cache_hits_total[5m])) + sum(rate(fluxai_cache_misses_total[5m])))
```

### Total Cost
```promql
sum(increase(fluxai_cost_dollars_total[1h]))
```

---

## 🎯 Common Tasks

### Monitor Real-Time Performance
1. Select **Overview** tab
2. Set time range to **15m**
3. Enable **auto-refresh** (30s interval)
4. Watch request rate and latency charts

### Analyze Daily Costs
1. Select **Cost Analytics** tab
2. Set time range to **24h**
3. Review:
   - Total cost metric
   - Cost by model pie chart
   - Cost timeline
   - Expensive requests table

### Optimize Cache
1. Select **Cache Performance** tab
2. Set time range to **7d**
3. Check:
   - Hit rate (target: >40%)
   - Savings timeline
   - Per-model performance
4. Identify models with low hit rates

### Debug Slow Requests
1. Select **Tracing** tab
2. Set **Min Duration** to 5000ms
3. Review slow traces
4. Click trace ID for detailed spans
5. Identify bottlenecks in span timeline

### Check Model Health
1. Select **Model Health** tab
2. Review status cards
3. Look for:
   - 🔴 Unhealthy models
   - High error rates (>5%)
   - High latencies (P95 >5s)
4. Check usage timeline for anomalies

---

## ⚡ Performance Tips

### For Real-Time Monitoring
- Use short time ranges (5m, 15m)
- Enable auto-refresh
- Filter by specific models/regions

### For Historical Analysis
- Use longer time ranges (7d, 30d)
- Disable auto-refresh
- Export data if needed

### For Large Deployments
- Use filters to reduce data volume
- Consider shorter retention periods
- Aggregate data in PostgreSQL

---

## 🔧 Troubleshooting

### Dashboard Won't Load
```bash
# Check if port is in use
netstat -ano | findstr :8501

# Use different port
streamlit run dashboard/app.py --server.port 8502
```

### No Data Showing
1. Check Prometheus: `curl http://localhost:9090/-/healthy`
2. Check metrics endpoint: `curl http://localhost:8080/metrics`
3. Verify database connection
4. Check sidebar connection status

### Slow Loading
1. Reduce time range
2. Use filters (account, model, region)
3. Disable auto-refresh
4. Check Prometheus performance

### Connection Errors
- **Prometheus**: Update `PROMETHEUS_URL` in sidebar status
- **Database**: Check `DATABASE_URL` environment variable
- **FluxAI Gateway**: Ensure gateway is running

---

## 🎨 Customization

### Change Theme
```bash
# Create ~/.streamlit/config.toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"
```

### Custom Port
```bash
streamlit run dashboard/app.py --server.port 8502
```

### Environment Variables
```bash
export PROMETHEUS_URL=http://prometheus:9090
export DATABASE_URL=postgresql://user:pass@host:5432/db
export AUTO_REFRESH=true
export REFRESH_INTERVAL=30
```

---

## 📱 Mobile Access

Dashboard is responsive and works on mobile devices:

1. Get server IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
2. Access from mobile: `http://<server-ip>:8501`
3. Use landscape mode for charts
4. Pinch to zoom on complex visualizations

---

## 🔐 Security

### Enable Authentication
```python
# Add to dashboard/app.py
import streamlit as st
import os

def check_password():
    # NOTE: For security, use environment variables or a secrets manager instead of hardcoded passwords.
    # Example: Set DASHBOARD_PASSWORD in your environment.
    def password_entered():
        expected_password = os.environ.get("DASHBOARD_PASSWORD")
        if st.session_state["password"] == expected_password:
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state.get("password_correct", False)

if not check_password():
    st.stop()
```

### Network Security
- Run behind reverse proxy (nginx)
- Use HTTPS in production
- Implement IP whitelisting
- Use VPN for remote access

---

## 📊 Sample Dashboards

### DevOps Dashboard
- Time Range: 1h
- Auto-Refresh: 30s
- Focus: Overview + Model Health

### Finance Dashboard
- Time Range: 24h
- Auto-Refresh: Off
- Focus: Cost Analytics + Forecasting

### SRE Dashboard
- Time Range: 15m
- Auto-Refresh: 15s
- Focus: Overview + Tracing

---

## 🆘 Support

- **Documentation**: [dashboard/README.md](README.md)
- **Issues**: GitHub Issues
- **Questions**: Check Streamlit docs
- **Updates**: Pull latest from main branch

---

**Last Updated**: October 2025  
**Version**: 1.0.0
