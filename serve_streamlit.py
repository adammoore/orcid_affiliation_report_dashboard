from pathlib import Path
import modal

def create_app():
    web_app = modal.Stub("orcid-affiliation-dashboard")

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

    @web_app.function(
        image=image,
        allow_concurrent_inputs=100,
        timeout=600,
    )
    @modal.web_endpoint()
    async def run():
        import streamlit.web.bootstrap
        import sys
        
        sys.argv = ["streamlit", "run", "/root/app.py", "--server.address=0.0.0.0", "--server.port=7860", "--server.headless=true"]
        
        streamlit.web.bootstrap.run("/root/app.py", "", [], [])

    return web_app

app = create_app()

if __name__ == "__main__":
    app.serve()
