import modal
from pathlib import Path

stub = modal.Stub("orcid-affiliation-dashboard")

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "streamlit~=1.41.1",
    "pandas~=2.2.3",
    "plotly~=5.24.1",
    "openpyxl~=3.1.5"
)

@stub.function(
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
    app_path = root_path / "app.py"
    
    if not app_path.exists():
        app_path = Path(__file__).parent / "app.py"
    
    sys.argv = ["streamlit", "run", str(app_path), "--server.address=0.0.0.0", "--server.port=7860", "--server.headless=true"]
    streamlit.web.bootstrap.run(str(app_path), "", [], [])

# Mount the app code into the container
stub.app_path = modal.Mount.from_local_file(
    Path(__file__).parent / "app.py",
    remote_path="/root/app.py"
)

if __name__ == "__main__":
    stub.serve()
