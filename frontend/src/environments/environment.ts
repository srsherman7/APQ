// Development environment configuration
// API base URL is injected at serve-time via the --define flag in start.ps1.
// Falls back to localhost for direct `npm start` usage.
declare const __API_BASE_URL__: string;
export const environment = {
  production: false,
  apiBaseUrl: (typeof __API_BASE_URL__ !== 'undefined' ? __API_BASE_URL__ : 'http://localhost:5000') + '/api'
};
