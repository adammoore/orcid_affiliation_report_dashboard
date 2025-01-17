import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

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

# Title and description
st.title("ORCID Affiliation Analysis Dashboard")
st.markdown("""
Upload your ORCID affiliation Excel file to analyze the data. The file should contain the following columns:
- ORCID ID
- Given Names
- Family Name
- Org Affiliation Relation Role
- Org Affiliation Relation Title
- Department
- Start Year
- End Year
- Date Created
- Last Modified
- Source
- Identifier Type
- Identifier Value
""")

# File uploader
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    # Load data
    @st.cache_data
    def load_data(file):
        df = pd.read_excel(file)
        df['Start Year'] = pd.to_numeric(df['Start Year'], errors='coerce')
        df['End Year'] = pd.to_numeric(df['End Year'], errors='coerce')
        df['Duration'] = df['End Year'] - df['Start Year']
        return df

    # Load the data
    try:
        df = load_data(uploaded_file)
        
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

        # Filter data
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
        tab1, tab2, tab3 = st.tabs(["Overview", "Temporal Analysis", "Network Analysis"])

        with tab1:
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

        with tab2:
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

        with tab3:
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

    except Exception as e:
        st.error(f"""
        Error loading the file. Please ensure your Excel file has the correct format.
        Error details: {str(e)}
        """)
else:
    st.info("Please upload an Excel file to begin the analysis.")
