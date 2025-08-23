import { useState, useCallback, useEffect, useRef } from 'react';
import { ImageGenerationAPI } from '@/lib/api';
import { GenerateRequest, SSEEvent, WorkflowState } from '@/lib/types';
import { API_URL } from '@/lib/config';

const TIMEOUT_DURATION = 300; // 5 minutes in seconds

export function useImageGeneration() {
  const [workflowState, setWorkflowState] = useState<WorkflowState>({
    isGenerating: false,
    iterations: [],
    isComplete: false,
    timeRemaining: TIMEOUT_DURATION,
  });

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Timer countdown
  useEffect(() => {
    if (workflowState.isGenerating && workflowState.timeRemaining > 0) {
      timeoutRef.current = setTimeout(() => {
        setWorkflowState(prev => {
          if (prev.timeRemaining <= 1) {
            return {
              ...prev,
              isGenerating: false,
              isComplete: true,
              timeRemaining: 0,
              error: 'Workflow timed out after 5 minutes',
            };
          }
          return {
            ...prev,
            timeRemaining: prev.timeRemaining - 1,
          };
        });
      }, 1000);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [workflowState.isGenerating, workflowState.timeRemaining]);

  const handleSSEEvent = useCallback((event: SSEEvent) => {
    setWorkflowState(prev => {
      const newState = { ...prev };

      switch (event.type) {
        case 'iteration_start':
          // Find or create iteration
          let iteration = newState.iterations.find(i => i.id === event.iteration);
          if (!iteration) {
            iteration = {
              id: event.iteration,
              timestamp: event.timestamp,
            };
            newState.iterations = [...newState.iterations, iteration];
          }
          break;

        case 'image_generated':
          const imageIteration = newState.iterations.find(i => i.id === event.iteration);
          if (imageIteration) {
            const fullImageUrl = event.image_url.startsWith('http') 
              ? event.image_url 
              : `${API_URL}${event.image_url}`;
            imageIteration.imageUrl = fullImageUrl;
            newState.currentImage = fullImageUrl;
          }
          break;

        case 'ocr_complete':
          const ocrIteration = newState.iterations.find(i => i.id === event.iteration);
          if (ocrIteration) {
            ocrIteration.extractedText = event.ocr_result;
            ocrIteration.isMatch = event.match_status;
          }
          break;

        case 'reasoning':
          const reasoningIteration = newState.iterations.find(i => i.id === event.iteration);
          if (reasoningIteration) {
            reasoningIteration.feedback = event.message;
          }
          break;

        case 'workflow_complete':
          newState.isGenerating = false;
          newState.isComplete = true;
          const finalImageUrl = event.final_image_url 
            ? (event.final_image_url.startsWith('http') 
                ? event.final_image_url 
                : `${API_URL}${event.final_image_url}`)
            : undefined;
          newState.finalResult = {
            success: event.success,
            final_image_url: finalImageUrl,
            ocr_text: event.ocr_text,
            total_iterations: event.total_iterations,
          };
          if (finalImageUrl) {
            newState.currentImage = finalImageUrl;
          }
          break;

        case 'workflow_timeout':
          newState.isGenerating = false;
          newState.isComplete = true;
          newState.error = `Workflow timed out after ${event.total_iterations} iterations`;
          if (event.last_image_url) {
            const lastImageUrl = event.last_image_url.startsWith('http') 
              ? event.last_image_url 
              : `${API_URL}${event.last_image_url}`;
            newState.currentImage = lastImageUrl;
          }
          break;

        case 'workflow_error':
          newState.isGenerating = false;
          newState.isComplete = true;
          newState.error = event.error_message;
          break;

        case 'stream_end':
          // Stream ended, no action needed
          break;
      }

      return newState;
    });
  }, []);

  const startGeneration = useCallback(async (request: GenerateRequest) => {
    // Reset state
    setWorkflowState({
      isGenerating: true,
      iterations: [],
      isComplete: false,
      timeRemaining: TIMEOUT_DURATION,
      error: undefined,
      currentImage: undefined,
      finalResult: undefined,
    });

    abortControllerRef.current = new AbortController();

    try {
      for await (const event of ImageGenerationAPI.generateImage(request)) {
        if (abortControllerRef.current?.signal.aborted) {
          break;
        }
        
        handleSSEEvent(event);
      }
    } catch (error) {
      console.error('Error in image generation:', error);
      setWorkflowState(prev => ({
        ...prev,
        isGenerating: false,
        isComplete: true,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      }));
    }
  }, [handleSSEEvent]);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    setWorkflowState({
      isGenerating: false,
      iterations: [],
      isComplete: false,
      timeRemaining: TIMEOUT_DURATION,
      error: undefined,
      currentImage: undefined,
      finalResult: undefined,
    });
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    workflowState,
    startGeneration,
    reset,
  };
}