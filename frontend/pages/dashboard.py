import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from components.metrics import create_metrics_dashboard

def show_dashboard():
    """Show main dashboard with overview and recent activity"""
    
    st.header("📊 Dashboard Overview")
    
    api_client = st.session_state.get('api_client')
    if not api_client:
        st.error("API client not initialized")
        return
    
    # Test API connection
    if not api_client.test_connection():
        st.error("❌ Cannot connect to backend API")
        st.info("Please ensure the backend service is running on http://localhost:8000")
        return
    
    # Metrics dashboard
    create_metrics_dashboard(api_client)
    
    st.markdown("---")
    
    # Recent activity section
    col1, col2 = st.columns(2)
    
    with col1:
        show_recent_rcas(api_client)
    
    with col2:
        show_recent_alerts(api_client)
    
    # Correlation groups section
    st.markdown("---")
    show_correlation_groups(api_client)

def show_recent_rcas(api_client):
    """Show recent RCA analyses"""
    st.subheader("🔍 Recent RCA Analyses")
    
    try:
        # Get recent RCAs
        rcas = api_client.get_rcas(limit=10)
        
        if rcas:
            rca_data = []
            for rca in rcas:
                rca_data.append({
                    "ID": rca['rca_id'][:8] + "...",
                    "Title": rca['title'][:40] + "..." if len(rca['title']) > 40 else rca['title'],
                    "Status": rca['status'],
                    "Priority": rca['priority'],
                    "Accuracy": f"{rca.get('accuracy_rating', 0):.1%}" if rca.get('accuracy_rating') else "N/A",
                    "Created": api_client.format_datetime(rca['created_at'])
                })
            
            df = pd.DataFrame(rca_data)
            
            # Style the dataframe
            def style_status(val):
                if val == 'open':
                    return 'background-color: #fee2e2; color: #dc2626;'
                elif val == 'in_progress':
                    return 'background-color: #fef3c7; color: #d97706;'
                elif val == 'closed':
                    return 'background-color: #d1fae5; color: #059669;'
                return ''
            
            def style_priority(val):
                if val == 'critical':
                    return 'color: #dc2626; font-weight: bold;'
                elif val == 'high':
                    return 'color: #f97316; font-weight: bold;'
                elif val == 'medium':
                    return 'color: #d97706;'
                return 'color: #059669;'
            
            styled_df = df.style.applymap(style_status, subset=['Status']).applymap(style_priority, subset=['Priority'])
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Quick action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Refresh RCAs"):
                    st.rerun()
            with col2:
                if st.button("📊 View All RCAs"):
                    st.session_state.selected_page = "RCA Details"
                    st.rerun()
            with col3:
                if st.button("🔍 Search RCAs"):
                    st.session_state.selected_page = "Search & Filter"
                    st.rerun()
        else:
            st.info("No RCA analyses found")
            
            if st.button("➕ Generate Sample RCA"):
                show_generate_rca_form(api_client)
    
    except Exception as e:
        st.error(f"Error loading recent RCAs: {str(e)}")

def show_recent_alerts(api_client):
    """Show recent alerts"""
    st.subheader("🚨 Recent Alerts")
    
    try:
        # Get recent alerts
        alerts = api_client.get_alerts(limit=10)
        
        if alerts:
            alert_data = []
            for alert in alerts:
                alert_data.append({
                    "ID": alert['alert_id'][:8] + "...",
                    "Source": alert['source'],
                    "Severity": alert['severity'],
                    "Type": alert['alert_type'],
                    "Status": alert['status'],
                    "Correlated": "Yes" if alert.get('correlation_id') else "No",
                    "Created": api_client.format_datetime(alert['created_at'])
                })
            
            df = pd.DataFrame(alert_data)
            
            # Style the dataframe
            def style_severity(val):
                if val == 'critical':
                    return 'background-color: #fee2e2; color: #dc2626; font-weight: bold;'
                elif val == 'high':
                    return 'background-color: #fed7aa; color: #ea580c;'
                elif val == 'medium':
                    return 'background-color: #fef3c7; color: #d97706;'
                return 'background-color: #d1fae5; color: #059669;'
            
            def style_correlated(val):
                if val == 'Yes':
                    return 'color: #059669; font-weight: bold;'
                return 'color: #6b7280;'
            
            styled_df = df.style.applymap(style_severity, subset=['Severity']).applymap(style_correlated, subset=['Correlated'])
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Quick action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Refresh Alerts", key="refresh_alerts"):
                    st.rerun()
            with col2:
                if st.button("📊 View All Alerts"):
                    # Switch to alerts view - could be implemented
                    st.info("Alert management view coming soon!")
            with col3:
                if st.button("🔍 Search Alerts"):
                    st.session_state.selected_page = "Search & Filter"
                    st.rerun()
        else:
            st.info("No alerts found")
            
            if st.button("➕ Create Sample Alert"):
                show_create_alert_form(api_client)
    
    except Exception as e:
        st.error(f"Error loading recent alerts: {str(e)}")

