import { SSE_RECONNECT_DELAYS, type SSEEvent, type NodeName } from '@/types';
import { resolveBaseUrl } from './api';

export interface StreamHandlers {
  onEvent: (event: SSEEvent) => void;
  onOpen?: () => void;
  onError?: (error: Event, willRetry: boolean, attempt: number) => void;
  onClose?: () => void;
}

export interface StreamController {
  close: () => void;
}

function isKnownNode(v: unknown): v is NodeName {
  return typeof v === 'string' && [
    'conversation', 'initialize', 'supervisor', 'planner',
    'programmer', 'executor', 'critic', 'reporter',
  ].includes(v);
}

function parseEvent(rawEvent: string, rawData: string): SSEEvent | null {
  const data = rawData.trim();
  if (!data) return null;
  let payload: Record<string, unknown>;
  try {
    payload = JSON.parse(data) as Record<string, unknown>;
  } catch {
    return null;
  }

  const node = isKnownNode(payload.node) ? payload.node : undefined;

  switch (rawEvent) {
    case 'node_start':
      if (!node) return null;
      return {
        event: 'node_start',
        node,
        progress: Number(payload.progress ?? 0),
        message: String(payload.message ?? ''),
        timestamp: String(payload.timestamp ?? new Date().toISOString()),
      };
    case 'node_end':
      if (!node) return null;
      return {
        event: 'node_end',
        node,
        metrics: (payload.metrics ?? {}) as Record<string, unknown>,
        progress: Number(payload.progress ?? 0),
        message: String(payload.message ?? ''),
        timestamp: String(payload.timestamp ?? new Date().toISOString()),
      };
    case 'decision':
      return { event: 'decision', decision: String(payload.decision ?? '') };
    case 'plan':
      return { event: 'plan', plan: String(payload.plan ?? '') };
    case 'retry':
      return {
        event: 'retry',
        retry_count: Number(payload.retry_count ?? 0),
        next_node: isKnownNode(payload.next_node) ? payload.next_node : 'programmer',
        message: String(payload.message ?? ''),
      };
    case 'warning':
      return {
        event: 'warning',
        message: String(payload.message ?? ''),
        node: isKnownNode(payload.node) ? payload.node : undefined,
      };
    case 'code':
      return {
        event: 'code',
        code: String(payload.code ?? ''),
      };
    case 'execution':
      return {
        event: 'execution',
        output: String(payload.output ?? ''),
      };
    case 'charts':
      return {
        event: 'charts',
        charts: Array.isArray(payload.charts) ? payload.charts.map(String) : [],
      };
    case 'critic':
      return {
        event: 'critic',
        verdict: String(payload.verdict ?? ''),
        retry: Number(payload.retry ?? 0),
      };
    case 'report':
      return {
        event: 'report',
        report: String(payload.report ?? ''),
        charts: Array.isArray(payload.charts) ? payload.charts.map(String) : [],
      };
    case 'message':
      return {
        event: 'message',
        content: String(payload.content ?? payload.message ?? ''),
      };
    case 'text':
      return {
        event: 'text',
        content: String(payload.content ?? payload.message ?? ''),
      };
    // 🛠️ ADDED: Parse the new live token stream
    case 'token':
      return {
        event: 'token',
        content: String(payload.content ?? ''),
      };
    case 'error':
      return {
        event: 'error',
        message: String(payload.message ?? 'Unknown error'),
        node: isKnownNode(payload.node) ? payload.node : undefined,
      };
    case 'complete':
      return { event: 'complete', duration: Number(payload.duration ?? 0) };
    default:
      // Some servers send unnamed data events; ignore unless it parses as a known event.
      if (typeof payload.event === 'string') {
        return parseEvent(payload.event as string, data);
      }
      return null;
  }
}

/**
 * Opens an SSE connection to /api/chat/stream.
 * Automatically reconnects with backoff up to SSE_RECONNECT_DELAYS.length attempts.
 */
export function streamChat(
  params: { message: string; threadId: string; apiKey?: string; model?: string; datasetPath?: string },
  handlers: StreamHandlers,
  options?: { baseUrl?: string | null; signal?: AbortSignal }
): StreamController {
  let attempt = 0;
  let closedByUser = false;
  let es: EventSource | null = null;
  const abortSignal = options?.signal;
  const baseUrl = resolveBaseUrl(options?.baseUrl);

  const buildUrl = (): string => {
    const q = new URLSearchParams({
      message: params.message,
      thread_id: params.threadId,
    });
    if (params.apiKey) q.set('api_key', params.apiKey);
    if (params.model) q.set('model', params.model);
    if (params.datasetPath) q.set('dataset_path', params.datasetPath);
    return `${baseUrl}/api/chat/stream?${q.toString()}`;
  };

  const open = () => {
    if (closedByUser || abortSignal?.aborted) return;
    es = new EventSource(buildUrl());

    es.onopen = () => {
      attempt = 0;
      handlers.onOpen?.();
    };

    es.addEventListener('node_start', (e: MessageEvent) => {
      const parsed = parseEvent('node_start', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('node_end', (e: MessageEvent) => {
      const parsed = parseEvent('node_end', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('decision', (e: MessageEvent) => {
      const parsed = parseEvent('decision', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('plan', (e: MessageEvent) => {
      const parsed = parseEvent('plan', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('retry', (e: MessageEvent) => {
      const parsed = parseEvent('retry', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('warning', (e: MessageEvent) => {
      const parsed = parseEvent('warning', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('code', (e: MessageEvent) => {
      const parsed = parseEvent('code', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('execution', (e: MessageEvent) => {
      const parsed = parseEvent('execution', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('charts', (e: MessageEvent) => {
      const parsed = parseEvent('charts', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('critic', (e: MessageEvent) => {
      const parsed = parseEvent('critic', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('report', (e: MessageEvent) => {
      const parsed = parseEvent('report', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('message', (e: MessageEvent) => {
      const parsed = parseEvent('message', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('text', (e: MessageEvent) => {
      const parsed = parseEvent('text', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    // 🛠️ ADDED: Listen for the backend's token event
    es.addEventListener('token', (e: MessageEvent) => {
      const parsed = parseEvent('token', e.data);
      if (parsed) handlers.onEvent(parsed);
    });
    es.addEventListener('error', (e: MessageEvent) => {
      const parsed = parseEvent('error', e.data);
      if (parsed) handlers.onEvent(parsed);
      // 'error' SSE event from server: backend said something went wrong
      close();
    });

    // The SSE "complete" event signals the workflow finished.
    es.addEventListener('complete', (e: MessageEvent) => {
      const parsed = parseEvent('complete', e.data);
      if (parsed) handlers.onEvent(parsed);
      close();
      return;
    });

    // Native onerror — network-level failure (disconnect, server down).
    es.onerror = (err) => {
      es?.close();
      es = null;
      if (closedByUser) return;
      if (attempt < SSE_RECONNECT_DELAYS.length) {
        const delay = SSE_RECONNECT_DELAYS[attempt];
        attempt += 1;
        handlers.onError?.(err, true, attempt);
        setTimeout(open, delay);
      } else {
        handlers.onError?.(err, false, attempt);
        handlers.onClose?.();
      }
    };
  };

  const close = () => {
    closedByUser = true;
    es?.close();
    es = null;
    handlers.onClose?.();
  };

  if (abortSignal) {
    abortSignal.addEventListener('abort', close, { once: true });
  }

  open();

  return { close };
}