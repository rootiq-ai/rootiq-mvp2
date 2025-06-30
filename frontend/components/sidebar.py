import streamlit as st
from utils.api_client import APIClient

def create_sidebar():
    """Create application sidebar with navigation and quick stats"""
    
    st.sidebar.title("🔍 Navigation")
    
    # Main navigation
    pages = [
        "Dashboard",
        "RCA Details", 
        "Search & Filter",
        "Analytics",
        "System Health"
    ]
    
    selected_page = st.sidebar.selectbox(
        "Select Page",
        pages,
        index=0
    )
    
    st.sidebar.markdown("---")
    
    # Quick stats section
    st.sidebar.subheader("📊 Quick Stats")
    
    try:
        api_client = st.session_state.get('api_client')
        if api_client:
            # Test connection
            if api_client.test_connection():
                st.sidebar.success("✅ API Connected")
                
                # Get quick stats
                rca_stats = api_client.get_rca_statistics()
                alert_stats = api_client.get_alert_statistics()
                
                if rca_stats:
                    st.sidebar.metric(
                        "Total RCAs", 
                        rca_stats.get('total_rcas', 0)
                    )
                    st.sidebar.metric(
                        "Open RCAs", 
                        rca_stats.get('open_rcas', 0)
                    )
                    st.sidebar.metric(
                        "Avg Accuracy", 
                        f"{rca_stats.get('average_accuracy', 0):.1%}"
                    )
                
                if alert_stats:
                    st.sidebar.metric(
                        "Total Alerts", 
                        alert_stats.get('total_alerts', 0)
                    )
                    st.sidebar.metric(
                        "Open Alerts", 
                        alert_stats.get('open_alerts', 0)
                    )
            else:
                st.sidebar.error("❌ API Disconnected")
                st.sidebar.info("Please check backend service")
    
    except Exception as e:
        st.sidebar.warning(f"⚠️ Stats unavailable: {str(e)}")
    
    st.sidebar.markdown("---")
    
    # Quick actions
    st.sidebar.subheader("⚡ Quick Actions")
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    if st.sidebar.button("📥 Create Test Alert"):
        show_create_alert_form()
    
    if st.sidebar.button("🏥 Health Check"):
        show_health_check()
    
    st.sidebar.markdown("---")
    
    # Settings
    with st.sidebar.expander("⚙️ Settings"):
        auto_refresh = st.checkbox("Auto-refresh", value=False)
        if auto_refresh:
            refresh_interval = st.selectbox(
                "Refresh interval (seconds)",
                [30, 60, 120, 300],
                index=1
            )
            st.info(f"Auto-refresh every {refresh_interval}s")
        
        # Theme selection
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark"],
            index=0
        )
        
        # API endpoint configuration
        api_endpoint = st.text_input(
            "API Endpoint",
            value="http://localhost:8000",
            help="Backend API endpoint"
        )
        
        if st.button("Update API Endpoint"):
            st.session_state.api_client = APIClient(api_endpoint)
            st.success("API endpoint updated!")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="text-align: center; color: gray; font-size: 0.8em;">
            AI Observability RCA v1.0.0<br>
            Powered by Llama3 & FastAPI
        </div>
        """,
        unsafe_allow_html=True
    )
    
    return selected_page

def show_create_alert_form():
    """Show form to create a test alert"""
    with st.sidebar.form("create_alert_form"):
        st.subheader("Create Test Alert")
        
        alert_source = st.selectbox(
            "Source",
            ["prometheus", "grafana", "datadog", "newrelic", "custom"]
        )
        
        alert_severity = st.selectbox(
            "Severity",
            ["low", "medium", "high", "critical"]
        )
        
        alert_type = st.selectbox(
            "Type",
            ["logs", "metrics", "traces", "events"]
        )
        
        alert_title = st.text_input(
            "Title",
            value="Test Alert"
        )
        
        alert_message = st.text_area(
            "Message",
            value="This is a test alert for demonstration purposes"
        )
        
        if st.form_submit_button("Create Alert"):
            try:
                api_client = st.session_state.get('api_client')
                if api_client:
                    alert_data = {
                        "alert_id": f"test-{int(st.time.time())}",
                        "source": alert_source,
                        "severity": alert_severity,
                        "title": alert_title,
                        "message": alert_message,
                        "alert_type": alert_type,
                        "raw_data": {
                            "test": True,
                            "created_from": "streamlit_ui"
                        }
                    }
                    
                    result = api_client.create_alert(alert_data)
                    if result:
                        st.success("✅ Alert created successfully!")
                    else:
                        st.error("❌ Failed to create alert")
                else:
                    st.error("❌ API client not available")
            except Exception as e:
                st.error(f"❌ Error creating alert: {str(e)}")

def show_health_check():
    """Show quick health check results"""
    try:
        api_client = st.session_state.get('api_client')
        if api_client:
            health_data = api_client.get_detailed_health()
            if health_data:
                overall_status = health_data.get('status', 'unknown')
                
                if overall_status == 'healthy':
                    st.sidebar.success(f"✅ System Status: {overall_status.upper()}")
                elif overall_status == 'degraded':
                    st.sidebar.warning(f"⚠️ System Status: {overall_status.upper()}")
                else:
                    st.sidebar.error(f"❌ System Status: {overall_status.upper()}")
                
                # Show component status
                components = health_data.get('components', {})
                for comp_name, comp_data in components.items():
                    comp_status = comp_data.get('status', 'unknown')
                    if comp_status == 'healthy':
                        st.sidebar.success(f"{comp_name}: ✅")
                    else:
                        st.sidebar.error(f"{comp_name}: ❌")
            else:
                st.sidebar.error("❌ Health check failed")
        else:
            st.sidebar.error("❌ API client not available")
    except Exception as e:
        st.sidebar.error(f"❌ Health check error: {str(e)}")
