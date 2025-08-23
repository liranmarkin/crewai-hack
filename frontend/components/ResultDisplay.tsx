import React from 'react';
import Image from 'next/image';
import { CheckCircle, Loader2 } from 'lucide-react';
import { WorkflowState } from '@/lib/types';

interface ResultDisplayProps {
  workflowState: WorkflowState;
}

export function ResultDisplay({ workflowState }: ResultDisplayProps) {
  const { currentImage, isGenerating, isComplete, finalResult } = workflowState;
  
  const getStatusText = () => {
    if (isGenerating) return 'Generating image...';
    if (isComplete && finalResult?.success) return 'Matched';
    if (isComplete && !finalResult?.success) return 'Timeout';
    return 'Ready';
  };

  const getStatusColor = () => {
    if (isGenerating) return 'bg-blue-600 text-white';
    if (isComplete && finalResult?.success) return 'bg-green-600 text-white';
    if (isComplete && !finalResult?.success) return 'bg-red-600 text-white';
    return 'bg-gray-600 text-white';
  };

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-900" style={{ fontFamily: 'var(--font-space-grotesk)' }}>Result</h2>
        <div className={`text-sm px-3 py-1 rounded-md ${getStatusColor()}`}>
          {getStatusText()}
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center border border-gray-200 rounded-lg overflow-hidden bg-gray-50 relative">
        {!currentImage && !isGenerating && (
          <div className="text-center p-6">
            <p className="mb-2 text-gray-600">No image yet</p>
            <p className="text-sm text-gray-600">
              Enter a prompt and click Generate
            </p>
          </div>
        )}

        {isGenerating && !currentImage && (
          <div className="text-center p-6">
            <Loader2 className="w-10 h-10 text-blue-600 animate-spin mx-auto mb-4" />
            <p className="text-gray-900">Generating image...</p>
          </div>
        )}

        {currentImage && (
          <>
            <Image
              src={currentImage}
              alt="Generated result"
              width={400}
              height={400}
              className="max-w-full max-h-[400px] object-contain"
              unoptimized
            />
            
          </>
        )}
      </div>

      {currentImage && finalResult && (
        <div className="mt-4 text-sm text-gray-500">
          <p>
            Completed in {finalResult.total_iterations} iteration{finalResult.total_iterations !== 1 ? 's' : ''}
            {finalResult.success && finalResult.ocr_text && (
              <>
                {' '}with text: &quot;{finalResult.ocr_text}&quot;
              </>
            )}
          </p>
        </div>
      )}
    </div>
  );
}