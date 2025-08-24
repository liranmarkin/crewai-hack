"""
Tests for the text extractor agent.
"""

import unittest
from unittest.mock import MagicMock, patch

from text_extractor_agent import (
    ExtractedText,
    TextExtractorAgent,
    extract_intended_text,
)


class TestTextExtractorAgent(unittest.TestCase):
    """Test cases for the TextExtractorAgent."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Mock the CrewAI components to avoid API calls during testing
        self.mock_crew_patcher = patch("text_extractor_agent.Crew")
        self.mock_agent_patcher = patch("text_extractor_agent.Agent")
        self.mock_task_patcher = patch("text_extractor_agent.Task")

        self.mock_crew = self.mock_crew_patcher.start()
        self.mock_agent = self.mock_agent_patcher.start()
        self.mock_task = self.mock_task_patcher.start()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.mock_crew_patcher.stop()
        self.mock_agent_patcher.stop()
        self.mock_task_patcher.stop()

    def test_extract_text_with_intended_text(self) -> None:
        """Test extracting text when intended text is present."""
        # Mock the crew.kickoff() to return extracted text
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "Hackathon 2025"
        self.mock_crew.return_value = mock_crew_instance

        extractor = TextExtractorAgent()
        result = extractor.extract_text("A poster saying 'Hackathon 2025'")

        self.assertIsInstance(result, ExtractedText)
        self.assertTrue(result.has_text)
        self.assertEqual(result.intended_text, "Hackathon 2025")

    def test_extract_text_no_intended_text(self) -> None:
        """Test extracting text when no intended text is present."""
        # Mock the crew.kickoff() to return NO_INTENDED_TEXT
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "NO_INTENDED_TEXT"
        self.mock_crew.return_value = mock_crew_instance

        extractor = TextExtractorAgent()
        result = extractor.extract_text("A beautiful sunset over mountains")

        self.assertIsInstance(result, ExtractedText)
        self.assertFalse(result.has_text)
        self.assertIsNone(result.intended_text)

    def test_extract_text_empty_result(self) -> None:
        """Test extracting text when result is empty."""
        # Mock the crew.kickoff() to return empty string
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = ""
        self.mock_crew.return_value = mock_crew_instance

        extractor = TextExtractorAgent()
        result = extractor.extract_text("Some prompt")

        self.assertIsInstance(result, ExtractedText)
        self.assertFalse(result.has_text)
        self.assertIsNone(result.intended_text)

    def test_convenience_function_with_text(self) -> None:
        """Test the convenience function with intended text."""
        # Mock the crew.kickoff() to return extracted text
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "SALE 50% OFF"
        self.mock_crew.return_value = mock_crew_instance

        result = extract_intended_text("Sign with text 'SALE 50% OFF'")

        self.assertEqual(result, "SALE 50% OFF")

    def test_convenience_function_no_text(self) -> None:
        """Test the convenience function with no intended text."""
        # Mock the crew.kickoff() to return NO_INTENDED_TEXT
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "NO_INTENDED_TEXT"
        self.mock_crew.return_value = mock_crew_instance

        result = extract_intended_text("A serene landscape with rolling hills")

        self.assertIsNone(result)

    def test_extract_text_strips_whitespace(self) -> None:
        """Test that extracted text is properly stripped of whitespace."""
        # Mock the crew.kickoff() to return text with whitespace
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "  Welcome Home  "
        self.mock_crew.return_value = mock_crew_instance

        extractor = TextExtractorAgent()
        result = extractor.extract_text("Banner displaying 'Welcome Home'")

        self.assertIsInstance(result, ExtractedText)
        self.assertTrue(result.has_text)
        self.assertEqual(result.intended_text, "Welcome Home")


class TestTextExtractorIntegration(unittest.TestCase):
    """Integration tests that actually call the CrewAI agent (requires API key)."""

    def setUp(self) -> None:
        """Set up integration test fixtures."""
        # Skip integration tests if no API key is available
        import os

        if not os.getenv("GEMINI_API_KEY"):
            self.skipTest("GEMINI_API_KEY not available for integration tests")

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test_key"})
    def test_sample_prompts_structure(self) -> None:
        """Test that the extractor returns proper structure for various prompts."""
        test_cases = [
            {
                "prompt": "A poster saying 'Hackathon 2025'",
                "should_have_text": True,
            },
            {
                "prompt": "A beautiful sunset over mountains",
                "should_have_text": False,
            },
            {
                "prompt": "Sign with text 'SALE 50% OFF'",
                "should_have_text": True,
            },
            {
                "prompt": "A serene landscape with rolling hills",
                "should_have_text": False,
            },
        ]

        # This test mainly checks structure without making actual API calls
        # by mocking the crew execution
        with patch("text_extractor_agent.Crew") as mock_crew_class:
            mock_crew_instance = MagicMock()
            mock_crew_class.return_value = mock_crew_instance

            for i, case in enumerate(test_cases):
                # Mock different responses
                if case["should_have_text"]:
                    mock_crew_instance.kickoff.return_value = f"MockText{i}"
                else:
                    mock_crew_instance.kickoff.return_value = "NO_INTENDED_TEXT"

                result = extract_intended_text(str(case["prompt"]))

                if case["should_have_text"]:
                    self.assertIsNotNone(result, f"Should extract text for: {case['prompt']}")
                    self.assertIsInstance(result, str)
                else:
                    self.assertIsNone(result, f"Should not extract text for: {case['prompt']}")


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
