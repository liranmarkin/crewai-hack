#!/usr/bin/env python3
"""
Image Text Validation Script using Gemini 2.5 Flash

Analyzes all generated images to determine if the text matches expectations
and updates the CSV with validation results.
"""

import csv
import os
import base64
from pathlib import Path
from google import genai
from google.genai import types

# Configuration
PROMPTS_CSV = "prompts.csv"
IMAGES_DIR = "images"

def load_env_file():
    """Load environment variables from .env.local if it exists"""
    env_file = ".env.local"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def validate_image_with_gemini(image_path, expected_text, user_prompt, model="gemini-2.5-flash"):
    """Use Gemini to validate if image text matches expected text"""
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in environment variables")
        return None, "API key not configured"
    
    try:
        # Create client with API key
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Single prompt that extracts text and validates in one call
        prompt = f"""
You are evaluating whether an AI image generator successfully created text that matches what a user requested.

User's request: "{user_prompt}"
Expected text content: "{expected_text}"

Your task:
1. Extract ALL readable text from this image
2. Identify which text matches the user's request and which is unwanted extra content
3. Check character-level accuracy for the intended text
4. Flag any additional content the user didn't request

Critical evaluation criteria:
- Every character, letter, and punctuation mark must be accurate
- Missing letters or malformed characters are errors (even if word is recognizable)
- Any extra words, text, or content not requested by the user is an error
- The image should contain EXACTLY what text the user requested - nothing more, nothing less
- The text is in the correct color, style, or font

When checking accuracy:
- Look for missing or incorrect letters within words
- Check for missing or wrong punctuation marks
- Verify capitalization matches the expected format
- Identify any unwanted additional text, symbols, or random content

Respond in this exact format:
EXTRACTED: [Only the text that appears to match the user's intended request]
UNWANTED: [Any extra text, words, or content not requested by the user - write "None" if no unwanted content]
RESULT: [CORRECT or INCORRECT]
ERRORS: [If INCORRECT, list specific character/word errors and unwanted content. If CORRECT, say "Perfect match"]
"""

        # Read and encode image file
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Single API call for extraction and validation with thinking enabled
        response = client.models.generate_content(
            model=model,
            contents=[
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_data
                            }
                        }
                    ]
                }
            ],
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=1024
                )
            )
        )
        
        # Parse the response
        content = response.text.strip()
        lines = content.split('\n')
        extracted_text = ""
        unwanted_text = ""
        result_line = ""
        errors_line = ""
        
        for line in lines:
            if line.startswith("EXTRACTED:"):
                extracted_text = line.replace("EXTRACTED:", "").strip()
            elif line.startswith("UNWANTED:"):
                unwanted_text = line.replace("UNWANTED:", "").strip()
            elif line.startswith("RESULT:"):
                result_line = line.replace("RESULT:", "").strip()
            elif line.startswith("ERRORS:"):
                errors_line = line.replace("ERRORS:", "").strip()
        
        # Determine correctness
        is_correct = result_line.upper() == "CORRECT"
        
        # Build comprehensive error description
        error_parts = []
        if not is_correct and errors_line:
            error_parts.append(errors_line)
        if unwanted_text and unwanted_text.lower() != "none":
            error_parts.append(f"Unwanted content: {unwanted_text}")
        
        error_description = ". ".join(error_parts) if error_parts else ""
        
        return is_correct, error_description, extracted_text
            
    except Exception as e:
        return None, f"Exception: {str(e)}", ""

