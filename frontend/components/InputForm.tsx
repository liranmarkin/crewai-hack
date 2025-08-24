import React, { useState, useEffect } from 'react';
import { Info, Play, Timer } from 'lucide-react';
import { GenerateRequest, WorkflowState } from '@/lib/types';

interface InputFormProps {
  onSubmit: (request: GenerateRequest) => void;
  workflowState: WorkflowState;
  onReset: () => void;
}

export function InputForm({ onSubmit, workflowState, onReset }: InputFormProps) {
  const [prompt, setPrompt] = useState('');
  const [isMounted, setIsMounted] = useState(false);
  
  // Find the extracted text position in the prompt
  const getHighlightedPrompt = () => {
    // Only highlight if we have both extracted text and current prompt, and we're currently generating
    if (!workflowState.extractedText || !prompt.trim() || !workflowState.isGenerating) {
      return { before: prompt, highlight: '', after: '' };
    }
    
    const extractedText = workflowState.extractedText.trim();
    if (!extractedText) {
      return { before: prompt, highlight: '', after: '' };
    }
    
    let startIndex = prompt.toLowerCase().indexOf(extractedText.toLowerCase());
    
    if (startIndex === -1) {
      // Try without quotes if they exist
      const textWithoutQuotes = extractedText.replace(/^["']|["']$/g, '').trim();
      if (textWithoutQuotes) {
        startIndex = prompt.toLowerCase().indexOf(textWithoutQuotes.toLowerCase());
        if (startIndex !== -1) {
          const endIndex = startIndex + textWithoutQuotes.length;
          return {
            before: prompt.substring(0, startIndex),
            highlight: prompt.substring(startIndex, endIndex),
            after: prompt.substring(endIndex)
          };
        }
      }
      
      console.warn(`Extracted text "${extractedText}" not found in prompt: "${prompt}"`);
      return { before: prompt, highlight: '', after: '' };
    }
    
    const endIndex = startIndex + extractedText.length;
    return {
      before: prompt.substring(0, startIndex),
      highlight: prompt.substring(startIndex, endIndex),
      after: prompt.substring(endIndex)
    };
  };
  
  const highlightedPrompt = getHighlightedPrompt();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim()) {
      onSubmit({
        prompt: prompt.trim(),
      });
    }
  };

  const handleReset = () => {
    setPrompt('');
    onReset();
  };
  
  // Clear highlighting if user changes prompt significantly
  useEffect(() => {
    if (workflowState.extractedText && prompt && !workflowState.isGenerating) {
      // If the extracted text is no longer in the current prompt, it's probably stale
      const extractedText = workflowState.extractedText.trim().toLowerCase();
      if (extractedText && !prompt.toLowerCase().includes(extractedText)) {
        console.log('Prompt changed significantly, extracted text may be stale');
      }
    }
  }, [prompt, workflowState.extractedText, workflowState.isGenerating]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const isFormValid = prompt.trim();

  return (
    <div className="p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'var(--font-space-grotesk)' }}>Input</h2>
      </div>

      <form onSubmit={handleSubmit} suppressHydrationWarning>
        <div className="mb-4">
          <label htmlFor="prompt" className="block font-medium mb-2 text-gray-900">
            Prompt
          </label>
          <div className="relative">
            {/* Highlight background - only show if there's text to highlight */}
            {highlightedPrompt.highlight && (
              <div 
                className="absolute inset-0 w-full rounded-md p-3 min-h-[100px] pointer-events-none whitespace-pre-wrap break-words text-transparent overflow-hidden"
                style={{ 
                  font: 'inherit',
                  fontSize: 'inherit',
                  fontFamily: 'inherit',
                  lineHeight: 'inherit',
                  letterSpacing: 'inherit',
                  wordSpacing: 'inherit'
                }}
              >
                <span>{highlightedPrompt.before}</span>
                <span className="bg-blue-100 rounded">{highlightedPrompt.highlight}</span>
                <span>{highlightedPrompt.after}</span>
              </div>
            )}
            {/* Actual textarea */}
            <textarea
              id="prompt"
              className="relative w-full border border-gray-300 rounded-md p-3 min-h-[100px] resize-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 bg-transparent"
              placeholder="A poster with bold text..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={workflowState.isGenerating}
              suppressHydrationWarning
            />
          </div>
        </div>


        <div className="flex justify-between">
          <button
            type="button"
            onClick={handleReset}
            className="px-4 py-2 border border-blue-600 rounded-md bg-white text-blue-600 hover:bg-blue-50 disabled:opacity-50"
            disabled={workflowState.isGenerating}
          >
            Reset
          </button>
          
          <button
            type="submit"
            className={`px-4 py-2 rounded-md text-white flex items-center disabled:opacity-50 ${
              workflowState.isGenerating || !isFormValid 
                ? 'bg-gray-600 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
            disabled={workflowState.isGenerating || !isFormValid}
          >
            {workflowState.isGenerating ? (
              <>
                <Timer className="w-4 h-4 mr-2" />
                <span>{formatTime(workflowState.timeRemaining)}</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                <span>Generate</span>
              </>
            )}
          </button>
        </div>
      </form>

      {workflowState.error && (
        <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md">
          {workflowState.error}
        </div>
      )}
    </div>
  );
}