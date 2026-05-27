from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router as recommend_router

app = FastAPI(
    title="Thola RIS Microservice",
    description="Retail Intelligence System API for Thola Mobile",
    version="1.2.0"
)

# STRICT CORS CONFIGURATION
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS", "GET"],
    allow_headers=["*"],
)

app.include_router(recommend_router, prefix="/v1", tags=["Recommendations"])

# Mount static files for the Testing Web Dashboard
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
