# ORCID Affiliation Dashboard

An interactive dashboard for analyzing ORCID affiliation data.

## Features

- Upload and analyze ORCID affiliation Excel files
- Interactive filters for roles and departments
- Visualizations including:
  - Distribution of roles
  - Top departments
  - Timeline of affiliations
  - Additional metrics and analysis
- Download filtered data as CSV
- Responsive design

## Local Development

1. Clone this repository:
```bash
git clone https://github.com/adammoore/orcid_affiliation_report_dashboard.git
cd orcid_affiliation_report_dashboard
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
pip install -r requirements.txt
```

3. Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

4. Open your web browser and go to http://localhost:8501

## Usage

1. Upload your ORCID affiliation Excel file
2. Use the sidebar filters to analyze specific data
3. View visualizations in different tabs
4. Export filtered data or summary statistics

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

## Deployment

The app is deployed to Streamlit Cloud and can be accessed at:
https://orcid-inst-dashboard.streamlit.app/

## License

MIT License
