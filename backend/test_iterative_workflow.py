#!/usr/bin/env python3

import asyncio
import json

import httpx


async def test_iterative_workflow() -> None:
    """Test the enhanced iterative workflow with intentional mismatch."""
    url = "http://localhost:8000/api/generate"

    # Test with a prompt that will likely not match exactly on first try
    payload = {
        "prompt": "A business card design for john smith ceo",
        "intended_text": "JOHN SMITH CEO",
    }

    print("Testing enhanced iterative workflow...")
    print(f"Request: {json.dumps(payload, indent=2)}")
    print("\nResponse events:")
    print("-" * 70)

    async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout
        async with client.stream("POST", url, json=payload) as response:
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(await response.aread())
                return

            iteration_count = 0
            reasoning_events = 0

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = line[6:]  # Remove "data: " prefix
                    try:
                        event = json.loads(event_data)
                        event_type = event.get("type", "unknown")
                        iteration = event.get("iteration", "N/A")

                        print(f"[Iter {iteration}] Event: {event_type}")

                        if event_type == "iteration_start":
                            iteration_count += 1
                            print(f"  Starting iteration {iteration}")

                        elif event_type == "image_generated":
                            image_url = event.get("image_url", "")
                            print(f"  Image generated: {image_url}")

                        elif event_type == "ocr_complete":
                            ocr_result = event.get("ocr_result", "")
                            match_status = event.get("match_status", False)
                            print(f"  OCR Result: '{ocr_result}'")
                            print(f"  Match Status: {match_status}")

                        elif event_type == "reasoning":
                            reasoning_events += 1
                            reasoning = event.get("reasoning", "")
                            print(f"  Reasoning: {reasoning}")

                        elif event_type == "workflow_complete":
                            success = event.get("success", False)
                            ocr_text = event.get("ocr_text", "")
                            total_iterations = event.get("total_iterations", 0)
                            print(f"  SUCCESS: {success}")
                            print(f"  Final OCR Text: '{ocr_text}'")
                            print(f"  Total Iterations: {total_iterations}")

                        elif event_type == "workflow_timeout":
                            success = event.get("success", False)
                            ocr_text = event.get("ocr_text", "")
                            total_iterations = event.get("total_iterations", 0)
                            print(f"  TIMEOUT: {success}")
                            print(f"  Final OCR Text: '{ocr_text}'")
                            print(f"  Total Iterations: {total_iterations}")

                        elif event_type == "workflow_error":
                            error_msg = event.get("error_message", "")
                            print(f"  ERROR: {error_msg}")

                        elif event_type == "stream_end":
                            print("  Stream ended")

                        print()

                    except json.JSONDecodeError:
                        print(f"Invalid JSON: {event_data}")

            print("Summary:")
            print(f"- Total iterations: {iteration_count}")
            print(f"- Reasoning events: {reasoning_events}")


if __name__ == "__main__":
    asyncio.run(test_iterative_workflow())
