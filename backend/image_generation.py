import os
from pathlib import Path
from uuid import uuid4

import fal_client
import httpx
from dotenv import load_dotenv

load_dotenv()


class ImageGenerator:
    def __init__(self, api_key: str | None = None):
        api_key = api_key or os.environ.get("FAL_KEY")
        if not api_key:
            raise ValueError(
                "FAL.AI API key is required. Set FAL_KEY environment variable "
                "or pass api_key to ImageGenerator"
            )

        # Configure fal_client with API key
        os.environ["FAL_KEY"] = api_key

        self.images_dir = Path("generated_images")
        self.images_dir.mkdir(exist_ok=True)

    async def generate_image(self, prompt: str) -> tuple[str, str]:
        """
        Generate an image using FAL.AI's FLUX Pro 1.1 API.

        Args:
            prompt: The image generation prompt

        Returns:
            tuple: (image_id, image_path) where image_id is used in the API
        """

        try:
            # Generate image using FLUX Pro 1.1
            result = fal_client.run(
                "fal-ai/flux-pro/v1.1",
                arguments={
                    "prompt": prompt,
                    "image_size": "landscape_4_3",  # Good balance for text generation
                    "num_images": 1,
                    "safety_tolerance": "2",
                    "enable_safety_checker": True,
                },
            )

            # Get the image URL from response
            if not result or "images" not in result or not result["images"]:
                raise Exception("No image returned from FAL.AI API")

            image_url = result["images"][0]["url"]
            if not image_url:
                raise Exception("No image URL returned from FAL.AI API")

            # Generate unique image ID
            image_id = str(uuid4())
            image_path = self.images_dir / f"{image_id}.png"

            # Download and save the image
            await self._download_image(image_url, image_path)

            return image_id, str(image_path)

        except Exception as e:
            raise Exception(f"Failed to generate image: {str(e)}") from e

    async def _download_image(self, url: str, save_path: Path) -> None:
        """Download image from URL and save to local file."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(response.content)

    def get_image_path(self, image_id: str) -> Path | None:
        """Get the path to a saved image by ID."""
        image_path = self.images_dir / f"{image_id}.png"
        if image_path.exists():
            return image_path
        return None


# Global instance - initialized lazily
image_generator = None


def get_image_generator() -> ImageGenerator:
    """Get or create the global image generator instance."""
    global image_generator
    if image_generator is None:
        image_generator = ImageGenerator()
    return image_generator
