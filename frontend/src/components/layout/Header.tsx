import { motion } from 'framer-motion';
import { PanelRight, Sparkles } from 'lucide-react';
import { Logo } from '@/components/common/Logo';
import { ConnectionIndicator } from '@/components/common/ConnectionIndicator';
import { useConnectionStatus } from '@/hooks/use-connection-status';
import { useSettings } from '@/contexts/SettingsContext';
import { cn } from '@/lib/utils';

interface HeaderProps {
  onToggleRightPanel: () => void;
  rightPanelOpen: boolean;
}

export function Header({ onToggleRightPanel, rightPanelOpen }: HeaderProps) {
  const { backendUrl } = useSettings();
  const health = useConnectionStatus(backendUrl);

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between gap-3 border-b border-border/60 bg-background/70 px-4 backdrop-blur sm:px-6">
      <div className="flex items-center gap-3">
        <div className="hidden sm:block">
          <Logo size={28} withWordmark />
        </div>
        <div className="sm:hidden">
          <Logo size={28} />
        </div>
        <span className="hidden text-xs text-muted-foreground md:inline">
          Multi-Agent AI Data Analysis Platform
        </span>
      </div>

      <div className="flex items-center gap-2">
        <ConnectionIndicator health={health} checking={health.checkedAt === 0} compact={false} />
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={onToggleRightPanel}
          className={cn(
            'grid h-9 w-9 place-items-center rounded-lg border transition-colors',
            rightPanelOpen
              ? 'border-gold-500/40 bg-gold-500/10 text-gold-400'
              : 'border-border/60 bg-card/40 text-muted-foreground hover:text-foreground'
          )}
          aria-label="Toggle agent monitor"
          title="Agent monitor"
        >
          <PanelRight className="h-4 w-4" />
        </motion.button>
      </div>
    </header>
  );
}

export function ChatHeaderMinimal() {
  const { backendUrl } = useSettings();
  const health = useConnectionStatus(backendUrl);
  return (
    <div className="flex items-center justify-between px-1 pb-3">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-gold-400" />
        <h1 className="font-display text-lg font-bold">
          Data<span className="text-gradient-gold">Scribe</span>
        </h1>
        <span className="hidden text-xs text-muted-foreground sm:inline">
          · Multi-Agent AI Data Analysis Platform
        </span>
      </div>
      <ConnectionIndicator health={health} checking={health.checkedAt === 0} compact />
    </div>
  );
}
