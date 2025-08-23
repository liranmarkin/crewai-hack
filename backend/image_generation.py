import os
from pathlib import Path
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class ImageGenerator:
    def __init__(self, api_key: str | None = None):
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or pass api_key to ImageGenerator"
            )
        self.client = OpenAI(api_key=api_key)
        self.images_dir = Path("generated_images")
        self.images_dir.mkdir(exist_ok=True)

    async def generate_image(self, prompt: str, intended_text: str) -> tuple[str, str]:
        """
        Generate an image using OpenAI's DALL-E 3 API.

        Args:
            prompt: The image generation prompt
            intended_text: The text that should appear in the image

        Returns:
            tuple: (image_id, image_path) where image_id is used in the API
        """
        # Enhance prompt to include the intended text
        enhanced_prompt = (
            f"{prompt}. The image must clearly display the text: '{intended_text}'"
        )

        try:
            # Generate image using DALL-E 3
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                n=1,
                size="1024x1024",
                quality="standard",
                response_format="url",
            )

            # Get the image URL
            image_url = response.data[0].url
            if not image_url:
                raise Exception("No image URL returned from OpenAI API")

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
