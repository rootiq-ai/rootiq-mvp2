import streamlit as st
import pandas as pd
import json
from datetime import datetime

def show_rca_details():
    """Show detailed RCA analysis view"""
    
    st.header("🔍 RCA Analysis Details")
    
    api_client = st.session_state.get('api_client')
    if not api_client:
        st.error("API client not initialized")
        return
    
    # RCA selection
    rca_id = st.session_state.get('selected_rca_id')
    
    # Get list of RCAs for selection
    try:
        rcas = api_client.get_rcas(limit=100)
        if rcas:
            rca_options = {f"{rca['title']} ({rca['rca_id'][:8]}...)": rca['rca_id'] for rca in rcas}
            
            selected_option = st.selectbox(
                "Select RCA to view:",
                options=list(rca_options.keys()),
                index=0 if not rca_id else (list(rca_options.values()).index(rca_id) if rca_id in rca_options.values() else 0)
            )
            
            rca_id = rca_options[selected_option]
            st.session_state.selected_rca_id = rca_id
        else:
            st.info("No RCA analyses found")
            return
    except Exception as e:
        st.error(f"Error loading RCA list: {str(e)}")
        return
    
    # Get RCA details
    try:
        rca = api_client.get_rca(rca_id)
        if not rca:
            st.error("RCA not found")
            return
        
        # Display RCA details
        show_rca_overview(rca, api_client)
        
        st.markdown("---")
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Analysis", 
            "🚨 Related Alerts", 
            "⚙️ Actions", 
            "📊 Feedback", 
            "🔧 Raw Data"
        ])
        
        with tab1:
            show_rca_analysis(rca)
        
        with tab2:
            show_related_alerts(rca, api_client)
        
        with tab3:
            show_rca_actions(rca, api_client)
        
        with tab4:
            show_feedback_section(rca, api_client)
        
        with tab5:
            show_raw_data(rca)
    
    except Exception as e:
        st.error(f"Error loading RCA details: {str(e)}")

