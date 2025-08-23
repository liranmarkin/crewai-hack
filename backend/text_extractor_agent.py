"""
Text Extractor Agent using CrewAI.
Extracts intended text from user prompts for the text-aware image generation workflow.
"""

import os
from pathlib import Path

from crewai import Agent, Crew, Task
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class ExtractedText(BaseModel):
    """Model for extracted text result."""

    intended_text: str | None = None
    has_text: bool = False


class TextExtractorAgent:
    """Agent for extracting intended text from user prompts."""

    def __init__(self, api_key: str | None = None):
        """Initialize the text extractor agent.

        Args:
            api_key: Optional API key for the LLM. If not provided,
                    uses environment variable.
        """
        # Set up API key for the LLM (defaults to OpenAI)
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        # Load the agent backstory from file
        prompt_file = Path(__file__).parent / "prompts" / "text_extractor_prompt.txt"
        with open(prompt_file, encoding="utf-8") as f:
            backstory = f.read().strip()

        # Create the text extraction agent
        self.agent = Agent(
            role="Text Extractor",
            goal="Extract the exact text that should appear in the generated " "image from the user's prompt",
            backstory=backstory,
            verbose=False,
            allow_delegation=False,
            max_iter=1,
        )

    def extract_text(self, prompt: str) -> ExtractedText:
        """Extract intended text from a user prompt.

        Args:
            prompt: The user's image generation prompt

        Returns:
            ExtractedText object with the extracted text or None if no text found
        """
        # Load the task description template from file
        task_prompt_file = Path(__file__).parent / "prompts" / "text_extractor_task_prompt.txt"
        with open(task_prompt_file, encoding="utf-8") as f:
            task_template = f.read().strip()

        # Create a task for text extraction
        task = Task(
            description=task_template.format(prompt=prompt),
            expected_output="The exact text to appear in the image, or " "NO_INTENDED_TEXT if none",
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

        # Parse the result
        extracted = str(result).strip()

        if extracted == "NO_INTENDED_TEXT" or not extracted:
            return ExtractedText(intended_text=None, has_text=False)

        return ExtractedText(intended_text=extracted, has_text=True)


def extract_intended_text(prompt: str, api_key: str | None = None) -> str | None:
    """Convenience function to extract intended text from a prompt.

    Args:
        prompt: The user's image generation prompt
        api_key: Optional API key for the LLM

    Returns:
        The extracted text or None if no text found
    """
    extractor = TextExtractorAgent(api_key=api_key)
    result = extractor.extract_text(prompt)
    return result.intended_text if result.has_text else None


if __name__ == "__main__":
    # Test the extractor with sample prompts
    test_prompts = [
        "A poster for a hackathon saying 'Hackathon 2025'",
        "Create a sign with text 'SALE 50% OFF'",
        "A beautiful sunset over mountains",
        "Meme with 'This is fine' text at the bottom",
        "Banner displaying 'Welcome to the Conference'",
        "An advertisement poster that says 'Buy One Get One Free'",
        "A serene landscape with rolling hills",
        "Generate an image with the words 'Happy New Year 2025'",
        "Street sign saying 'One Way'",
        "A cat sitting on a couch",
    ]

    print("Testing Text Extractor Agent\n" + "=" * 50)

    for prompt in test_prompts:
        print(f"\nPrompt: {prompt}")
        result = extract_intended_text(prompt)
        if result:
            print(f"Extracted Text: '{result}'")
        else:
            print("No intended text found")
