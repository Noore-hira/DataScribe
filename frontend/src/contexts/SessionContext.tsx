// @refresh reset
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { v4 as uuidv4 } from "uuid";
import type { DatasetMeta } from "@/types";

interface SessionContextValue {
  dataset: DatasetMeta | null;
  threadId: string;
  setDataset: (dataset: DatasetMeta | null) => void;
  setThreadId: (threadId: string) => void;
  startNewSession: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [dataset, setDataset] = useState<DatasetMeta | null>(null);
  const [threadId, setThreadId] = useState<string>(() => uuidv4());

  const startNewSession = useCallback(() => {
    setDataset(null);
    setThreadId(uuidv4());
  }, []);

  const value = useMemo(
    () => ({
      dataset,
      threadId,
      setDataset,
      setThreadId,
      startNewSession,
    }),
    [dataset, threadId, startNewSession]
  );

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);

  if (!ctx) {
    throw new Error("useSession must be used within SessionProvider");
  }

  return ctx;
}