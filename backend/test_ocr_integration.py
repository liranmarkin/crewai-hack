#!/usr/bin/env python3

import asyncio
import json

import httpx


async def test_ocr_integration() -> None:
    """Test the OCR integration with a simple request."""
    url = "http://localhost:8000/api/generate"

    # Test with a simple prompt that might generate readable text
    payload = {
        "prompt": "A simple birthday card with balloons",
        "intended_text": "HAPPY BIRTHDAY",
    }

    print("Testing OCR integration...")
    print(f"Request: {json.dumps(payload, indent=2)}")
    print("\nResponse events:")
    print("-" * 50)

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(await response.aread())
                return

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = line[6:]  # Remove "data: " prefix
                    try:
                        event = json.loads(event_data)
                        event_type = event.get("type", "unknown")

                        print(f"Event: {event_type}")

                        if event_type == "ocr_complete":
                            ocr_result = event.get("ocr_result", "")
                            match_status = event.get("match_status", False)
                            print(f"  OCR Result: '{ocr_result}'")
                            print(f"  Match Status: {match_status}")
                        elif event_type == "workflow_complete":
                            success = event.get("success", False)
                            ocr_text = event.get("ocr_text", "")
                            print(f"  Success: {success}")
                            print(f"  Final OCR Text: '{ocr_text}'")
                        elif event_type == "image_generated":
                            image_url = event.get("image_url", "")
                            print(f"  Image URL: {image_url}")
                        elif event_type == "workflow_error":
                            error_msg = event.get("error_message", "")
                            print(f"  Error: {error_msg}")

                        print()

                    except json.JSONDecodeError:
                        print(f"Invalid JSON: {event_data}")


if __name__ == "__main__":
    asyncio.run(test_ocr_integration())
