import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional

def create_metrics_dashboard(api_client):
    """Create metrics dashboard with key performance indicators"""
    
    try:
        # Get statistics
        rca_stats = api_client.get_rca_statistics()
        alert_stats = api_client.get_alert_statistics()
        perf_metrics = api_client.get_performance_metrics()
        
        # Top-level metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if rca_stats:
                total_rcas = rca_stats.get('total_rcas', 0)
                recent_rcas = rca_stats.get('recent_rcas', 0)
                delta = f"+{recent_rcas} today" if recent_rcas > 0 else None
                
                st.metric(
                    label="Total RCAs",
                    value=total_rcas,
                    delta=delta
                )
        
        with col2:
            if rca_stats:
                open_rcas = rca_stats.get('open_rcas', 0)
                in_progress = rca_stats.get('in_progress_rcas', 0)
                
                st.metric(
                    label="Active RCAs",
                    value=open_rcas + in_progress,
                    delta=f"{open_rcas} open, {in_progress} in progress"
                )
        
        with col3:
            if rca_stats:
                avg_accuracy = rca_stats.get('average_accuracy', 0)
                feedback_count = rca_stats.get('rcas_with_feedback', 0)
                
                st.metric(
                    label="Avg Accuracy",
                    value=f"{avg_accuracy:.1%}",
                    delta=f"{feedback_count} reviews"
                )
        
        with col4:
            if alert_stats:
                total_alerts = alert_stats.get('total_alerts', 0)
                recent_alerts = alert_stats.get('recent_alerts', 0)
                
                st.metric(
                    label="Total Alerts",
                    value=f"{total_alerts:,}",
                    delta=f"+{recent_alerts} today"
                )
        
        with col5:
            if perf_metrics:
                uptime = perf_metrics.get('system_uptime', 0)
                color = "normal" if uptime >= 95 else "inverse"
                
                st.metric(
                    label="System Uptime",
                    value=f"{uptime:.1f}%",
                    delta="Operational" if uptime >= 95 else "Degraded",
                    delta_color=color
                )
        
        st.markdown("---")
        
        # Charts section
        col1, col2 = st.columns(2)
        
        with col1:
            # RCA Status Distribution
            if rca_stats:
                create_rca_status_chart(rca_stats)
        
        with col2:
            # Alert Severity Distribution
            if alert_stats and alert_stats.get('severity_distribution'):
                create_alert_severity_chart(alert_stats['severity_distribution'])
        
        # Performance metrics section
        if perf_metrics:
            create_performance_section(perf_metrics)
    
    except Exception as e:
        st.error(f"Error loading metrics: {str(e)}")
        st.info("Please ensure the backend API is running and accessible.")

def create_rca_status_chart(rca_stats: Dict[str, Any]):
    """Create RCA status distribution chart"""
    st.subheader("RCA Status Distribution")
    
    status_data = {
        'Open': rca_stats.get('open_rcas', 0),
        'In Progress': rca_stats.get('in_progress_rcas', 0),
        'Closed': rca_stats.get('closed_rcas', 0)
    }
    
    # Filter out zero values
    status_data = {k: v for k, v in status_data.items() if v > 0}
    
    if status_data:
        fig = px.pie(
            values=list(status_data.values()),
            names=list(status_data.keys()),
            color_discrete_map={
                'Open': '#ef4444',
                'In Progress': '#f59e0b',
                'Closed': '#10b981'
            },
            hole=0.4
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            showlegend=True,
            height=300,
            margin=dict(t=30, b=30, l=30, r=30)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No RCA data available")

def create_alert_severity_chart(severity_dist: Dict[str, int]):
    """Create alert severity distribution chart"""
    st.subheader("Alert Severity Distribution")
    
    # Filter out zero values
    severity_data = {k: v for k, v in severity_dist.items() if v > 0}
    
    if severity_data:
        # Define color mapping for severity
        color_map = {
            'low': '#10b981',
            'medium': '#f59e0b', 
            'high': '#f97316',
            'critical': '#ef4444'
        }
        
        # Create bar chart
        fig = px.bar(
            x=list(severity_data.keys()),
            y=list(severity_data.values()),
            color=list(severity_data.keys()),
            color_discrete_map=color_map,
            text=list(severity_data.values())
        )
        
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(
            xaxis_title="Severity",
            yaxis_title="Count",
            showlegend=False,
            height=300,
            margin=dict(t=30, b=30, l=30, r=30)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No alert data available")

def create_performance_section(perf_metrics: Dict[str, Any]):
    """Create performance metrics section"""
    st.subheader("Performance Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        resolution_time = perf_metrics.get('average_resolution_time', 0)
        st.metric(
            "Avg Resolution Time",
            f"{resolution_time:.1f} min",
            help="Average time to resolve RCAs"
        )
    
    with col2:
        correlation_accuracy = perf_metrics.get('correlation_accuracy', 0)
        st.metric(
            "Correlation Accuracy",
            f"{correlation_accuracy:.1f}%",
            help="Accuracy of alert correlation algorithm"
        )
    
    with col3:
        total_processed = perf_metrics.get('total_alerts_processed', 0)
        st.metric(
            "Alerts Processed",
            f"{total_processed:,}",
            help="Total number of alerts processed"
        )

def create_trend_chart(data: list, title: str, x_col: str, y_col: str, color: str = "#3b82f6"):
    """Create a generic trend chart"""
    if not data:
        st.info(f"No data available for {title}")
        return
    
    df = pd.DataFrame(data)
    
    fig = px.line(
        df, 
        x=x_col, 
        y=y_col,
        title=title,
        markers=True,
        color_discrete_sequence=[color]
    )
    
    fig.update_layout(
        height=300,
        margin=dict(t=50, b=30, l=30, r=30)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_gauge_chart(value: float, title: str, max_value: float = 100, 
                      color_ranges: Optional[Dict[str, tuple]] = None):
    """Create a gauge chart for metrics"""
    
    if color_ranges is None:
        color_ranges = {
            "red": (0, 30),
            "yellow": (30, 70), 
            "green": (70, 100)
        }
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        gauge = {
            'axis': {'range': [None, max_value]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': color_ranges["red"], 'color': "lightgray"},
                {'range': color_ranges["yellow"], 'color': "yellow"},
                {'range': color_ranges["green"], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

def display_metric_card(title: str, value: str, delta: Optional[str] = None, 
                       color: str = "blue"):
    """Display a metric card with custom styling"""
    
    delta_html = f"<div style='color: gray; font-size: 0.8em;'>{delta}</div>" if delta else ""
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="color: {color}; font-size: 0.9em; font-weight: 600;">{title}</div>
        <div style="font-size: 1.8em; font-weight: bold; margin: 0.2em 0;">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)
