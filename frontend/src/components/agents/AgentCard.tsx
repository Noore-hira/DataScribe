import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Code2,
  Terminal,
  ShieldCheck,
  FileBarChart,
  MessageSquare,
  Rocket,
  Network,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { StatusBadge } from '@/components/common/StatusBadge';
import { NODE_LABELS, NODE_DESCRIPTIONS, type NodeName, type WorkflowNodeState, type TimelineEntry } from '@/types';

const NODE_ICONS: Record<NodeName, typeof Brain> = {
  conversation: MessageSquare,
  initialize: Rocket,
  supervisor: Network,
  planner: Brain,
  programmer: Code2,
  executor: Terminal,
  critic: ShieldCheck,
  reporter: FileBarChart,
};

interface AgentCardProps {
  state: WorkflowNodeState;
  index: number;
  timeline?: TimelineEntry[]; // Added timeline prop
}

export function AgentCard({ state, index, timeline = [] }: AgentCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const Icon = NODE_ICONS[state.node];
  const isActive = state.status === 'running' || state.status === 'retrying';
  
  // Filter timeline events for this specific node
  const nodeEvents = timeline.filter((t) => t.node === state.node);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className={cn(
        'relative flex flex-col rounded-xl border bg-card/40 p-3 transition-all',
        state.status === 'waiting' && 'border-border/40 opacity-60',
        isActive && 'border-warning/40 glow-soft',
        state.status === 'completed' && 'border-success/30',
        state.status === 'failed' && 'border-destructive/40'
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'grid h-7 w-7 place-items-center rounded-lg',
              isActive ? 'bg-gradient-gold text-black' : 'bg-secondary text-muted-foreground'
            )}
          >
            <Icon className="h-3.5 w-3.5" />
          </span>
          <span className="text-xs font-semibold">{NODE_LABELS[state.node]}</span>
        </div>
        <StatusBadge status={state.status} withLabel={false} />
      </div>

      <p className="mt-1.5 line-clamp-2 text-[11px] text-muted-foreground/80">
        {NODE_DESCRIPTIONS[state.node]}
      </p>

      <MetricsCard state={state} />

      <div className="mt-2 flex items-center gap-3 text-[10px] text-muted-foreground/70">
        {state.durationMs != null && <span>{(state.durationMs / 1000).toFixed(2)}s</span>}
        {state.retries != null && state.retries > 0 && (
          <span className="text-warning">{state.retries} retry{state.retries > 1 ? 's' : ''}</span>
        )}
      </div>

      {/* --- NEW: Agent Timeline Dropdown --- */}
      {nodeEvents.length > 0 && (
        <div className="mt-3 border-t border-border/40 pt-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex w-full items-center justify-between text-[10px] font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            <span>Activity Logs ({nodeEvents.length})</span>
            {isExpanded ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </button>

          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-2 flex flex-col gap-1.5">
                  {nodeEvents.map((event) => (
                    <div key={event.id} className="flex items-start gap-2 text-[10px] leading-tight">
                      <span className="shrink-0 text-muted-foreground/50">
                        {new Date(event.createdAt).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                        })}
                      </span>
                      <span
                        className={cn(
                          'text-muted-foreground/80 break-words',
                          event.status === 'error' && 'text-destructive font-medium',
                          event.status === 'warning' && 'text-warning font-medium',
                          event.status === 'retry' && 'text-warning'
                        )}
                      >
                        {event.message}
                      </span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );
}

function MetricsCard({ state }: { state: WorkflowNodeState }) {
  const m = state.metrics;
  if (!m || Object.keys(m).length === 0) return null;

  const items: { label: string; value: string }[] = [];

  if (state.node === 'planner') {
    if (m.analysis_tasks != null) items.push({ label: 'Analysis tasks', value: String(m.analysis_tasks) });
    if (m.visualization_tasks != null) items.push({ label: 'Viz tasks', value: String(m.visualization_tasks) });
  } else if (state.node === 'programmer') {
    if (m.lines_of_code != null) items.push({ label: 'Lines of code', value: String(m.lines_of_code) });
  } else if (state.node === 'executor') {
    if (m.charts_generated != null) items.push({ label: 'Charts', value: String(m.charts_generated) });
    if (m.execution_status) items.push({ label: 'Status', value: String(m.execution_status) });
  } else if (state.node === 'critic') {
    if (m.critic_verdict) items.push({ label: 'Verdict', value: String(m.critic_verdict) });
    if (m.retry_count != null) items.push({ label: 'Retries', value: String(m.retry_count) });
  } else if (state.node === 'reporter') {
    if (m.report_generated != null) items.push({ label: 'Report', value: m.report_generated ? 'Generated' : 'Pending' });
  }

  if (items.length === 0) return null;

  return (
    <div className="mt-2 grid grid-cols-2 gap-1.5">
      {items.map((it) => (
        <div key={it.label} className="rounded-md bg-secondary/40 px-2 py-1 text-[10px]">
          <div className="text-muted-foreground/70">{it.label}</div>
          <div className="font-semibold capitalize text-foreground/90">{it.value}</div>
        </div>
      ))}
    </div>
  );
}