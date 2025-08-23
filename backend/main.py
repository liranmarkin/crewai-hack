from collections.abc import AsyncGenerator
from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from models import (
    GenerateRequest,
    GenerateResponse,
    SSEEventType,
    WorkflowStatus,
)

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
def generate_workflow(request: GenerateRequest) -> GenerateResponse:
    """Start a new text-aware image generation workflow."""
    # Mock response
    return GenerateResponse(
        workflow_id=str(uuid4()),
        status=WorkflowStatus.PROCESSING,
        created_at=datetime.utcnow().isoformat() + "Z",
    )


@app.get("/api/images/{image_id}")
def get_image(image_id: str) -> Response:
    """Get generated image by ID."""
    # Mock response - return a 1x1 transparent PNG
    mock_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00"
        b"\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\r"
        b"IDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x00\x00\x00\x00"
        b"IEND\xaeB`\x82"
    )
    return Response(content=mock_png, media_type="image/png")


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


@app.get("/api/workflow/{workflow_id}/stream")
def stream_workflow_progress(workflow_id: str) -> StreamingResponse:
    """Stream workflow progress updates via Server-Sent Events."""
    return StreamingResponse(
        generate_sse_events(workflow_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
