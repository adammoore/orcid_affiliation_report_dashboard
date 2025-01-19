import logging
import sys
from datetime import datetime
import streamlit as st

class StreamlitHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []
    
    def emit(self, record):
        try:
            msg = self.format(record)
            self.logs.append(msg)
            
            # Create or update the log display in Streamlit
            if 'log_container' not in st.session_state:
                st.session_state.log_container = st.empty()
            
            # Display logs in the container
            with st.session_state.log_container:
                st.text_area("Search Logs", "\n".join(self.logs), height=150)
        except Exception:
            self.handleError(record)

def setup_logging():
    logger = logging.getLogger('orcid_dashboard')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Add StreamlitHandler
    st_handler = StreamlitHandler()
    st_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    st_handler.setFormatter(formatter)
    logger.addHandler(st_handler)
    
    # Add file handler
    file_handler = logging.FileHandler('orcid_dashboard.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
