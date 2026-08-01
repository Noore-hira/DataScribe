import { motion } from 'framer-motion';
import { Check, Loader2, AlertTriangle, Clock, RotateCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { StatusBadge } from '@/components/common/StatusBadge';
import { NODE_LABELS } from '@/types';
import type { WorkflowNodeState } from '@/types';

interface WorkflowNodeProps {
  state: WorkflowNodeState;
  index: number;
  isLast: boolean;
}

export function WorkflowNode({ state, index, isLast }: WorkflowNodeProps) {
  const status = state.status;
  const isActive = status === 'running' || status === 'retrying';

  return (
    <div className="relative flex flex-col items-stretch">
      <motion.div
        initial={{ opacity: 0, x: -8 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.05 }}
        className={cn(
          'relative rounded-xl border p-3 transition-all',
          status === 'waiting' && 'border-border/50 bg-card/30 opacity-60',
          status === 'running' && 'border-warning/40 bg-warning/5 glow-soft',
          status === 'retrying' && 'border-warning/40 bg-warning/5',
          status === 'completed' && 'border-success/30 bg-success/5',
          status === 'failed' && 'border-destructive/40 bg-destructive/5'
        )}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <NodeIcon status={status} />
            <span className="text-sm font-semibold">{NODE_LABELS[state.node]}</span>
          </div>
          <StatusBadge status={status} />
        </div>

        {state.message && (
          <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">{state.message}</p>
        )}

        {(state.durationMs != null || state.retries) && (
          <div className="mt-2 flex items-center gap-3 text-[11px] text-muted-foreground/80">
            {state.durationMs != null && (
              <span>{(state.durationMs / 1000).toFixed(2)}s</span>
            )}
            {state.retries != null && state.retries > 0 && (
              <span className="text-warning">{state.retries} retry{state.retries > 1 ? 's' : ''}</span>
            )}
            {state.progress != null && state.progress > 0 && (
              <span>{state.progress}%</span>
            )}
          </div>
        )}

        {isActive && (
          <motion.div
            className="absolute left-0 top-0 h-full w-1 rounded-l-xl bg-gradient-gold"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.4, repeat: Infinity }}
          />
        )}
      </motion.div>

      {!isLast && (
        <div className="relative mx-auto my-1 h-4 w-px bg-border">
          {status === 'completed' && (
            <motion.div
              className="absolute inset-0 bg-gradient-gold"
              animate={{ scaleY: [0, 1] }}
              style={{ transformOrigin: 'top' }}
              transition={{ duration: 0.3 }}
            />
          )}
          {isActive && (
            <motion.div
              className="absolute -left-[3px] h-2 w-2 rounded-full bg-gold-400"
              animate={{ y: [0, 12, 0], opacity: [1, 0, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
          )}
        </div>
      )}
    </div>
  );
}

function NodeIcon({ status }: { status: WorkflowNodeState['status'] }) {
  switch (status) {
    case 'running':
      return <Loader2 className="h-4 w-4 animate-spin text-warning" />;
    case 'retrying':
      return <RotateCw className="h-4 w-4 animate-spin text-warning" />;
    case 'completed':
      return <Check className="h-4 w-4 text-success" />;
    case 'failed':
      return <AlertTriangle className="h-4 w-4 text-destructive" />;
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />;
  }
}
