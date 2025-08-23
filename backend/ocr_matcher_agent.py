"""
OCR Matcher Agent using CrewAI.
Compares OCR results with intended text using LLM-based intelligent matching.
"""

import os
from pathlib import Path

from crewai import Agent, Crew, Task
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class OCRMatchResult(BaseModel):
    """Model for OCR matching result."""

    match_status: bool
    message: str
    suggested_prompt_adjustment: str


class OCRMatcherAgent:
    """Agent for intelligent OCR result comparison with intended text."""

    def __init__(self, api_key: str | None = None):
        """Initialize the OCR matcher agent.

        Args:
            api_key: Optional API key for the LLM. If not provided,
                    uses environment variable.
        """
        # Set up API key for the LLM (defaults to OpenAI)
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        # Load the agent backstory from file
        prompt_file = Path(__file__).parent / "prompts" / "ocr_matcher_prompt.txt"
        with open(prompt_file, encoding="utf-8") as f:
            backstory = f.read().strip()

        # Create the OCR matching agent
        self.agent = Agent(
            role="OCR Text Matcher",
            goal=(
                "Intelligently compare OCR results with intended text, "
                "being strict about typos but lenient about formatting differences"
            ),
            backstory=backstory,
            verbose=False,
            allow_delegation=False,
            max_iter=1,
        )

    def compare_texts(self, ocr_result: str, intended_text: str, current_prompt: str) -> OCRMatchResult:
        """Compare OCR result with intended text using intelligent matching.

        Args:
            ocr_result: Text extracted from the generated image via OCR
            intended_text: The text that should have appeared in the image
            current_prompt: The current image generation prompt being used

        Returns:
            OCRMatchResult with match status, reasoning message, and prompt suggestion
        """
        # Load the task description template from file
        task_prompt_file = Path(__file__).parent / "prompts" / "ocr_matcher_task_prompt.txt"
        with open(task_prompt_file, encoding="utf-8") as f:
            task_template = f.read().strip()

        # Create a task for OCR comparison
        task = Task(
            description=task_template.format(
                ocr_result=ocr_result, intended_text=intended_text, current_prompt=current_prompt
            ),
            expected_output="JSON with match_status (true/false), message (reasoning), and suggested_prompt_adjustment",
            agent=self.agent,
        )

        # Create crew with single agent and task
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=False,
        )

        # Execute the task
        result = crew.kickoff()

        # Parse the result - expect JSON format
        try:
            import json

            result_str = str(result).strip()

            # Handle case where result might be wrapped in markdown code blocks
            if result_str.startswith("```json"):
                result_str = result_str.split("```json")[1].split("```")[0].strip()
            elif result_str.startswith("```"):
                result_str = result_str.split("```")[1].split("```")[0].strip()

            parsed_result = json.loads(result_str)

            return OCRMatchResult(
                match_status=parsed_result.get("match_status", False),
                message=parsed_result.get("message", "No reasoning provided"),
                suggested_prompt_adjustment=parsed_result.get("suggested_prompt_adjustment", current_prompt),
            )

        except (json.JSONDecodeError, KeyError, AttributeError):
            # Fallback parsing if JSON fails
            result_str = str(result).strip().lower()

            # Simple keyword-based fallback
            match_status = "true" in result_str or "match" in result_str

            return OCRMatchResult(
                match_status=match_status,
                message=f"Parsing error, fallback analysis: {str(result)[:200]}",
                suggested_prompt_adjustment=current_prompt,
            )


def compare_ocr_with_intended_text(
    ocr_result: str, intended_text: str, current_prompt: str, api_key: str | None = None
) -> OCRMatchResult:
    """Convenience function to compare OCR result with intended text.

    Args:
        ocr_result: Text extracted from the generated image via OCR
        intended_text: The text that should have appeared in the image
        current_prompt: The current image generation prompt being used
        api_key: Optional API key for the LLM

    Returns:
        OCRMatchResult with match status, reasoning, and prompt suggestion
    """
    matcher = OCRMatcherAgent(api_key=api_key)
    return matcher.compare_texts(ocr_result, intended_text, current_prompt)
