import { motion } from 'framer-motion';
import { Check, Loader2, AlertTriangle, Clock, RotateCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { NodeStatus } from '@/types';

interface StatusBadgeProps {
  status: NodeStatus;
  className?: string;
  withLabel?: boolean;
}

const CONFIG: Record<NodeStatus, { label: string; cls: string; icon: typeof Check }> = {
  waiting: { label: 'Waiting', cls: 'bg-muted text-muted-foreground border-border', icon: Clock },
  running: { label: 'Running', cls: 'bg-warning/15 text-warning border-warning/40', icon: Loader2 },
  completed: { label: 'Completed', cls: 'bg-success/15 text-success border-success/40', icon: Check },
  failed: { label: 'Failed', cls: 'bg-destructive/15 text-destructive border-destructive/40', icon: AlertTriangle },
  retrying: { label: 'Retrying', cls: 'bg-warning/15 text-warning border-warning/40', icon: RotateCw },
};

export function StatusBadge({ status, className, withLabel = true }: StatusBadgeProps) {
  const cfg = CONFIG[status];
  const Icon = cfg.icon;
  const animate = status === 'running' || status === 'retrying';

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold',
        cfg.cls,
        className
      )}
    >
      <motion.span
        animate={animate ? { rotate: 360 } : { rotate: 0 }}
        transition={animate ? { duration: 1, repeat: Infinity, ease: 'linear' } : { duration: 0 }}
        className="flex"
      >
        <Icon className="h-3 w-3" />
      </motion.span>
      {withLabel && cfg.label}
    </span>
  );
}
