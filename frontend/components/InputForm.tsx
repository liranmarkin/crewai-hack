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
  const [intendedText, setIntendedText] = useState('');
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && intendedText.trim()) {
      onSubmit({
        prompt: prompt.trim(),
        intended_text: intendedText.trim(),
      });
    }
  };

  const handleReset = () => {
    setPrompt('');
    setIntendedText('');
    onReset();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const isFormValid = prompt.trim() && intendedText.trim();

  return (
    <div className="p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold">Input</h2>
      </div>

      <form onSubmit={handleSubmit} suppressHydrationWarning>
        <div className="mb-4">
          <div className="flex items-center mb-2">
            <label htmlFor="prompt" className="font-medium text-gray-700">
              Prompt
            </label>
            <Info className="w-4 h-4 text-gray-400 ml-1" />
          </div>
          <textarea
            id="prompt"
            className="w-full border border-gray-300 rounded-md p-3 min-h-[100px] focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            placeholder="Describe the image you want to generate..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={workflowState.isGenerating}
            suppressHydrationWarning
          />
        </div>

        <div className="mb-6">
          <label
            htmlFor="intendedText"
            className="block font-medium text-gray-700 mb-2"
          >
            Intended Text
          </label>
          <input
            id="intendedText"
            type="text"
            className="w-full border border-gray-300 rounded-md p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Text that should appear in the image..."
            value={intendedText}
            onChange={(e) => setIntendedText(e.target.value)}
            disabled={workflowState.isGenerating}
            suppressHydrationWarning
          />
        </div>

        <div className="flex justify-between">
          <button
            type="button"
            onClick={handleReset}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            disabled={workflowState.isGenerating}
          >
            Reset
          </button>
          
          <button
            type="submit"
            className={`px-4 py-2 rounded-md text-white flex items-center ${
              workflowState.isGenerating || !isFormValid
                ? 'bg-gray-400 cursor-not-allowed' 
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
                <span>Run</span>
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