import requests
import streamlit as st
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

class APIClient:
    """Client for interacting with the AI Observability RCA API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 204:  # No content
                return {"success": True}
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend API. Please ensure the backend is running.")
            return None
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ API Error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            return None
    
    # Health endpoints
    def get_health(self) -> Optional[Dict[str, Any]]:
        """Get basic health status"""
        return self._make_request("GET", "/api/health")
    
    def get_detailed_health(self) -> Optional[Dict[str, Any]]:
        """Get detailed health status"""
        return self._make_request("GET", "/api/health/detailed")
    
    # Alert endpoints
    def create_alert(self, alert_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new alert"""
        return self._make_request("POST", "/api/alerts/", json=alert_data)
    
    def get_alerts(self, **filters) -> Optional[List[Dict[str, Any]]]:
        """Get alerts with optional filters"""
        params = {k: v for k, v in filters.items() if v is not None}
        return self._make_request("GET", "/api/alerts/", params=params)
    
    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get specific alert by ID"""
        return self._make_request("GET", f"/api/alerts/{alert_id}")
    
    def update_alert(self, alert_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update alert"""
        return self._make_request("PUT", f"/api/alerts/{alert_id}", json=update_data)
    
    def get_alert_statistics(self) -> Optional[Dict[str, Any]]:
        """Get alert statistics"""
        return self._make_request("GET", "/api/alerts/stats/summary")
    
    def get_correlation_groups(self, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Get correlation groups"""
        return self._make_request("GET", "/api/alerts/correlations/groups", params={"limit": limit})
    
    # RCA endpoints
    def generate_rca(self, correlation_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Generate RCA for correlation ID"""
        data = {"correlation_id": correlation_id, **kwargs}
        return self._make_request("POST", "/api/rca/generate", json=data)
    
    def get_rcas(self, **filters) -> Optional[List[Dict[str, Any]]]:
        """Get RCAs with optional filters"""
        params = {k: v for k, v in filters.items() if v is not None}
        return self._make_request("GET", "/api/rca/", params=params)
    
    def get_rca(self, rca_id: str) -> Optional[Dict[str, Any]]:
        """Get specific RCA by ID"""
        return self._make_request("GET", f"/api/rca/{rca_id}")
    
    def update_rca(self, rca_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update RCA"""
        return self._make_request("PUT", f"/api/rca/{rca_id}", json=update_data)
    
    def update_rca_status(self, rca_id: str, status: str, assigned_to: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update RCA status"""
        params = {"status": status}
        if assigned_to:
            params["assigned_to"] = assigned_to
        return self._make_request("PUT", f"/api/rca/{rca_id}/status", params=params)
    
    def submit_feedback(self, rca_id: str, feedback_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Submit feedback for RCA"""
        return self._make_request("POST", f"/api/rca/{rca_id}/feedback", json=feedback_data)
    
    def get_rca_statistics(self) -> Optional[Dict[str, Any]]:
        """Get RCA statistics"""
        return self._make_request("GET", "/api/rca/stats/summary")
    
    def get_accuracy_metrics(self, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get accuracy metrics"""
        return self._make_request("GET", "/api/rca/stats/accuracy", params={"days": days})
    
    def get_performance_metrics(self) -> Optional[Dict[str, Any]]:
        """Get performance metrics"""
        return self._make_request("GET", "/api/rca/stats/performance")
    
    # Utility methods
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = self.get_health()
            return response is not None and response.get("status") == "healthy"
        except Exception:
            return False
    
    def format_datetime(self, dt_str: str) -> str:
        """Format datetime string for display"""
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return dt_str
    
    def get_status_color(self, status: str) -> str:
        """Get color for status display"""
        colors = {
            "open": "red",
            "in_progress": "orange", 
            "closed": "green",
            "healthy": "green",
            "degraded": "orange",
            "unhealthy": "red"
        }
        return colors.get(status.lower(), "gray")
    
    def get_priority_color(self, priority: str) -> str:
        """Get color for priority display"""
        colors = {
            "low": "green",
            "medium": "orange",
            "high": "red",
            "critical": "darkred"
        }
        return colors.get(priority.lower(), "gray")
    
    def get_severity_color(self, severity: str) -> str:
        """Get color for severity display"""
        colors = {
            "low": "green",
            "medium": "orange",
            "high": "red",
            "critical": "darkred"
        }
        return colors.get(severity.lower(), "gray")
