import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import os
import tempfile
from utils.orcid_api import OrcidAPI

# Set page config
st.set_page_config(
    page_title="ORCID Affiliation Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_data' not in st.session_state:
    st.session_state.api_data = pd.DataFrame()
if 'file_data' not in st.session_state:
    st.session_state.file_data = pd.DataFrame()
if 'merged_data' not in st.session_state:
    st.session_state.merged_data = pd.DataFrame()

# Title and description
st.title("ORCID Affiliation Analysis Dashboard")

# Create tabs for data input methods
data_input_tab, analysis_tab = st.tabs(["Data Input", "Analysis"])

with data_input_tab:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Upload ORCID Affiliation File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
        
        if uploaded_file is not None:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                st.session_state.file_data = pd.read_excel(tmp_path)
                os.unlink(tmp_path)  # Clean up the temporary file
                
                st.success(f"Successfully loaded {len(st.session_state.file_data)} records from file")
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
    
    with col2:
        st.subheader("Search ORCID by Email Domains")
        email_domains = st.text_area(
            "Enter email domains (one per line)",
            help="Example:\njisc.ac.uk\nox.ac.uk",
            height=100
        )
        max_results = st.number_input("Maximum number of results", min_value=1, value=1000, step=100)
        
        if st.button("Search ORCID Registry"):
            if email_domains:
                domains = [domain.strip() for domain in email_domains.split('\n') if domain.strip()]
                with st.spinner("Searching ORCID registry..."):
                    orcid_api = OrcidAPI()
                    st.session_state.api_data = orcid_api.search_by_email_domains(domains, max_results)
                    st.success(f"Found {len(st.session_state.api_data)} records from ORCID API")
    
    # Merge data option
    st.subheader("Merge Data Sources")
    if not st.session_state.file_data.empty or not st.session_state.api_data.empty:
        if st.button("Merge File and API Data"):
            orcid_api = OrcidAPI()
            st.session_state.merged_data = orcid_api.merge_with_existing_data(
                st.session_state.api_data,
                st.session_state.file_data
            )
            st.success(f"Successfully merged data: {len(st.session_state.merged_data)} total records")

with analysis_tab:
    # Get the active dataset
    if not st.session_state.merged_data.empty:
        df = st.session_state.merged_data
        st.info("Analyzing merged data from file and API")
    elif not st.session_state.file_data.empty:
        df = st.session_state.file_data
        st.info("Analyzing data from file upload")
    elif not st.session_state.api_data.empty:
        df = st.session_state.api_data
        st.info("Analyzing data from ORCID API")
    else:
        st.warning("Please upload a file or search ORCID registry in the Data Input tab")
        st.stop()
    
    # Continue with the existing analysis code...
    # Sidebar filters
    st.sidebar.header("Filters")

    # Date range filter
    min_year = int(df['Start Year'].min())
    max_year = int(datetime.now().year)
    year_range = st.sidebar.slider(
        "Select Year Range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )

    # Role filter
    selected_roles = st.sidebar.multiselect(
        "Select Roles",
        options=df['Org Affiliation Relation Role'].unique(),
        default=df['Org Affiliation Relation Role'].unique()
    )

    # Department filter
    selected_departments = st.sidebar.multiselect(
        "Select Departments",
        options=df['Department'].dropna().unique(),
        default=df['Department'].dropna().unique()
    )

    # Source filter (if merged data)
    if 'Source' in df.columns and df['Source'].nunique() > 1:
        selected_sources = st.sidebar.multiselect(
            "Select Data Sources",
            options=df['Source'].unique(),
            default=df['Source'].unique()
        )
        # Add source to filter
        filtered_df = df[
            (df['Org Affiliation Relation Role'].isin(selected_roles)) &
            ((df['Department'].isin(selected_departments)) | (df['Department'].isna())) &
            (df['Start Year'] >= year_range[0]) &
            (df['Start Year'] <= year_range[1]) &
            (df['Source'].isin(selected_sources))
        ]
    else:
        filtered_df = df[
            (df['Org Affiliation Relation Role'].isin(selected_roles)) &
            ((df['Department'].isin(selected_departments)) | (df['Department'].isna())) &
            (df['Start Year'] >= year_range[0]) &
            (df['Start Year'] <= year_range[1])
        ]

    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Affiliations", len(filtered_df))

    with col2:
        st.metric("Unique ORCID IDs", filtered_df['ORCID ID'].nunique())

    with col3:
        active_count = len(filtered_df[filtered_df['End Year'].isna()])
        st.metric("Active Affiliations", active_count)

    with col4:
        avg_duration = filtered_df['Duration'].mean()
        st.metric("Avg Duration (Years)", f"{avg_duration:.1f}" if pd.notna(avg_duration) else "N/A")

    # Create tabs for different visualizations
    viz_tab1, viz_tab2, viz_tab3 = st.tabs(["Overview", "Temporal Analysis", "Network Analysis"])

    with viz_tab1:
        col1, col2 = st.columns(2)

        with col1:
            # Role distribution
            st.subheader("Distribution of Roles")
            role_counts = filtered_df['Org Affiliation Relation Role'].value_counts()
            fig_roles = px.pie(values=role_counts.values, 
                            names=role_counts.index,
                            title="Distribution of Roles")
            st.plotly_chart(fig_roles, use_container_width=True)

        with col2:
            # Department distribution
            st.subheader("Top Departments")
            dept_counts = filtered_df['Department'].value_counts().head(10)
            fig_dept = px.bar(x=dept_counts.index, 
                            y=dept_counts.values,
                            title="Top 10 Departments")
            fig_dept.update_layout(xaxis_title="Department",
                                yaxis_title="Count",
                                xaxis_tickangle=45)
            st.plotly_chart(fig_dept, use_container_width=True)

        # Add source distribution if merged data
        if 'Source' in filtered_df.columns and filtered_df['Source'].nunique() > 1:
            st.subheader("Data Source Distribution")
            source_counts = filtered_df['Source'].value_counts()
            fig_source = px.pie(values=source_counts.values,
                              names=source_counts.index,
                              title="Distribution by Data Source")
            st.plotly_chart(fig_source, use_container_width=True)

    with viz_tab2:
        col1, col2 = st.columns(2)

        with col1:
            # Timeline of affiliations
            st.subheader("Timeline of Affiliations")
            timeline_df = filtered_df.dropna(subset=['Start Year'])
            fig_timeline = px.histogram(timeline_df, 
                                    x='Start Year',
                                    title="Distribution of Start Years")
            fig_timeline.update_layout(xaxis_title="Year",
                                    yaxis_title="Number of Affiliations")
            st.plotly_chart(fig_timeline, use_container_width=True)

        with col2:
            # Duration distribution
            st.subheader("Duration Distribution")
            duration_df = filtered_df.dropna(subset=['Duration'])
            fig_duration = px.box(duration_df, 
                                y='Duration',
                                points="all",
                                title="Distribution of Affiliation Durations")
            st.plotly_chart(fig_duration, use_container_width=True)

    with viz_tab3:
        # Network visualization of departments and roles
        st.subheader("Department-Role Network")
        
        # Create network data
        dept_role_counts = filtered_df.groupby(['Department', 'Org Affiliation Relation Role']).size().reset_index(name='count')
        dept_role_counts = dept_role_counts.dropna(subset=['Department'])
        
        # Create network graph
        fig_network = go.Figure()
        
        # Add nodes for departments
        for dept in dept_role_counts['Department'].unique():
            fig_network.add_trace(go.Scatter(
                x=[0],
                y=[np.random.random()],
                mode='markers+text',
                name=dept,
                text=[dept],
                marker=dict(size=20),
                textposition="middle right"
            ))
        
        # Add nodes for roles
        for role in dept_role_counts['Org Affiliation Relation Role'].unique():
            fig_network.add_trace(go.Scatter(
                x=[1],
                y=[np.random.random()],
                mode='markers+text',
                name=role,
                text=[role],
                marker=dict(size=20),
                textposition="middle left"
            ))
        
        fig_network.update_layout(
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            title="Department-Role Relationships"
        )
        
        st.plotly_chart(fig_network, use_container_width=True)

    # Export options
    st.subheader("Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download Filtered Data as CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="filtered_orcid_data.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Download Summary Statistics"):
            summary_stats = {
                "Total Affiliations": len(filtered_df),
                "Unique ORCID IDs": filtered_df['ORCID ID'].nunique(),
                "Active Affiliations": active_count,
                "Average Duration": float(avg_duration) if pd.notna(avg_duration) else None,
                "Role Distribution": role_counts.to_dict(),
                "Department Distribution": dept_counts.to_dict()
            }
            st.json(summary_stats)

    # Show raw data
    if st.checkbox("Show Raw Data"):
        st.subheader("Raw Data")
        st.dataframe(filtered_df)
