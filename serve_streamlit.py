import sys
from pathlib import Path
import modal
import subprocess

def run_streamlit():
    import streamlit.web.bootstrap
    from streamlit.web.bootstrap import run
    
    filename = "/root/app.py"
    command_line = f"streamlit run {filename} --server.address=0.0.0.0 --server.port=7860 --server.headless=true"
    
    sys.argv = command_line.split(" ")
    run(sys.argv, "", "", [])

# Create a Modal app
app = modal.App()

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
    keep_warm=1,
    allow_concurrent_inputs=3,
    timeout=600,
)
@modal.asgi_app()
def fastapi_app():
    import streamlit.web.bootstrap
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    import uvicorn
    
    web_app = FastAPI()
    
    @web_app.get("/")
    async def root():
        # Start Streamlit in a separate process
        process = subprocess.Popen(
            ["streamlit", "run", "/root/app.py", 
             "--server.address=0.0.0.0", 
             "--server.port=8501",
             "--server.headless=true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Return an HTML page that embeds the Streamlit app
        return HTMLResponse(content="""
        <html>
            <head>
                <title>ORCID Affiliation Dashboard</title>
                <style>
                    body, html { margin: 0; padding: 0; height: 100%; }
                    iframe { width: 100%; height: 100%; border: none; }
                </style>
            </head>
            <body>
                <iframe src="http://localhost:8501"></iframe>
            </body>
        </html>
        """)
    
    return web_app

if __name__ == "__main__":
    modal.runner.deploy_stub(app)
