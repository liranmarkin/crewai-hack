#!/usr/bin/env python3
"""
Bulk Image Generation Script

Simple script to generate all 30 test images using fal.ai API.
Uses FLUX.1 [dev] model for high-quality text rendering.
"""

import csv
import os
import requests
import time
from pathlib import Path

# Load environment variables from .env.local if it exists
def load_env_file():
    env_file = ".env.local"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load .env.local file
load_env_file()

# Configuration
API_PROVIDER = "fal"
API_KEY = os.getenv("FAL_KEY")  # Loaded from .env.local or environment variable
IMAGE_SIZE = "landscape_4_3"  # Options: square_hd, square, portrait_4_3, portrait_16_9, landscape_4_3, landscape_16_9
OUTPUT_DIR = "images"
DEFAULT_GENERATION_LIMIT = 5  # Generate only first 5 images by default for cheap testing

# Model configurations
MODELS = {
    "flux": {
        "name": "FLUX.1 Schnell",
        "url": "https://fal.run/fal-ai/flux/schnell",
        "headers": {
            "Authorization": f"Key {API_KEY}",
            "Content-Type": "application/json"
        },
        "payload_template": {
            "prompt": "",
            "image_size": IMAGE_SIZE,
            "num_inference_steps": 4,  # Schnell uses fewer steps for speed
            "num_images": 1,
            "enable_safety_checker": True,
            "seed": None
        }
    },
    "imagen4": {
        "name": "Google Imagen 4",
        "url": "https://fal.run/fal-ai/imagen4/preview",
        "headers": {
            "Authorization": f"Key {API_KEY}",
            "Content-Type": "application/json"
        },
        "payload_template": {
            "prompt": "",
            "image_size": IMAGE_SIZE,
            "num_images": 1,
            "enable_safety_checker": True
        }
    }
}

def load_prompts(csv_file="prompts.csv"):
    """Load prompts from CSV file."""
    prompts = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prompts.append(row)
        print(f"Loaded {len(prompts)} prompts from {csv_file}")
        return prompts
    except FileNotFoundError:
        print(f"Error: {csv_file} not found!")
        return []

def generate_image_fal(prompt, prompt_id, model="flux"):
    """Generate image using fal.ai with specified model."""
    if model not in MODELS:
        print(f"Unknown model: {model}")
        return False
    
    config = MODELS[model]
    payload = config["payload_template"].copy()
    payload["prompt"] = prompt
    
    try:
        response = requests.post(
            config["url"],
            headers=config["headers"],
            json=payload,
            timeout=120  # Increased timeout for Imagen 4
        )
        
        if response.status_code == 200:
            data = response.json()
            # fal.ai returns images in the "images" array
            if "images" in data and len(data["images"]) > 0:
                image_url = data["images"][0]["url"]
                return download_image(image_url, prompt_id, OUTPUT_DIR)
            else:
                print(f"No images returned for {prompt_id}")
                return False
        else:
            print(f"Error generating image {prompt_id}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception generating image {prompt_id}: {str(e)}")
        return False



def download_image(image_url, prompt_id, output_dir="images"):
    """Download image from URL and save with prompt ID."""
    try:
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            filename = f"{output_dir}/{prompt_id}.png"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ Saved {filename}")
            return True
        else:
            print(f"Error downloading image {prompt_id}: {response.status_code}")
            return False
    except Exception as e:
        print(f"Exception downloading image {prompt_id}: {str(e)}")
        return False

def generate_image_with_custom_output(prompt, prompt_id, model="flux", output_dir="images"):
    """Generate image using fal.ai with custom output directory."""
    if model not in MODELS:
        print(f"Unknown model: {model}")
        return False
    
    config = MODELS[model]
    payload = config["payload_template"].copy()
    payload["prompt"] = prompt
    
    try:
        response = requests.post(
            config["url"],
            headers=config["headers"],
            json=payload,
            timeout=120  # Increased timeout for Imagen 4
        )
        
        if response.status_code == 200:
            data = response.json()
            # fal.ai returns images in the "images" array
            if "images" in data and len(data["images"]) > 0:
                image_url = data["images"][0]["url"]
                return download_image(image_url, prompt_id, output_dir)
            else:
                print(f"No images returned for {prompt_id}")
                return False
        else:
            print(f"Error generating image {prompt_id}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception generating image {prompt_id}: {str(e)}")
        return False

