'use client';

import { InputForm } from '@/components/InputForm';
import { ResultDisplay } from '@/components/ResultDisplay';
import { IterationHistory } from '@/components/IterationHistory';
import { useImageGeneration } from '@/hooks/useImageGeneration';

export default function Home() {
  const { workflowState, startGeneration, reset } = useImageGeneration();

  return (
    <div className="flex flex-col w-full min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <img 
              src="/logo.png" 
              alt="CaptionCrew Logo" 
              className="w-8 h-8 mr-3"
            />
            <h1 className="text-2xl font-semibold text-gray-900" style={{ fontFamily: 'var(--font-space-grotesk)' }}>
              CaptionCrew
            </h1>
          </div>
          <div className="text-sm text-gray-500 italic">
            Text on images, always right ✨
          </div>
        </div>
      </header>

      <main className="flex flex-col flex-1 p-4 gap-6">
        <div className="max-w-7xl mx-auto w-full space-y-6">
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
        </div>
      </main>
    </div>
  );
}
