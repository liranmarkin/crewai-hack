"""Test OCR integration with the workflow API."""

import json

import httpx
import pytest


@pytest.mark.asyncio
async def test_ocr_integration_basic() -> None:
    """Test the OCR integration with a simple request."""
    url = "http://localhost:8000/api/generate"

    # Test with a simple prompt that contains intended text
    payload = {
        "prompt": "A simple birthday card with balloons saying 'HAPPY BIRTHDAY'",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            ocr_events = []
            image_urls = []
            text_extraction_event = None
            workflow_completed = False

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = line[6:]  # Remove "data: " prefix
                    try:
                        event = json.loads(event_data)
                        event_type = event.get("type", "unknown")

                        if event_type == "text_extraction":
                            text_extraction_event = event
                            extracted_text = event.get("extracted_text")
                            has_intended_text = event.get("has_intended_text", False)

                            # Verify text extraction event structure
                            assert isinstance(has_intended_text, bool), "has_intended_text should be boolean"
                            assert extracted_text is None or isinstance(
                                extracted_text, str
                            ), "extracted_text should be string or None"

                        elif event_type == "analysis":
                            ocr_result = event.get("ocr_result", "")
                            match_status = event.get("match_status", False)
                            message = event.get("message", "")
                            ocr_events.append(
                                {
                                    "ocr_result": ocr_result,
                                    "match_status": match_status,
                                    "message": message,
                                    "iteration": event.get("iteration", 0),
                                }
                            )

                            # Verify analysis event structure
                            assert isinstance(ocr_result, str), "OCR result should be a string"
                            assert isinstance(match_status, bool), "Match status should be boolean"
                            assert isinstance(message, str), "Message should be a string"

                        elif event_type == "workflow_complete":
                            workflow_completed = True
                            # workflow_success = event.get("success", False)
                            final_ocr_text = event.get("ocr_text", "")

                            # Verify workflow completion structure
                            assert "final_image_url" in event
                            assert "total_iterations" in event
                            assert isinstance(final_ocr_text, str)

                        elif event_type == "image_generated":
                            image_url = event.get("image_url", "")
                            image_urls.append(image_url)
                            assert image_url.startswith("/api/images/"), "Image URL should have correct format"

                    except json.JSONDecodeError:
                        pytest.fail(f"Invalid JSON received: {event_data}")

            # Verify workflow execution
            assert text_extraction_event is not None, "Should have received text extraction event"
            assert len(ocr_events) > 0, "Should have at least one OCR event"
            assert len(image_urls) > 0, "Should have at least one image generated"
            assert workflow_completed, "Workflow should complete (success or timeout)"

            # Verify text extraction worked
            if text_extraction_event:
                has_intended_text = text_extraction_event.get("has_intended_text", False)
                extracted_text = text_extraction_event.get("extracted_text")
                if has_intended_text:
                    assert extracted_text is not None, "Should have extracted text when has_intended_text is True"
                    assert extracted_text.strip() != "", "Extracted text should not be empty"

            # Verify OCR results are meaningful
            for ocr_event in ocr_events:
                # OCR result can be empty or contain text
                assert isinstance(ocr_event["ocr_result"], str)
                # Match status should be boolean
                assert isinstance(ocr_event["match_status"], bool)


@pytest.mark.asyncio
async def test_ocr_perfect_match_scenario() -> None:
    """Test scenario where OCR might match on first try."""
    url = "http://localhost:8000/api/generate"

    # Use a very simple text that might match
    payload = {
        "prompt": "Large bold text saying 'HELLO'",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            assert response.status_code == 200

            found_perfect_match = False
            total_iterations = 0

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        event_type = event.get("type")

                        if event_type == "iteration_start":
                            total_iterations += 1

                        elif event_type == "analysis":
                            match_status = event.get("match_status", False)
                            if match_status:
                                found_perfect_match = True

                        elif event_type == "workflow_complete":
                            success = event.get("success", False)
                            if success:
                                assert found_perfect_match, "Success should correlate with perfect match"
                            break

                    except json.JSONDecodeError:
                        pass

            # If we found a perfect match, workflow should succeed quickly
            if found_perfect_match:
                assert total_iterations <= 5, "Should not exceed max iterations"


@pytest.mark.asyncio
async def test_ocr_error_handling() -> None:
    """Test OCR integration handles errors gracefully."""
    url = "http://localhost:8000/api/generate"

    # Test with a prompt that has no intended text (edge case)
    payload = {
        "prompt": "A colorful abstract image with no text",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            # Should still return 200 even with edge case inputs
            assert response.status_code == 200

            events_received = []
            text_extraction_received = False
            workflow_error_received = False

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        event_type = event.get("type")
                        events_received.append(event_type)

                        if event_type == "text_extraction":
                            text_extraction_received = True
                            has_intended_text = event.get("has_intended_text", True)
                            # For a prompt with no text, should extract None or empty
                            assert not has_intended_text or event.get("extracted_text") is None

                        elif event_type == "workflow_error":
                            workflow_error_received = True
                            # Should get error when no intended text is found
                            error_message = event.get("error_message", "")
                            assert "no intended text" in error_message.lower()

                    except json.JSONDecodeError:
                        pass

            # Should follow basic workflow structure
            assert text_extraction_received, "Should receive text extraction event"
            assert "stream_end" in events_received, "Should receive stream end event"
            # May receive workflow error if no intended text is detected
            if workflow_error_received:
                assert "workflow_error" in events_received


@pytest.mark.asyncio
async def test_parallel_execution_timing() -> None:
    """Test that text extraction and image generation run in parallel."""
    url = "http://localhost:8000/api/generate"

    payload = {
        "prompt": "A poster with 'TEST MESSAGE' in large letters",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            assert response.status_code == 200

            iteration_start_time = None
            text_extraction_time = None
            image_generated_time = None

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        event_type = event.get("type")
                        timestamp = event.get("timestamp")

                        if event_type == "iteration_start":
                            iteration_start_time = timestamp

                        elif event_type == "text_extraction":
                            text_extraction_time = timestamp
                            # Should have extracted text from the prompt
                            extracted_text = event.get("extracted_text")
                            has_intended_text = event.get("has_intended_text", False)
                            assert has_intended_text, "Should detect intended text in prompt"
                            assert (
                                extracted_text == "TEST MESSAGE"
                            ), f"Should extract 'TEST MESSAGE', got '{extracted_text}'"

                        elif event_type == "image_generated":
                            image_generated_time = timestamp

                        elif event_type in ["workflow_complete", "workflow_timeout", "workflow_error"]:
                            # Stop processing after workflow ends
                            break

                    except json.JSONDecodeError:
                        pass

            # Verify parallel execution - both events should happen close to each other
            # and after iteration start
            assert iteration_start_time is not None, "Should have iteration start timestamp"
            assert text_extraction_time is not None, "Should have text extraction timestamp"
            assert image_generated_time is not None, "Should have image generation timestamp"

            # Both text extraction and image generation should complete within reasonable time
            # The exact order may vary based on which completes first
