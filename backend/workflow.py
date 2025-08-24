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
from ocr_matcher_agent import compare_ocr_with_intended_text
from text_extractor_agent import extract_intended_text

# Legacy functions removed - now using LLM-based OCR matching and prompt adjustment


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

                                # Always end with stream_end event even on error
                                end_event = {
                                    "type": SSEEventType.STREAM_END,
                                    "timestamp": datetime.utcnow().isoformat() + "Z",
                                }
                                yield f"data: {json.dumps(end_event)}\n\n"
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

            # Check if OCR result matches intended text using LLM-based intelligent matching
            # intended_text should not be None at this point due to earlier checks
            assert intended_text is not None, "intended_text should not be None at this point"

            # Use LLM-based OCR matching instead of simple string comparison
            match_result = compare_ocr_with_intended_text(ocr_result, intended_text, current_prompt)
            match_status = match_result.match_status
            message = match_result.message

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
                # Use LLM-suggested prompt adjustment instead of rule-based adjustment
                current_prompt = match_result.suggested_prompt

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