def generate_images(limit=None, model="flux"):
    """Generate images from the prompts CSV with optional limit and model."""
    # Check configuration
    if not API_KEY:
        print("Error: Please set your FAL_KEY environment variable")
        print("Run: export FAL_KEY=your_fal_api_key")
        return
    
    # Load prompts
    prompts = load_prompts()
    if not prompts:
        return
    
    # Apply limit if specified
    if limit:
        prompts = prompts[:limit]
        print(f"\\nLimited to first {limit} prompts for faster/cheaper testing")
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    # Generate images
    successful = 0
    failed = 0
    
    model_name = MODELS[model]["name"]
    print(f"\\nStarting generation of {len(prompts)} images using {model_name}...")
    if model == "flux":
        print("Fast & cheap model - optimized for speed over text accuracy")
    else:
        print("High quality model - optimized for text accuracy")
    print("=" * 60)
    
    for i, prompt_data in enumerate(prompts, 1):
        prompt_id = prompt_data["id"]
        prompt_text = prompt_data["prompt"]
        expected_text = prompt_data["expected_text"]
        
        print(f"\\n[{i}/{len(prompts)}] Generating {prompt_id}")
        print(f"Expected text: {expected_text}")
        print(f"Prompt: {prompt_text[:100]}...")
        
        # Check if image already exists
        output_file = f"{OUTPUT_DIR}/{prompt_id}.png"
        if os.path.exists(output_file):
            print(f"⚠ {output_file} already exists, skipping...")
            successful += 1
            continue
        
        # Generate image using fal.ai
        success = generate_image_fal(prompt_text, prompt_id, model)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Rate limiting - schnell is very fast, minimal delay needed
        time.sleep(1)
    
    print(f"\\n" + "=" * 60)
    print(f"Generation complete!")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"📁 Images saved in: {OUTPUT_DIR}/")
    
    if failed > 0:
        print(f"\\nTo retry failed generations, run option 4 (Generate missing images only)")

def generate_images_with_custom_settings(csv_file="prompts.csv", output_dir="images", model="flux", limit=None):
    """Generate images with custom CSV file, output directory, and model."""
    # Check configuration
    if not API_KEY:
        print("Error: Please set your FAL_KEY environment variable")
        print("Run: export FAL_KEY=your_fal_api_key")
        return
    
    # Load prompts from custom CSV
    prompts = load_prompts(csv_file)
    if not prompts:
        return
    
    # Apply limit if specified
    if limit:
        prompts = prompts[:limit]
        print(f"\\nLimited to first {limit} prompts for faster/cheaper testing")
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Generate images
    successful = 0
    failed = 0
    
    model_name = MODELS[model]["name"]
    print(f"\\nStarting generation of {len(prompts)} images using {model_name}...")
    if model == "flux":
        print("Fast & cheap model - optimized for speed over text accuracy")
    else:
        print("High quality model - optimized for text accuracy")
    print("=" * 60)
    
    for i, prompt_data in enumerate(prompts, 1):
        prompt_id = prompt_data["id"]
        prompt_text = prompt_data["prompt"]
        expected_text = prompt_data["expected_text"]
        
        print(f"\\n[{i}/{len(prompts)}] Generating {prompt_id}")
        print(f"Expected text: {expected_text}")
        print(f"Prompt: {prompt_text[:100]}...")
        
        # Check if image already exists
        output_file = f"{output_dir}/{prompt_id}.png"
        if os.path.exists(output_file):
            print(f"⚠ {output_file} already exists, skipping...")
            successful += 1
            continue
        
        # Generate image using fal.ai with custom output directory
        success = generate_image_with_custom_output(prompt_text, prompt_id, model, output_dir)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Rate limiting
        time.sleep(2 if model == "imagen4" else 1)
    
    print(f"\\n" + "=" * 60)
    print(f"Generation complete!")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"📁 Images saved in: {output_dir}/")
    
    if failed > 0:
        print(f"\\nTo retry failed generations, run the generation again")

