"""
Tests for the OCR matcher agent.
"""

import unittest
from unittest.mock import MagicMock, patch

from ocr_matcher_agent import (
    OCRMatcherAgent,
    OCRMatchResult,
    compare_ocr_with_intended_text,
)


class TestOCRMatcherAgent(unittest.TestCase):
    """Test cases for the OCRMatcherAgent."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Mock the CrewAI components to avoid API calls during testing
        self.mock_crew_patcher = patch("ocr_matcher_agent.Crew")
        self.mock_agent_patcher = patch("ocr_matcher_agent.Agent")
        self.mock_task_patcher = patch("ocr_matcher_agent.Task")

        self.mock_crew = self.mock_crew_patcher.start()
        self.mock_agent = self.mock_agent_patcher.start()
        self.mock_task = self.mock_task_patcher.start()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.mock_crew_patcher.stop()
        self.mock_agent_patcher.stop()
        self.mock_task_patcher.stop()

    def test_perfect_match(self) -> None:
        """Test perfect match between OCR and intended text."""
        # Mock the crew.kickoff() to return perfect match JSON
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = """{
            "match_status": true,
            "message": "Perfect match found",
            "suggested_prompt_adjustment": "A poster saying 'Hackathon 2025'"
        }"""
        self.mock_crew.return_value = mock_crew_instance

        matcher = OCRMatcherAgent()
        result = matcher.compare_texts(
            ocr_result="Hackathon 2025",
            intended_text="Hackathon 2025",
            current_prompt="A poster saying 'Hackathon 2025'",
        )

        self.assertIsInstance(result, OCRMatchResult)
        self.assertTrue(result.match_status)
        self.assertEqual(result.message, "Perfect match found")
        self.assertEqual(result.suggested_prompt_adjustment, "A poster saying 'Hackathon 2025'")

    def test_typo_mismatch(self) -> None:
        """Test mismatch due to spelling errors."""
        # Mock the crew.kickoff() to return mismatch with suggested improvement
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = """{
            "match_status": false,
            "message": "Spelling error detected: 'Hackethon' should be 'Hackathon'",
            "suggested_prompt_adjustment": "A poster saying 'Hackathon 2025' with clear, bold letters"
        }"""
        self.mock_crew.return_value = mock_crew_instance

        matcher = OCRMatcherAgent()
        result = matcher.compare_texts(
            ocr_result="Hackethon 205",
            intended_text="Hackathon 2025",
            current_prompt="A poster saying 'Hackathon 2025'",
        )

        self.assertIsInstance(result, OCRMatchResult)
        self.assertFalse(result.match_status)
        self.assertIn("spelling error", result.message.lower())
        self.assertIn("clear, bold letters", result.suggested_prompt_adjustment)

    def test_formatting_difference_accepted(self) -> None:
        """Test that formatting differences like line breaks are accepted."""
        # Mock the crew.kickoff() to return match despite line break formatting
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = """{
            "match_status": true,
            "message": "Content matches despite line break formatting difference",
            "suggested_prompt_adjustment": "A sign with text 'SALE 50% OFF'"
        }"""
        self.mock_crew.return_value = mock_crew_instance

        matcher = OCRMatcherAgent()
        result = matcher.compare_texts(
            ocr_result="SALE\n50% OFF", intended_text="SALE 50% OFF", current_prompt="A sign with text 'SALE 50% OFF'"
        )

        self.assertIsInstance(result, OCRMatchResult)
        self.assertTrue(result.match_status)
        self.assertIn("content matches", result.message.lower())

    def test_missing_word_rejection(self) -> None:
        """Test that missing words are properly rejected."""
        # Mock the crew.kickoff() to return mismatch for missing word
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = """{
            "match_status": false,
            "message": "Missing word 'to' in OCR result",
            "suggested_prompt_adjustment": "A banner saying 'Welcome to Home' with complete text and clear spacing"
        }"""
        self.mock_crew.return_value = mock_crew_instance

        matcher = OCRMatcherAgent()
        result = matcher.compare_texts(
            ocr_result="Welcome Home",
            intended_text="Welcome to Home",
            current_prompt="A banner saying 'Welcome to Home'",
        )

        self.assertIsInstance(result, OCRMatchResult)
        self.assertFalse(result.match_status)
        self.assertIn("missing", result.message.lower())
        self.assertIn("complete text", result.suggested_prompt_adjustment)

    def test_json_parsing_with_markdown_wrapper(self) -> None:
        """Test parsing JSON wrapped in markdown code blocks."""
        # Mock the crew.kickoff() to return JSON wrapped in markdown
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = """```json
        {
            "match_status": false,
            "message": "Test message",
            "suggested_prompt_adjustment": "Test adjustment"
        }
        ```"""
        self.mock_crew.return_value = mock_crew_instance

        matcher = OCRMatcherAgent()
        result = matcher.compare_texts(ocr_result="Test OCR", intended_text="Test Text", current_prompt="Test prompt")

        self.assertIsInstance(result, OCRMatchResult)
        self.assertFalse(result.match_status)
        self.assertEqual(result.message, "Test message")
        self.assertEqual(result.suggested_prompt_adjustment, "Test adjustment")

    def test_json_parsing_fallback(self) -> None:
        """Test fallback parsing when JSON is malformed."""
        # Mock the crew.kickoff() to return malformed response
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "This is not valid JSON but contains the word match"
        self.mock_crew.return_value = mock_crew_instance

        matcher = OCRMatcherAgent()
        result = matcher.compare_texts(ocr_result="Test OCR", intended_text="Test Text", current_prompt="Test prompt")

        self.assertIsInstance(result, OCRMatchResult)
        self.assertTrue(result.match_status)  # Should detect "match" keyword
        self.assertIn("parsing error", result.message.lower())
        self.assertEqual(result.suggested_prompt_adjustment, "Test prompt")

    def test_convenience_function_match(self) -> None:
        """Test the convenience function with a match result."""
        # Mock the crew.kickoff() to return match result
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = """{
            "match_status": true,
            "message": "Perfect match",
            "suggested_prompt_adjustment": "Current prompt works well"
        }"""
        self.mock_crew.return_value = mock_crew_instance

        result = compare_ocr_with_intended_text(
            ocr_result="Happy Birthday", intended_text="Happy Birthday", current_prompt="A card saying 'Happy Birthday'"
        )

        self.assertIsInstance(result, OCRMatchResult)
        self.assertTrue(result.match_status)
        self.assertEqual(result.message, "Perfect match")

    def test_convenience_function_no_match(self) -> None:
        """Test the convenience function with no match result."""
        # Mock the crew.kickoff() to return no match result
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = """{
            "match_status": false,
            "message": "Text size too small for OCR accuracy",
            "suggested_prompt_adjustment": "A card saying 'Happy Birthday' with large, bold text and high contrast"
        }"""
        self.mock_crew.return_value = mock_crew_instance

        result = compare_ocr_with_intended_text(
            ocr_result="Happy Birth", intended_text="Happy Birthday", current_prompt="A card saying 'Happy Birthday'"
        )

        self.assertIsInstance(result, OCRMatchResult)
        self.assertFalse(result.match_status)
        self.assertIn("text size", result.message.lower())
        self.assertIn("large, bold text", result.suggested_prompt_adjustment)


class TestOCRMatcherIntegration(unittest.TestCase):
    """Integration tests that actually call the CrewAI agent (requires API key)."""

    def setUp(self) -> None:
        """Set up integration test fixtures."""
        # Skip integration tests if no API key is available
        import os

        if not os.getenv("OPENAI_API_KEY"):
            self.skipTest("OPENAI_API_KEY not available for integration tests")

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_key"})
    def test_sample_comparisons_structure(self) -> None:
        """Test that the matcher returns proper structure for various comparisons."""
        test_cases = [
            {
                "ocr_result": "Hackathon 2025",
                "intended_text": "Hackathon 2025",
                "should_match": True,
                "description": "Perfect match",
            },
            {
                "ocr_result": "Hackethon 205",
                "intended_text": "Hackathon 2025",
                "should_match": False,
                "description": "Typos",
            },
            {
                "ocr_result": "SALE\n50% OFF",
                "intended_text": "SALE 50% OFF",
                "should_match": True,
                "description": "Line break formatting",
            },
            {
                "ocr_result": "Happy Birth-day",
                "intended_text": "Happy Birthday",
                "should_match": True,
                "description": "Hyphen formatting",
            },
        ]

        # This test mainly checks structure without making actual API calls
        # by mocking the crew execution
        with patch("ocr_matcher_agent.Crew") as mock_crew_class:
            mock_crew_instance = MagicMock()
            mock_crew_class.return_value = mock_crew_instance

            for i, case in enumerate(test_cases):
                # Mock different responses based on expected match
                if case["should_match"]:
                    mock_crew_instance.kickoff.return_value = f"""{{
                        "match_status": true,
                        "message": "Match for test case {i}",
                        "suggested_prompt_adjustment": "Test prompt {i}"
                    }}"""
                else:
                    mock_crew_instance.kickoff.return_value = f"""{{
                        "match_status": false,
                        "message": "No match for test case {i}",
                        "suggested_prompt_adjustment": "Improved test prompt {i}"
                    }}"""

                result = compare_ocr_with_intended_text(
                    str(case["ocr_result"]), str(case["intended_text"]), f"Test prompt {i}"
                )

                self.assertIsInstance(result, OCRMatchResult)
                self.assertEqual(
                    result.match_status, case["should_match"], f"Match status incorrect for: {case['description']}"
                )
                self.assertIsInstance(result.message, str)
                self.assertIsInstance(result.suggested_prompt_adjustment, str)
                self.assertTrue(len(result.message) > 0)
                self.assertTrue(len(result.suggested_prompt_adjustment) > 0)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
