import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

from utils.api_client import APIClient
from components.sidebar import create_sidebar
from components.metrics import create_metrics_dashboard
from pages.dashboard import show_dashboard
from pages.rca_details import show_rca_details
from pages.search import show_search_page

# Page configuration
st.set_page_config(
    page_title="AI Observability RCA",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
    }
    
    .status-open {
        background-color: #fee2e2;
        color: #dc2626;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .status-in-progress {
        background-color: #fef3c7;
        color: #d97706;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .status-closed {
        background-color: #d1fae5;
        color: #059669;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .priority-high {
        color: #dc2626;
        font-weight: 600;
    }
    
    .priority-medium {
        color: #d97706;
        font-weight: 600;
    }
    
    .priority-low {
        color: #059669;
        font-weight: 600;
    }
    
    .accuracy-high {
        color: #059669;
        font-weight: 600;
    }
    
    .accuracy-medium {
        color: #d97706;
        font-weight: 600;
    }
    
    .accuracy-low {
        color: #dc2626;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Initialize API client
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient()
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 AI Observability RCA Dashboard</h1>
        <p>Automated Root Cause Analysis for Modern IT Systems</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    selected_page = create_sidebar()
    
    # Page routing
    if selected_page == "Dashboard":
        show_dashboard()
    elif selected_page == "RCA Details":
        show_rca_details()
    elif selected_page == "Search & Filter":
        show_search_page()
    elif selected_page == "Analytics":
        show_analytics()
    elif selected_page == "System Health":
        show_system_health()

def show_analytics():
    """Show analytics and metrics page"""
    st.header("📊 Analytics & Metrics")
    
    try:
        # Get metrics data
        api_client = st.session_state.api_client
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("RCA Accuracy Metrics")
            
            # Get accuracy metrics
            accuracy_data = api_client.get_accuracy_metrics(days=30)
            
            if accuracy_data:
                # Display accuracy summary
                st.metric(
                    "Average Accuracy",
                    f"{accuracy_data.get('average_accuracy', 0):.1%}",
                    delta=f"{accuracy_data.get('with_feedback', 0)} reviews"
                )
                
                # Accuracy trend chart
                if accuracy_data.get('accuracy_trend'):
                    trend_df = pd.DataFrame(accuracy_data['accuracy_trend'])
                    trend_df['week'] = pd.to_datetime(trend_df['week'])
                    
                    fig = px.line(
                        trend_df, 
                        x='week', 
                        y='accuracy',
                        title='Accuracy Trend Over Time',
                        markers=True
                    )
                    fig.update_layout(
                        yaxis_title="Accuracy",
                        xaxis_title="Week",
                        yaxis=dict(range=[0, 1])
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Performance Metrics")
            
            # Get performance metrics
            perf_data = api_client.get_performance_metrics()
            
            if perf_data:
                st.metric(
                    "Avg Resolution Time",
                    f"{perf_data.get('average_resolution_time', 0):.1f} min"
                )
                
                st.metric(
                    "System Uptime",
                    f"{perf_data.get('system_uptime', 0):.1f}%"
                )
                
                st.metric(
                    "Correlation Accuracy",
                    f"{perf_data.get('correlation_accuracy', 0):.1f}%"
                )
                
                st.metric(
                    "Total Alerts Processed",
                    f"{perf_data.get('total_alerts_processed', 0):,}"
                )
        
        # RCA Status Distribution
        st.subheader("RCA Status Distribution")
        
        rca_stats = api_client.get_rca_statistics()
        if rca_stats:
            status_data = {
                'Open': rca_stats.get('open_rcas', 0),
                'In Progress': rca_stats.get('in_progress_rcas', 0),
                'Closed': rca_stats.get('closed_rcas', 0)
            }
            
            fig = px.pie(
                values=list(status_data.values()),
                names=list(status_data.keys()),
                title='RCA Status Distribution',
                color_discrete_map={
                    'Open': '#ef4444',
                    'In Progress': '#f59e0b',
                    'Closed': '#10b981'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Alert Statistics
        st.subheader("Alert Statistics")
        
        alert_stats = api_client.get_alert_statistics()
        if alert_stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Alerts", alert_stats.get('total_alerts', 0))
            with col2:
                st.metric("Open Alerts", alert_stats.get('open_alerts', 0))
            with col3:
                st.metric("Resolved Alerts", alert_stats.get('resolved_alerts', 0))
            with col4:
                st.metric("Recent Alerts (24h)", alert_stats.get('recent_alerts', 0))
            
            # Severity distribution
            severity_dist = alert_stats.get('severity_distribution', {})
            if severity_dist:
                fig = px.bar(
                    x=list(severity_dist.keys()),
                    y=list(severity_dist.values()),
                    title='Alert Severity Distribution',
                    color=list(severity_dist.keys()),
                    color_discrete_map={
                        'low': '#10b981',
                        'medium': '#f59e0b',
                        'high': '#f97316',
                        'critical': '#ef4444'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")
        st.info("Please check the backend API connection.")

def show_system_health():
    """Show system health and status"""
    st.header("🏥 System Health")
    
    try:
        api_client = st.session_state.api_client
        
        # Get detailed health check
        health_data = api_client.get_detailed_health()
        
        if health_data:
            # Overall status
            overall_status = health_data.get('status', 'unknown')
            status_color = {
                'healthy': 'green',
                'degraded': 'orange',
                'unhealthy': 'red'
            }.get(overall_status, 'gray')
            
            st.markdown(f"""
            ### Overall System Status: 
            <span style="color: {status_color}; font-weight: bold; font-size: 1.2em;">
            {overall_status.upper()}
            </span>
            """, unsafe_allow_html=True)
            
            st.write(f"**Last Check:** {health_data.get('timestamp', 'Unknown')}")
            
            # Component status
            st.subheader("Component Status")
            
            components = health_data.get('components', {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                db_status = components.get('database', {})
                db_health = db_status.get('status', 'unknown')
                db_color = 'green' if db_health == 'healthy' else 'red'
                
                st.markdown(f"""
                **Database**  
                Status: <span style="color: {db_color}">{db_health}</span>  
                Details: {db_status.get('details', 'N/A')}
                """, unsafe_allow_html=True)
            
            with col2:
                llm_status = components.get('llm', {})
                llm_health = llm_status.get('status', 'unknown')
                llm_color = 'green' if llm_health == 'healthy' else 'red'
                
                st.markdown(f"""
                **LLM Service (Ollama)**  
                Status: <span style="color: {llm_color}">{llm_health}</span>  
                Details: {llm_status.get('details', 'N/A')}
                """, unsafe_allow_html=True)
            
            with col3:
                vector_status = components.get('vector_store', {})
                vector_health = vector_status.get('status', 'unknown')
                vector_color = 'green' if vector_health == 'healthy' else 'red'
                
                st.markdown(f"""
                **Vector Store**  
                Status: <span style="color: {vector_color}">{vector_health}</span>  
                Details: {vector_status.get('details', 'N/A')}
                """, unsafe_allow_html=True)
            
            # Refresh button
            if st.button("🔄 Refresh Health Status"):
                st.rerun()
        
        else:
            st.error("Unable to retrieve system health information")
    
    except Exception as e:
        st.error(f"Error checking system health: {str(e)}")
        st.info("The backend API may be unavailable.")

if __name__ == "__main__":
    main()
