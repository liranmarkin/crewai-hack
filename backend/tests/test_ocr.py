from pathlib import Path

from ocr import extract_text_from_image


def test_ocr_happy_birthday_image() -> None:
    """Test OCR function on happy birthday image."""
    # Path to test image
    test_image_path = Path(__file__).parent / "test_ocr_images" / "happy_birthday.png"

    # Verify test image exists
    assert test_image_path.exists(), f"Test image not found at {test_image_path}"

    # Extract text using OCR
    extracted_text = extract_text_from_image(test_image_path)

    # Print what we got for debugging
    print(f"OCR extracted: '{extracted_text}'")

    # Google Cloud Vision should accurately detect the text
    # Clean up any extra whitespace and normalize
    cleaned_text = " ".join(extracted_text.split()).upper()

    # Should detect "HAPPY BIRTHDAY" exactly
    assert "HAPPY BIRTHDAY" == cleaned_text, f"Expected 'HAPPY BIRTHDAY', got '{cleaned_text}'"


def test_ocr_function_with_string_path() -> None:
    """Test OCR function with string path input."""
    test_image_path = str(Path(__file__).parent / "test_ocr_images" / "happy_birthday.png")

    # Extract text using OCR
    extracted_text = extract_text_from_image(test_image_path)

    # Should return some text (not empty)
    assert extracted_text.strip(), "Expected non-empty text from OCR"
    assert len(extracted_text.strip()) > 3, "Expected meaningful text output"
