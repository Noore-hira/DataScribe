import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import type { BackendHealth } from '@/services/api';

interface ConnectionIndicatorProps {
  health: BackendHealth;
  checking?: boolean;
  className?: string;
  compact?: boolean;
}

export function ConnectionIndicator({ health, checking, className, compact }: ConnectionIndicatorProps) {
  const online = health.online;
  const label = online ? 'Backend online' : checking ? 'Checking…' : 'Backend offline';
  const dotColor = online ? 'bg-success' : checking ? 'bg-warning' : 'bg-destructive';

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2 rounded-full border border-border/60 bg-card/50 px-3 py-1.5 text-xs font-medium backdrop-blur',
        className
      )}
    >
      <span className="relative flex h-2 w-2">
        {online && (
          <motion.span
            className={cn('absolute inline-flex h-full w-full rounded-full opacity-75', dotColor)}
            animate={{ scale: [1, 2.2, 1], opacity: [0.7, 0, 0.7] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          />
        )}
        <span className={cn('relative inline-flex h-2 w-2 rounded-full', dotColor)} />
      </span>
      {!compact && <span className="text-muted-foreground">{label}</span>}
      {!compact && online && health.latencyMs != null && (
        <span className="text-muted-foreground/60">{health.latencyMs}ms</span>
      )}
    </div>
  );
}
