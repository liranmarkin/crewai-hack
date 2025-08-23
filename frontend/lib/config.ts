const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const API_URL = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl;