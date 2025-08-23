from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from image_generation import get_image_generator
from models import GenerateRequest
from workflow import generate_workflow_events

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


@app.post("/api/generate")
async def generate_workflow(request: GenerateRequest) -> StreamingResponse:
    """Start a new text-aware image generation workflow and stream progress."""
    workflow_id = str(uuid4())

    return StreamingResponse(
        generate_workflow_events(workflow_id, request.prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/images/{image_id}")
async def get_image(image_id: str) -> Response:
    """Get generated image by ID."""
    # Remove .png extension if present
    if image_id.endswith(".png"):
        image_id = image_id[:-4]

    # Get image path
    generator = get_image_generator()
    image_path = generator.get_image_path(image_id)

    if not image_path:
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image_path, media_type="image/png")
