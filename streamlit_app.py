import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import os
import tempfile
from utils.orcid_api import OrcidAPI
from utils.logging_utils import setup_logging

# Set up logging
logger = setup_logger()

[Previous streamlit_app.py content...]

# Update the email domain search section in the data_input_tab:
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
                st.session_state.api_data, search_results = orcid_api.search_by_email_domains(domains, max_results)
                
                # Display search results
                st.subheader("Search Results")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Records Found", search_results['total_found'])
                
                with col2:
                    st.metric("Successfully Processed", search_results['successful'])
                
                with col3:
                    st.metric("Errors", search_results['errors'])
                
                # Show ORCID IDs found
                if search_results['orcid_ids']:
                    with st.expander("View Found ORCID IDs"):
                        st.write("ORCID IDs found:")
                        for orcid_id in search_results['orcid_ids']:
                            st.code(orcid_id)
                
                # Show any errors
                if search_results['error_details']:
                    with st.expander("View Error Details"):
                        st.write("Errors encountered:")
                        for error in search_results['error_details']:
                            st.error(f"Stage: {error['stage']}\nError: {error['error']}")
                
                if not st.session_state.api_data.empty:
                    st.success(f"Found {len(st.session_state.api_data)} affiliation records")
                    
                    # Show sample of the data
                    with st.expander("View Sample Data"):
                        st.dataframe(st.session_state.api_data.head())
                else:
                    st.warning("No affiliation records found in the search results")

[Rest of streamlit_app.py content...]
