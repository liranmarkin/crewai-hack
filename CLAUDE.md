# Text-Aware Image Generation Workflow - Hackathon Project

## Project Overview
This is a hackathon project that automates the verification and correction loop for text-aware image generation. The system combines image generation, OCR text extraction, and workflow automation to ensure generated images contain correct text without manual intervention.

## Core Problem
When users generate images with text (posters, memes, ads), the generated text is often misspelled, distorted, or incorrect. Manual feedback loops are slow, inconsistent, and frustrating.

## Solution
Automated verification and correction loop combining:
- Image generation model (LLM-powered text-to-image)
- OCR model to extract and check text
- Workflow/agent loop that retries until image matches user intent

## Technical Architecture

### Frontend
- Simple web UI with left/right layout
- Left: User prompt + intended text field
- Right: Generated image display
- Show iteration steps with OCR results and match status
- Display system reasoning ("thinking") process
- Timeline view of all attempts until success

### Backend
- Orchestrator agent that coordinates the workflow
- Image generation API integration
- OCR model integration
- Verification and retry logic
- REST API endpoints for frontend

### Workflow Logic
- Structured iteration loop (max 8 attempts)
- 5-minute timeout mechanism
- Feedback system: "OCR read X, expected Y → retry with adjusted prompt"
- Prompt engineering to encourage text correction on each iteration

## Core Features

### 1. Input Interface
- Text prompt input field
- Intended text specification field
- Real-time iteration display
- Success/failure indicators for each attempt

### 2. Workflow Engine
- Maximum 8 iterations per request
- 5-minute total timeout
- OCR-based verification
- Automated prompt adjustment based on OCR feedback
- Clear reasoning display for each retry

### 3. API Layer
- Image generation endpoint
- OCR processing endpoint
- Workflow orchestration endpoint
- Real-time status updates

## Demo Flow Example
1. User input: Prompt "A poster for Hackathon", Intended text "Hackathon 2025"
2. System generates first image
3. OCR extracts: "Hackethon 205"
4. System shows: Image 1 → OCR result → ❌ mismatch
5. Workflow retries with adjusted prompt
6. After iterations, OCR matches: "Hackathon 2025"
7. Final success: Image N → OCR result → ✅ match
8. Timeline shows complete journey from problem to solution

## Development Approach
- **Hackathon Speed**: Focus on getting working demo quickly
- **No mock/demo data**: Core logic must use real data and services
- **Minimal viable approach**: Function over form for 6-hour constraint

## Success Criteria
- **Functional**: At least one successful automated text correction demo
- **Visual**: Clear iteration steps visible to judges
- **Storytelling**: Demonstrates value proposition (saves time, automatic correction)
- **Time-boxed**: Completed within 6-hour hackathon timeframe

## Technical Constraints
- 6-hour development window
- Maximum 8 iteration attempts per request
- 5-minute timeout per workflow
- Basic web interface (no fancy UI/UX)
- Off-the-shelf OCR solution
- English text only for MVP

## Non-Goals (Scope Control)
- Complex UI/UX beyond basic functionality
- OCR optimization or custom training
- Multi-language support
- Guarantees beyond timeout handling
- Production-level error handling and edge cases

## Important Instructions
- Don't keep memory of agent types - refer to this README for project overview
- Never return mock data in core logic
- Prefer editing existing files over creating new ones
- Don't create documentation files unless explicitly requested