import { lazy, Suspense, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';

import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { RightPanel } from '@/components/layout/RightPanel';

import { SettingsProvider } from '@/contexts/SettingsContext';
import { SessionProvider } from '@/contexts/SessionContext';
import { WorkflowProvider } from '@/contexts/WorkflowContext';

import { Toaster } from '@/components/ui/sonner';

const ChatPage = lazy(() => import('@/pages/ChatPage'));
const ReportsPage = lazy(() => import('@/pages/ReportsPage'));
const SettingsPage = lazy(() => import('@/pages/SettingsPage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      refetchOnWindowFocus: false,
    },
  },
});

function PageFallback() {
  return (
    <div className="flex h-full items-center justify-center">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: 'linear',
        }}
        className="h-8 w-8 rounded-full border-2 border-gold-500/30 border-t-gold-400"
      />
    </div>
  );
}

function AppShell() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [rightPanelOpen, setRightPanelOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((c) => !c)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header
          onToggleRightPanel={() => setRightPanelOpen((o) => !o)}
          rightPanelOpen={rightPanelOpen}
        />

        <main className="flex min-h-0 flex-1 overflow-hidden">
          <div className="min-w-0 flex-1 overflow-hidden">
            <Suspense fallback={<PageFallback />}>
              <AnimatePresence mode="wait">
                <RoutesWithTransitions />
              </AnimatePresence>
            </Suspense>
          </div>

          <RightPanel
            open={rightPanelOpen}
            onClose={() => setRightPanelOpen(false)}
          />
        </main>
      </div>
    </div>
  );
}

function RoutesWithTransitions() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <PageWrapper>
            <ChatPage />
          </PageWrapper>
        }
      />

      <Route
        path="/reports"
        element={
          <PageWrapper>
            <ReportsPage />
          </PageWrapper>
        }
      />

      <Route
        path="/settings"
        element={
          <PageWrapper>
            <SettingsPage />
          </PageWrapper>
        }
      />
    </Routes>
  );
}

function PageWrapper({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.25 }}
      className="h-full overflow-hidden"
    >
      {children}
    </motion.div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SettingsProvider>
        <SessionProvider>
          <WorkflowProvider>
            <HashRouter>
              <AppShell />
            </HashRouter>

            <Toaster
              position="bottom-right"
              richColors
              closeButton
            />
          </WorkflowProvider>
        </SessionProvider>
      </SettingsProvider>
    </QueryClientProvider>
  );
}