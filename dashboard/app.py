"""
FluxAI Observability Dashboard

Real-time observability dashboard built with Streamlit.
Provides comprehensive monitoring of:
- Request metrics and performance
- Cost analytics and forecasting
- Cache performance
- Model health
- Distributed tracing
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.metrics_client import MetricsClient
from dashboard.config import DashboardConfig

# Page configuration
st.set_page_config(
    page_title="FluxAI Observability",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .success-metric {
        color: #28a745;
        font-weight: bold;
    }
    .warning-metric {
        color: #ffc107;
        font-weight: bold;
    }
    .danger-metric {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


class ObservabilityDashboard:
    """Main observability dashboard application."""
    
    def __init__(self):
        self.config = DashboardConfig()
        self.metrics_client = MetricsClient(
            prometheus_url=self.config.prometheus_url,
            database_url=self.config.database_url,
        )
        
    def run(self):
        """Run the dashboard application."""
        # Sidebar
        self.render_sidebar()
        
        # Main content
        st.title("📊 FluxAI Observability Dashboard")
        st.markdown("---")
        
        # Get selected time range
        time_range = st.session_state.get("time_range", "1h")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Overview",
            "💰 Cost Analytics",
            "🗄️ Cache Performance",
            "🤖 Model Health",
            "🔍 Tracing"
        ])
        
        with tab1:
            self.render_overview(time_range)
        
        with tab2:
            self.render_cost_analytics(time_range)
        
        with tab3:
            self.render_cache_performance(time_range)
        
        with tab4:
            self.render_model_health(time_range)
        
        with tab5:
            self.render_tracing()
    
    def render_sidebar(self):
        """Render sidebar with filters and settings."""
        with st.sidebar:
            st.title("⚙️ Settings")
            
            # Time range selector
            st.subheader("Time Range")
            time_range = st.selectbox(
                "Select time range",
                ["5m", "15m", "1h", "6h", "24h", "7d", "30d"],
                index=2,  # Default to 1h
                key="time_range",
            )
            
            # Auto-refresh
            st.subheader("Auto-Refresh")
            auto_refresh = st.checkbox("Enable auto-refresh", value=True)
            if auto_refresh:
                refresh_interval = st.slider(
                    "Refresh interval (seconds)",
                    min_value=5,
                    max_value=60,
                    value=30,
                )
                st.session_state["auto_refresh"] = True
                st.session_state["refresh_interval"] = refresh_interval
            else:
                st.session_state["auto_refresh"] = False
            
            # Filters
            st.subheader("Filters")
            
            # Account filter
            accounts = self.metrics_client.get_accounts()
            selected_account = st.selectbox(
                "Account",
                ["All"] + accounts,
                key="selected_account",
            )
            
            # Model filter
            models = self.metrics_client.get_models()
            selected_models = st.multiselect(
                "Models",
                models,
                default=models[:5] if len(models) > 5 else models,
                key="selected_models",
            )
            
            # Region filter
            regions = self.metrics_client.get_regions()
            selected_regions = st.multiselect(
                "Regions",
                regions,
                default=regions,
                key="selected_regions",
            )
            
            st.markdown("---")
            
            # Connection status
            st.subheader("Status")
            prometheus_status = self.metrics_client.check_prometheus_health()
            db_status = self.metrics_client.check_database_health()
            
            if prometheus_status:
                st.success("✅ Prometheus Connected")
            else:
                st.error("❌ Prometheus Disconnected")
            
            if db_status:
                st.success("✅ Database Connected")
            else:
                st.error("❌ Database Disconnected")
    
    def render_overview(self, time_range: str):
        """Render overview dashboard."""
        st.header("System Overview")
        
        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        # Fetch metrics
        metrics = self.metrics_client.get_overview_metrics(time_range)
        
        with col1:
            st.metric(
                label="Total Requests",
                value=f"{metrics['total_requests']:,}",
                delta=f"{metrics['requests_change']:+.1f}% vs previous",
            )
        
        with col2:
            st.metric(
                label="Avg Latency",
                value=f"{metrics['avg_latency_ms']:.0f}ms",
                delta=f"{metrics['latency_change']:+.1f}%",
                delta_color="inverse",
            )
        
        with col3:
            st.metric(
                label="Total Cost",
                value=f"${metrics['total_cost']:.2f}",
                delta=f"${metrics['cost_change']:+.2f}",
            )
        
        with col4:
            error_rate = metrics['error_rate'] * 100
            st.metric(
                label="Error Rate",
                value=f"{error_rate:.2f}%",
                delta=f"{metrics['error_rate_change']:+.2f}%",
                delta_color="inverse",
            )
        
        st.markdown("---")
        
        # Request rate chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Request Rate")
            request_data = self.metrics_client.get_request_rate(time_range)
            fig = px.line(
                request_data,
                x="timestamp",
                y="requests_per_second",
                title="Requests per Second",
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Latency Distribution")
            latency_data = self.metrics_client.get_latency_percentiles(time_range)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=latency_data["timestamp"],
                y=latency_data["p50"],
                name="P50",
                mode="lines",
            ))
            fig.add_trace(go.Scatter(
                x=latency_data["timestamp"],
                y=latency_data["p95"],
                name="P95",
                mode="lines",
            ))
            fig.add_trace(go.Scatter(
                x=latency_data["timestamp"],
                y=latency_data["p99"],
                name="P99",
                mode="lines",
            ))
            fig.update_layout(
                title="Latency Percentiles (ms)",
                height=300,
                yaxis_title="Latency (ms)",
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Token usage chart
        st.subheader("Token Usage")
        token_data = self.metrics_client.get_token_usage(time_range)
        fig = px.area(
            token_data,
            x="timestamp",
            y=["input_tokens", "output_tokens"],
            title="Token Usage Over Time",
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_cost_analytics(self, time_range: str):
        """Render cost analytics dashboard."""
        st.header("Cost Analytics")
        
        # Cost metrics
        col1, col2, col3, col4 = st.columns(4)
        
        cost_metrics = self.metrics_client.get_cost_metrics(time_range)
        
        with col1:
            st.metric(
                label="Total Cost",
                value=f"${cost_metrics['total_cost']:.2f}",
                delta=f"{cost_metrics['cost_change']:+.1f}%",
            )
        
        with col2:
            st.metric(
                label="Avg Cost/Request",
                value=f"${cost_metrics['avg_cost_per_request']:.4f}",
                delta=f"{cost_metrics['avg_cost_change']:+.1f}%",
                delta_color="inverse",
            )
        
        with col3:
            st.metric(
                label="Cache Savings",
                value=f"${cost_metrics['cache_savings']:.2f}",
                delta=f"{cost_metrics['savings_change']:+.1f}%",
            )
        
        with col4:
            savings_pct = (cost_metrics['cache_savings'] / 
                          (cost_metrics['total_cost'] + cost_metrics['cache_savings'])) * 100
            st.metric(
                label="Savings Rate",
                value=f"{savings_pct:.1f}%",
            )
        
        st.markdown("---")
        
        # Cost breakdown charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Cost by Model")
            model_costs = self.metrics_client.get_cost_by_model(time_range)
            fig = px.pie(
                model_costs,
                values="cost",
                names="model",
                title="Cost Distribution by Model",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Cost Over Time")
            cost_timeline = self.metrics_client.get_cost_timeline(time_range)
            fig = px.area(
                cost_timeline,
                x="timestamp",
                y="cumulative_cost",
                title="Cumulative Cost",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Cost forecast
        st.subheader("Cost Forecast")
        forecast_data = self.metrics_client.get_cost_forecast()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Projected Daily Cost",
                f"${forecast_data['daily_projection']:.2f}",
            )
        with col2:
            st.metric(
                "Projected Monthly Cost",
                f"${forecast_data['monthly_projection']:.2f}",
            )
        with col3:
            st.metric(
                "Forecast Confidence",
                f"{forecast_data['confidence'] * 100:.1f}%",
            )
        
        # Top expensive requests
        st.subheader("Most Expensive Requests")
        expensive_requests = self.metrics_client.get_expensive_requests(limit=10)
        st.dataframe(
            expensive_requests,
            use_container_width=True,
            hide_index=True,
        )
    
    def render_cache_performance(self, time_range: str):
        """Render cache performance dashboard."""
        st.header("Cache Performance")
        
        # Cache metrics
        col1, col2, col3, col4 = st.columns(4)
        
        cache_metrics = self.metrics_client.get_cache_metrics(time_range)
        
        with col1:
            hit_rate = cache_metrics['hit_rate'] * 100
            color = "success" if hit_rate >= 40 else "warning" if hit_rate >= 20 else "danger"
            st.metric(
                label="Cache Hit Rate",
                value=f"{hit_rate:.1f}%",
                delta=f"{cache_metrics['hit_rate_change']:+.1f}%",
            )
        
        with col2:
            st.metric(
                label="Total Hits",
                value=f"{cache_metrics['total_hits']:,}",
                delta=f"{cache_metrics['hits_change']:+.1f}%",
            )
        
        with col3:
            st.metric(
                label="Cost Saved",
                value=f"${cache_metrics['cost_saved']:.2f}",
                delta=f"{cache_metrics['savings_change']:+.1f}%",
            )
        
        with col4:
            st.metric(
                label="Tokens Saved",
                value=f"{cache_metrics['tokens_saved'] / 1_000_000:.1f}M",
            )
        
        st.markdown("---")
        
        # Cache performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Cache Hit Rate Over Time")
            hit_rate_data = self.metrics_client.get_cache_hit_rate_timeline(time_range)
            fig = px.line(
                hit_rate_data,
                x="timestamp",
                y="hit_rate",
                title="Cache Hit Rate",
            )
            fig.update_layout(height=300)
            fig.add_hline(y=0.4, line_dash="dash", line_color="green", 
                         annotation_text="Target: 40%")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Cache Type Distribution")
            cache_type_data = self.metrics_client.get_cache_by_type(time_range)
            fig = px.pie(
                cache_type_data,
                values="hits",
                names="cache_type",
                title="Hits by Cache Type",
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # Cache savings over time
        st.subheader("Cost Savings from Cache")
        savings_data = self.metrics_client.get_cache_savings_timeline(time_range)
        fig = px.area(
            savings_data,
            x="timestamp",
            y="cumulative_savings",
            title="Cumulative Cache Savings ($)",
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Cache performance by model
        st.subheader("Cache Performance by Model")
        model_cache_data = self.metrics_client.get_cache_by_model(time_range)
        st.dataframe(
            model_cache_data,
            use_container_width=True,
            hide_index=True,
        )
    
    def render_model_health(self, time_range: str):
        """Render model health dashboard."""
        st.header("Model Health & Performance")
        
        # Get model health data
        health_data = self.metrics_client.get_model_health(time_range)
        
        # Health status cards
        st.subheader("Model Status")
        
        cols = st.columns(3)
        for idx, model in enumerate(health_data[:6]):  # Show top 6 models
            col = cols[idx % 3]
            with col:
                availability = model['availability'] * 100
                
                if availability >= 99:
                    status_color = "🟢"
                    status_text = "Healthy"
                elif availability >= 95:
                    status_color = "🟡"
                    status_text = "Degraded"
                else:
                    status_color = "🔴"
                    status_text = "Unhealthy"
                
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{status_color} {model['model_name']}</h4>
                    <p><strong>Status:</strong> {status_text}</p>
                    <p><strong>Availability:</strong> {availability:.2f}%</p>
                    <p><strong>Error Rate:</strong> {model['error_rate'] * 100:.2f}%</p>
                    <p><strong>P95 Latency:</strong> {model['p95_latency_ms']:.0f}ms</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Performance comparison charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Latency Comparison")
            latency_comparison = pd.DataFrame(health_data)
            fig = px.bar(
                latency_comparison,
                x="model_name",
                y=["p50_latency_ms", "p95_latency_ms", "p99_latency_ms"],
                title="Latency Percentiles by Model",
                barmode="group",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Availability & Error Rate")
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=latency_comparison["model_name"],
                y=latency_comparison["availability"] * 100,
                name="Availability %",
                marker_color="green",
            ))
            fig.add_trace(go.Bar(
                x=latency_comparison["model_name"],
                y=latency_comparison["error_rate"] * 100,
                name="Error Rate %",
                marker_color="red",
            ))
            fig.update_layout(
                title="Model Availability & Error Rate",
                height=400,
                barmode="group",
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Model usage over time
        st.subheader("Model Usage Over Time")
        usage_data = self.metrics_client.get_model_usage_timeline(time_range)
        fig = px.area(
            usage_data,
            x="timestamp",
            y="requests",
            color="model",
            title="Requests per Model",
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed health table
        st.subheader("Detailed Health Metrics")
        st.dataframe(
            pd.DataFrame(health_data),
            use_container_width=True,
            hide_index=True,
        )
    
    def render_tracing(self):
        """Render distributed tracing view."""
        st.header("Distributed Tracing")
        
        # Search for traces
        col1, col2, col3 = st.columns(3)
        
        with col1:
            trace_id = st.text_input("Trace ID", placeholder="Enter trace ID...")
        
        with col2:
            min_duration = st.number_input("Min Duration (ms)", value=0, step=100)
        
        with col3:
            only_errors = st.checkbox("Only Errors")
        
        # Get recent traces
        st.subheader("Recent Traces")
        traces = self.metrics_client.get_recent_traces(
            limit=50,
            min_duration_ms=min_duration if min_duration > 0 else None,
            only_errors=only_errors,
        )
        
        if trace_id:
            # Show specific trace details
            trace_details = self.metrics_client.get_trace_details(trace_id)
            if trace_details:
                self.render_trace_details(trace_details)
            else:
                st.warning(f"Trace {trace_id} not found")
        else:
            # Show trace list
            trace_df = pd.DataFrame(traces)
            if not trace_df.empty:
                # Make trace IDs clickable (in a future enhancement)
                st.dataframe(
                    trace_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "trace_id": st.column_config.TextColumn("Trace ID"),
                        "duration_ms": st.column_config.NumberColumn(
                            "Duration (ms)",
                            format="%.0f",
                        ),
                        "status": st.column_config.TextColumn("Status"),
                        "model": st.column_config.TextColumn("Model"),
                        "cost": st.column_config.NumberColumn(
                            "Cost",
                            format="$%.4f",
                        ),
                    },
                )
            else:
                st.info("No traces found matching the criteria")
    
    def render_trace_details(self, trace_details: Dict):
        """Render detailed trace information."""
        st.subheader(f"Trace Details: {trace_details['trace_id']}")
        
        # Trace metadata
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Duration", f"{trace_details['duration_ms']:.0f}ms")
        with col2:
            st.metric("Status", trace_details['status'])
        with col3:
            st.metric("Model", trace_details['model'])
        with col4:
            st.metric("Cost", f"${trace_details['cost']:.4f}")
        
        # Span timeline
        st.subheader("Span Timeline")
        spans_df = pd.DataFrame(trace_details['spans'])
        
        # Create Gantt-like chart
        fig = px.timeline(
            spans_df,
            x_start="start_time",
            x_end="end_time",
            y="operation",
            color="status",
            title="Trace Span Timeline",
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Span details table
        st.subheader("Span Details")
        st.dataframe(
            spans_df,
            use_container_width=True,
            hide_index=True,
        )


def main():
    """Main entry point for the dashboard."""
    dashboard = ObservabilityDashboard()
    
    # Auto-refresh logic
    if st.session_state.get("auto_refresh", False):
        refresh_interval = st.session_state.get("refresh_interval", 30)
        st_autorefresh = st.empty()
        with st_autorefresh:
            st.info(f"Auto-refresh enabled (every {refresh_interval}s)")
        
        # Note: Actual auto-refresh would require streamlit-autorefresh package
        # For now, users can manually refresh
    
    dashboard.run()


if __name__ == "__main__":
    main()
