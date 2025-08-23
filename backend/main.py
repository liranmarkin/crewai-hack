from collections.abc import AsyncGenerator
from datetime import datetime
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from image_generation import get_image_generator
from models import (
    GenerateRequest,
    GenerateResponse,
    SSEEventType,
    WorkflowStatus,
)

app = FastAPI(title="Text-Aware Image Generation API")

# Store workflow data in memory (for hackathon demo)
workflows: dict[str, dict] = {}

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
async def generate_workflow(
    request: GenerateRequest, background_tasks: BackgroundTasks
) -> GenerateResponse:
    """Start a new text-aware image generation workflow."""
    workflow_id = str(uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"

    # Store workflow data
    workflows[workflow_id] = {
        "prompt": request.prompt,
        "intended_text": request.intended_text,
        "status": WorkflowStatus.PROCESSING,
        "created_at": created_at,
        "images": [],
        "iterations": 0,
    }

    # Start image generation in background
    background_tasks.add_task(
        process_workflow, workflow_id, request.prompt, request.intended_text
    )

    return GenerateResponse(
        workflow_id=workflow_id,
        status=WorkflowStatus.PROCESSING,
        created_at=created_at,
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


async def generate_sse_events(workflow_id: str) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events for workflow progress."""
    # Mock SSE stream
    events = [
        {
            "type": SSEEventType.ITERATION_START,
            "iteration": 1,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        {
            "type": SSEEventType.IMAGE_GENERATED,
            "iteration": 1,
            "image_url": f"/api/images/{uuid4()}.png",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        {
            "type": SSEEventType.OCR_COMPLETE,
            "iteration": 1,
            "ocr_result": "Hackethon 205",
            "match_status": False,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        {
            "type": SSEEventType.REASONING,
            "iteration": 1,
            "message": (
                "OCR detected 'Hackethon 205' but expected 'Hackathon 2025'. "
                "Retrying with emphasis on correct spelling..."
            ),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        {
            "type": SSEEventType.WORKFLOW_COMPLETE,
            "success": True,
            "final_image_url": f"/api/images/{uuid4()}.png",
            "ocr_text": "Hackathon 2025",
            "total_iterations": 2,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        {
            "type": SSEEventType.STREAM_END,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    ]

    import json

    for event in events:
        # SSE format: data: {json}\n\n
        yield f"data: {json.dumps(event)}\n\n"


async def process_workflow(workflow_id: str, prompt: str, intended_text: str) -> None:
    """Background task to process image generation workflow."""
    try:
        # Generate the image
        generator = get_image_generator()
        image_id, image_path = await generator.generate_image(prompt, intended_text)

        # Update workflow with generated image
        if workflow_id in workflows:
            workflows[workflow_id]["images"].append(image_id)
            workflows[workflow_id]["iterations"] += 1
            workflows[workflow_id]["status"] = WorkflowStatus.SUCCESS
            workflows[workflow_id]["final_image_id"] = image_id

    except Exception as e:
        # Update workflow status on error
        if workflow_id in workflows:
            workflows[workflow_id]["status"] = WorkflowStatus.FAILED
            workflows[workflow_id]["error"] = str(e)


@app.get("/api/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str) -> dict:
    """Get workflow status."""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflows[workflow_id]


@app.get("/api/workflow/{workflow_id}/stream")
async def stream_workflow_progress(workflow_id: str) -> StreamingResponse:
    """Stream workflow progress updates via Server-Sent Events."""
    return StreamingResponse(
        generate_sse_events(workflow_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
