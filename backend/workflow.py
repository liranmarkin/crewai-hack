"""
Text-aware image generation workflow implementation.
Contains the main business logic for iterative image generation with OCR verification.
"""

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from image_generation import get_image_generator
from models import SSEEventType
from ocr import extract_text_from_image
from text_extractor_agent import extract_intended_text


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
    for i, (actual, expected) in enumerate(zip(cleaned_ocr, cleaned_intended, strict=False)):
        if actual != expected:
            differences.append(f"position {i+1}: got '{actual}' need '{expected}'")

    if differences:
        diff_summary = ", ".join(differences[:3])  # Show first 3 differences
        return f"OCR: '{ocr_result}' vs '{intended_text}'. Diff: {diff_summary}."

    return f"OCR: '{ocr_result}' vs '{intended_text}'. Need better clarity."


def adjust_prompt_for_retry(original_prompt: str, intended_text: str, ocr_result: str, iteration: int) -> str:
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
        specific_improvements.append("prioritizing perfect text rendering above all else")

    # Combine improvements
    improvements = base_improvements + specific_improvements
    improvement_text = ", ".join(improvements[:3])  # Limit to avoid overly long prompts

    return f"{original_prompt}, {improvement_text}. Text: '{intended_text}'."


async def generate_workflow_events(workflow_id: str, prompt: str) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events for workflow progress."""
    # mypy: disable-error-code=dict-item

    max_iterations = 10
    current_prompt = prompt
    final_image_url = None
    final_ocr_text = ""
    success = False

    try:
        # Start text extraction in parallel (non-blocking)
        loop = asyncio.get_event_loop()
        text_extraction_task = loop.run_in_executor(None, extract_intended_text, prompt)

        # Start image generator initialization immediately
        generator = get_image_generator()
        intended_text = None  # Will be set when text extraction completes

        for iteration in range(1, max_iterations + 1):
            # Start iteration event
            event = {
                "type": SSEEventType.ITERATION_START,
                "iteration": iteration,  # type: ignore[dict-item]
                "prompt": current_prompt,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            yield f"data: {json.dumps(event)}\n\n"

            # Start both tasks in parallel (only on first iteration for text extraction)
            if iteration == 1:
                # Start text extraction task (runs in background)
                async def send_text_extraction_event() -> tuple[dict[str, Any], str | None]:
                    extracted_text = await text_extraction_task
                    event = {
                        "type": SSEEventType.TEXT_EXTRACTION,
                        "extracted_text": extracted_text,
                        "has_intended_text": extracted_text is not None,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    }
                    return event, extracted_text

                text_event_task = asyncio.create_task(send_text_extraction_event())

            # Start image generation task (runs in background)
            async def send_image_generated_event(prompt: str, iter_num: int) -> tuple[dict[str, Any], str, str]:
                image_id, image_path = await generator.generate_image(prompt)
                event = {
                    "type": SSEEventType.IMAGE_GENERATED,
                    "iteration": iter_num,  # type: ignore[dict-item]
                    "image_url": f"/api/images/{image_id}.png",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
                return event, image_id, image_path

            image_event_task = asyncio.create_task(send_image_generated_event(current_prompt, iteration))

            # Wait for both tasks to complete and send events as they finish
            if iteration == 1:
                # On first iteration, we need both text extraction and image generation
                pending = {text_event_task, image_event_task}
                image_data: tuple[str, str] | None = None
                text_data: str | None = None

                while pending:
                    done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                    for task in done:
                        if task == text_event_task:
                            text_result = await task  # type: ignore[misc]
                            event, extracted_text = text_result  # type: ignore[assignment]
                            yield f"data: {json.dumps(event)}\n\n"
                            text_data = extracted_text  # type: ignore[assignment]

                            # If no intended text was detected, we can't proceed
                            if extracted_text is None:
                                error_event = {
                                    "type": SSEEventType.WORKFLOW_ERROR,
                                    "error_message": (
                                        "No intended text detected in prompt. "
                                        "Please include specific text you want to appear in the "
                                        "image."
                                    ),
                                    "iteration": iteration,  # type: ignore[dict-item]
                                    "timestamp": datetime.utcnow().isoformat() + "Z",
                                }
                                yield f"data: {json.dumps(error_event)}\n\n"
                                return

                        elif task == image_event_task:
                            image_result = await task  # type: ignore[misc]
                            event, image_id, image_path = image_result  # type: ignore[assignment]
                            yield f"data: {json.dumps(event)}\n\n"
                            image_data = (image_id, image_path)  # type: ignore[assignment]

                # Both tasks completed, use the results
                assert image_data is not None, "image_data should not be None"
                assert text_data is not None, "text_data should not be None"
                image_id, image_path = image_data
                intended_text = text_data
            else:
                # On subsequent iterations, only wait for image generation
                event, image_id, image_path = await image_event_task
                yield f"data: {json.dumps(event)}\n\n"

            # Perform OCR on the generated image
            ocr_result = extract_text_from_image(image_path)

            # Check if OCR result matches intended text
            # intended_text should not be None at this point due to earlier checks
            assert intended_text is not None, "intended_text should not be None at this point"

            # Clean up whitespace and normalize for comparison
            cleaned_ocr = " ".join(ocr_result.split()).upper()
            cleaned_intended = " ".join(intended_text.split()).upper()
            match_status = cleaned_ocr == cleaned_intended

            # Generate reasoning message
            if match_status:
                message = f"OCR detected '{ocr_result}' which matches expected " f"'{intended_text}'. Success!"
            else:
                message = generate_reasoning(ocr_result, intended_text, iteration)

            # Send combined analysis event
            event = {
                "type": SSEEventType.ANALYSIS,
                "iteration": iteration,  # type: ignore[dict-item]
                "ocr_result": ocr_result,
                "match_status": match_status,
                "message": message,
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
                # Adjust prompt for next iteration
                current_prompt = adjust_prompt_for_retry(prompt, intended_text, ocr_result, iteration)

        # Send final workflow result
        if success:
            event = {
                "type": SSEEventType.WORKFLOW_COMPLETE,
                "success": True,
                "final_image_url": final_image_url,
                "ocr_text": final_ocr_text,
                "total_iterations": iteration,  # type: ignore[dict-item]
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        else:
            event = {
                "type": SSEEventType.WORKFLOW_TIMEOUT,
                "success": False,
                "final_image_url": final_image_url,
                "ocr_text": final_ocr_text,
                "total_iterations": max_iterations,  # type: ignore[dict-item]
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        yield f"data: {json.dumps(event)}\n\n"

    except Exception as e:
        # Send error event
        event = {
            "type": SSEEventType.WORKFLOW_ERROR,
            "error_message": str(e),
            "iteration": 1,  # type: ignore[dict-item]
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        yield f"data: {json.dumps(event)}\n\n"

    # Always end with stream_end event
    event = {
        "type": SSEEventType.STREAM_END,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    yield f"data: {json.dumps(event)}\n\n"
