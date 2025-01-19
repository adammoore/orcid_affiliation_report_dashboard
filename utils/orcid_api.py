import requests
import pandas as pd
from typing import List, Dict, Any
import time
from datetime import datetime

class OrcidAPI:
    BASE_URL = "https://pub.orcid.org/v3.0"
    HEADERS = {
        "Accept": "application/json"
    }
    
    @staticmethod
    def build_email_query(domains: List[str]) -> str:
        """Build a query string for email domains."""
        domain_queries = [f"email:*@{domain}" for domain in domains]
        return " OR ".join(domain_queries)
    
    @staticmethod
    def parse_record(record: Dict[Any, Any]) -> Dict[str, Any]:
        """Parse an ORCID record into a standardized format."""
        try:
            person = record.get("person", {})
            activities = record.get("activities-summary", {})
            
            # Extract basic information
            orcid = record.get("orcid-identifier", {}).get("path", "")
            given_names = person.get("name", {}).get("given-names", {}).get("value", "")
            family_name = person.get("name", {}).get("family-name", {}).get("value", "")
            
            # Extract email information
            emails = []
            email_section = person.get("emails", {}).get("email", [])
            for email in email_section:
                if email.get("email") and email.get("visibility") == "public":
                    emails.append(email.get("email"))
            
            # Extract affiliations
            affiliations = []
            employment_section = activities.get("employments", {}).get("employment-summary", [])
            
            for emp in employment_section:
                org = emp.get("organization", {})
                start_date = emp.get("start-date", {})
                end_date = emp.get("end-date", {})
                
                affiliation = {
                    "ORCID ID": orcid,
                    "Given Names": given_names,
                    "Family Name": family_name,
                    "Org Affiliation Relation Role": "EMPLOYMENT",
                    "Org Affiliation Relation Title": emp.get("role-title", ""),
                    "Department": emp.get("department-name", ""),
                    "Start Year": start_date.get("year", {}).get("value") if start_date else None,
                    "End Year": end_date.get("year", {}).get("value") if end_date else None,
                    "Date Created": emp.get("created-date", {}).get("value"),
                    "Last Modified": emp.get("last-modified-date", {}).get("value"),
                    "Source": "ORCID API",
                    "Identifier Type": org.get("disambiguated-organization", {}).get("disambiguation-source", ""),
                    "Identifier Value": org.get("disambiguated-organization", {}).get("disambiguated-organization-identifier", ""),
                    "Email Addresses": ", ".join(emails)
                }
                affiliations.append(affiliation)
            
            return {"affiliations": affiliations, "emails": emails}
        
        except Exception as e:
            print(f"Error parsing record: {e}")
            return {"affiliations": [], "emails": []}
    
    def search_by_email_domains(self, domains: List[str], max_results: int = 1000) -> pd.DataFrame:
        """Search ORCID records by email domains and return results as a DataFrame."""
        all_affiliations = []
        rows_processed = 0
        
        try:
            query = self.build_email_query(domains)
            
            while rows_processed < max_results:
                url = f"{self.BASE_URL}/expanded-search/"
                params = {
                    "q": query,
                    "start": rows_processed,
                    "rows": min(200, max_results - rows_processed)  # ORCID API limit is 200 per request
                }
                
                response = requests.get(url, headers=self.HEADERS, params=params)
                response.raise_for_status()
                
                data = response.json()
                total_results = data.get("num-found", 0)
                
                if total_results == 0:
                    break
                
                for result in data.get("expanded-result", []):
                    orcid = result.get("orcid-id")
                    if orcid:
                        record_url = f"{self.BASE_URL}/{orcid}/record"
                        record_response = requests.get(record_url, headers=self.HEADERS)
                        
                        if record_response.status_code == 200:
                            record_data = record_response.json()
                            parsed_data = self.parse_record(record_data)
                            all_affiliations.extend(parsed_data["affiliations"])
                        
                        # Rate limiting - be nice to the API
                        time.sleep(0.1)
                
                rows_processed += len(data.get("expanded-result", []))
                
                if rows_processed >= total_results:
                    break
        
        except Exception as e:
            print(f"Error searching ORCID records: {e}")
        
        if all_affiliations:
            df = pd.DataFrame(all_affiliations)
            # Convert date columns
            for col in ['Date Created', 'Last Modified']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], unit='ms')
            return df
        else:
            return pd.DataFrame()

    def merge_with_existing_data(self, api_data: pd.DataFrame, file_data: pd.DataFrame) -> pd.DataFrame:
        """Merge API data with existing file data."""
        if api_data.empty:
            return file_data
        if file_data.empty:
            return api_data
        
        # Add source column to file data if it doesn't exist
        if 'Source' not in file_data.columns:
            file_data['Source'] = 'File Upload'
        
        # Add email addresses column to file data if it doesn't exist
        if 'Email Addresses' not in file_data.columns:
            file_data['Email Addresses'] = None
        
        # Concatenate the dataframes
        merged_df = pd.concat([file_data, api_data], ignore_index=True)
        
        # Remove duplicates based on ORCID ID and other key fields
        merged_df = merged_df.drop_duplicates(
            subset=['ORCID ID', 'Org Affiliation Relation Role', 'Start Year', 'End Year'],
            keep='first'
        )
        
        return merged_df
