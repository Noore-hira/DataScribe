import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  Check,
  AlertTriangle,
  Info,
  RotateCw,
  FileText,
  Flag,
  Lightbulb,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TimelineEntry } from '@/types';
import { NODE_LABELS } from '@/types';

interface WorkflowTimelineProps {
  entries: TimelineEntry[];
}

const ICONS: Record<TimelineEntry['status'], typeof Play> = {
  start: Play,
  end: Check,
  info: Info,
  retry: RotateCw,
  warning: AlertTriangle,
  decision: Lightbulb,
  report: FileText,
  complete: Flag,
  error: AlertTriangle,
};

const COLORS: Record<TimelineEntry['status'], string> = {
  start: 'text-warning bg-warning/10',
  end: 'text-success bg-success/10',
  info: 'text-muted-foreground bg-secondary',
  retry: 'text-warning bg-warning/10',
  warning: 'text-warning bg-warning/10',
  decision: 'text-gold-400 bg-gold-500/10',
  report: 'text-gold-400 bg-gold-500/10',
  complete: 'text-success bg-success/10',
  error: 'text-destructive bg-destructive/10',
};

export function WorkflowTimeline({ entries }: WorkflowTimelineProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [entries.length]);

  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-10 text-center text-xs text-muted-foreground/60">
        <Info className="h-5 w-5" />
        <p>Workflow events will appear here as they stream in.</p>
      </div>
    );
  }

  return (
    <div className="relative space-y-1 py-2">
      <AnimatePresence initial={false}>
        {entries.map((entry) => {
          const Icon = ICONS[entry.status];
          return (
            <motion.div
              key={entry.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-start gap-2.5 text-xs"
            >
              <span className={cn('mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full', COLORS[entry.status])}>
                <Icon className="h-3 w-3" />
              </span>
              <div className="min-w-0 flex-1">
                <span className="font-medium text-muted-foreground">{NODE_LABELS[entry.node]}</span>
                <span className="ml-2 text-foreground/80">{entry.message}</span>
              </div>
              <span className="shrink-0 text-muted-foreground/50">
                {new Date(entry.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
            </motion.div>
          );
        })}
      </AnimatePresence>
      <div ref={endRef} />
    </div>
  );
}
