'use client';

import { InputForm } from '@/components/InputForm';
import { ResultDisplay } from '@/components/ResultDisplay';
import { IterationHistory } from '@/components/IterationHistory';
import { useImageGeneration } from '@/hooks/useImageGeneration';

export default function Home() {
  const { workflowState, startGeneration, reset } = useImageGeneration();

  return (
    <div className="flex flex-col w-full min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 p-4">
        <h1 className="text-xl font-bold text-gray-800">
          Text-to-Image with OCR Verification
        </h1>
      </header>

      <main className="flex flex-col flex-1 p-4 gap-6">
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="w-full lg:w-1/2 bg-white rounded-lg shadow-sm border border-gray-200">
            <InputForm
              onSubmit={startGeneration}
              workflowState={workflowState}
              onReset={reset}
            />
          </div>
          <div className="w-full lg:w-1/2 bg-white rounded-lg shadow-sm border border-gray-200">
            <ResultDisplay workflowState={workflowState} />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <IterationHistory iterations={workflowState.iterations} />
        </div>
      </main>
    </div>
  );
}
