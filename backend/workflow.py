"""
Text-aware image generation workflow implementation.
Contains the main business logic for iterative image generation with OCR verification.
"""

import json
from collections.abc import AsyncGenerator
from datetime import datetime

from image_generation import get_image_generator
from models import SSEEventType
from ocr import extract_text_from_image


def generate_reasoning(ocr_result: str, intended_text: str, iteration: int) -> str:
    """Generate reasoning for why OCR didn't match and what to improve."""
    cleaned_ocr = " ".join(ocr_result.split()).upper()
    cleaned_intended = " ".join(intended_text.split()).upper()

    if not ocr_result.strip():
        return f"No text detected. Need clearer text saying '{intended_text}'."

    if len(cleaned_ocr) < len(cleaned_intended):
        return f"OCR: '{ocr_result}' vs '{intended_text}'. Partial. Need complete."

    if len(cleaned_ocr) > len(cleaned_intended):
        return f"OCR: '{ocr_result}' vs '{intended_text}'. Too much. Need cleaner."

    # Find character differences
    differences = []
    for i, (actual, expected) in enumerate(
        zip(cleaned_ocr, cleaned_intended, strict=False)
    ):
        if actual != expected:
            differences.append(f"position {i+1}: got '{actual}' need '{expected}'")

    if differences:
        diff_summary = ", ".join(differences[:3])  # Show first 3 differences
        return f"OCR: '{ocr_result}' vs '{intended_text}'. Diff: {diff_summary}."

    return f"OCR: '{ocr_result}' vs '{intended_text}'. Need better clarity."


def adjust_prompt_for_retry(
    original_prompt: str, intended_text: str, ocr_result: str, iteration: int
) -> str:
    """Adjust the prompt for the next iteration based on OCR feedback."""
    base_improvements = [
        "with clear, bold, readable text",
        "with high contrast text that is easy to read",
        "with simple, clean typography",
        "ensuring the text is the main focus",
    ]

    specific_improvements = []

    if not ocr_result.strip():
        specific_improvements.extend(
            [
                "with very large, prominent text",
                "with text that stands out clearly against the background",
                "with bold, high-visibility lettering",
            ]
        )
    elif len(ocr_result.split()) < len(intended_text.split()):
        specific_improvements.extend(
            [
                "with complete, uncut text",
                "ensuring all words fit within the image boundaries",
                "with text that is not cropped or partially hidden",
            ]
        )
    elif len(ocr_result.split()) > len(intended_text.split()):
        specific_improvements.extend(
            [
                "with minimal, clean text layout",
                "focusing only on the essential text",
                "with simplified design to avoid text confusion",
            ]
        )
    else:
        specific_improvements.extend(
            [
                "with perfect spelling and clear letterforms",
                "with anti-aliased, crisp text rendering",
                "with optimal font choice for readability",
            ]
        )

    # Add iteration-specific improvements
    if iteration >= 2:
        specific_improvements.append("with extra attention to text accuracy")
    if iteration >= 3:
        specific_improvements.append("with maximum text clarity and contrast")
    if iteration >= 4:
        specific_improvements.append(
            "prioritizing perfect text rendering above all else"
        )

    # Combine improvements
    improvements = base_improvements + specific_improvements
    improvement_text = ", ".join(improvements[:3])  # Limit to avoid overly long prompts

    return f"{original_prompt}, {improvement_text}. Text: '{intended_text}'."


async def generate_workflow_events(
    workflow_id: str, prompt: str, intended_text: str
) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events for workflow progress."""

    max_iterations = 5
    current_prompt = prompt
    final_image_url = None
    final_ocr_text = ""
    success = False

    try:
        generator = get_image_generator()

        for iteration in range(1, max_iterations + 1):
            # Start iteration event
            event = {
                "type": SSEEventType.ITERATION_START,
                "iteration": iteration,
                "prompt": current_prompt,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            yield f"data: {json.dumps(event)}\n\n"

            # Generate the image
            image_id, image_path = await generator.generate_image(current_prompt)

            # Send image generated event
            event = {
                "type": SSEEventType.IMAGE_GENERATED,
                "iteration": iteration,
                "image_url": f"/api/images/{image_id}.png",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            yield f"data: {json.dumps(event)}\n\n"

            # Perform OCR on the generated image
            ocr_result = extract_text_from_image(image_path)

            # Check if OCR result matches intended text
            # Clean up whitespace and normalize for comparison
            cleaned_ocr = " ".join(ocr_result.split()).upper()
            cleaned_intended = " ".join(intended_text.split()).upper()
            match_status = cleaned_ocr == cleaned_intended

            # Send OCR complete event
            event = {
                "type": SSEEventType.OCR_COMPLETE,
                "iteration": iteration,
                "ocr_result": ocr_result,
                "match_status": match_status,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            yield f"data: {json.dumps(event)}\n\n"

            # Store results for final response
            final_image_url = f"/api/images/{image_id}.png"
            final_ocr_text = ocr_result

            if match_status:
                # Perfect match found!
                success = True
                break
            elif iteration < max_iterations:
                # Send reasoning event immediately after OCR mismatch
                reasoning = generate_reasoning(ocr_result, intended_text, iteration)
                event = {
                    "type": SSEEventType.REASONING,
                    "iteration": iteration,
                    "reasoning": reasoning,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
                yield f"data: {json.dumps(event)}\n\n"

                # Adjust prompt for next iteration
                current_prompt = adjust_prompt_for_retry(
                    prompt, intended_text, ocr_result, iteration
                )

        # Send final workflow result
        if success:
            event = {
                "type": SSEEventType.WORKFLOW_COMPLETE,
                "success": True,
                "final_image_url": final_image_url,
                "ocr_text": final_ocr_text,
                "total_iterations": iteration,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        else:
            event = {
                "type": SSEEventType.WORKFLOW_TIMEOUT,
                "success": False,
                "final_image_url": final_image_url,
                "ocr_text": final_ocr_text,
                "total_iterations": max_iterations,
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
