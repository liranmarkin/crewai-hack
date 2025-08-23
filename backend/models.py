from enum import Enum

from pydantic import BaseModel


# Enums
class WorkflowStatus(str, Enum):
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class SSEEventType(str, Enum):
    ITERATION_START = "iteration_start"
    IMAGE_GENERATED = "image_generated"
    OCR_COMPLETE = "ocr_complete"
    REASONING = "reasoning"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_TIMEOUT = "workflow_timeout"
    WORKFLOW_ERROR = "workflow_error"
    STREAM_END = "stream_end"


# Request/Response Models
class GenerateRequest(BaseModel):
    prompt: str
    intended_text: str


class GenerateResponse(BaseModel):
    workflow_id: str
    status: WorkflowStatus
    created_at: str
