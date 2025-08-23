import React from 'react';
import { CheckCircle, Loader2 } from 'lucide-react';
import { WorkflowState } from '@/lib/types';

interface ResultDisplayProps {
  workflowState: WorkflowState;
}

export function ResultDisplay({ workflowState }: ResultDisplayProps) {
  const { currentImage, isGenerating, isComplete, finalResult } = workflowState;
  
  const getStatusText = () => {
    if (isGenerating) return 'Generating';
    if (isComplete && finalResult?.success) return 'Success';
    if (isComplete && !finalResult?.success) return 'Timeout';
    return 'Idle';
  };

  const getStatusColor = () => {
    if (isGenerating) return 'bg-blue-100 text-blue-600';
    if (isComplete && finalResult?.success) return 'bg-green-100 text-green-600';
    if (isComplete && !finalResult?.success) return 'bg-yellow-100 text-yellow-600';
    return 'bg-gray-100 text-gray-600';
  };

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Result</h2>
        <div className={`text-sm px-3 py-1 rounded-md ${getStatusColor()}`}>
          {getStatusText()}
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center border border-gray-200 rounded-lg overflow-hidden bg-gray-50 relative">
        {!currentImage && !isGenerating && (
          <div className="text-center p-6">
            <p className="text-gray-500 mb-2">No image generated yet</p>
            <p className="text-sm text-gray-400">
              Enter a prompt and click Run to start
            </p>
          </div>
        )}

        {isGenerating && !currentImage && (
          <div className="text-center p-6">
            <Loader2 className="w-10 h-10 text-blue-500 animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Generating image...</p>
          </div>
        )}

        {currentImage && (
          <>
            <img
              src={currentImage}
              alt="Generated result"
              className="max-w-full max-h-[400px] object-contain"
            />
            
            {isComplete && finalResult?.success && (
              <div className="absolute top-2 right-2 bg-green-100 text-green-800 px-3 py-1 rounded-full flex items-center text-sm">
                <CheckCircle className="w-4 h-4 mr-1" />
                Success
              </div>
            )}
            
            {isComplete && !finalResult?.success && (
              <div className="absolute top-2 right-2 bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full flex items-center text-sm">
                Timeout
              </div>
            )}
          </>
        )}
      </div>

      {currentImage && finalResult && (
        <div className="mt-4 text-sm text-gray-500">
          <p>
            Completed in {finalResult.total_iterations} iteration{finalResult.total_iterations !== 1 ? 's' : ''}
            {finalResult.success && finalResult.ocr_text && (
              <>
                {' '}with text: "{finalResult.ocr_text}"
              </>
            )}
          </p>
        </div>
      )}
    </div>
  );
}