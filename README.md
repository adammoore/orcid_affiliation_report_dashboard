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

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/orcid_affiliation_report_dashboard.git
cd orcid_affiliation_report_dashboard
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and go to http://localhost:8501

3. Upload your ORCID affiliation Excel file

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

You can deploy this dashboard to various platforms:

### Streamlit Cloud (Recommended)
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy directly from your GitHub repository

### Modal
You can also deploy to Modal using the provided `serve_streamlit.py` script.

## License

MIT License
