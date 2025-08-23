export interface GenerateRequest {
  prompt: string;
  intended_text: string;
}

export type SSEEventType = 
  | 'iteration_start'
  | 'image_generated'
  | 'ocr_complete'
  | 'reasoning'
  | 'workflow_complete'
  | 'workflow_timeout'
  | 'workflow_error'
  | 'stream_end';

export interface BaseSSEEvent {
  type: SSEEventType;
  timestamp: string;
}

export interface IterationStartEvent extends BaseSSEEvent {
  type: 'iteration_start';
  iteration: number;
}

export interface ImageGeneratedEvent extends BaseSSEEvent {
  type: 'image_generated';
  iteration: number;
  image_url: string;
}

export interface OCRCompleteEvent extends BaseSSEEvent {
  type: 'ocr_complete';
  iteration: number;
  ocr_result: string;
  match_status: boolean;
}

export interface ReasoningEvent extends BaseSSEEvent {
  type: 'reasoning';
  iteration: number;
  message: string;
}

export interface WorkflowCompleteEvent extends BaseSSEEvent {
  type: 'workflow_complete';
  success: boolean;
  final_image_url?: string;
  ocr_text?: string;
  total_iterations: number;
}

export interface WorkflowTimeoutEvent extends BaseSSEEvent {
  type: 'workflow_timeout';
  total_iterations: number;
  last_image_url?: string;
}

export interface WorkflowErrorEvent extends BaseSSEEvent {
  type: 'workflow_error';
  error_message: string;
  iteration?: number;
}

export interface StreamEndEvent extends BaseSSEEvent {
  type: 'stream_end';
}

export type SSEEvent = 
  | IterationStartEvent
  | ImageGeneratedEvent
  | OCRCompleteEvent
  | ReasoningEvent
  | WorkflowCompleteEvent
  | WorkflowTimeoutEvent
  | WorkflowErrorEvent
  | StreamEndEvent;

export interface Iteration {
  id: number;
  imageUrl?: string;
  extractedText?: string;
  isMatch?: boolean;
  feedback?: string;
  timestamp: string;
}

export interface WorkflowState {
  isGenerating: boolean;
  iterations: Iteration[];
  currentImage?: string;
  isComplete: boolean;
  timeRemaining: number;
  error?: string;
  finalResult?: {
    success: boolean;
    final_image_url?: string;
    ocr_text?: string;
    total_iterations: number;
  };
}