def show_correlation_groups(api_client):
    """Show correlation groups"""
    st.subheader("🔗 Alert Correlation Groups")
    
    try:
        # Get correlation groups
        groups = api_client.get_correlation_groups(limit=5)
        
        if groups:
            for i, group in enumerate(groups):
                with st.expander(f"Correlation Group {i+1} - {group['alert_count']} alerts"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Alert Count", group['alert_count'])
                    with col2:
                        st.metric("Confidence", f"{group['confidence_score']:.1%}")
                    with col3:
                        st.metric("Method", group['correlation_method'].title())
                    with col4:
                        # Check if RCA exists for this correlation
                        rcas = api_client.get_rcas(limit=1, correlation_id=group['correlation_id'])
                        if rcas:
                            st.success("RCA Generated")
                            if st.button(f"View RCA", key=f"view_rca_{i}"):
                                st.session_state.selected_rca_id = rcas[0]['rca_id']
                                st.session_state.selected_page = "RCA Details"
                                st.rerun()
                        else:
                            if st.button(f"Generate RCA", key=f"gen_rca_{i}"):
                                generate_rca_for_correlation(api_client, group['correlation_id'])
                    
                    # Show alert IDs
                    st.write("**Alert IDs:**", ", ".join(group['alerts'][:5]))
                    if len(group['alerts']) > 5:
                        st.write(f"... and {len(group['alerts']) - 5} more")
                    
                    st.write(f"**Time Range:** {api_client.format_datetime(group['start_time'])} - {api_client.format_datetime(group['end_time'])}")
        else:
            st.info("No correlation groups found")
    
    except Exception as e:
        st.error(f"Error loading correlation groups: {str(e)}")

def show_generate_rca_form(api_client):
    """Show form to generate RCA"""
    with st.form("generate_rca_form"):
        st.subheader("Generate RCA")
        
        # Get correlation groups for selection
        groups = api_client.get_correlation_groups(limit=20)
        
        if groups:
            correlation_options = {
                f"Group {i+1} ({group['alert_count']} alerts)": group['correlation_id'] 
                for i, group in enumerate(groups)
            }
            
            selected_group = st.selectbox(
                "Select Correlation Group",
                options=list(correlation_options.keys())
            )
            
            title = st.text_input("RCA Title", value="Automated RCA Analysis")
            priority = st.selectbox("Priority", ["low", "medium", "high", "critical"])
            use_historical = st.checkbox("Use Historical Context", value=True)
            
            if st.form_submit_button("Generate RCA"):
                correlation_id = correlation_options[selected_group]
                generate_rca_for_correlation(api_client, correlation_id, title, priority, use_historical)
        else:
            st.info("No correlation groups available for RCA generation")

def show_create_alert_form(api_client):
    """Show form to create sample alert"""
    with st.form("create_alert_form"):
        st.subheader("Create Sample Alert")
        
        col1, col2 = st.columns(2)
        
        with col1:
            source = st.selectbox("Source", ["prometheus", "grafana", "datadog", "newrelic"])
            severity = st.selectbox("Severity", ["low", "medium", "high", "critical"])
            alert_type = st.selectbox("Type", ["logs", "metrics", "traces", "events"])
        
        with col2:
            title = st.text_input("Title", value="Sample Alert")
            message = st.text_area("Message", value="This is a sample alert for testing")
        
        if st.form_submit_button("Create Alert"):
            alert_data = {
                "alert_id": f"sample-{int(datetime.now().timestamp())}",
                "source": source,
                "severity": severity,
                "title": title,
                "message": message,
                "alert_type": alert_type,
                "raw_data": {
                    "sample": True,
                    "created_from": "dashboard"
                }
            }
            
            result = api_client.create_alert(alert_data)
            if result:
                st.success("✅ Sample alert created successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to create alert")

def generate_rca_for_correlation(api_client, correlation_id, title="Automated RCA", 
                               priority="medium", use_historical=True):
    """Generate RCA for a correlation group"""
    try:
        with st.spinner("Generating RCA analysis..."):
            result = api_client.generate_rca(
                correlation_id=correlation_id,
                title=title,
                priority=priority,
                use_historical_context=use_historical
            )
            
            if result:
                st.success(f"✅ RCA generation started! ID: {result['rca_id']}")
                st.info(f"Estimated completion time: {result.get('estimated_completion_time', 120)} seconds")
                
                # Offer to navigate to RCA details
                if st.button("View RCA Progress"):
                    st.session_state.selected_rca_id = result['rca_id']
                    st.session_state.selected_page = "RCA Details"
                    st.rerun()
            else:
                st.error("❌ Failed to start RCA generation")
    
    except Exception as e:
        st.error(f"❌ Error generating RCA: {str(e)}")
