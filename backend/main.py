from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Text-Aware Image Generation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Text-Aware Image Generation API"}


@app.get("/test")
def test_endpoint() -> dict[str, str | dict[str, str | bool]]:
    return {
        "status": "success",
        "message": "Test endpoint working!",
        "data": {
            "project": "Text-Aware Image Generation",
            "backend": "FastAPI",
            "ready": True,
        },
    }
