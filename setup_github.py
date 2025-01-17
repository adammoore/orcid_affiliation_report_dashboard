import keyring
import requests
import subprocess
import sys

def setup_github_repo():
    # Get GitHub token from keyring
    token = keyring.get_password("github", "pat")
    
    if not token:
        print("Please enter your GitHub Personal Access Token (PAT):")
        token = input().strip()
        keyring.set_password("github", "pat", token)
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Create repository
    repo_data = {
        'name': 'orcid_affiliation_report_dashboard',
        'description': 'Interactive dashboard for analyzing ORCID affiliation data',
        'private': False,
        'has_issues': True,
        'has_projects': True,
        'has_wiki': True
    }
    
    response = requests.post(
        'https://api.github.com/user/repos',
        headers=headers,
        json=repo_data
    )
    
    if response.status_code == 201:
        print("Repository created successfully!")
        repo_info = response.json()
        print(f"\nRepository is now available at: {repo_info['html_url']}")
    else:
        print(f"Error creating repository: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    setup_github_repo()
