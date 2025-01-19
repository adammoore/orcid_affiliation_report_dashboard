import requests
import pandas as pd
from typing import List, Dict, Any, Tuple
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import logging

class OrcidAPI:
    BASE_URL = "https://pub.orcid.org/v3.0"
    HEADERS = {
        "Accept": "application/vnd.orcid+json"
    }
    
    def __init__(self):
        self.logger = logging.getLogger('orcid_dashboard')
        self.search_results = {
            'total_found': 0,
            'processed': 0,
            'successful': 0,
            'errors': 0,
            'orcid_ids': [],
            'error_details': []
        }
    
    @staticmethod
    def build_email_query(domains: List[str]) -> str:
        """Build a query string for email domains."""
        domain_queries = [f"email:*@{domain}" for domain in domains]
        return " OR ".join(domain_queries)
    
    def parse_record(self, record: Dict[Any, Any], orcid_id: str, search_domain: str) -> Dict[str, Any]:
        """Parse an ORCID record into a standardized format."""
        try:
            person = record.get("person", {})
            
            # Extract basic information
            given_names = person.get("name", {}).get("given-names", {}).get("value", "")
            family_name = person.get("name", {}).get("family-name", {}).get("value", "")
            
            self.logger.debug(f"Processing record for {orcid_id} ({given_names} {family_name})")
            
            # Extract email information
            emails = []
            matching_emails = []
            email_section = person.get("emails", {}).get("email", [])
            for email in email_section:
                if email.get("email") and email.get("visibility") == "public":
                    email_value = email.get("email")
                    emails.append(email_value)
                    if email_value.lower().endswith(f"@{search_domain.lower()}"):
                        matching_emails.append(email_value)
            
            self.logger.debug(f"Found {len(emails)} public emails for {orcid_id}, {len(matching_emails)} matching search domain")
            
            # Create base record
            record_data = {
                "ORCID ID": orcid_id,
                "Given Names": given_names,
                "Family Name": family_name,
                "Org Affiliation Relation Role": "EMAIL_DOMAIN",
                "Org Affiliation Relation Title": f"Email domain: {search_domain}",
                "Department": None,
                "Start Year": None,
                "End Year": None,
                "Duration": None,
                "Date Created": None,
                "Last Modified": None,
                "Source": "ORCID API - Email Domain",
                "Identifier Type": "EMAIL_DOMAIN",
                "Identifier Value": search_domain,
                "Email Addresses": ", ".join(matching_emails),
                "Organization Name": search_domain,
                "All Email Addresses": ", ".join(emails)
            }
            
            return record_data
            
        except Exception as e:
            self.logger.error(f"Error parsing record for {orcid_id}: {str(e)}")
            self.search_results['errors'] += 1
            self.search_results['error_details'].append({
                'orcid_id': orcid_id,
                'error': str(e),
                'stage': 'record_parsing'
            })
            return None
    
    def search_by_email_domains(self, domains: List[str], max_results: int = 1000) -> Tuple[pd.DataFrame, Dict]:
        """Search ORCID records by email domains and return results as a DataFrame."""
        all_records = []
        self.search_results = {
            'total_found': 0,
            'processed': 0,
            'successful': 0,
            'errors': 0,
            'orcid_ids': [],
            'error_details': [],
            'domains': domains
        }
        
        try:
            for domain in domains:
                self.logger.info(f"Searching for email domain: {domain}")
                query = f"email:*@{domain}"
                
                # First, get all ORCID IDs matching the email domain
                url = f"{self.BASE_URL}/search"
                params = {
                    "q": query,
                    "rows": max_results
                }
                
                self.logger.debug(f"Search URL: {url}?q={query}")
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(response.content)
                ns = {'search': 'http://www.orcid.org/ns/search',
                      'common': 'http://www.orcid.org/ns/common'}
                
                # Get total results count for this domain
                domain_total = int(root.attrib.get('num-found', '0'))
                self.search_results['total_found'] += domain_total
                self.logger.info(f"Found {domain_total} records for domain {domain}")
                
                # Extract ORCID IDs
                orcid_ids = []
                for result in root.findall('.//common:path', ns):
                    orcid_ids.append(result.text)
                
                self.search_results['orcid_ids'].extend(orcid_ids)
                self.logger.info(f"Processing {len(orcid_ids)} ORCID records for domain {domain}")
                
                # Now fetch details for each ORCID ID
                for orcid_id in orcid_ids:
                    self.search_results['processed'] += 1
                    record_url = f"{self.BASE_URL}/{orcid_id}/record"
                    
                    try:
                        record_response = requests.get(record_url, headers=self.HEADERS)
                        record_response.raise_for_status()
                        
                        record_data = record_response.json()
                        parsed_record = self.parse_record(record_data, orcid_id, domain)
                        
                        if parsed_record:
                            all_records.append(parsed_record)
                            self.search_results['successful'] += 1
                            self.logger.debug(f"Successfully processed record for {orcid_id}")
                        
                    except Exception as e:
                        self.logger.error(f"Error processing record {orcid_id}: {str(e)}")
                        self.search_results['errors'] += 1
                        self.search_results['error_details'].append({
                            'orcid_id': orcid_id,
                            'error': str(e),
                            'stage': 'record_fetching'
                        })
                    
                    # Rate limiting
                    time.sleep(0.1)
        
        except Exception as e:
            self.logger.error(f"Error in search operation: {str(e)}")
            self.search_results['error_details'].append({
                'error': str(e),
                'stage': 'search'
            })
        
        if all_records:
            df = pd.DataFrame(all_records)
            self.logger.info(f"Successfully created DataFrame with {len(df)} records")
            return df, self.search_results
        else:
            self.logger.warning("No records found, returning empty DataFrame")
            return pd.DataFrame(columns=[
                'ORCID ID', 'Given Names', 'Family Name', 'Org Affiliation Relation Role',
                'Start Year', 'End Year', 'Duration', 'Department', 'Source', 'Email Addresses',
                'Organization Name', 'All Email Addresses'
            ]), self.search_results

    def merge_with_existing_data(self, api_data: pd.DataFrame, file_data: pd.DataFrame) -> pd.DataFrame:
        """Merge API data with existing file data."""
        self.logger.info("Starting data merge")
        
        if api_data.empty:
            self.logger.info("No API data to merge, using file data only")
            if 'Duration' not in file_data.columns:
                file_data['Duration'] = pd.to_numeric(file_data['End Year'], errors='coerce') - pd.to_numeric(file_data['Start Year'], errors='coerce')
            return file_data
        
        if file_data.empty:
            self.logger.info("No file data to merge, using API data only")
            return api_data
        
        try:
            # Add source column to file data if it doesn't exist
            if 'Source' not in file_data.columns:
                file_data['Source'] = 'File Upload'
            
            # Add email addresses column to file data if it doesn't exist
            if 'Email Addresses' not in file_data.columns:
                file_data['Email Addresses'] = None
            
            # Add all email addresses column to file data if it doesn't exist
            if 'All Email Addresses' not in file_data.columns:
                file_data['All Email Addresses'] = None
            
            # Calculate Duration for file data if not present
            if 'Duration' not in file_data.columns:
                file_data['Duration'] = pd.to_numeric(file_data['End Year'], errors='coerce') - pd.to_numeric(file_data['Start Year'], errors='coerce')
            
            # Concatenate the dataframes
            merged_df = pd.concat([file_data, api_data], ignore_index=True)
            
            # Remove duplicates based on ORCID ID and other key fields
            original_len = len(merged_df)
            merged_df = merged_df.drop_duplicates(
                subset=['ORCID ID', 'Org Affiliation Relation Role', 'Start Year', 'End Year', 'Email Addresses'],
                keep='first'
            )
            
            self.logger.info(f"Merged data: {len(merged_df)} records (removed {original_len - len(merged_df)} duplicates)")
            return merged_df
            
        except Exception as e:
            self.logger.error(f"Error during data merge: {str(e)}")
            raise