def generate_images_for_ids(target_ids, model="flux"):
    """Generate images for specific prompt IDs only."""
    # Check configuration
    if not API_KEY:
        print("Error: Please set your FAL_KEY environment variable")
        print("Run: export FAL_KEY=your_fal_api_key")
        return
    
    # Load all prompts and filter for target IDs
    all_prompts = load_prompts()
    prompts = [p for p in all_prompts if p["id"] in target_ids]
    
    if not prompts:
        print("No matching prompts found!")
        return
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    # Generate images
    successful = 0
    failed = 0
    
    model_name = MODELS[model]["name"]
    print(f"\\nStarting generation of {len(prompts)} specific images using {model_name}...")
    if model == "flux":
        print("Fast & cheap model - optimized for speed over text accuracy")
    else:
        print("High quality model - optimized for text accuracy")
    print("=" * 60)
    
    for i, prompt_data in enumerate(prompts, 1):
        prompt_id = prompt_data["id"]
        prompt_text = prompt_data["prompt"]
        expected_text = prompt_data["expected_text"]
        
        print(f"\\n[{i}/{len(prompts)}] Generating {prompt_id}")
        print(f"Expected text: {expected_text}")
        print(f"Prompt: {prompt_text[:100]}...")
        
        # Check if image already exists
        output_file = f"{OUTPUT_DIR}/{prompt_id}.png"
        if os.path.exists(output_file):
            print(f"⚠ {output_file} already exists, skipping...")
            successful += 1
            continue
        
        # Generate image using fal.ai
        success = generate_image_fal(prompt_text, prompt_id, model)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Rate limiting - schnell is very fast, minimal delay needed
        time.sleep(1)
    
    print(f"\\n" + "=" * 60)
    print(f"Generation complete!")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"📁 Images saved in: {OUTPUT_DIR}/")
    
    if failed > 0:
        print(f"\\nTo retry failed generations, run option 5 again")

def check_missing_images(limit=None):
    """Check which images are missing."""
    prompts = load_prompts()
    if not prompts:
        return
    
    # Apply limit if specified
    if limit:
        prompts = prompts[:limit]
        print(f"Checking first {limit} images only")
    
    missing = []
    for prompt_data in prompts:
        prompt_id = prompt_data["id"]
        output_file = f"{OUTPUT_DIR}/{prompt_id}.png"
        if not os.path.exists(output_file):
            missing.append(prompt_id)
    
    total_expected = len(prompts)
    total_present = total_expected - len(missing)
    
    print(f"\\nImage Status:")
    print(f"✓ Present: {total_present}/{total_expected}")
    if missing:
        print(f"✗ Missing: {len(missing)} images: {', '.join(missing)}")
    else:
        print("🎉 All expected images are present!")
    
    return missing

