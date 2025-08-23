# API Schema for Text-Aware Image Generation Workflow

## Request/Response Models

### POST /api/generate
**Request:**
```json
{
  "prompt": "string"
}
```

**Response:** Server-Sent Events stream (Content-Type: text/event-stream)
The stream starts immediately with `iteration_start` event and continues with workflow progress events. The workflow automatically extracts intended text from the user prompt using AI analysis.

### GET /api/images/{image_id}
**Response:** Binary image data (Content-Type: image/png)

## Workflow Flow

### Success Path (Single Iteration)
1. `iteration_start` (iteration: 1, prompt: original user prompt)
2. **Parallel execution begins:**
   - Text extraction runs in background using CrewAI agent
   - Image generation starts immediately (non-blocking)
3. `text_extraction` (extracted_text, has_intended_text: true) - sent when AI analysis completes
4. `image_generated` (iteration: 1, image_url) - sent when image generation completes
5. `analysis` (iteration: 1, ocr_result, match_status: true, message)
6. `workflow_complete` (success: true)
7. `stream_end`

### Failure Path with Retry Loop
1. `iteration_start` (iteration: 1, prompt: original user prompt)
2. **Parallel execution begins (first iteration only):**
   - Text extraction runs in background using CrewAI agent
   - Image generation starts immediately (non-blocking)
3. `text_extraction` (extracted_text, has_intended_text: true) - sent when AI analysis completes
4. `image_generated` (iteration: 1, image_url) - sent when image generation completes
5. `analysis` (iteration: 1, ocr_result, match_status: false, message explaining OCR mismatch and retry strategy)
6. `iteration_start` (iteration: 2, prompt: adjusted prompt based on OCR feedback)
7. `image_generated` (iteration: 2, image_url) - subsequent iterations only wait for image generation
8. `analysis` (iteration: 2, ocr_result, match_status, message)
9. ... (loop continues until match_status: true or max iterations/timeout)
10. Either:
   - `workflow_complete` (success: true) if match found
   - `workflow_timeout` if max retries reached
11. `stream_end`

### Error Path (No Intended Text Detected)
1. `iteration_start` (iteration: 1, prompt: original user prompt)
2. **Parallel execution begins:**
   - Text extraction runs in background using CrewAI agent
   - Image generation starts immediately (non-blocking)
3. `text_extraction` (extracted_text: null, has_intended_text: false) - AI finds no intended text
4. `workflow_error` (error_message: "No intended text detected in prompt...")
5. `stream_end`

## Server-Sent Events Stream

### Event Types

**text_extraction**
```json
{
  "type": "text_extraction",
  "extracted_text": "Hackathon 2025",
  "has_intended_text": true,
  "timestamp": "2025-01-23T10:30:05Z"
}
```
*Note: This event is sent when the CrewAI agent completes analysis of the user prompt. If no intended text is found, `extracted_text` will be null and `has_intended_text` will be false.*

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

**analysis**
```json
{
  "type": "analysis",
  "iteration": 1,
  "ocr_result": "Hackethon 205",
  "match_status": false,
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
  "error_message": "No intended text detected in prompt. Please include specific text you want to appear in the image.",
  "iteration": 1,
  "timestamp": "2025-01-23T10:31:22Z"
}
```
*Note: This event is sent when the workflow cannot proceed, such as when no intended text is detected in the user prompt, or when technical errors occur.*

**stream_end**
```json
{
  "type": "stream_end",
  "timestamp": "2025-01-23T10:32:46Z"
}
```

## Implementation Notes

### Text Extraction Process
- **Automatic Text Detection**: The workflow uses a CrewAI agent to automatically analyze the user prompt and extract intended text
- **Parallel Execution**: Text extraction and image generation run simultaneously for optimal performance
- **Event Timing**: The `text_extraction` event is sent as soon as the AI analysis completes, which may occur before or after the `image_generated` event
- **No Intended Text**: If the AI agent cannot detect any intended text in the prompt, the workflow stops with a `workflow_error` event

### Iteration Loop Logic
- Maximum 10 iterations per workflow
- 5-minute total timeout
- **Text extraction occurs only on first iteration** - subsequent iterations reuse the extracted text
- Each OCR result triggers an `analysis` event with OCR results, match status, and reasoning
- The analysis event contains strategy for next iteration when match fails (adjusted prompt)
- The `iteration_start` event includes the prompt that will be used for image generation in that iteration
- For iteration 1: uses the original user prompt
- For iterations 2+: uses an adjusted prompt based on OCR feedback from previous iteration
- Loop continues until:
  - OCR text matches intended text (success)
  - Maximum iterations reached (timeout)
  - 5-minute timeout exceeded (timeout)
  - No intended text detected (error)
  - Unrecoverable error occurs (error)

### OCR Matching Rules
- Text comparison is case-insensitive
- Whitespace is normalized (multiple spaces become single space)
- Leading/trailing whitespace is ignored
- Match must be exact after normalization

### Analysis Event Purpose
- Contains OCR results and match status for current iteration
- For failed matches: explains why iteration failed and describes what was detected vs expected
- For failed matches: indicates strategy for next attempt (e.g. "emphasizing correct spelling", "adjusting text size")
- For successful matches: confirms text detection success

### CrewAI Text Extraction
- **AI Agent**: Uses CrewAI framework with specialized text extraction agent
- **Prompt Analysis**: Analyzes user prompts to identify text that should appear in generated images
- **Pattern Recognition**: Detects patterns like quotes, "saying", "with text", "displaying" to extract intended text
- **Smart Extraction**: Distinguishes between descriptive text and literal text that should appear in the image
- **Examples**:
  - Input: `"A poster saying 'SALE 50% OFF'"` → Extracted: `"SALE 50% OFF"`
  - Input: `"A birthday card with 'Happy Birthday' text"` → Extracted: `"Happy Birthday"`
  - Input: `"A beautiful sunset over mountains"` → Extracted: `null` (no intended text)

## Enums

**SSEEventType:** `text_extraction`, `iteration_start`, `image_generated`, `analysis`, `workflow_complete`, `workflow_timeout`, `workflow_error`, `stream_end`