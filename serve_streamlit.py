import modal
from pathlib import Path

app = modal.App("orcid-affiliation-dashboard")

# Define container dependencies
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "streamlit~=1.41.1",
    "pandas~=2.2.3",
    "plotly~=5.24.1",
    "openpyxl~=3.1.5",
    "fastapi[standard]",
    "uvicorn"
)

# Add the app.py file to the image
app_path = Path(__file__).parent / "streamlit_app.py"
image = image.add_local_file(app_path, "/root/streamlit_app.py")

@app.function(
    image=image,
    gpu=None,
    timeout=600,
    keep_warm=1
)
@modal.web_endpoint(method="GET")
async def run():
    import streamlit.web.bootstrap
    import sys
    from pathlib import Path
    
    root_path = Path("/root")
    app_path = root_path / "streamlit_app.py"
    
    if not app_path.exists():
        app_path = Path(__file__).parent / "streamlit_app.py"
    
    sys.argv = ["streamlit", "run", str(app_path), "--server.address=0.0.0.0", "--server.port=7860", "--server.headless=true"]
    streamlit.web.bootstrap.run(str(app_path), "", [], [])

if __name__ == "__main__":
    app.serve()
