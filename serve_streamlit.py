from pathlib import Path
import modal

app = modal.App("orcid-affiliation-dashboard")

# Define container dependencies
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "streamlit~=1.41.1",
    "pandas~=2.2.3",
    "plotly~=5.24.1",
    "openpyxl~=3.1.5",
    "fastapi[standard]"
)

# Add the app.py file to the image
app_path = Path(__file__).parent / "app.py"
image = image.add_local_file(app_path, "/root/app.py")

@app.function(
    image=image,
    allow_concurrent_inputs=100,
    gpu=None,
    timeout=600,
)
@modal.web_endpoint(method="GET")
async def run():
    import streamlit.web.bootstrap
    import sys
    
    sys.argv = ["streamlit", "run", "/root/app.py", "--server.address=0.0.0.0", "--server.port=7860", "--server.headless=true"]
    
    streamlit.web.bootstrap.run("/root/app.py", "", [], [])

if __name__ == "__main__":
    app.serve()
