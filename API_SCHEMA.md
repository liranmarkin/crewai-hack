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

## Workflow Flow

### Success Path (Single Iteration)
1. `iteration_start` (iteration: 1, prompt: original user prompt)
2. `image_generated` (iteration: 1, image_url)
3. `ocr_complete` (iteration: 1, ocr_result, match_status: true)
4. `workflow_complete` (success: true)
5. `stream_end`

### Failure Path with Retry Loop
1. `iteration_start` (iteration: 1, prompt: original user prompt)
2. `image_generated` (iteration: 1, image_url)
3. `ocr_complete` (iteration: 1, ocr_result, match_status: false)
4. `reasoning` (iteration: 1, message explaining OCR mismatch and retry strategy)
5. `iteration_start` (iteration: 2, prompt: adjusted prompt based on OCR feedback)
6. `image_generated` (iteration: 2, image_url)
7. `ocr_complete` (iteration: 2, ocr_result, match_status)
8. ... (loop continues until match_status: true or max iterations/timeout)
9. Either:
   - `workflow_complete` (success: true) if match found
   - `workflow_timeout` if max retries reached
10. `stream_end`

## Server-Sent Events Stream

### Event Types

**iteration_start**
```json
{
  "type": "iteration_start",
  "iteration": 1,
  "prompt": "A poster for Hackathon, with clear, bold, readable text. Text: 'Hackathon 2025'.",
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

## Implementation Notes

### Iteration Loop Logic
- Maximum 8 iterations per workflow
- 5-minute total timeout
- Each failed OCR result triggers a `reasoning` event explaining why it failed
- The reasoning event contains strategy for next iteration (adjusted prompt)
- The `iteration_start` event includes the prompt that will be used for image generation in that iteration
- For iteration 1: uses the original user prompt
- For iterations 2+: uses an adjusted prompt based on OCR feedback from previous iteration
- Loop continues until:
  - OCR text matches intended text (success)
  - Maximum iterations reached (timeout)
  - 5-minute timeout exceeded (timeout)
  - Unrecoverable error occurs (error)

### OCR Matching Rules
- Text comparison is case-insensitive
- Whitespace is normalized (multiple spaces become single space)
- Leading/trailing whitespace is ignored
- Match must be exact after normalization

### Reasoning Event Purpose
- Explains why current iteration failed
- Describes what was detected vs what was expected
- Indicates strategy for next attempt (e.g. "emphasizing correct spelling", "adjusting text size")

## Enums

**SSEEventType:** `iteration_start`, `image_generated`, `ocr_complete`, `reasoning`, `workflow_complete`, `workflow_timeout`, `workflow_error`, `stream_end`