def load_prompts():
    """Load prompts from CSV file"""
    prompts = []
    try:
        with open(PROMPTS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prompts.append(row)
        return prompts
    except FileNotFoundError:
        print(f"Error: {PROMPTS_CSV} not found!")
        return []

def save_prompts_with_validation(validated_prompts, all_prompts):
    """Save prompts back to CSV with validation columns, preserving all original prompts"""
    fieldnames = ['id', 'prompt', 'expected_text', 'difficulty_notes', 'extracted_text', 'is_correct', 'error_description']
    
    # Create a lookup dict for validated prompts
    validated_dict = {prompt['id']: prompt for prompt in validated_prompts}
    
    # Update all_prompts with validation results
    for prompt in all_prompts:
        prompt_id = prompt['id']
        if prompt_id in validated_dict:
            # Update with validation results
            prompt['extracted_text'] = validated_dict[prompt_id]['extracted_text']
            prompt['is_correct'] = validated_dict[prompt_id]['is_correct']
            prompt['error_description'] = validated_dict[prompt_id]['error_description']
        else:
            # Ensure columns exist but are empty for non-validated prompts
            if 'extracted_text' not in prompt:
                prompt['extracted_text'] = ''
            if 'is_correct' not in prompt:
                prompt['is_correct'] = ''
            if 'error_description' not in prompt:
                prompt['error_description'] = ''
    
    try:
        with open(PROMPTS_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for prompt in all_prompts:
                writer.writerow(prompt)
        print(f"✓ Updated {PROMPTS_CSV} with validation results (preserved all {len(all_prompts)} prompts)")
    except Exception as e:
        print(f"Error saving CSV: {e}")

def main():
    """Main validation function"""
    print("AI Image Text Validation - Gemini 2.5")
    print("=" * 50)
    
    # Load environment variables
    load_env_file()
    
    # Check API key
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: Please set GEMINI_API_KEY in your .env.local file")
        print("Get your API key from: https://aistudio.google.com/app/apikey")
        return
    
    # Load all prompts
    all_prompts = load_prompts()
    if not all_prompts:
        return
    
    print(f"Loaded {len(all_prompts)} prompts")
    print()
    
    # Model selection
    print("Model Options:")
    print("1. Gemini 2.5 Flash (faster, cheaper)")
    print("2. Gemini 2.5 Pro (more accurate, slower)")
    print()
    
    model_choice = input("Choose model (1 or 2): ").strip()
    if model_choice == "2":
        model = "gemini-2.5-pro"
        model_name = "Gemini 2.5 Pro"
    else:
        model = "gemini-2.5-flash"
        model_name = "Gemini 2.5 Flash"
    
    print()
    print("Validation Options:")
    print("1. Test mode: Validate first 5 images (recommended)")
    print("2. Full validation: Validate all 30 images")
    print()
    
    choice = input("Choose validation option (1 or 2): ").strip()
    
    if choice == "1":
        prompts_to_validate = all_prompts[:5]
        print(f"\\nTest mode: Processing first 5 images...")
    elif choice == "2":
        prompts_to_validate = all_prompts
        print(f"\\nFull validation: Processing all {len(all_prompts)} images...")
    else:
        print("Invalid choice. Defaulting to test mode (first 5 images)...")
        prompts_to_validate = all_prompts[:5]
    
    print(f"Using {model_name} for validation...")
    print()
    
    # Validate each image
    successful = 0
    failed = 0
    correct_count = 0
    incorrect_count = 0
    
    for i, prompt in enumerate(prompts_to_validate, 1):
        prompt_id = prompt['id']
        expected_text = prompt['expected_text']
        user_prompt = prompt['prompt']
        image_path = f"{IMAGES_DIR}/{prompt_id}.png"
        
        print(f"[{i}/{len(prompts_to_validate)}] Validating {prompt_id}")
        print(f"Expected: {expected_text[:60]}...")
        
        # Check if image exists
        if not os.path.exists(image_path):
            print(f"⚠ Image not found: {image_path}")
            prompt['extracted_text'] = ""
            prompt['is_correct'] = "MISSING"
            prompt['error_description'] = "Image file not found"
            failed += 1
            continue
        
        # Validate with Gemini (now returns 3 values)
        is_correct, error_description, extracted_text = validate_image_with_gemini(image_path, expected_text, user_prompt, model)
        
        if is_correct is None:
            print(f"✗ Validation failed: {error_description}")
            prompt['extracted_text'] = ""
            prompt['is_correct'] = "ERROR"
            prompt['error_description'] = error_description
            failed += 1
        else:
            status = "✓ CORRECT" if is_correct else "✗ INCORRECT"
            print(f"{status}")
            print(f"Extracted: {extracted_text}")
            if error_description:
                print(f"Issues: {error_description}")
            
            prompt['extracted_text'] = extracted_text
            prompt['is_correct'] = "TRUE" if is_correct else "FALSE"
            prompt['error_description'] = error_description or ""
            
            successful += 1
            if is_correct:
                correct_count += 1
            else:
                incorrect_count += 1
        
        print()
    
    # Save results (preserve all prompts, only update validated ones)
    save_prompts_with_validation(prompts_to_validate, all_prompts)
    
    # Summary
    print("=" * 50)
    print("Validation Complete!")
    print(f"✓ Successfully validated: {successful}")
    print(f"✗ Failed to validate: {failed}")
    print(f"📊 Results breakdown:")
    print(f"   - Correct text: {correct_count}")
    print(f"   - Incorrect text: {incorrect_count}")
    print(f"📁 Results saved to: {PROMPTS_CSV}")
    
    if incorrect_count > 0:
        print(f"\n🔍 Found {incorrect_count} images with text errors - perfect for training!")

if __name__ == "__main__":
    main()
