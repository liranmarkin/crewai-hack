import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { CheckCircle, XCircle, ChevronRight, ChevronDown } from 'lucide-react';
import { Iteration } from '@/lib/types';

interface IterationHistoryProps {
  iterations: Iteration[];
}

export function IterationHistory({ iterations }: IterationHistoryProps) {
  const [expandedIterations, setExpandedIterations] = useState<number[]>([]);

  // Auto-expand new iterations
  useEffect(() => {
    if (iterations.length > 0) {
      const allIterationIds = iterations.map(iteration => iteration.id);
      setExpandedIterations(allIterationIds);
    }
  }, [iterations]);

  const toggleExpand = (iterationId: number) => {
    setExpandedIterations(prev =>
      prev.includes(iterationId)
        ? prev.filter(id => id !== iterationId)
        : [...prev, iterationId]
    );
  };

  if (iterations.length === 0) {
    return (
      <div className="text-center py-8">
        <h2 className="text-lg font-semibold mb-2">Iterations</h2>
        <p className="text-gray-500">
          No iterations yet. Start by running your prompt.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-semibold mb-6">Iterations</h2>
      <div className="space-y-8">
        {iterations.map((iteration, index) => {
          const isExpanded = expandedIterations.includes(iteration.id);
          const isLastIteration = index === iterations.length - 1;

          return (
            <div key={iteration.id} className="relative">
              <div className="flex items-start">
                {/* Iteration number badge */}
                <div className="flex-shrink-0 mr-4">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      iteration.isMatch === true
                        ? 'bg-green-100 text-green-600'
                        : iteration.isMatch === false
                        ? 'bg-red-100 text-red-600'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    #{iteration.id}
                  </div>
                </div>

                <div className="flex-1">
                  <div className="flex items-start gap-6">
                    {/* Image thumbnail */}
                    <div className="flex-shrink-0">
                      <div className="border border-gray-200 rounded-md overflow-hidden w-48 h-36 bg-gray-50">
                        {iteration.imageUrl ? (
                          <Image
                            src={iteration.imageUrl}
                            alt={`Iteration ${iteration.id}`}
                            width={192}
                            height={144}
                            className="w-full h-full object-cover"
                            unoptimized
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-gray-400">
                            Loading...
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Details */}
                    <div className="flex-1">
                      <div className="bg-gray-50 p-4 rounded-md">
                        <button
                          onClick={() => toggleExpand(iteration.id)}
                          className="flex items-center mb-2 hover:bg-gray-100 p-1 rounded-md w-full text-left transition-colors"
                        >
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 mr-2 text-gray-500" />
                          ) : (
                            <ChevronRight className="w-4 h-4 mr-2 text-gray-500" />
                          )}
                          <div className="flex items-center">
                            {iteration.isMatch === true ? (
                              <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                            ) : iteration.isMatch === false ? (
                              <XCircle className="w-5 h-5 text-red-500 mr-2" />
                            ) : (
                              <div className="w-5 h-5 bg-gray-300 rounded-full mr-2 animate-pulse" />
                            )}
                            <p
                              className={`font-medium ${
                                iteration.isMatch === true
                                  ? 'text-green-600'
                                  : iteration.isMatch === false
                                  ? 'text-red-600'
                                  : 'text-gray-600'
                              }`}
                            >
                              {iteration.isMatch === true
                                ? 'Success'
                                : iteration.isMatch === false
                                ? 'Mismatch'
                                : 'Processing...'}
                            </p>
                          </div>
                        </button>

                        {isExpanded && (
                          <div className="ml-6 space-y-3">
                            {iteration.prompt && (
                              <div className="bg-blue-50 p-3 rounded-md">
                                <p className="text-sm text-gray-600">
                                  <span className="font-medium text-blue-800">Image Prompt:</span>
                                </p>
                                <p className="text-sm text-blue-700 mt-1">
                                  {iteration.prompt}
                                </p>
                              </div>
                            )}
                            {iteration.extractedText && (
                              <div className="bg-gray-50 p-3 rounded-md">
                                <p className="text-sm text-gray-600">
                                  <span className="font-medium text-gray-800">OCR Result:</span>
                                </p>
                                <p className="text-sm text-gray-700 mt-1">
                                  &quot;{iteration.extractedText}&quot;
                                </p>
                              </div>
                            )}
                            {iteration.feedback && (
                              <div className="bg-gray-50 p-3 rounded-md">
                                <p className="text-sm text-gray-600">
                                  <span className="font-medium text-gray-800">Reasoning:</span>
                                </p>
                                <p className="text-sm text-gray-700 mt-1">
                                  {iteration.feedback}
                                </p>
                              </div>
                            )}
                            <p className="text-xs text-gray-400">
                              {new Date(iteration.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Timeline connector */}
              {!isLastIteration && (
                <div className="absolute left-4 top-16 bottom-0 w-px bg-gray-200 -mb-4" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}