import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import vision

load_dotenv()


class OCRProcessor:
    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize Google Cloud Vision OCR processor.

        Args:
            api_key: Google Cloud Vision API key. If None, will try to get from
                    GOOGLE_CLOUD_VISION_API_KEY environment variable, then fall back
                    to application default credentials.
        """
        if api_key is None:
            api_key = os.getenv("GOOGLE_CLOUD_VISION_API_KEY")

        if api_key:
            # Use API key authentication
            self.client = vision.ImageAnnotatorClient(
                client_options={"api_key": api_key}
            )
        else:
            # Fall back to application default credentials
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


def get_ocr_processor(api_key: str | None = None) -> OCRProcessor:
    """
    Get or create the global OCR processor instance.

    Args:
        api_key: Google Cloud Vision API key. Only used when creating a new instance.
                If None, will try to get from GOOGLE_CLOUD_VISION_API_KEY env var.
    """
    global ocr_processor
    if ocr_processor is None:
        ocr_processor = OCRProcessor(api_key=api_key)
    return ocr_processor


def extract_text_from_image(image_path: str | Path, api_key: str | None = None) -> str:
    """
    Convenience function to extract text from an image.

    Args:
        image_path: Path to the image file
        api_key: Google Cloud Vision API key. If None, will try to get from
                GOOGLE_CLOUD_VISION_API_KEY environment variable.

    Returns:
        Extracted text as a single string
    """
    processor = get_ocr_processor(api_key=api_key)
    return processor.extract_text(image_path)
