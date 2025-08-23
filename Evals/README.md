# AI Image Text Generation Test

Simple framework for testing how well AI image generation models can accurately render specific text within images.

## Overview

This project contains 30 challenging but realistic prompts that require AI models to generate images with specific text. Each prompt is designed to test different aspects of text rendering that commonly cause errors.

## Project Structure

```
image-generator-agents/
├── README.md              # This file
├── prompts.csv            # 30 test prompts with expected text
├── generate_images.py     # Script to bulk generate images via API
└── images/               # Generated images (001.png - 030.png)
```

## Quick Start

1. **Get a fal.ai API key** from [fal.ai](https://fal.ai/)
2. **Set environment variable**: `export FAL_KEY=your_api_key`
3. **Run the generation script**: `python generate_images.py`
4. **Choose option 3** to generate first 5 images (~$0.15, recommended)
5. **Images save automatically** as `001.png`, `002.png`, etc.
6. **Compare generated text** with expected text from CSV

## The 30 Test Prompts

Each prompt tests different challenging text scenarios:

- **Neon signs** with cursive lettering and special characters
- **Movie posters** with metallic effects and colons
- **Warning signs** with technical terminology
- **Foreign text** (Japanese characters)
- **Mathematical equations** with superscripts
- **Product labels** with prices and punctuation
- **And 24 more...**

View all prompts in `prompts.csv` with expected text and difficulty notes.

## API Support

The generation script uses **[fal.ai](https://fal.ai/)** with the **FLUX.1 [schnell]** model, which is optimized for speed and cost-effectiveness with deliberately imperfect text rendering.

Set your API key as an environment variable:
```bash
export FAL_KEY=your_fal_api_key_here
```

## File Mapping

Super simple: Image `001.png` corresponds to row 1 in `prompts.csv`, `002.png` to row 2, etc.

## Evaluation

For each generated image, check:
1. **Text accuracy**: Does the text match exactly?
2. **Readability**: Is the text clear and legible?
3. **Style**: Does it match the requested visual style?

Common errors to look for:
- Character substitutions (O→0, I→l)
- Missing punctuation
- Spacing issues
- Partial text rendering

## Sample Prompts

| ID | Expected Text | Difficulty |
|----|---------------|------------|
| 001 | "Mama's Kitchen & Bakery Co." | Cursive, apostrophe, ampersand |
| 002 | "QUANTUM LEAP: BEYOND THE VOID" | All caps, colon, metallic effect |
| 013 | "SENATUS POPULUSQUE ROMANUS ANNO DOMINI MMXXIV" | Latin text, Roman numerals |
| 029 | "東京駅 / Tokyo Station - 新宿方面 / To Shinjuku" | Japanese characters, bilingual |

## Usage Examples

**Quick test (recommended):**
```bash
export FAL_KEY=your_api_key
python generate_images.py
# Choose option 3: Generate first 5 images (~$0.15)
```

**Full dataset:**
```bash
python generate_images.py
# Choose option 4: Generate all 30 images (~$0.90)
```

**Custom amount:**
```bash
python generate_images.py
# Choose option 6: Generate specific number (1-30)
```

**Check what's missing:**
```bash
python generate_images.py  
# Choose option 2: Check missing images
```

## 💰 Cost-Effective Testing

- **Default**: 5 images for ~$0.15 (perfect for quick testing)
- **Full dataset**: 30 images for ~$0.90 (complete evaluation)
- **Custom**: Choose any amount 1-30 for flexible testing

**Why FLUX.1 [schnell]?** 
- ⚡ **Super fast**: 4 inference steps vs 28
- 💰 **Very cheap**: Start testing for under $0.20
- 🎯 **Imperfect text**: Perfect for testing text detection agents