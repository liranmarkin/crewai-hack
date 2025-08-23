import json
from collections.abc import AsyncGenerator
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from image_generation import get_image_generator
from models import GenerateRequest, SSEEventType

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
        generate_workflow_events(workflow_id, request.prompt, request.intended_text),
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


async def generate_workflow_events(
    workflow_id: str, prompt: str, intended_text: str
) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events for workflow progress."""

    # Start with iteration_start event
    event = {
        "type": SSEEventType.ITERATION_START,
        "iteration": 1,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    yield f"data: {json.dumps(event)}\n\n"

    try:
        # Generate the image
        generator = get_image_generator()
        image_id, image_path = await generator.generate_image(prompt, intended_text)

        # Send image generated event
        event = {
            "type": SSEEventType.IMAGE_GENERATED,
            "iteration": 1,
            "image_url": f"/api/images/{image_id}.png",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        yield f"data: {json.dumps(event)}\n\n"

        # Send OCR complete event (mock for now)
        event = {
            "type": SSEEventType.OCR_COMPLETE,
            "iteration": 1,
            "ocr_result": intended_text,  # For now, assume perfect match
            "match_status": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        yield f"data: {json.dumps(event)}\n\n"

        # Send workflow complete event
        event = {
            "type": SSEEventType.WORKFLOW_COMPLETE,
            "success": True,
            "final_image_url": f"/api/images/{image_id}.png",
            "ocr_text": intended_text,
            "total_iterations": 1,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        yield f"data: {json.dumps(event)}\n\n"

    except Exception as e:
        # Send error event
        event = {
            "type": SSEEventType.WORKFLOW_ERROR,
            "error_message": str(e),
            "iteration": 1,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        yield f"data: {json.dumps(event)}\n\n"

    # Always end with stream_end event
    event = {
        "type": SSEEventType.STREAM_END,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    yield f"data: {json.dumps(event)}\n\n"
