#!/usr/bin/env python3
"""
Sample Alert Generator for AI Observability RCA
This script generates realistic sample alerts for testing the system.
"""

import requests
import json
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse

# API Configuration
API_BASE_URL = "http://localhost:8000"
ALERTS_ENDPOINT = f"{API_BASE_URL}/api/alerts/"

# Sample data for realistic alerts
MONITORING_SOURCES = [
    "prometheus", "grafana", "datadog", "newrelic", "zabbix", 
    "nagios", "splunk", "elastic", "dynatrace", "pingdom"
]

SERVICES = [
    "web-service", "api-gateway", "user-service", "payment-service",
    "database", "cache", "message-queue", "auth-service", "notification-service"
]

HOSTS = [
    "web-01", "web-02", "api-01", "api-02", "db-master", "db-slave",
    "cache-01", "queue-01", "worker-01", "worker-02", "lb-01"
]

ENVIRONMENTS = ["production", "staging", "development", "testing"]

# Alert templates for different scenarios
ALERT_TEMPLATES = {
    "high_cpu": {
        "title": "High CPU Usage Detected",
        "message": "CPU usage is above {threshold}% for more than {duration} minutes",
        "alert_type": "metrics",
        "severity_weights": {"critical": 30, "high": 50, "medium": 20},
        "raw_data_template": {
            "metric": "cpu_usage",
            "threshold": lambda: random.uniform(80, 95),
            "current_value": lambda: random.uniform(85, 98),
            "duration": lambda: random.randint(5, 30)
        }
    },
    "memory_leak": {
        "title": "Memory Usage Critical",
        "message": "Memory usage is at {usage}% and continuously increasing",
        "alert_type": "metrics",
        "severity_weights": {"critical": 40, "high": 40, "medium": 20},
        "raw_data_template": {
            "metric": "memory_usage",
            "usage": lambda: random.uniform(85, 99),
            "trend": "increasing",
            "rate": lambda: random.uniform(1, 5)
        }
    },
    "disk_space": {
        "title": "Disk Space Low",
        "message": "Disk space on {mount} is {usage}% full",
        "alert_type": "metrics",
        "severity_weights": {"critical": 25, "high": 35, "medium": 40},
        "raw_data_template": {
            "metric": "disk_usage",
            "mount": lambda: random.choice(["/", "/var", "/tmp", "/home"]),
            "usage": lambda: random.uniform(80, 98),
            "available_gb": lambda: random.uniform(0.5, 10)
        }
    },
    "service_down": {
        "title": "Service Unavailable",
        "message": "{service} is not responding to health checks",
        "alert_type": "events",
        "severity_weights": {"critical": 60, "high": 30, "medium": 10},
        "raw_data_template": {
            "service": lambda: random.choice(SERVICES),
            "last_response": lambda: (datetime.now() - timedelta(minutes=random.randint(1, 30))).isoformat(),
            "health_check_url": lambda: f"http://localhost:{random.randint(8000, 9000)}/health"
        }
    },
    "database_connection": {
        "title": "Database Connection Pool Exhausted",
        "message": "Cannot establish database connections - pool is full",
        "alert_type": "logs",
        "severity_weights": {"critical": 50, "high": 40, "medium": 10},
        "raw_data_template": {
            "component": "database",
            "pool_size": lambda: random.randint(10, 100),
            "active_connections": lambda: random.randint(90, 100),
            "wait_time_ms": lambda: random.randint(5000, 30000)
        }
    },
    "api_latency": {
        "title": "API Response Time High",
        "message": "Average response time for {endpoint} is {latency}ms",
        "alert_type": "metrics",
        "severity_weights": {"critical": 20, "high": 50, "medium": 30},
        "raw_data_template": {
            "metric": "response_time",
            "endpoint": lambda: random.choice(["/api/users", "/api/orders", "/api/payments", "/api/auth"]),
            "latency": lambda: random.randint(2000, 10000),
            "p95": lambda: random.randint(3000, 15000),
            "requests_per_second": lambda: random.randint(10, 1000)
        }
    },
    "network_error": {
        "title": "Network Connectivity Issues",
        "message": "High packet loss detected on interface {interface}",
        "alert_type": "metrics",
        "severity_weights": {"critical": 30, "high": 40, "medium": 30},
        "raw_data_template": {
            "interface": lambda: random.choice(["eth0", "eth1", "bond0"]),
            "packet_loss": lambda: random.uniform(5, 25),
            "latency_ms": lambda: random.uniform(100, 500),
            "bandwidth_utilization": lambda: random.uniform(80, 100)
        }
    },
    "log_errors": {
        "title": "Error Rate Spike",
        "message": "Error rate increased to {rate}% in the last {duration} minutes",
        "alert_type": "logs",
        "severity_weights": {"critical": 25, "high": 45, "medium": 30},
        "raw_data_template": {
            "log_level": "ERROR",
            "rate": lambda: random.uniform(10, 50),
            "duration": lambda: random.randint(5, 30),
            "error_count": lambda: random.randint(50, 500),
            "total_requests": lambda: random.randint(1000, 10000)
        }
    }
}

