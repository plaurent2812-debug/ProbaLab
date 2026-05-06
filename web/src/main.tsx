import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { validateEnv } from './env';
import './styles/globals.css';

// Fail fast at boot if env vars are missing or malformed.
validateEnv();

createRoot(document.getElementById('root') as HTMLElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);