def main():
    """Main function with simple menu."""
    print("AI Image Text Generation - fal.ai Bulk Generator")
    print("=" * 50)
    
    # Model selection
    print("\\nModel Options:")
    print("1. FLUX.1 Schnell (fast, cheap, imperfect text)")
    print("2. Google Imagen 4 (high quality, better text)")
    print()
    
    model_choice = input("Choose model (1 or 2): ").strip()
    if model_choice == "2":
        selected_model = "imagen4"
        model_name = "Google Imagen 4"
        print(f"Selected: {model_name} - High quality text generation")
    else:
        selected_model = "flux"
        model_name = "FLUX.1 Schnell"
        print(f"Selected: {model_name} - Fast and cheap generation")
    
    while True:
        print("\\nOptions:")
        print("1. Check configuration")
        print("2. Check missing images (first 5)")
        print("3. Generate first 5 images (default - cheap & fast)")
        print("4. Generate all 60 images (full dataset)")
        print("5. Generate missing images only")
        print("6. Custom: Generate specific number of images")
        print("7. Generate new prompts 031-060 (Imagen 4 recommended)")
        print("8. COMPARISON: Generate same 30 prompts with Imagen 4")
        print("9. Exit")
        
        choice = input("\\nChoose option (1-9): ").strip()
        
        if choice == "1":
            print(f"\\nConfiguration:")
            print(f"API Provider: fal.ai")
            print(f"Selected Model: {model_name}")
            print(f"API Key: {'Set' if API_KEY else 'NOT SET - Please set FAL_KEY environment variable'}")
            print(f"Image Size: {IMAGE_SIZE}")
            print(f"Output Directory: {OUTPUT_DIR}")
            
            if selected_model == "flux":
                print(f"Model Details: Fast & cheap, imperfect text rendering")
                print(f"Cost: ~$0.03 per image")
                print(f"Default Limit: {DEFAULT_GENERATION_LIMIT} images (~$0.15)")
                print(f"Full Dataset: 60 images (~$1.80)")
            else:
                print(f"Model Details: High quality, better text accuracy")
                print(f"Cost: ~$0.10 per image")
                print(f"Default Limit: {DEFAULT_GENERATION_LIMIT} images (~$0.50)")
                print(f"Full Dataset: 60 images (~$6.00)")
            
        elif choice == "2":
            check_missing_images(DEFAULT_GENERATION_LIMIT)
            
        elif choice == "3":
            print(f"\\nGenerating first {DEFAULT_GENERATION_LIMIT} images (recommended for testing)...")
            generate_images(DEFAULT_GENERATION_LIMIT, selected_model)
            
        elif choice == "4":
            print("\\nGenerating ALL 60 images (full dataset)...")
            cost_estimate = 60 * (0.03 if selected_model == "flux" else 0.10)
            confirm = input(f"This will cost ~${cost_estimate:.2f}. Continue? (y/n): ").strip().lower()
            if confirm == 'y':
                generate_images(None, selected_model)
            else:
                print("Cancelled.")
                
        elif choice == "5":
            missing = check_missing_images()
            if missing:
                print(f"\\nGenerating {len(missing)} missing images...")
                generate_images_for_ids(missing, selected_model)
            else:
                print("No missing images to generate!")
                
        elif choice == "6":
            try:
                limit = int(input("How many images to generate (1-60)? "))
                if 1 <= limit <= 60:
                    cost_estimate = limit * (0.03 if selected_model == "flux" else 0.10)
                    print(f"\\nGenerating first {limit} images (estimated cost: ~${cost_estimate:.2f})...")
                    generate_images(limit, selected_model)
                else:
                    print("Please enter a number between 1 and 60.")
            except ValueError:
                print("Please enter a valid number.")
                
        elif choice == "7":
            print("\\nGenerating new prompts 031-060 (easier prompts for positive examples)...")
            new_prompt_ids = [f"{i:03d}" for i in range(31, 61)]
            cost_estimate = 30 * (0.03 if selected_model == "flux" else 0.10)
            print(f"Model: {model_name}")
            print(f"Estimated cost: ~${cost_estimate:.2f}")
            confirm = input("Continue? (y/n): ").strip().lower()
            if confirm == 'y':
                generate_images_for_ids(new_prompt_ids, selected_model)
            else:
                print("Cancelled.")
                
        elif choice == "8":
            print("\\nCOMPARISON MODE: Generate same 30 challenging prompts with Imagen 4")
            print("This will create images_imagen4/ folder with high-quality versions")
            print("CSV: prompts_imagen4.csv")
            print("Model: Google Imagen 4 (high quality)")
            cost_estimate = 30 * 0.10
            print(f"Estimated cost: ~${cost_estimate:.2f}")
            confirm = input("Continue? (y/n): ").strip().lower()
            if confirm == 'y':
                generate_images_with_custom_settings(
                    csv_file="prompts_imagen4.csv", 
                    output_dir="images_imagen4", 
                    model="imagen4"
                )
            else:
                print("Cancelled.")
                
        elif choice == "9":
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
