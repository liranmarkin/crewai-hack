export interface GenerateRequest {
  prompt: string;
}

export type SSEEventType = 
  | 'text_extraction'
  | 'iteration_start'
  | 'image_generated'
  | 'analysis'
  | 'workflow_complete'
  | 'workflow_timeout'
  | 'workflow_error'
  | 'stream_end';

export interface BaseSSEEvent {
  type: SSEEventType;
  timestamp: string;
}

export interface TextExtractionEvent extends BaseSSEEvent {
  type: 'text_extraction';
  extracted_text: string | null;
  has_intended_text: boolean;
}

export interface IterationStartEvent extends BaseSSEEvent {
  type: 'iteration_start';
  iteration: number;
  prompt: string;
}

export interface ImageGeneratedEvent extends BaseSSEEvent {
  type: 'image_generated';
  iteration: number;
  image_url: string;
}

export interface AnalysisEvent extends BaseSSEEvent {
  type: 'analysis';
  iteration: number;
  ocr_result: string;
  match_status: boolean;
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
  | TextExtractionEvent
  | IterationStartEvent
  | ImageGeneratedEvent
  | AnalysisEvent
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
  prompt?: string;
  timestamp: string;
}

export interface WorkflowState {
  isGenerating: boolean;
  iterations: Iteration[];
  currentImage?: string;
  isComplete: boolean;
  timeRemaining: number;
  error?: string;
  extractedText?: string;
  finalResult?: {
    success: boolean;
    final_image_url?: string;
    ocr_text?: string;
    total_iterations: number;
  };
}