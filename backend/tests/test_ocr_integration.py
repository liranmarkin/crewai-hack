"""Test OCR integration with the workflow API."""

import json

import httpx
import pytest


@pytest.mark.asyncio
async def test_ocr_integration_basic() -> None:
    """Test the OCR integration with a simple request."""
    url = "http://localhost:8000/api/generate"

    # Test with a simple prompt that might generate readable text
    payload = {
        "prompt": "A simple birthday card with balloons",
        "intended_text": "HAPPY BIRTHDAY",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}"

            ocr_events = []
            image_urls = []
            workflow_completed = False

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = line[6:]  # Remove "data: " prefix
                    try:
                        event = json.loads(event_data)
                        event_type = event.get("type", "unknown")

                        if event_type == "ocr_complete":
                            ocr_result = event.get("ocr_result", "")
                            match_status = event.get("match_status", False)
                            ocr_events.append(
                                {
                                    "ocr_result": ocr_result,
                                    "match_status": match_status,
                                    "iteration": event.get("iteration", 0),
                                }
                            )

                            # Verify OCR event structure
                            assert isinstance(
                                ocr_result, str
                            ), "OCR result should be a string"
                            assert isinstance(
                                match_status, bool
                            ), "Match status should be boolean"

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
                            assert image_url.startswith(
                                "/api/images/"
                            ), "Image URL should have correct format"

                    except json.JSONDecodeError:
                        pytest.fail(f"Invalid JSON received: {event_data}")

            # Verify workflow execution
            assert len(ocr_events) > 0, "Should have at least one OCR event"
            assert len(image_urls) > 0, "Should have at least one image generated"
            assert workflow_completed, "Workflow should complete (success or timeout)"

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
        "intended_text": "HELLO",
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

                        elif event_type == "ocr_complete":
                            match_status = event.get("match_status", False)
                            if match_status:
                                found_perfect_match = True

                        elif event_type == "workflow_complete":
                            success = event.get("success", False)
                            if success:
                                assert (
                                    found_perfect_match
                                ), "Success should correlate with perfect match"
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

    # Test with empty intended text (edge case)
    payload = {
        "prompt": "A colorful abstract image",
        "intended_text": "",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            # Should still return 200 even with edge case inputs
            assert response.status_code == 200

            events_received = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        events_received.append(event.get("type"))
                    except json.JSONDecodeError:
                        pass

            # Should still follow basic workflow structure
            assert "iteration_start" in events_received
            assert "stream_end" in events_received
