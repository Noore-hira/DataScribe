import { useEffect, useRef, useState } from 'react';
import { checkBackendHealth, type BackendHealth } from '@/services/api';

const POLL_INTERVAL = 15000;

export function useConnectionStatus(backendUrl?: string | null): BackendHealth & { checking: boolean } {
  const [health, setHealth] = useState<BackendHealth>({ online: false, checkedAt: 0 });
  const [checking, setChecking] = useState(false);
  const urlRef = useRef(backendUrl);
  urlRef.current = backendUrl;

  useEffect(() => {
    let cancelled = false;

    const tick = async () => {
      setChecking(true);
      const result = await checkBackendHealth(urlRef.current);
      if (!cancelled) {
        setHealth(result);
        setChecking(false);
      }
    };

    tick();
    const interval = window.setInterval(tick, POLL_INTERVAL);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  return { ...health, checking };
}
