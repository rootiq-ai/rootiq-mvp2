import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def show_search_page():
    """Show search and filter interface"""
    
    st.header("🔍 Search & Filter")
    
    api_client = st.session_state.get('api_client')
    if not api_client:
        st.error("API client not initialized")
        return
    
    # Search type selection
    search_type = st.radio(
        "Search Type",
        ["RCA Analyses", "Alerts", "Correlation Groups"],
        horizontal=True
    )
    
    if search_type == "RCA Analyses":
        show_rca_search(api_client)
    elif search_type == "Alerts":
        show_alert_search(api_client)
    else:
        show_correlation_search(api_client)

def show_rca_search(api_client):
    """Show RCA search and filter interface"""
    
    st.subheader("🔍 Search RCA Analyses")
    
    # Search filters
    with st.expander("🎛️ Search Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.multiselect(
                "Status",
                ["open", "in_progress", "closed"],
                default=[]
            )
            
            priority_filter = st.multiselect(
                "Priority",
                ["low", "medium", "high", "critical"],
                default=[]
            )
        
        with col2:
            assigned_to_filter = st.text_input("Assigned To")
            team_filter = st.text_input("Team")
            
            has_feedback_filter = st.selectbox(
                "Has Feedback",
                [None, True, False],
                format_func=lambda x: "Any" if x is None else ("Yes" if x else "No")
            )
        
        with col3:
            min_accuracy = st.slider(
                "Minimum Accuracy",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1,
                format="%.1f"
            )
            
            # Date range
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                format="YYYY-MM-DD"
            )
        
        # Pagination
        col1, col2 = st.columns(2)
        with col1:
            limit = st.number_input("Results per page", min_value=10, max_value=1000, value=50)
        with col2:
            offset = st.number_input("Offset", min_value=0, value=0)
    
    # Search button
    if st.button("🔎 Search RCAs"):
        search_rcas(api_client, status_filter, priority_filter, assigned_to_filter, 
                   team_filter, has_feedback_filter, min_accuracy, date_range, limit, offset)

def search_rcas(api_client, status_filter, priority_filter, assigned_to_filter, 
               team_filter, has_feedback_filter, min_accuracy, date_range, limit, offset):
    """Execute RCA search"""
    
    try:
        # Prepare search parameters
        search_params = {
            "limit": limit,
            "offset": offset
        }
        
        if status_filter:
            search_params["status"] = status_filter
        if priority_filter:
            search_params["priority"] = priority_filter
        if assigned_to_filter:
            search_params["assigned_to"] = assigned_to_filter
        if team_filter:
            search_params["team"] = team_filter
        if has_feedback_filter is not None:
            search_params["has_feedback"] = has_feedback_filter
        if min_accuracy > 0:
            search_params["min_accuracy"] = min_accuracy
        
        if date_range and len(date_range) == 2:
            search_params["start_date"] = date_range[0].isoformat()
            search_params["end_date"] = date_range[1].isoformat()
        
        # Execute search
        with st.spinner("Searching RCAs..."):
            rcas = api_client.get_rcas(**search_params)
        
        if rcas:
            st.success(f"Found {len(rcas)} RCA(s)")
            display_rca_results(rcas, api_client)
        else:
            st.info("No RCAs found matching the search criteria")
    
    except Exception as e:
        st.error(f"Error searching RCAs: {str(e)}")

