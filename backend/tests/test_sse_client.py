#!/usr/bin/env python3
"""
Simple test client for the /api/generate SSE endpoint.
Listens to events, logs them, and saves the final image.
"""

import json
from pathlib import Path

import requests


def test_generate_endpoint() -> None:
    """Test the /api/generate SSE endpoint."""
    url = "http://localhost:8000/api/generate"
    payload = {
        "prompt": "A birthday poster with balloons and 'HAPPY BIRTHDAY' text",
    }

    print(f"🚀 Sending request to {url}")
    print(f"📝 Payload: {json.dumps(payload, indent=2)}")
    print("=" * 50)

    try:
        # Make the POST request with streaming enabled
        response = requests.post(
            url,
            json=payload,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=60,
        )

        response.raise_for_status()
        print(f"✅ Connected! Status: {response.status_code}")
        print("🎧 Listening for SSE events...\n")

        final_image_url = None

        # Process the SSE stream
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                # Extract JSON data
                json_data = line[6:]  # Remove "data: " prefix

                # Skip empty lines
                if not json_data.strip():
                    continue

                try:
                    event = json.loads(json_data)
                    event_type = event.get("type")
                    timestamp = event.get("timestamp")

                    print(f"📡 [{timestamp}] {event_type.upper()}")

                    # Log specific event details
                    if event_type == "text_extraction":
                        extracted_text = event.get("extracted_text")
                        has_intended_text = event.get("has_intended_text")
                        print(f"   Extracted intended text: '{extracted_text}'")
                        print(f"   Has intended text: {has_intended_text}")

                    elif event_type == "iteration_start":
                        iteration = event.get("iteration")
                        print(f"   Starting iteration {iteration}")

                    elif event_type == "image_generated":
                        image_url = event.get("image_url")
                        iteration = event.get("iteration")
                        print(f"   Image generated for iteration {iteration}: {image_url}")

                    elif event_type == "analysis":
                        ocr_result = event.get("ocr_result")
                        match_status = event.get("match_status")
                        message = event.get("message")
                        iteration = event.get("iteration")
                        print(f"   Analysis for iteration {iteration}:")
                        print(f"   OCR result: '{ocr_result}' (match: {match_status})")
                        print(f"   Message: {message}")

                    elif event_type == "workflow_complete":
                        success = event.get("success")
                        final_image_url = event.get("final_image_url")
                        ocr_text = event.get("ocr_text")
                        total_iterations = event.get("total_iterations")
                        print(f"   Workflow completed! Success: {success}")
                        print(f"   Final OCR text: '{ocr_text}'")
                        print(f"   Total iterations: {total_iterations}")
                        print(f"   Final image URL: {final_image_url}")

                    elif event_type == "workflow_timeout":
                        total_iterations = event.get("total_iterations")
                        last_image_url = event.get("last_image_url")
                        print(f"   Workflow timed out after {total_iterations} iterations")
                        print(f"   Last image URL: {last_image_url}")
                        final_image_url = last_image_url

                    elif event_type == "workflow_error":
                        error_message = event.get("error_message")
                        iteration = event.get("iteration")
                        print(f"   Error in iteration {iteration}: {error_message}")

                    elif event_type == "stream_end":
                        print("   Stream ended")

                    print()  # Empty line for readability

                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    print(f"   Raw data: {json_data}")

        # Save the final image if we got one
        if final_image_url:
            save_image(final_image_url)
        else:
            print("⚠️  No final image URL received")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def save_image(image_url: str) -> None:
    """Download and save the final image."""
    print(f"💾 Downloading final image from: {image_url}")

    try:
        # Extract image filename from URL
        filename = image_url.split("/")[-1]
        if not filename.endswith(".png"):
            filename += ".png"

        # Create downloads directory
        downloads_dir = Path("test_downloads")
        downloads_dir.mkdir(exist_ok=True)

        # Full path for the image
        image_path = downloads_dir / filename

        # Download the image
        image_response = requests.get(f"http://localhost:8000{image_url}", timeout=30)
        image_response.raise_for_status()

        # Save to file
        with open(image_path, "wb") as f:
            f.write(image_response.content)

        print(f"✅ Image saved to: {image_path}")
        print(f"📊 Image size: {len(image_response.content)} bytes")

    except Exception as e:
        print(f"❌ Failed to save image: {e}")
