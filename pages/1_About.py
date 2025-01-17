import streamlit as st

st.set_page_config(
    page_title="About - ORCID Affiliation Dashboard",
    page_icon="ℹ️",
    layout="wide"
)

st.title("About ORCID Affiliation Dashboard")

st.markdown("""
This dashboard provides interactive visualization and analysis tools for ORCID affiliation data. 
It allows institutions to upload their ORCID affiliation data and gain insights through various visualizations and metrics.

## Features

- **Interactive Data Upload**: Upload ORCID affiliation data in Excel format
- **Dynamic Filtering**: Filter data by date range, roles, and departments
- **Multiple Visualizations**:
  - Role distribution
  - Department analysis
  - Timeline views
  - Network analysis
- **Data Export**: Download filtered data and summary statistics

## How to Use

1. Return to the main page by clicking "ORCID Affiliation Analysis Dashboard" in the sidebar
2. Upload your ORCID affiliation Excel file
3. Use the sidebar filters to analyze specific subsets of data
4. View different visualizations in the tabs
5. Export data or statistics as needed

## Data Format

The Excel file should contain the following columns:
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

## Privacy & Security

- All data processing is done in your browser
- No data is stored on our servers
- Files are processed in memory and immediately discarded

## Support

For issues or feature requests, please visit the [GitHub repository](https://github.com/adammoore/orcid_affiliation_report_dashboard).
""")

st.sidebar.success("Select a page above.")
