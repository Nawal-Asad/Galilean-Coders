"""
Unified SPHEREx application entrypoint.

Combines the FastAPI backend (for /api/* endpoints and /docs) with the
Flask frontend (for the 3D landing page and /explorer) under a single
ASGI application running on one host and port.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware

from backend.main import app as fastapi_app
from frontend.app import app as flask_app
from spherex.config import CORS_ORIGINS, HOST, PORT

# Create the top-level unified ASGI application
app = FastAPI(
    title="SPHEREx Sky Explorer (Unified)",
    description="Unified SPHEREx mission landing page, Data Explorer, and scientific comparison API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Enable CORS for external API clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api")
@app.get("/api/health")
def api_status():
    """API health and status check."""
    return {
        "message": "SPHEREx Sky Explorer backend API is running",
        "status": "ok",
        "unified": True,
    }


# Include all FastAPI routes (such as /api/compare, /api/candidates, /api/cutout)
for route in fastapi_app.routes:
    # Skip FastAPI's root '/' route so the Flask landing page serves '/'
    if getattr(route, "path", None) != "/":
        app.routes.append(route)

# Mount the Flask WSGI application to handle '/', '/explorer', and frontend assets
app.mount("/", WSGIMiddleware(flask_app))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("unified_app:app", host=HOST, port=PORT, reload=False)
