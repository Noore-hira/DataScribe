import { DEFAULT_BACKEND_URL } from '@/types';
import type { DatasetMeta } from '@/types';

export interface UploadResponse {
  filename: string;
  rows: number;
  columns: number;
  thread_id: string;
  path: string;
}

export interface BackendHealth {
  online: boolean;
  latencyMs?: number;
  checkedAt: number;
}

function resolveBaseUrl(override?: string | null): string {
  const v = (override ?? '').trim();
  return v.length > 0 ? v.replace(/\/$/, '') : DEFAULT_BACKEND_URL;
}

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function parseJsonSafely(res: Response): Promise<Record<string, unknown>> {
  const text = await res.text();

  if (!text) return {};

  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

export async function checkBackendHealth(
  baseUrl?: string | null
): Promise<BackendHealth> {
  const url = `${resolveBaseUrl(baseUrl)}/api/health`;

  const checkedAt = Date.now();

  const controller = new AbortController();

  const timer = setTimeout(() => controller.abort(), 4000);

  try {
    const res = await fetch(url, {
      method: 'GET',
      signal: controller.signal,
    });

    clearTimeout(timer);

    if (res.ok) {
      return {
        online: true,
        latencyMs: Date.now() - checkedAt,
        checkedAt,
      };
    }

    return {
      online: false,
      checkedAt,
    };
  } catch {
    clearTimeout(timer);

    return {
      online: false,
      checkedAt,
    };
  }
}

export async function uploadDataset(
  file: File,
  baseUrl?: string |null,
  onProgress?: (percent: number) => void
): Promise<DatasetMeta> {
  const url = `${resolveBaseUrl(baseUrl)}/api/upload`;

  const formData = new FormData();
  formData.append('file', file);

  return new Promise<DatasetMeta>((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.open('POST', url, true);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText) as UploadResponse;

          resolve({
            filename: data.filename,
            rows: Number(data.rows) || 0,
            columns: Number(data.columns) || 0,
            threadId: data.thread_id,
            uploadedAt: Date.now(),
            path: data.path,
          });
        } catch {
          reject(new ApiError('Invalid upload response.'));
        }
      } else {
        reject(new ApiError(`Upload failed (${xhr.status})`, xhr.status));
      }
    };

    xhr.onerror = () =>
      reject(new ApiError('Network error during upload.'));

    xhr.ontimeout = () =>
      reject(new ApiError('Upload timed out.'));

    xhr.timeout = 120000;

    xhr.send(formData);
  });
}

/*
 * History has been removed.
 * Conversation memory now lives entirely inside
 * LangGraph MemorySaver and disappears when the backend restarts.
 */

export { resolveBaseUrl };