# Related alert scenarios (for correlation testing)
CORRELATION_SCENARIOS = [
    {
        "name": "cpu_memory_cascade",
        "description": "High CPU leading to memory issues",
        "alerts": ["high_cpu", "memory_leak"],
        "delay_between": (30, 120),  # seconds
        "same_host": True
    },
    {
        "name": "service_database_failure",
        "description": "Service failure due to database issues",
        "alerts": ["database_connection", "service_down", "api_latency"],
        "delay_between": (10, 60),
        "same_service": True
    },
    {
        "name": "network_cascade",
        "description": "Network issues causing multiple service problems",
        "alerts": ["network_error", "api_latency", "service_down"],
        "delay_between": (20, 90),
        "same_environment": True
    },
    {
        "name": "disk_full_cascade",
        "description": "Disk space issues causing log and service problems",
        "alerts": ["disk_space", "log_errors", "service_down"],
        "delay_between": (30, 180),
        "same_host": True
    }
]

class AlertGenerator:
    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.alerts_endpoint = f"{api_url}/api/alerts/"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def generate_alert(self, template_name: str = None, **overrides) -> Dict[str, Any]:
        """Generate a single alert based on template"""
        
        if template_name is None:
            template_name = random.choice(list(ALERT_TEMPLATES.keys()))
        
        template = ALERT_TEMPLATES[template_name]
        
        # Generate base alert data
        alert_data = {
            "alert_id": str(uuid.uuid4()),
            "source": overrides.get("source", random.choice(MONITORING_SOURCES)),
            "severity": self._choose_severity(template["severity_weights"]),
            "title": template["title"],
            "alert_type": template["alert_type"],
            "alert_timestamp": datetime.now().isoformat()
        }
        
        # Generate raw data from template
        raw_data = {}
        for key, value_func in template["raw_data_template"].items():
            if callable(value_func):
                raw_data[key] = value_func()
            else:
                raw_data[key] = value_func
        
        # Add common fields to raw data
        raw_data.update({
            "host": overrides.get("host", random.choice(HOSTS)),
            "service": overrides.get("service", random.choice(SERVICES)),
            "environment": overrides.get("environment", random.choice(ENVIRONMENTS)),
            "generated_by": "sample_generator",
            "timestamp": datetime.now().isoformat()
        })
        
        # Format message with raw data
        try:
            message = template["message"].format(**raw_data)
        except KeyError:
            message = template["message"]
        
        alert_data.update({
            "message": message,
            "description": f"Generated {template_name} alert for testing",
            "raw_data": raw_data
        })
        
        # Apply overrides
        alert_data.update(overrides)
        
        return alert_data
    
    def _choose_severity(self, weights: Dict[str, int]) -> str:
        """Choose severity based on weights"""
        severities = list(weights.keys())
        weight_values = list(weights.values())
        return random.choices(severities, weights=weight_values)[0]
    
    def send_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to the API"""
        try:
            response = self.session.post(self.alerts_endpoint, json=alert_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send alert: {e}")
            return None
    
    def generate_random_alerts(self, count: int = 10, delay: float = 1.0) -> List[Dict[str, Any]]:
        """Generate multiple random alerts"""
        alerts = []
        
        print(f"🔥 Generating {count} random alerts...")
        
        for i in range(count):
            alert_data = self.generate_alert()
            result = self.send_alert(alert_data)
            
            if result:
                alerts.append(result)
                print(f"✅ Alert {i+1}/{count}: {alert_data['title']} ({alert_data['severity']})")
            else:
                print(f"❌ Alert {i+1}/{count}: Failed to send")
            
            if delay > 0 and i < count - 1:
                time.sleep(delay)
        
        return alerts
    
    def generate_correlation_scenario(self, scenario_name: str = None) -> List[Dict[str, Any]]:
        """Generate alerts that should be correlated"""
        
        if scenario_name is None:
            scenario = random.choice(CORRELATION_SCENARIOS)
        else:
            scenario = next((s for s in CORRELATION_SCENARIOS if s["name"] == scenario_name), None)
            if not scenario:
                raise ValueError(f"Unknown scenario: {scenario_name}")
        
        print(f"🔗 Generating correlation scenario: {scenario['description']}")
        
        alerts = []
        
        # Common attributes for correlation
        common_attrs = {}
        if scenario.get("same_host"):
            common_attrs["host"] = random.choice(HOSTS)
        if scenario.get("same_service"):
            common_attrs["service"] = random.choice(SERVICES)
        if scenario.get("same_environment"):
            common_attrs["environment"] = random.choice(ENVIRONMENTS)
        
        # Generate alerts in sequence
        for i, alert_type in enumerate(scenario["alerts"]):
            if i > 0:
                delay = random.randint(*scenario["delay_between"])
                print(f"⏳ Waiting {delay} seconds before next alert...")
                time.sleep(delay)
            
            alert_data = self.generate_alert(alert_type, **common_attrs)
            result = self.send_alert(alert_data)
            
            if result:
                alerts.append(result)
                print(f"✅ Scenario alert {i+1}: {alert_data['title']} ({alert_data['severity']})")
            else:
                print(f"❌ Scenario alert {i+1}: Failed to send")
        
        return alerts
    
    def generate_realistic_workload(self, duration_minutes: int = 30) -> None:
        """Generate a realistic alert workload over time"""
        
        print(f"🏭 Starting realistic workload generation for {duration_minutes} minutes...")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        scenario_probability = 0.3  # 30% chance of correlation scenario
        alert_count = 0
        
        while time.time() < end_time:
            # Decide whether to generate single alert or scenario
            if random.random() < scenario_probability:
                alerts = self.generate_correlation_scenario()
                alert_count += len(alerts)
            else:
                alert = self.generate_alert()
                result = self.send_alert(alert)
                if result:
                    alert_count += 1
                    print(f"✅ Random alert: {alert['title']} ({alert['severity']})")
            
            # Variable delay between alerts (more realistic)
            delay = random.uniform(10, 120)  # 10 seconds to 2 minutes
            print(f"⏳ Next alert in {delay:.1f} seconds...")
            time.sleep(delay)
        
        print(f"🏁 Workload complete! Generated {alert_count} alerts in {duration_minutes} minutes")

def main():
    parser = argparse.ArgumentParser(description="Generate sample alerts for AI Observability RCA")
    parser.add_argument("--api-url", default=API_BASE_URL, help="Base URL for the API")
    parser.add_argument("--count", "-c", type=int, default=10, help="Number of random alerts to generate")
    parser.add_argument("--delay", "-d", type=float, default=1.0, help="Delay between alerts in seconds")
    parser.add_argument("--scenario", "-s", help="Generate specific correlation scenario")
    parser.add_argument("--workload", "-w", type=int, help="Generate realistic workload for N minutes")
    parser.add_argument("--list-scenarios", action="store_true", help="List available correlation scenarios")
    parser.add_argument("--list-templates", action="store_true", help="List available alert templates")
    
    args = parser.parse_args()
    
    if args.list_scenarios:
        print("📋 Available correlation scenarios:")
        for scenario in CORRELATION_SCENARIOS:
            print(f"  • {scenario['name']}: {scenario['description']}")
            print(f"    Alerts: {', '.join(scenario['alerts'])}")
        return
    
    if args.list_templates:
        print("📋 Available alert templates:")
        for name, template in ALERT_TEMPLATES.items():
            print(f"  • {name}: {template['title']}")
        return
    
    generator = AlertGenerator(args.api_url)
    
    # Test API connection
    try:
        health_response = requests.get(f"{args.api_url}/api/health")
        if health_response.status_code != 200:
            print("❌ API health check failed. Make sure the backend is running.")
            return
        print("✅ API connection successful")
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API. Make sure the backend is running on", args.api_url)
        return
    
    if args.workload:
        generator.generate_realistic_workload(args.workload)
    elif args.scenario:
        generator.generate_correlation_scenario(args.scenario)
    else:
        generator.generate_random_alerts(args.count, args.delay)

if __name__ == "__main__":
    main()