def display_rca_results(rcas, api_client):
    """Display RCA search results"""
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_count = len(rcas)
        st.metric("Total Results", total_count)
    
    with col2:
        open_count = len([rca for rca in rcas if rca['status'] == 'open'])
        st.metric("Open RCAs", open_count)
    
    with col3:
        high_priority = len([rca for rca in rcas if rca['priority'] in ['high', 'critical']])
        st.metric("High Priority", high_priority)
    
    with col4:
        with_feedback = len([rca for rca in rcas if rca.get('accuracy_rating')])
        st.metric("With Feedback", with_feedback)
    
    # Results table
    st.subheader("📋 Search Results")
    
    # Prepare data for display
    rca_data = []
    for rca in rcas:
        rca_data.append({
            "RCA ID": rca['rca_id'][:8] + "...",
            "Title": rca['title'][:50] + "..." if len(rca['title']) > 50 else rca['title'],
            "Status": rca['status'],
            "Priority": rca['priority'],
            "Assigned To": rca.get('assigned_to', 'Unassigned'),
            "Accuracy": f"{rca.get('accuracy_rating', 0):.1%}" if rca.get('accuracy_rating') else "N/A",
            "Confidence": f"{rca.get('confidence_score', 0):.1%}" if rca.get('confidence_score') else "N/A",
            "Created": api_client.format_datetime(rca['created_at']),
            "Actions": rca['rca_id']  # Store full ID for actions
        })
    
    df = pd.DataFrame(rca_data)
    
    # Display results with selection
    selected_indices = st.multiselect(
        "Select RCAs for bulk actions:",
        range(len(df)),
        format_func=lambda x: f"{df.iloc[x]['RCA ID']} - {df.iloc[x]['Title']}"
    )
    
    # Style the dataframe
    def style_status(val):
        colors = {
            'open': 'background-color: #fee2e2; color: #dc2626;',
            'in_progress': 'background-color: #fef3c7; color: #d97706;',
            'closed': 'background-color: #d1fae5; color: #059669;'
        }
        return colors.get(val, '')
    
    def style_priority(val):
        colors = {
            'low': 'color: #059669;',
            'medium': 'color: #d97706;',
            'high': 'color: #f97316; font-weight: bold;',
            'critical': 'color: #dc2626; font-weight: bold;'
        }
        return colors.get(val, '')
    
    styled_df = df.drop('Actions', axis=1).style.applymap(
        style_status, subset=['Status']
    ).applymap(
        style_priority, subset=['Priority']
    )
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Individual RCA actions
    for i, rca in enumerate(rcas):
        with st.expander(f"Actions for {rca['title'][:40]}..."):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button(f"View Details", key=f"view_{i}"):
                    st.session_state.selected_rca_id = rca['rca_id']
                    st.session_state.selected_page = "RCA Details"
                    st.rerun()
            
            with col2:
                new_status = st.selectbox(
                    "Status", 
                    ["open", "in_progress", "closed"],
                    index=["open", "in_progress", "closed"].index(rca['status']),
                    key=f"status_{i}"
                )
                if st.button(f"Update", key=f"update_{i}"):
                    update_rca_status(api_client, rca['rca_id'], new_status)
            
            with col3:
                if st.button(f"Generate Report", key=f"report_{i}"):
                    generate_rca_report_from_search(rca)
            
            with col4:
                if st.button(f"Export Data", key=f"export_{i}"):
                    export_rca_data_from_search(rca)
    
    # Bulk actions
    if selected_indices:
        st.subheader("🔧 Bulk Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            bulk_status = st.selectbox("Set Status", ["open", "in_progress", "closed"])
            if st.button("Apply to Selected"):
                perform_bulk_status_update(api_client, selected_indices, rcas, bulk_status)
        
        with col2:
            bulk_assignee = st.text_input("Assign To")
            if st.button("Assign Selected"):
                perform_bulk_assignment(api_client, selected_indices, rcas, bulk_assignee)
        
        with col3:
            if st.button("Export Selected"):
                export_selected_rcas(selected_indices, rcas)

def show_alert_search(api_client):
    """Show alert search interface"""
    
    st.subheader("🚨 Search Alerts")
    
    # Search filters
    with st.expander("🎛️ Search Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.multiselect(
                "Status",
                ["open", "acknowledged", "resolved"],
                default=[]
            )
            
            severity_filter = st.multiselect(
                "Severity",
                ["low", "medium", "high", "critical"],
                default=[]
            )
        
        with col2:
            source_filter = st.multiselect(
                "Source",
                ["prometheus", "grafana", "datadog", "newrelic", "custom"],
                default=[]
            )
            
            alert_type_filter = st.multiselect(
                "Type",
                ["logs", "metrics", "traces", "events"],
                default=[]
            )
        
        with col3:
            correlation_id_filter = st.text_input("Correlation ID")
            
            # Date range
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=7), datetime.now()),
                format="YYYY-MM-DD"
            )
        
        # Pagination
        col1, col2 = st.columns(2)
        with col1:
            limit = st.number_input("Results per page", min_value=10, max_value=1000, value=50, key="alert_limit")
        with col2:
            offset = st.number_input("Offset", min_value=0, value=0, key="alert_offset")
    
    # Search button
    if st.button("🔎 Search Alerts"):
        search_alerts(api_client, status_filter, severity_filter, source_filter, 
                     alert_type_filter, correlation_id_filter, date_range, limit, offset)

