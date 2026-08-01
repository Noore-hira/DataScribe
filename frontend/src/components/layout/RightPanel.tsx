import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { AgentMonitor } from '@/components/agents/AgentMonitor';
import { useWorkflow } from '@/contexts/WorkflowContext';
import type { NodeName, WorkflowNodeState, TimelineEntry } from '@/types';

interface RightPanelProps {
  open: boolean;
  onClose: () => void;
}

export function RightPanel({ open, onClose }: RightPanelProps) {
  // 1. Grab timeline from context
  const { nodes, isStreaming, timeline } = useWorkflow();

  return (
    <>
      {/* Desktop: persistent panel */}
      <aside className="hidden w-80 shrink-0 border-l border-border/60 bg-card/30 backdrop-blur lg:block">
        {/* 2. Pass timeline down to AgentMonitor */}
        <AgentMonitor 
          nodes={nodes as Record<NodeName, WorkflowNodeState>} 
          isStreaming={isStreaming} 
          timeline={timeline} 
        />
      </aside>

      {/* Mobile / tablet: drawer */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
              onClick={onClose}
            />
            <motion.aside
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', stiffness: 360, damping: 36 }}
              className="fixed right-0 top-0 z-50 h-full w-80 border-l border-border/60 bg-card shadow-2xl lg:hidden"
            >
              <button
                onClick={onClose}
                className="absolute right-3 top-3 z-10 grid h-8 w-8 place-items-center rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground"
                aria-label="Close agent monitor"
              >
                <X className="h-4 w-4" />
              </button>
              {/* 2. Pass timeline down to AgentMonitor */}
              <AgentMonitor 
                nodes={nodes as Record<NodeName, WorkflowNodeState>} 
                isStreaming={isStreaming} 
                timeline={timeline} 
              />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}