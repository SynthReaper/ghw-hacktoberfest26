/**
 * Sentry Distributed Agent Tracing & Telemetry
 * Captures spans for Browserbase navigation, Gemma local OCR/extraction, and TabPFN inference.
 */

import * as Sentry from '@sentry/node';

let isInitialized = false;

export function initSentry() {
  if (isInitialized) return;

  const dsn = process.env.SENTRY_DSN || 'https://fakePublicKey@o0.ingest.sentry.io/0';
  const environment = process.env.SENTRY_ENVIRONMENT || 'development';

  try {
    Sentry.init({
      dsn,
      environment,
      tracesSampleRate: 1.0,
      integrations: [],
    });
    isInitialized = true;
    console.log('[Sentry] Agent Tracing initialized successfully.');
  } catch (err) {
    console.warn('[Sentry] Warning: Sentry initialized in simulation mode:', err);
  }
}

export async function traceSpan<T>(
  name: string,
  op: string,
  fn: () => Promise<T>,
  data?: Record<string, any>
): Promise<T> {
  initSentry();
  const startTime = Date.now();
  console.log(`[Trace] Starting span: [${op}] ${name}`);
  
  try {
    const result = await fn();
    const durationMs = Date.now() - startTime;
    console.log(`[Trace] Completed span: [${op}] ${name} (${durationMs}ms)`);
    
    // Record span metric to Sentry
    Sentry.captureMessage(`[Span] ${name} (${op}) completed in ${durationMs}ms`, {
      level: 'info',
      extra: {
        op,
        durationMs,
        ...data,
      },
    });
    
    return result;
  } catch (error: any) {
    const durationMs = Date.now() - startTime;
    console.error(`[Trace] Failed span: [${op}] ${name} after ${durationMs}ms:`, error.message);
    Sentry.captureException(error, {
      extra: {
        op,
        durationMs,
        ...data,
      },
    });
    throw error;
  }
}
