import requests
import pandas as pd
from typing import List, Dict, Any, Tuple
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import logging
import json

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
    
    def parse_record(self, record: Dict[Any, Any], orcid_id: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Parse an ORCID record into a standardized format."""
        affiliations = []
        emails = []
        
        try:
            person = record.get("person", {})
            activities = record.get("activities-summary", {})
            
            # Extract basic information
            given_names = person.get("name", {}).get("given-names", {}).get("value", "")
            family_name = person.get("name", {}).get("family-name", {}).get("value", "")
            
            self.logger.debug(f"Processing record for {orcid_id} ({given_names} {family_name})")
            
            # Extract email information
            email_section = person.get("emails", {}).get("email", [])
            for email in email_section:
                if email.get("email") and email.get("visibility") == "public":
                    emails.append(email.get("email"))
            
            self.logger.debug(f"Found {len(emails)} public emails for {orcid_id}")
            
            # Extract affiliations
            employment_section = activities.get("employments", {}).get("employment-summary", [])
            
            for emp in employment_section:
                org = emp.get("organization", {})
                start_date = emp.get("start-date", {})
                end_date = emp.get("end-date", {})
                
                start_year = start_date.get("year", {}).get("value") if start_date else None
                end_year = end_date.get("year", {}).get("value") if end_date else None
                
                affiliation = {
                    "ORCID ID": orcid_id,
                    "Given Names": given_names,
                    "Family Name": family_name,
                    "Org Affiliation Relation Role": "EMPLOYMENT",
                    "Org Affiliation Relation Title": emp.get("role-title", ""),
                    "Department": emp.get("department-name", ""),
                    "Start Year": start_year,
                    "End Year": end_year,
                    "Duration": end_year - start_year if (start_year and end_year) else None,
                    "Date Created": emp.get("created-date", {}).get("value"),
                    "Last Modified": emp.get("last-modified-date", {}).get("value"),
                    "Source": "ORCID API",
                    "Identifier Type": org.get("disambiguated-organization", {}).get("disambiguation-source", ""),
                    "Identifier Value": org.get("disambiguated-organization", {}).get("disambiguated-organization-identifier", ""),
                    "Email Addresses": ", ".join(emails),
                    "Organization Name": org.get("name", "")
                }
                affiliations.append(affiliation)
            
            self.logger.debug(f"Found {len(affiliations)} affiliations for {orcid_id}")
            
        except Exception as e:
            self.logger.error(f"Error parsing record for {orcid_id}: {str(e)}")
            self.search_results['errors'] += 1
            self.search_results['error_details'].append({
                'orcid_id': orcid_id,
                'error': str(e),
                'stage': 'record_parsing'
            })
        
        return affiliations, emails
    
    def search_by_email_domains(self, domains: List[str], max_results: int = 1000) -> Tuple[pd.DataFrame, Dict]:
        """Search ORCID records by email domains and return results as a DataFrame."""
        all_affiliations = []
        self.search_results = {
            'total_found': 0,
            'processed': 0,
            'successful': 0,
            'errors': 0,
            'orcid_ids': [],
            'error_details': []
        }
        
        try:
            query = self.build_email_query(domains)
            self.logger.info(f"Searching for email domains: {', '.join(domains)}")
            
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
            
            # Get total results count
            num_found = root.attrib.get('num-found', '0')
            self.search_results['total_found'] = int(num_found)
            self.logger.info(f"Found {num_found} total records")
            
            # Extract ORCID IDs
            orcid_ids = []
            for result in root.findall('.//common:path', ns):
                orcid_ids.append(result.text)
            
            self.search_results['orcid_ids'] = orcid_ids
            self.logger.info(f"Processing {len(orcid_ids)} ORCID records")
            
            # Now fetch details for each ORCID ID
            for orcid_id in orcid_ids:
                self.search_results['processed'] += 1
                record_url = f"{self.BASE_URL}/{orcid_id}/record"
                
                try:
                    record_response = requests.get(record_url, headers=self.HEADERS)
                    record_response.raise_for_status()
                    
                    record_data = record_response.json()
                    affiliations, emails = self.parse_record(record_data, orcid_id)
                    all_affiliations.extend(affiliations)
                    
                    if affiliations:
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
        
        if all_affiliations:
            df = pd.DataFrame(all_affiliations)
            
            # Convert date columns
            for col in ['Date Created', 'Last Modified']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], unit='ms')
            
            # Ensure all required columns exist
            required_columns = [
                'ORCID ID', 'Given Names', 'Family Name', 'Org Affiliation Relation Role',
                'Start Year', 'End Year', 'Department', 'Source', 'Email Addresses',
                'Organization Name'
            ]
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None
            
            # Calculate Duration
            df['Duration'] = pd.to_numeric(df['End Year'], errors='coerce') - pd.to_numeric(df['Start Year'], errors='coerce')
            
            self.logger.info(f"Successfully created DataFrame with {len(df)} rows")
            return df, self.search_results
        else:
            self.logger.warning("No affiliations found, returning empty DataFrame")
            return pd.DataFrame(columns=[
                'ORCID ID', 'Given Names', 'Family Name', 'Org Affiliation Relation Role',
                'Start Year', 'End Year', 'Duration', 'Department', 'Source', 'Email Addresses',
                'Organization Name'
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
            
            # Calculate Duration for file data if not present
            if 'Duration' not in file_data.columns:
                file_data['Duration'] = pd.to_numeric(file_data['End Year'], errors='coerce') - pd.to_numeric(file_data['Start Year'], errors='coerce')
            
            # Concatenate the dataframes
            merged_df = pd.concat([file_data, api_data], ignore_index=True)
            
            # Remove duplicates based on ORCID ID and other key fields
            original_len = len(merged_df)
            merged_df = merged_df.drop_duplicates(
                subset=['ORCID ID', 'Org Affiliation Relation Role', 'Start Year', 'End Year'],
                keep='first'
            )
            
            self.logger.info(f"Merged data: {len(merged_df)} records (removed {original_len - len(merged_df)} duplicates)")
            return merged_df
            
        except Exception as e:
            self.logger.error(f"Error during data merge: {str(e)}")
            raise