def show_rca_overview(rca, api_client):
    """Show RCA overview information"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = api_client.get_status_color(rca['status'])
        st.markdown(f"""
        **Status:**  
        <span style="color: {status_color}; font-weight: bold; font-size: 1.1em;">
        {rca['status'].replace('_', ' ').title()}
        </span>
        """, unsafe_allow_html=True)
    
    with col2:
        priority_color = api_client.get_priority_color(rca['priority'])
        st.markdown(f"""
        **Priority:**  
        <span style="color: {priority_color}; font-weight: bold; font-size: 1.1em;">
        {rca['priority'].title()}
        </span>
        """, unsafe_allow_html=True)
    
    with col3:
        if rca.get('confidence_score'):
            confidence = rca['confidence_score']
            confidence_color = "green" if confidence >= 0.8 else "orange" if confidence >= 0.5 else "red"
            st.markdown(f"""
            **Confidence:**  
            <span style="color: {confidence_color}; font-weight: bold; font-size: 1.1em;">
            {confidence:.1%}
            </span>
            """, unsafe_allow_html=True)
        else:
            st.write("**Confidence:** N/A")
    
    with col4:
        if rca.get('accuracy_rating'):
            accuracy = rca['accuracy_rating']
            accuracy_color = "green" if accuracy >= 0.8 else "orange" if accuracy >= 0.5 else "red"
            st.markdown(f"""
            **Accuracy:**  
            <span style="color: {accuracy_color}; font-weight: bold; font-size: 1.1em;">
            {accuracy:.1%}
            </span>
            """, unsafe_allow_html=True)
        else:
            st.write("**Accuracy:** Not rated")
    
    # Basic information
    st.markdown("### 📄 Basic Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**RCA ID:** {rca['rca_id']}")
        st.write(f"**Correlation ID:** {rca['correlation_id']}")
        st.write(f"**Created:** {api_client.format_datetime(rca['created_at'])}")
        if rca.get('resolved_at'):
            st.write(f"**Resolved:** {api_client.format_datetime(rca['resolved_at'])}")
    
    with col2:
        st.write(f"**Assigned To:** {rca.get('assigned_to', 'Unassigned')}")
        st.write(f"**Team:** {rca.get('team', 'N/A')}")
        if rca.get('resolution_time'):
            st.write(f"**Resolution Time:** {rca['resolution_time']} minutes")
        if rca.get('business_impact'):
            st.write(f"**Business Impact:** {rca['business_impact'].title()}")
    
    # Title and summary
    st.markdown("### 📝 Title & Summary")
    st.write(f"**Title:** {rca['title']}")
    if rca.get('summary'):
        st.write(f"**Summary:** {rca['summary']}")

def show_rca_analysis(rca):
    """Show detailed RCA analysis"""
    
    st.markdown("### 🔍 Root Cause Analysis")
    
    if rca.get('root_cause'):
        st.markdown("#### 🎯 Root Cause")
        st.write(rca['root_cause'])
    else:
        st.info("Root cause analysis not available")
    
    if rca.get('solution'):
        st.markdown("#### 💡 Recommended Solution")
        st.write(rca['solution'])
    
    if rca.get('impact_analysis'):
        st.markdown("#### 📊 Impact Analysis")
        st.write(rca['impact_analysis'])
    
    # Additional analysis from LLM
    if rca.get('llm_analysis'):
        llm_data = rca['llm_analysis']
        
        col1, col2 = st.columns(2)
        
        with col1:
            if llm_data.get('prevention_measures'):
                st.markdown("#### 🛡️ Prevention Measures")
                st.write(llm_data['prevention_measures'])
        
        with col2:
            if llm_data.get('monitoring_recommendations'):
                st.markdown("#### 📈 Monitoring Recommendations")
                st.write(llm_data['monitoring_recommendations'])
        
        if llm_data.get('affected_systems'):
            st.markdown("#### 🖥️ Affected Systems")
            systems = llm_data['affected_systems']
            if isinstance(systems, list):
                for system in systems:
                    st.write(f"• {system}")
            else:
                st.write(systems)

def show_related_alerts(rca, api_client):
    """Show alerts related to this RCA"""
    
    st.markdown("### 🚨 Related Alerts")
    
    try:
        # Get alerts for this correlation ID
        alerts = api_client.get_alerts(correlation_id=rca['correlation_id'])
        
        if alerts:
            alert_data = []
            for alert in alerts:
                alert_data.append({
                    "Alert ID": alert['alert_id'],
                    "Source": alert['source'],
                    "Severity": alert['severity'],
                    "Type": alert['alert_type'],
                    "Title": alert['title'],
                    "Status": alert['status'],
                    "Created": api_client.format_datetime(alert['created_at'])
                })
            
            df = pd.DataFrame(alert_data)
            
            # Display alerts table
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Alert details expander
            for i, alert in enumerate(alerts):
                with st.expander(f"Alert Details: {alert['alert_id']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Source:** {alert['source']}")
                        st.write(f"**Severity:** {alert['severity']}")
                        st.write(f"**Type:** {alert['alert_type']}")
                        st.write(f"**Status:** {alert['status']}")
                    
                    with col2:
                        st.write(f"**Created:** {api_client.format_datetime(alert['created_at'])}")
                        if alert.get('updated_at'):
                            st.write(f"**Updated:** {api_client.format_datetime(alert['updated_at'])}")
                    
                    st.write(f"**Title:** {alert['title']}")
                    st.write(f"**Description:** {alert.get('description', 'N/A')}")
                    st.write(f"**Message:** {alert['message']}")
                    
                    if alert.get('raw_data'):
                        st.write("**Raw Data:**")
                        st.json(alert['raw_data'])
        else:
            st.info("No related alerts found")
    
    except Exception as e:
        st.error(f"Error loading related alerts: {str(e)}")

def show_rca_actions(rca, api_client):
    """Show RCA management actions"""
    
    st.markdown("### ⚙️ RCA Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Status Management")
        
        current_status = rca['status']
        new_status = st.selectbox(
            "Update Status",
            ["open", "in_progress", "closed"],
            index=["open", "in_progress", "closed"].index(current_status)
        )
        
        assigned_to = st.text_input(
            "Assign To",
            value=rca.get('assigned_to', '')
        )
        
        if st.button("Update Status & Assignment"):
            try:
                result = api_client.update_rca_status(
                    rca['rca_id'], 
                    new_status, 
                    assigned_to if assigned_to else None
                )
                if result:
                    st.success("✅ RCA updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update RCA")
            except Exception as e:
                st.error(f"❌ Error updating RCA: {str(e)}")
    
    with col2:
        st.markdown("#### Additional Actions")
        
        if st.button("🔄 Refresh RCA Data"):
            st.rerun()
        
        if st.button("📧 Generate Report"):
            generate_rca_report(rca)
        
        if st.button("🔗 Copy RCA Link"):
            st.info(f"RCA Link: /rca/{rca['rca_id']}")
        
        if st.button("⬇️ Export RCA Data"):
            export_rca_data(rca)

def show_feedback_section(rca, api_client):
    """Show feedback submission and history"""
    
    st.markdown("### 📊 Feedback & Accuracy Rating")
    
    # Existing feedback display
    if rca.get('user_feedback'):
        st.markdown("#### 📝 Previous Feedback")
        feedback = rca['user_feedback']
        
        if isinstance(feedback, list):
            for i, fb in enumerate(feedback):
                with st.expander(f"Feedback {i+1}"):
                    show_feedback_item(fb)
        else:
            show_feedback_item(feedback)
    
    # New feedback form
    st.markdown("#### ➕ Submit New Feedback")
    
    with st.form("feedback_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            is_accurate = st.radio(
                "Is this RCA accurate?",
                ["Yes", "No"],
                horizontal=True
            )
            
            accuracy_rating = st.slider(
                "Accuracy Rating (0-100%)",
                min_value=0,
                max_value=100,
                value=80,
                step=5
            ) / 100.0
        
        with col2:
            user_id = st.text_input("User ID", value="streamlit_user")
            user_role = st.selectbox("Role", ["engineer", "manager", "analyst", "other"])
        
        feedback_text = st.text_area(
            "Feedback Comments",
            placeholder="Please provide detailed feedback about the accuracy and usefulness of this analysis..."
        )
        
        if st.form_submit_button("Submit Feedback"):
            try:
                feedback_data = {
                    "is_accurate": is_accurate == "Yes",
                    "accuracy_rating": accuracy_rating,
                    "feedback_text": feedback_text,
                    "user_id": user_id,
                    "user_role": user_role
                }
                
                result = api_client.submit_feedback(rca['rca_id'], feedback_data)
                if result:
                    st.success("✅ Feedback submitted successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to submit feedback")
            except Exception as e:
                st.error(f"❌ Error submitting feedback: {str(e)}")

def show_feedback_item(feedback):
    """Display a single feedback item"""
    col1, col2 = st.columns(2)
    
    with col1:
        is_accurate = feedback.get('is_accurate', False)
        accuracy_icon = "✅" if is_accurate else "❌"
        st.write(f"**Accurate:** {accuracy_icon} {is_accurate}")
        
        if feedback.get('accuracy_rating'):
            st.write(f"**Rating:** {feedback['accuracy_rating']:.1%}")
    
    with col2:
        if feedback.get('user_id'):
            st.write(f"**User:** {feedback['user_id']}")
        if feedback.get('user_role'):
            st.write(f"**Role:** {feedback['user_role']}")
        if feedback.get('timestamp'):
            st.write(f"**Date:** {feedback['timestamp']}")
    
    if feedback.get('feedback_text'):
        st.write(f"**Comments:** {feedback['feedback_text']}")

def show_raw_data(rca):
    """Show raw RCA data"""
    
    st.markdown("### 🔧 Raw Data")
    
    # Display raw RCA data
    st.json(rca)

def generate_rca_report(rca):
    """Generate a formatted report for the RCA"""
    
    report = f"""
# RCA Report: {rca['title']}

**RCA ID:** {rca['rca_id']}  
**Status:** {rca['status']}  
**Priority:** {rca['priority']}  
**Created:** {rca['created_at']}  
**Assigned To:** {rca.get('assigned_to', 'Unassigned')}  

## Summary
{rca.get('summary', 'N/A')}

## Root Cause
{rca.get('root_cause', 'N/A')}

## Recommended Solution
{rca.get('solution', 'N/A')}

## Impact Analysis
{rca.get('impact_analysis', 'N/A')}

## Confidence Score
{rca.get('confidence_score', 0):.1%}

## Accuracy Rating
{rca.get('accuracy_rating', 0):.1%}
"""
    
    st.download_button(
        label="📄 Download Report",
        data=report,
        file_name=f"rca_report_{rca['rca_id'][:8]}.md",
        mime="text/markdown"
    )

def export_rca_data(rca):
    """Export RCA data as JSON"""
    
    st.download_button(
        label="📊 Download JSON",
        data=json.dumps(rca, indent=2),
        file_name=f"rca_data_{rca['rca_id'][:8]}.json",
        mime="application/json"
    )
