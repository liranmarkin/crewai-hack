import { API_URL } from './config';
import { GenerateRequest, SSEEvent } from './types';

export class ImageGenerationAPI {
  static async* generateImage(request: GenerateRequest): AsyncGenerator<SSEEvent> {
    const response = await fetch(`${API_URL}/api/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const eventData: SSEEvent = JSON.parse(line.slice(6));
              yield eventData;
            } catch (error) {
              console.error('Error parsing SSE event:', error);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  static getImageUrl(imageId: string): string {
    return `${API_URL}/api/images/${imageId}`;
  }
}