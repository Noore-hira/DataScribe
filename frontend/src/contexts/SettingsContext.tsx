import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  DEFAULT_BACKEND_URL,
  GROQ_MODELS,
  type GroqModel,
} from "@/types";

type Theme = "dark" | "light";

interface SettingsState {
  apiKey: string;
  model: GroqModel;
  backendUrl: string;
  theme: Theme;
}

interface SettingsContextValue extends SettingsState {
  setApiKey: (value: string) => void;
  setModel: (value: GroqModel) => void;
  setBackendUrl: (value: string) => void;
  setTheme: (value: Theme) => void;
  toggleTheme: () => void;
  resetSession: () => void;
}

const DEFAULTS: SettingsState = {
  apiKey: "",
  model: "llama-3.3-70b-versatile",
  backendUrl: DEFAULT_BACKEND_URL,
  theme: "dark",
};

function load(): SettingsState {
  if (typeof window === "undefined") {
    return DEFAULTS;
  }

  const storedApiKey = sessionStorage.getItem("groq_api_key") ?? "";

  const storedModel = sessionStorage.getItem("groq_model");

  const validModel = GROQ_MODELS.some(
    (m) => m.value === storedModel
  )
    ? (storedModel as GroqModel)
    : DEFAULTS.model;

  return {
    apiKey: storedApiKey,
    model: validModel,
    backendUrl: DEFAULT_BACKEND_URL,
    theme: DEFAULTS.theme,
  };
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

export function SettingsProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [state, setState] = useState<SettingsState>(load);

  useEffect(() => {
    sessionStorage.setItem("groq_api_key", state.apiKey);
  }, [state.apiKey]);

  useEffect(() => {
    sessionStorage.setItem("groq_model", state.model);
  }, [state.model]);

  useEffect(() => {
    document.documentElement.classList.remove("dark", "light");
    document.documentElement.classList.add(state.theme);
  }, [state.theme]);

  const setApiKey = useCallback((value: string) => {
    setState((prev) => ({
      ...prev,
      apiKey: value,
    }));
  }, []);

  const setModel = useCallback((value: GroqModel) => {
    setState((prev) => ({
      ...prev,
      model: value,
    }));
  }, []);

  // Backend URL is fixed.
  const setBackendUrl = useCallback((_value: string) => {}, []);

  const setTheme = useCallback((value: Theme) => {
    setState((prev) => ({
      ...prev,
      theme: value,
    }));
  }, []);

  const toggleTheme = useCallback(() => {
    setState((prev) => ({
      ...prev,
      theme: prev.theme === "dark" ? "light" : "dark",
    }));
  }, []);

  const resetSession = useCallback(() => {
    sessionStorage.removeItem("groq_api_key");
    sessionStorage.removeItem("groq_model");

    setState(DEFAULTS);
  }, []);

  const value = useMemo(
    () => ({
      ...state,
      setApiKey,
      setModel,
      setBackendUrl,
      setTheme,
      toggleTheme,
      resetSession,
    }),
    [
      state,
      setApiKey,
      setModel,
      setBackendUrl,
      setTheme,
      toggleTheme,
      resetSession,
    ]
  );

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);

  if (!ctx) {
    throw new Error(
      "useSettings must be used within SettingsProvider"
    );
  }

  return ctx;
}