def search_alerts(api_client, status_filter, severity_filter, source_filter, 
                 alert_type_filter, correlation_id_filter, date_range, limit, offset):
    """Execute alert search"""
    
    try:
        # Prepare search parameters
        search_params = {
            "limit": limit,
            "offset": offset
        }
        
        if status_filter:
            search_params["status"] = status_filter
        if severity_filter:
            search_params["severity"] = severity_filter
        if source_filter:
            search_params["source"] = source_filter
        if alert_type_filter:
            search_params["alert_type"] = alert_type_filter
        if correlation_id_filter:
            search_params["correlation_id"] = correlation_id_filter
        
        if date_range and len(date_range) == 2:
            search_params["start_date"] = date_range[0].isoformat()
            search_params["end_date"] = date_range[1].isoformat()
        
        # Execute search
        with st.spinner("Searching alerts..."):
            alerts = api_client.get_alerts(**search_params)
        
        if alerts:
            st.success(f"Found {len(alerts)} alert(s)")
            display_alert_results(alerts, api_client)
        else:
            st.info("No alerts found matching the search criteria")
    
    except Exception as e:
        st.error(f"Error searching alerts: {str(e)}")

def display_alert_results(alerts, api_client):
    """Display alert search results"""
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_count = len(alerts)
        st.metric("Total Results", total_count)
    
    with col2:
        critical_count = len([alert for alert in alerts if alert['severity'] == 'critical'])
        st.metric("Critical Alerts", critical_count)
    
    with col3:
        open_count = len([alert for alert in alerts if alert['status'] == 'open'])
        st.metric("Open Alerts", open_count)
    
    with col4:
        correlated_count = len([alert for alert in alerts if alert.get('correlation_id')])
        st.metric("Correlated", correlated_count)
    
    # Results table
    st.subheader("📋 Alert Results")
    
    # Prepare data for display
    alert_data = []
    for alert in alerts:
        alert_data.append({
            "Alert ID": alert['alert_id'][:12] + "..." if len(alert['alert_id']) > 12 else alert['alert_id'],
            "Source": alert['source'],
            "Severity": alert['severity'],
            "Type": alert['alert_type'],
            "Title": alert['title'][:40] + "..." if len(alert['title']) > 40 else alert['title'],
            "Status": alert['status'],
            "Correlated": "Yes" if alert.get('correlation_id') else "No",
            "Created": api_client.format_datetime(alert['created_at'])
        })
    
    df = pd.DataFrame(alert_data)
    
    # Style the dataframe
    def style_severity(val):
        colors = {
            'low': 'background-color: #d1fae5; color: #059669;',
            'medium': 'background-color: #fef3c7; color: #d97706;',
            'high': 'background-color: #fed7aa; color: #ea580c;',
            'critical': 'background-color: #fee2e2; color: #dc2626; font-weight: bold;'
        }
        return colors.get(val, '')
    
    def style_correlated(val):
        return 'color: #059669; font-weight: bold;' if val == 'Yes' else 'color: #6b7280;'
    
    styled_df = df.style.applymap(
        style_severity, subset=['Severity']
    ).applymap(
        style_correlated, subset=['Correlated']
    )
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

