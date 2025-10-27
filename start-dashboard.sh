#!/bin/bash
# FluxAI Observability Dashboard Launcher

echo "🚀 Starting FluxAI Observability Dashboard..."

# Check if Streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit is not installed. Installing..."
    pip install streamlit plotly pandas sqlalchemy requests
fi

# Check if Prometheus is running
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus is running"
else
    echo "⚠️  Warning: Prometheus not reachable at http://localhost:9090"
    echo "   Dashboard will have limited functionality without Prometheus"
fi

# Check if PostgreSQL is running
if psql -U fluxai -h localhost -d fluxai -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  Warning: PostgreSQL not reachable"
    echo "   Historical data queries will not work"
fi

echo ""
echo "📊 Dashboard Configuration:"
echo "   Prometheus: ${PROMETHEUS_URL:-http://localhost:9090}"
echo "   Database:   ${DATABASE_URL:-postgresql://fluxai:dev_password@localhost:5432/fluxai}"
echo ""

# Start Streamlit
echo "🌐 Starting dashboard at http://localhost:8501"
echo ""
streamlit run dashboard/app.py
