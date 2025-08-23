from pathlib import Path

from google.cloud import vision


class OCRProcessor:
    def __init__(self) -> None:
        """Initialize Google Cloud Vision OCR processor."""
        self.client = vision.ImageAnnotatorClient()

    def extract_text(self, image_path: str | Path) -> str:
        """
        Extract text from an image using Google Cloud Vision OCR.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text as a single string
        """
        image_path = Path(image_path)

        # Read the image file
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        # Create Vision API image object
        image = vision.Image(content=content)

        # Perform text detection
        response = self.client.text_detection(image=image)
        texts = response.text_annotations

        # Check for errors
        if response.error.message:
            raise Exception(f"Google Cloud Vision API error: {response.error.message}")

        # Return the first (most comprehensive) text annotation if available
        if texts:
            description: str = texts[0].description
            return description.strip()
        else:
            return ""


# Global instance - initialized lazily
ocr_processor = None


def get_ocr_processor() -> OCRProcessor:
    """Get or create the global OCR processor instance."""
    global ocr_processor
    if ocr_processor is None:
        ocr_processor = OCRProcessor()
    return ocr_processor


def extract_text_from_image(image_path: str | Path) -> str:
    """
    Convenience function to extract text from an image.

    Args:
        image_path: Path to the image file

    Returns:
        Extracted text as a single string
    """
    processor = get_ocr_processor()
    return processor.extract_text(image_path)
