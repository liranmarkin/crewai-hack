from enum import Enum

from pydantic import BaseModel


# Enums
class SSEEventType(str, Enum):
    TEXT_EXTRACTION = "text_extraction"
    ITERATION_START = "iteration_start"
    IMAGE_GENERATED = "image_generated"
    ANALYSIS = "analysis"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_TIMEOUT = "workflow_timeout"
    WORKFLOW_ERROR = "workflow_error"
    STREAM_END = "stream_end"


# Request Models
class GenerateRequest(BaseModel):
    prompt: str
