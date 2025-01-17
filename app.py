import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="ORCID Affiliation Dashboard",
    page_icon="📊",
    layout="wide"
)

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
        return df

    # Load the data
    try:
        df = load_data(uploaded_file)

        # Sidebar filters
        st.sidebar.header("Filters")

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
            ((df['Department'].isin(selected_departments)) | (df['Department'].isna()))
        ]

        # Create two columns for metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Affiliations", len(filtered_df))

        with col2:
            st.metric("Unique ORCID IDs", filtered_df['ORCID ID'].nunique())

        with col3:
            st.metric("Active Affiliations", 
                    len(filtered_df[filtered_df['End Year'].isna()]))

        # Create two columns for charts
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

        # Timeline of affiliations
        st.subheader("Timeline of Affiliations")
        timeline_df = filtered_df.dropna(subset=['Start Year'])
        fig_timeline = px.histogram(timeline_df, 
                                x='Start Year',
                                title="Distribution of Start Years")
        fig_timeline.update_layout(xaxis_title="Year",
                                yaxis_title="Number of Affiliations")
        st.plotly_chart(fig_timeline, use_container_width=True)

        # Additional Analysis
        st.subheader("Additional Analysis")
        col1, col2 = st.columns(2)

        with col1:
            # Average duration of completed affiliations
            completed_affiliations = filtered_df.dropna(subset=['Start Year', 'End Year'])
            if not completed_affiliations.empty:
                avg_duration = (completed_affiliations['End Year'] - completed_affiliations['Start Year']).mean()
                st.metric("Average Duration (Years)", f"{avg_duration:.1f}")

        with col2:
            # Most common titles
            st.write("Top 5 Position Titles")
            title_counts = filtered_df['Org Affiliation Relation Title'].value_counts().head()
            st.write(title_counts)

        # Show raw data
        if st.checkbox("Show Raw Data"):
            st.subheader("Raw Data")
            st.dataframe(filtered_df)

        # Download filtered data
        if st.button("Download Filtered Data as CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="filtered_orcid_data.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"""
        Error loading the file. Please ensure your Excel file has the correct format.
        Error details: {str(e)}
        """)
else:
    st.info("Please upload an Excel file to begin the analysis.")
