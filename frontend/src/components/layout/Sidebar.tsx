import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  MessageSquare,
  FileText,
  Settings as SettingsIcon,
  Plus,
  PanelLeftClose,
  PanelLeft,
  Hash,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Logo } from '@/components/common/Logo';
import { ApiKeyInput } from '@/components/settings/ApiKeyInput';
import { ModelSelector } from '@/components/settings/ModelSelector';
import { ThemeToggle } from '@/components/settings/ThemeToggle';
import { useSession } from '@/contexts/SessionContext';
import { useSettings } from '@/contexts/SettingsContext';
import { DEFAULT_BACKEND_URL } from '@/types';

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
}

const NAV = [
  { to: '/', label: 'Chat', icon: MessageSquare },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
];

export function Sidebar({ collapsed, onToggleCollapse }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { threadId, dataset, startNewSession} = useSession();
  const { backendUrl } = useSettings();
  const [settingsOpen, setSettingsOpen] = useState(true);

  const effectiveUrl = (backendUrl || DEFAULT_BACKEND_URL).replace(/\/$/, '');

  if (collapsed) {
    return (
      <aside className="flex h-full w-16 flex-col items-center gap-3 border-r border-border/60 bg-card/40 py-4 backdrop-blur">
        <button
          onClick={onToggleCollapse}
          className="grid h-10 w-10 place-items-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          aria-label="Expand sidebar"
        >
          <PanelLeft className="h-5 w-5" />
        </button>
        <Separator className="w-8" />
        {NAV.map((item) => {
          const active = location.pathname === item.to;
          const Icon = item.icon;
          return (
            <button
              key={item.to}
              onClick={() => navigate(item.to)}
              className={cn(
                'grid h-10 w-10 place-items-center rounded-lg transition-colors',
                active
                  ? 'bg-gradient-gold text-black'
                  : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
              )}
              title={item.label}
            >
              <Icon className="h-5 w-5" />
            </button>
          );
        })}
      </aside>
    );
  }

  return (
    <aside className="flex h-full w-72 flex-col border-r border-border/60 bg-card/40 backdrop-blur">
      {/* Header / Collapse Action Only */}
      <div className="flex items-center justify-end p-4">
        <button
          onClick={onToggleCollapse}
          className="grid h-8 w-8 place-items-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          aria-label="Collapse sidebar"
        >
          <PanelLeftClose className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4 scrollbar-thin">
        {/* API Settings */}
        <Section title="API Settings" defaultOpen>
          <ApiKeyInput />
          <div className="pt-1">
            <ModelSelector />
          </div>
          <div className="pt-2">
            <ThemeToggle />
          </div>
        </Section>

        {/* Session */}
        <Section title="Session">
          <div className="rounded-lg border border-border/60 bg-background/40 p-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Thread ID</span>
              <span className="flex items-center gap-1 font-mono text-foreground/80">
                <Hash className="h-3 w-3 text-gold-400" />
                {threadId ? threadId.slice(0, 8) : '—'}
              </span>
            </div>
            {dataset && (
              <div className="mt-2 truncate text-muted-foreground">
                {dataset.filename}
              </div>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            className="w-full border-gold-500/30 bg-gold-500/5 text-gold-300 hover:bg-gold-500/10 hover:text-gold-200"
            onClick={() => {
              startNewSession();
              navigate('/');
            }}
          >
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            New session
          </Button>
        </Section>

        <Section title="Navigation">
          <nav className="space-y-1">
            {NAV.map((item) => {
              const active = location.pathname === item.to;
              const Icon = item.icon;

              return (
                <button
                  key={item.to}
                  onClick={() => navigate(item.to)}
                  className={cn(
                    "relative group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all",
                    active
                      ? "bg-secondary text-foreground"
                      : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
                  )}
                >
                  <Icon
                    className={cn(
                      "h-4 w-4 transition-colors",
                      active
                        ? "text-gold-400"
                        : "text-muted-foreground group-hover:text-gold-400"
                    )}
                  />

                  {item.label}

                  {active && (
                    <motion.span
                      layoutId="nav-active"
                      className="absolute left-0 h-6 w-0.5 rounded-full bg-gradient-gold"
                    />
                  )}
                </button>
              );
            })}
          </nav>
        </Section>
      </div>
    </aside>
  );
}

function Section({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="mb-4">
      <button
        onClick={() => setOpen((o) => !o)}
        // 🛠️ Changed text-muted-foreground/70 to text-foreground font-semibold (or text-gold-400)
        className="mb-2 flex w-full items-center justify-between text-[11px] font-bold uppercase tracking-wider text-foreground transition-colors hover:text-gold-400"
      >
        {title}
        <motion.span animate={{ rotate: open ? 90 : 0 }} className="text-gold-400">
          ›
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="space-y-3 overflow-hidden"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}