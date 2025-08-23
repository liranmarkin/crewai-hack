# API Schema for Text-Aware Image Generation Workflow

## Request/Response Models

### POST /api/generate
**Request:**
```json
{
  "prompt": "string",
  "intended_text": "string"
}
```

**Response:** Server-Sent Events stream (Content-Type: text/event-stream)
The stream starts immediately with `iteration_start` event and continues with workflow progress events.

### GET /api/images/{image_id}
**Response:** Binary image data (Content-Type: image/png)

## Server-Sent Events Stream

### Event Types

**iteration_start**
```json
{
  "type": "iteration_start",
  "iteration": 1,
  "timestamp": "2025-01-23T10:30:01Z"
}
```

**image_generated**
```json
{
  "type": "image_generated",
  "iteration": 1,
  "image_url": "/api/images/abc123.png",
  "timestamp": "2025-01-23T10:30:15Z"
}
```

**ocr_complete**
```json
{
  "type": "ocr_complete",
  "iteration": 1,
  "ocr_result": "Hackethon 205",
  "match_status": false,
  "timestamp": "2025-01-23T10:30:18Z"
}
```

**reasoning**
```json
{
  "type": "reasoning",
  "iteration": 1,
  "message": "OCR detected 'Hackethon 205' but expected 'Hackathon 2025'. Retrying with emphasis on correct spelling...",
  "timestamp": "2025-01-23T10:30:19Z"
}
```

**workflow_complete**
```json
{
  "type": "workflow_complete",
  "success": true,
  "final_image_url": "/api/images/final123.png",
  "ocr_text": "Hackathon 2025",
  "total_iterations": 3,
  "timestamp": "2025-01-23T10:32:45Z"
}
```

**workflow_timeout**
```json
{
  "type": "workflow_timeout",
  "total_iterations": 8,
  "last_image_url": "/api/images/last456.png",
  "timestamp": "2025-01-23T10:35:00Z"
}
```

**workflow_error**
```json
{
  "type": "workflow_error",
  "error_message": "Image generation service unavailable",
  "iteration": 3,
  "timestamp": "2025-01-23T10:31:22Z"
}
```

**stream_end**
```json
{
  "type": "stream_end",
  "timestamp": "2025-01-23T10:32:46Z"
}
```

## Enums

**SSEEventType:** `iteration_start`, `image_generated`, `ocr_complete`, `reasoning`, `workflow_complete`, `workflow_timeout`, `workflow_error`, `stream_end`