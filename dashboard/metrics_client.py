"""
Metrics Client for FluxAI Dashboard

Handles data fetching from Prometheus and PostgreSQL.
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime, timedelta
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import structlog

logger = structlog.get_logger()


class MetricsClient:
    """Client for fetching metrics from Prometheus and database."""
    
    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        database_url: str = "postgresql://fluxai:dev_password@localhost:5432/fluxai",
    ):
        self.prometheus_url = prometheus_url
        self.database_url = database_url
        
        # Initialize database connection
        try:
            self.engine = create_engine(database_url)
            self.Session = sessionmaker(bind=self.engine)
        except Exception as e:
            logger.error("Failed to connect to database", error=str(e))
            self.engine = None
            self.Session = None
    
    def check_prometheus_health(self) -> bool:
        """Check if Prometheus is accessible."""
        try:
            response = requests.get(f"{self.prometheus_url}/-/healthy", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def check_database_health(self) -> bool:
        """Check if database is accessible."""
        if not self.Session:
            return False
        try:
            with self.Session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
    
    def _query_prometheus(
        self,
        query: str,
        time_range: str = "1h",
    ) -> Optional[Dict[str, Any]]:
        """Execute Prometheus query."""
        try:
            # Convert time range to seconds
            time_map = {
                "5m": 300,
                "15m": 900,
                "1h": 3600,
                "6h": 21600,
                "24h": 86400,
                "7d": 604800,
                "30d": 2592000,
            }
            seconds = time_map.get(time_range, 3600)
            
            # Query Prometheus
            url = f"{self.prometheus_url}/api/v1/query"
            params = {"query": query}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error("Prometheus query failed", query=query, error=str(e))
            return None
    
    def _query_prometheus_range(
        self,
        query: str,
        time_range: str = "1h",
        step: str = "1m",
    ) -> Optional[Dict[str, Any]]:
        """Execute Prometheus range query."""
        try:
            # Calculate start and end times
            end_time = datetime.now()
            
            time_map = {
                "5m": timedelta(minutes=5),
                "15m": timedelta(minutes=15),
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
            }
            delta = time_map.get(time_range, timedelta(hours=1))
            start_time = end_time - delta
            
            # Query Prometheus
            url = f"{self.prometheus_url}/api/v1/query_range"
            params = {
                "query": query,
                "start": start_time.timestamp(),
                "end": end_time.timestamp(),
                "step": step,
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error("Prometheus range query failed", query=query, error=str(e))
            return None
    
    def get_accounts(self) -> List[str]:
        """Get list of all accounts."""
        if not self.Session:
            return []
        
        try:
            with self.Session() as session:
                result = session.execute(
                    text("SELECT DISTINCT name FROM accounts ORDER BY name")
                )
                return [row[0] for row in result]
        except Exception:
            return []
    
    def get_models(self) -> List[str]:
        """Get list of all models."""
        query = "group by(model) (fluxai_requests_total)"
        result = self._query_prometheus(query)
        
        if result and result.get("status") == "success":
            return [
                metric["metric"]["model"]
                for metric in result["data"]["result"]
            ]
        return []
    
    def get_regions(self) -> List[str]:
        """Get list of all regions."""
        query = "group by(region) (fluxai_requests_total)"
        result = self._query_prometheus(query)
        
        if result and result.get("status") == "success":
            return [
                metric["metric"]["region"]
                for metric in result["data"]["result"]
            ]
        return ["us-east-1", "us-west-2", "eu-west-1"]
    
    def get_overview_metrics(self, time_range: str) -> Dict[str, float]:
        """Get overview metrics for dashboard."""
        # Total requests
        query = f"sum(increase(fluxai_requests_total[{time_range}]))"
        result = self._query_prometheus(query, time_range)
        total_requests = 0
        if result and result["data"]["result"]:
            total_requests = float(result["data"]["result"][0]["value"][1])
        
        # Average latency (P50)
        query = f"histogram_quantile(0.5, sum(rate(fluxai_request_duration_seconds_bucket[{time_range}])) by (le))"
        result = self._query_prometheus(query, time_range)
        avg_latency_ms = 0
        if result and result["data"]["result"]:
            avg_latency_ms = float(result["data"]["result"][0]["value"][1]) * 1000
        
        # Total cost
        query = f"sum(increase(fluxai_cost_dollars_total[{time_range}]))"
        result = self._query_prometheus(query, time_range)
        total_cost = 0
        if result and result["data"]["result"]:
            total_cost = float(result["data"]["result"][0]["value"][1])
        
        # Error rate
        query = f"sum(rate(fluxai_request_errors_total[{time_range}])) / sum(rate(fluxai_requests_total[{time_range}]))"
        result = self._query_prometheus(query, time_range)
        error_rate = 0
        if result and result["data"]["result"]:
            error_rate = float(result["data"]["result"][0]["value"][1])
        
        return {
            "total_requests": int(total_requests),
            "requests_change": 5.2,  # Mock change percentage
            "avg_latency_ms": avg_latency_ms,
            "latency_change": -2.1,  # Mock
            "total_cost": total_cost,
            "cost_change": 3.5,  # Mock
            "error_rate": error_rate,
            "error_rate_change": -0.5,  # Mock
        }
    
    def get_request_rate(self, time_range: str) -> pd.DataFrame:
        """Get request rate over time."""
        query = "sum(rate(fluxai_requests_total[1m]))"
        result = self._query_prometheus_range(query, time_range, step="1m")
        
        if not result or not result["data"]["result"]:
            return pd.DataFrame(columns=["timestamp", "requests_per_second"])
        
        values = result["data"]["result"][0]["values"]
        df = pd.DataFrame(values, columns=["timestamp", "requests_per_second"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df["requests_per_second"] = df["requests_per_second"].astype(float)
        
        return df
    
    def get_latency_percentiles(self, time_range: str) -> pd.DataFrame:
        """Get latency percentiles over time."""
        percentiles = {"p50": 0.5, "p95": 0.95, "p99": 0.99}
        dfs = []
        
        for name, percentile in percentiles.items():
            query = f"histogram_quantile({percentile}, sum(rate(fluxai_request_duration_seconds_bucket[5m])) by (le)) * 1000"
            result = self._query_prometheus_range(query, time_range, step="1m")
            
            if result and result["data"]["result"]:
                values = result["data"]["result"][0]["values"]
                df = pd.DataFrame(values, columns=["timestamp", name])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
                df[name] = df[name].astype(float)
                dfs.append(df)
        
        if dfs:
            merged = dfs[0]
            for df in dfs[1:]:
                merged = merged.merge(df, on="timestamp")
            return merged
        
        return pd.DataFrame(columns=["timestamp", "p50", "p95", "p99"])
    
    def get_token_usage(self, time_range: str) -> pd.DataFrame:
        """Get token usage over time."""
        input_query = "sum(rate(fluxai_input_tokens_total[1m])) * 60"
        output_query = "sum(rate(fluxai_output_tokens_total[1m])) * 60"
        
        input_result = self._query_prometheus_range(input_query, time_range, step="1m")
        output_result = self._query_prometheus_range(output_query, time_range, step="1m")
        
        data = []
        
        if input_result and input_result["data"]["result"]:
            for timestamp, value in input_result["data"]["result"][0]["values"]:
                data.append({
                    "timestamp": pd.to_datetime(timestamp, unit="s"),
                    "input_tokens": float(value),
                    "output_tokens": 0,
                })
        
        if output_result and output_result["data"]["result"]:
            for i, (timestamp, value) in enumerate(output_result["data"]["result"][0]["values"]):
                if i < len(data):
                    data[i]["output_tokens"] = float(value)
        
        return pd.DataFrame(data)
    
    def get_cost_metrics(self, time_range: str) -> Dict[str, float]:
        """Get cost metrics."""
        # Total cost
        query = f"sum(increase(fluxai_cost_dollars_total[{time_range}]))"
        result = self._query_prometheus(query, time_range)
        total_cost = 0
        if result and result["data"]["result"]:
            total_cost = float(result["data"]["result"][0]["value"][1])
        
        # Average cost per request
        query = f"sum(increase(fluxai_cost_dollars_total[{time_range}])) / sum(increase(fluxai_requests_total[{time_range}]))"
        result = self._query_prometheus(query, time_range)
        avg_cost = 0
        if result and result["data"]["result"]:
            avg_cost = float(result["data"]["result"][0]["value"][1])
        
        # Cache savings
        query = f"sum(increase(fluxai_cache_savings_dollars_total[{time_range}]))"
        result = self._query_prometheus(query, time_range)
        cache_savings = 0
        if result and result["data"]["result"]:
            cache_savings = float(result["data"]["result"][0]["value"][1])
        
        return {
            "total_cost": total_cost,
            "cost_change": 4.2,  # Mock
            "avg_cost_per_request": avg_cost,
            "avg_cost_change": -1.5,  # Mock
            "cache_savings": cache_savings,
            "savings_change": 8.3,  # Mock
        }
    
    def get_cost_by_model(self, time_range: str) -> pd.DataFrame:
        """Get cost breakdown by model."""
        query = f"sum(increase(fluxai_cost_dollars_total[{time_range}])) by (model)"
        result = self._query_prometheus(query, time_range)
        
        if not result or not result["data"]["result"]:
            return pd.DataFrame(columns=["model", "cost"])
        
        data = [
            {
                "model": metric["metric"]["model"],
                "cost": float(metric["value"][1]),
            }
            for metric in result["data"]["result"]
        ]
        
        return pd.DataFrame(data)
    
    def get_cost_timeline(self, time_range: str) -> pd.DataFrame:
        """Get cumulative cost over time."""
        query = "sum(fluxai_cost_dollars_total)"
        result = self._query_prometheus_range(query, time_range, step="5m")
        
        if not result or not result["data"]["result"]:
            return pd.DataFrame(columns=["timestamp", "cumulative_cost"])
        
        values = result["data"]["result"][0]["values"]
        df = pd.DataFrame(values, columns=["timestamp", "cumulative_cost"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df["cumulative_cost"] = df["cumulative_cost"].astype(float)
        
        return df
    
    def get_cost_forecast(self) -> Dict[str, float]:
        """Get cost forecast (simplified)."""
        # This would typically use time-series forecasting
        # For now, return mock data
        return {
            "daily_projection": 125.50,
            "monthly_projection": 3765.00,
            "confidence": 0.87,
        }
    
    def get_expensive_requests(self, limit: int = 10) -> pd.DataFrame:
        """Get most expensive requests from database."""
        if not self.Session:
            return pd.DataFrame()
        
        try:
            with self.Session() as session:
                query = text("""
                    SELECT 
                        request_id,
                        model_id,
                        timestamp,
                        input_tokens,
                        output_tokens,
                        total_cost,
                        latency_ms
                    FROM request_metrics
                    WHERE timestamp > NOW() - INTERVAL '24 hours'
                    ORDER BY total_cost DESC
                    LIMIT :limit
                """)
                
                result = session.execute(query, {"limit": limit})
                data = result.fetchall()
                
                return pd.DataFrame(
                    data,
                    columns=[
                        "request_id", "model_id", "timestamp",
                        "input_tokens", "output_tokens", "total_cost", "latency_ms"
                    ]
                )
        except Exception:
            return pd.DataFrame()
    
    def get_cache_metrics(self, time_range: str) -> Dict[str, Any]:
        """Get cache performance metrics."""
        # Hit rate
        hits_query = f"sum(increase(fluxai_cache_hits_total[{time_range}]))"
        misses_query = f"sum(increase(fluxai_cache_misses_total[{time_range}]))"
        
        hits_result = self._query_prometheus(hits_query, time_range)
        misses_result = self._query_prometheus(misses_query, time_range)
        
        hits = 0
        misses = 0
        
        if hits_result and hits_result["data"]["result"]:
            hits = float(hits_result["data"]["result"][0]["value"][1])
        if misses_result and misses_result["data"]["result"]:
            misses = float(misses_result["data"]["result"][0]["value"][1])
        
        hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
        
        # Cost saved
        savings_query = f"sum(increase(fluxai_cache_savings_dollars_total[{time_range}]))"
        savings_result = self._query_prometheus(savings_query, time_range)
        cost_saved = 0
        if savings_result and savings_result["data"]["result"]:
            cost_saved = float(savings_result["data"]["result"][0]["value"][1])
        
        return {
            "hit_rate": hit_rate,
            "hit_rate_change": 2.3,  # Mock
            "total_hits": int(hits),
            "hits_change": 5.7,  # Mock
            "cost_saved": cost_saved,
            "savings_change": 12.4,  # Mock
            "tokens_saved": int(hits * 1500),  # Mock estimate
        }
    
    def get_cache_hit_rate_timeline(self, time_range: str) -> pd.DataFrame:
        """Get cache hit rate over time."""
        hits_query = "sum(rate(fluxai_cache_hits_total[5m]))"
        misses_query = "sum(rate(fluxai_cache_misses_total[5m]))"
        
        hits_result = self._query_prometheus_range(hits_query, time_range, step="1m")
        misses_result = self._query_prometheus_range(misses_query, time_range, step="1m")
        
        if not hits_result or not misses_result:
            return pd.DataFrame(columns=["timestamp", "hit_rate"])
        
        data = []
        if hits_result["data"]["result"] and misses_result["data"]["result"]:
            hits_values = hits_result["data"]["result"][0]["values"]
            misses_values = misses_result["data"]["result"][0]["values"]
            
            for (ts_h, h), (ts_m, m) in zip(hits_values, misses_values):
                hits = float(h)
                misses = float(m)
                hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
                
                data.append({
                    "timestamp": pd.to_datetime(ts_h, unit="s"),
                    "hit_rate": hit_rate,
                })
        
        return pd.DataFrame(data)
    
    def get_cache_by_type(self, time_range: str) -> pd.DataFrame:
        """Get cache hits by type (exact vs semantic)."""
        query = f"sum(increase(fluxai_cache_hits_total[{time_range}])) by (cache_type)"
        result = self._query_prometheus(query, time_range)
        
        if not result or not result["data"]["result"]:
            return pd.DataFrame(columns=["cache_type", "hits"])
        
        data = [
            {
                "cache_type": metric["metric"]["cache_type"],
                "hits": float(metric["value"][1]),
            }
            for metric in result["data"]["result"]
        ]
        
        return pd.DataFrame(data)
    
    def get_cache_savings_timeline(self, time_range: str) -> pd.DataFrame:
        """Get cumulative cache savings over time."""
        query = "sum(fluxai_cache_savings_dollars_total)"
        result = self._query_prometheus_range(query, time_range, step="5m")
        
        if not result or not result["data"]["result"]:
            return pd.DataFrame(columns=["timestamp", "cumulative_savings"])
        
        values = result["data"]["result"][0]["values"]
        df = pd.DataFrame(values, columns=["timestamp", "cumulative_savings"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df["cumulative_savings"] = df["cumulative_savings"].astype(float)
        
        return df
    
    def get_cache_by_model(self, time_range: str) -> pd.DataFrame:
        """Get cache performance by model."""
        query = f"""
            sum(increase(fluxai_cache_hits_total[{time_range}])) by (model) /
            (sum(increase(fluxai_cache_hits_total[{time_range}])) by (model) +
             sum(increase(fluxai_cache_misses_total[{time_range}])) by (model))
        """
        result = self._query_prometheus(query, time_range)
        
        if not result or not result["data"]["result"]:
            return pd.DataFrame(columns=["model", "hit_rate", "savings"])
        
        data = [
            {
                "model": metric["metric"]["model"],
                "hit_rate": f"{float(metric['value'][1]) * 100:.1f}%",
                "savings": "$125.50",  # Mock - would calculate from actual data
            }
            for metric in result["data"]["result"]
        ]
        
        return pd.DataFrame(data)
    
    def get_model_health(self, time_range: str) -> List[Dict[str, Any]]:
        """Get model health metrics."""
        # This would typically query from database
        # For now, return mock data
        return [
            {
                "model_name": "Claude 3.5 Sonnet",
                "availability": 0.998,
                "error_rate": 0.002,
                "p50_latency_ms": 1200,
                "p95_latency_ms": 2500,
                "p99_latency_ms": 3800,
            },
            {
                "model_name": "Llama 3.1 70B",
                "availability": 0.995,
                "error_rate": 0.005,
                "p50_latency_ms": 1500,
                "p95_latency_ms": 3000,
                "p99_latency_ms": 4500,
            },
            # Add more models...
        ]
    
    def get_model_usage_timeline(self, time_range: str) -> pd.DataFrame:
        """Get model usage over time."""
        query = "sum(rate(fluxai_requests_total[5m])) by (model)"
        result = self._query_prometheus_range(query, time_range, step="5m")
        
        if not result or not result["data"]["result"]:
            return pd.DataFrame(columns=["timestamp", "model", "requests"])
        
        data = []
        for metric in result["data"]["result"]:
            model = metric["metric"]["model"]
            for timestamp, value in metric["values"]:
                data.append({
                    "timestamp": pd.to_datetime(timestamp, unit="s"),
                    "model": model,
                    "requests": float(value) * 60,  # Convert to requests/min
                })
        
        return pd.DataFrame(data)
    
    def get_recent_traces(
        self,
        limit: int = 50,
        min_duration_ms: Optional[int] = None,
        only_errors: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get recent traces from database."""
        if not self.Session:
            return []
        
        try:
            with self.Session() as session:
                conditions = ["timestamp > NOW() - INTERVAL '1 hour'"]
                
                if min_duration_ms:
                    conditions.append(f"latency_ms >= {min_duration_ms}")
                
                if only_errors:
                    conditions.append("status != 'success'")
                
                where_clause = " AND ".join(conditions)
                
                query = text(f"""
                    SELECT 
                        request_id as trace_id,
                        timestamp,
                        latency_ms as duration_ms,
                        status,
                        model_id as model,
                        total_cost as cost
                    FROM request_metrics
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """)
                
                result = session.execute(query, {"limit": limit})
                
                return [
                    {
                        "trace_id": row[0],
                        "timestamp": row[1],
                        "duration_ms": row[2],
                        "status": row[3],
                        "model": row[4],
                        "cost": row[5],
                    }
                    for row in result
                ]
        except Exception:
            return []
    
    def get_trace_details(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed trace information."""
        # This would integrate with Jaeger or similar
        # For now, return mock data
        return {
            "trace_id": trace_id,
            "duration_ms": 2340,
            "status": "success",
            "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "cost": 0.0125,
            "spans": [
                {
                    "operation": "gateway.auth",
                    "start_time": "2024-01-15T10:30:45.123Z",
                    "end_time": "2024-01-15T10:30:45.125Z",
                    "status": "ok",
                },
                {
                    "operation": "cache.lookup",
                    "start_time": "2024-01-15T10:30:45.125Z",
                    "end_time": "2024-01-15T10:30:45.230Z",
                    "status": "ok",
                },
                # More spans...
            ],
        }
