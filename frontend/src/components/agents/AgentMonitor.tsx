import { motion } from 'framer-motion';
import { Activity, Gauge } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AgentCard } from './AgentCard';
import { NODE_ORDER, type NodeName, type TimelineEntry } from '@/types';
import type { WorkflowNodeState } from '@/types';

interface AgentMonitorProps {
  nodes: Record<NodeName, WorkflowNodeState>;
  isStreaming: boolean;
  onOpenInDrawer?: boolean;
  timeline?: TimelineEntry[]; // <-- Added timeline prop
}

export function AgentMonitor({ nodes, isStreaming, timeline = [] }: AgentMonitorProps) {
  const completedCount = Object.values(nodes).filter((n) => n.status === 'completed').length;
  const activeNode = Object.values(nodes).find((n) => n.status === 'running' || n.status === 'retrying');

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border/60 px-4 py-3">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-gold-400" />
          <span className="text-sm font-semibold">Agent Monitor</span>
        </div>
        <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] text-muted-foreground">
          {completedCount}/{NODE_ORDER.length}
        </span>
      </div>

      <div className="border-b border-border/40 px-4 py-2.5">
        {activeNode ? (
          <motion.div
            key={activeNode.node}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-2 text-xs"
          >
            <Gauge className="h-3.5 w-3.5 animate-pulse text-warning" />
            <span className="text-muted-foreground">Active:</span>
            <span className="font-semibold text-warning">{activeNode.node}</span>
          </motion.div>
        ) : (
          <div className="flex items-center gap-2 text-xs text-muted-foreground/60">
            <Gauge className="h-3.5 w-3.5" />
            <span>{isStreaming ? 'Idle' : 'Awaiting run'}</span>
          </div>
        )}
      </div>

      <ScrollArea className="flex-1 px-3 py-3">
        <div className="space-y-2">
          {NODE_ORDER.map((name, i) => (
            // Pass the timeline prop down to the AgentCard
            <AgentCard key={name} state={nodes[name]} index={i} timeline={timeline} />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}