def show_correlation_search(api_client):
    """Show correlation group search"""
    
    st.subheader("🔗 Correlation Groups")
    
    try:
        with st.spinner("Loading correlation groups..."):
            groups = api_client.get_correlation_groups(limit=100)
        
        if groups:
            st.success(f"Found {len(groups)} correlation group(s)")
            
            for i, group in enumerate(groups):
                with st.expander(f"Group {i+1}: {group['alert_count']} alerts - {group['correlation_method']}"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Alert Count", group['alert_count'])
                    with col2:
                        st.metric("Confidence", f"{group['confidence_score']:.1%}")
                    with col3:
                        st.metric("Method", group['correlation_method'].title())
                    with col4:
                        # Check if RCA exists
                        rcas = api_client.get_rcas(limit=1, correlation_id=group['correlation_id'])
                        if rcas:
                            st.success("Has RCA")
                            if st.button(f"View RCA", key=f"view_group_rca_{i}"):
                                st.session_state.selected_rca_id = rcas[0]['rca_id']
                                st.session_state.selected_page = "RCA Details"
                                st.rerun()
                        else:
                            st.info("No RCA")
                            if st.button(f"Generate RCA", key=f"gen_group_rca_{i}"):
                                generate_rca_for_group(api_client, group['correlation_id'])
                    
                    st.write(f"**Correlation ID:** {group['correlation_id']}")
                    st.write(f"**Time Range:** {api_client.format_datetime(group['start_time'])} - {api_client.format_datetime(group['end_time'])}")
                    st.write(f"**Alert IDs:** {', '.join(group['alerts'][:5])}")
                    if len(group['alerts']) > 5:
                        st.write(f"... and {len(group['alerts']) - 5} more alerts")
        else:
            st.info("No correlation groups found")
    
    except Exception as e:
        st.error(f"Error loading correlation groups: {str(e)}")

# Helper functions for actions
def update_rca_status(api_client, rca_id, new_status):
    """Update RCA status"""
    try:
        result = api_client.update_rca_status(rca_id, new_status)
        if result:
            st.success(f"✅ RCA status updated to {new_status}")
            st.rerun()
        else:
            st.error("❌ Failed to update RCA status")
    except Exception as e:
        st.error(f"❌ Error updating RCA: {str(e)}")

def generate_rca_report_from_search(rca):
    """Generate report from search results"""
    report = f"""# RCA Report: {rca['title']}
**ID:** {rca['rca_id']}
**Status:** {rca['status']}
**Priority:** {rca['priority']}
**Created:** {rca['created_at']}
"""
    st.download_button(
        f"📄 Download Report",
        data=report,
        file_name=f"rca_report_{rca['rca_id'][:8]}.md",
        mime="text/markdown"
    )

def export_rca_data_from_search(rca):
    """Export RCA data from search results"""
    import json
    st.download_button(
        f"📊 Download Data",
        data=json.dumps(rca, indent=2),
        file_name=f"rca_data_{rca['rca_id'][:8]}.json",
        mime="application/json"
    )

def perform_bulk_status_update(api_client, selected_indices, rcas, bulk_status):
    """Perform bulk status update"""
    try:
        for idx in selected_indices:
            rca = rcas[idx]
            api_client.update_rca_status(rca['rca_id'], bulk_status)
        
        st.success(f"✅ Updated {len(selected_indices)} RCA(s) to {bulk_status}")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error updating RCAs: {str(e)}")

def perform_bulk_assignment(api_client, selected_indices, rcas, bulk_assignee):
    """Perform bulk assignment"""
    try:
        for idx in selected_indices:
            rca = rcas[idx]
            update_data = {"assigned_to": bulk_assignee}
            api_client.update_rca(rca['rca_id'], update_data)
        
        st.success(f"✅ Assigned {len(selected_indices)} RCA(s) to {bulk_assignee}")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error assigning RCAs: {str(e)}")

def export_selected_rcas(selected_indices, rcas):
    """Export selected RCAs"""
    import json
    selected_rcas = [rcas[i] for i in selected_indices]
    
    st.download_button(
        f"📊 Export {len(selected_rcas)} RCAs",
        data=json.dumps(selected_rcas, indent=2),
        file_name=f"bulk_rca_export_{len(selected_rcas)}_items.json",
        mime="application/json"
    )

def generate_rca_for_group(api_client, correlation_id):
    """Generate RCA for correlation group"""
    try:
        with st.spinner("Generating RCA..."):
            result = api_client.generate_rca(correlation_id=correlation_id)
            if result:
                st.success(f"✅ RCA generation started: {result['rca_id']}")
                st.rerun()
            else:
                st.error("❌ Failed to generate RCA")
    except Exception as e:
        st.error(f"❌ Error generating RCA: {str(e)}")
