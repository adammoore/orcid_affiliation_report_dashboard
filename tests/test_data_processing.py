import pandas as pd
import pytest
from pathlib import Path
import sys

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

def test_data_structure():
    # Create sample data
    data = {
        'ORCID ID': ['0000-0001-2345-6789'],
        'Given Names': ['John'],
        'Family Name': ['Doe'],
        'Org Affiliation Relation Role': ['EMPLOYMENT'],
        'Org Affiliation Relation Title': ['Professor'],
        'Department': ['Computer Science'],
        'Start Year': [2020],
        'End Year': [2023],
        'Date Created': ['2020-01-01'],
        'Last Modified': ['2023-01-01'],
        'Source': [None],
        'Identifier Type': ['ROR'],
        'Identifier Value': ['https://ror.org/123456789']
    }
    df = pd.DataFrame(data)
    
    # Test data structure
    required_columns = [
        'ORCID ID', 'Given Names', 'Family Name', 
        'Org Affiliation Relation Role', 'Start Year'
    ]
    
    for col in required_columns:
        assert col in df.columns, f"Required column {col} missing from DataFrame"
    
    # Test data types
    assert pd.api.types.is_numeric_dtype(df['Start Year']), "Start Year should be numeric"
    assert pd.api.types.is_numeric_dtype(df['End Year']), "End Year should be numeric"

def test_date_validation():
    # Create sample data with invalid dates
    data = {
        'Start Year': [2020, 1800, 2025],
        'End Year': [2019, None, None]
    }
    df = pd.DataFrame(data)
    
    # Test date range validation
    current_year = pd.Timestamp.now().year
    
    # Start Year should not be in the future
    assert all(year <= current_year for year in df['Start Year'].dropna()), \
        "Start Year should not be in the future"
    
    # End Year should be after Start Year when present
    mask = df['End Year'].notna()
    if any(mask):
        assert all(df.loc[mask, 'End Year'] >= df.loc[mask, 'Start Year']), \
            "End Year should be after or equal to Start Year"

def test_orcid_format():
    # Create sample data with ORCID IDs
    data = {
        'ORCID ID': [
            'https://orcid.org/0000-0001-2345-6789',
            'https://orcid.org/0000-0002-3456-7890'
        ]
    }
    df = pd.DataFrame(data)
    
    # Test ORCID format
    orcid_pattern = r'https://orcid\.org/\d{4}-\d{4}-\d{4}-\d{4}'
    assert all(df['ORCID ID'].str.match(orcid_pattern)), \
        "ORCID IDs should match the expected format"

if __name__ == '__main__':
    pytest.main([__file__])
