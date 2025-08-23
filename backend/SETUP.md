# Backend Setup Guide

## Prerequisites

- Python 3.11+
- uv (or pip)

## API Key Setup

### Google Cloud Vision API Key

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create a project** (if you don't have one)
3. **Enable the Cloud Vision API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Cloud Vision API"
   - Click "Enable"
4. **Create an API Key**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the generated API key
5. **Restrict the API Key** (recommended for security):
   - Click on the API key to edit it
   - Under "API restrictions", select "Restrict key"
   - Choose "Cloud Vision API"
   - Save the changes

### OpenAI API Key

1. **Go to OpenAI Platform**: https://platform.openai.com/
2. **Create an API key** in your account settings
3. **Copy the API key**

## Environment Configuration

1. **Copy the example environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** and add your API keys:
   ```env
   GOOGLE_CLOUD_VISION_API_KEY=your_actual_google_vision_api_key
   OPENAI_API_KEY=your_actual_openai_api_key
   ```

## Installation

```bash
# Install dependencies
uv sync

# Or with pip
pip install -e .
```

## Running the Backend

```bash
# Development server
uv run uvicorn main:app --reload

# Or with python directly
python -m uvicorn main:app --reload
```

The API will be available at: http://localhost:8000

## Testing

```bash
# Run all tests
uv run pytest

# Run specific test
uv run pytest tests/test_ocr_integration.py

# Run with verbose output
uv run pytest -v
```

## Code Quality

```bash
# Format code
make format

# Check linting and types
make check

# Fix auto-fixable issues
make lint-fix
```

## API Endpoints

- `GET /` - API health check
- `GET /test` - Test endpoint
- `POST /api/generate` - Generate workflow (SSE stream)
- `GET /api/images/{image_id}` - Get generated image

## Sharing with Team Members

When sharing this project with other developers:

1. Share the repository (without `.env` file)
2. Provide them with the API keys or ask them to create their own
3. They should follow this setup guide
4. The `.env` file should never be committed to git

## Troubleshooting

### "Google Cloud Vision API not enabled"
- Make sure you enabled the Cloud Vision API in the Google Cloud Console
- Verify your project has billing enabled

### "Authentication failed"
- Double-check your API key is correct
- Ensure the API key has the right permissions (Cloud Vision API)

### "OpenAI API errors"
- Verify your OpenAI API key is valid
- Check your OpenAI account has sufficient credits