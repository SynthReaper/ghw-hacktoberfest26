import * as Sentry from '@sentry/node';

let isInitialized = false;

export function initSentry() {
  if (isInitialized) return;

  const dsn = process.env.SENTRY_DSN || 'https://fakePublicHex@o0.ingest.sentry.io/0';
  const environment = process.env.SENTRY_ENVIRONMENT || 'development';
  const tracesSampleRate = parseFloat(process.env.SENTRY_TRACES_SAMPLE_RATE || '1.0');

  try {
    Sentry.init({
      dsn,
      environment,
      tracesSampleRate,
      integrations: [
        Sentry.onUncaughtExceptionIntegration(),
        Sentry.onUnhandledRejectionIntegration(),
      ],
    });
    isInitialized = true;
    console.log('[Sentry] NecroGit Agent Tracing & Spans initialized.');
  } catch (err: any) {
    console.warn('[Sentry] Failed to initialize Sentry:', err.message);
  }
}

export async function withSpan<T>(
  name: string,
  op: string,
  fn: () => Promise<T>,
  data?: Record<string, any>
): Promise<T> {
  initSentry();
  const startTime = Date.now();
  console.log(`[Trace] 🕯️ Starting séance span: [${op}] ${name}`);

  try {
    const result = await fn();
    const duration = Date.now() - startTime;
    console.log(`[Trace] ⚰️ Completed span: [${op}] ${name} (${duration}ms)`);
    return result;
  } catch (err: any) {
    console.error(`[Trace] 💀 Error in span [${op}] ${name}:`, err.message);
    Sentry.captureException(err, { extra: { spanName: name, spanOp: op, ...data } });
    throw err;
  }
}
