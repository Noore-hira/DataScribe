import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ListChecks, Copy, Check } from 'lucide-react';
import { MarkdownContent } from '@/components/chat/ChatMessage';
import { useSettings } from '@/contexts/SettingsContext';
import type { PlanSummary } from '@/types';

export function PlanCard({ plan }: { plan: PlanSummary }) {
  const [open, setOpen] = useState(true);
  const [copied, setCopied] = useState(false);
  
  // 1. Fetch the backend URL to satisfy the new MarkdownContent requirements
  const { backendUrl } = useSettings() ?? {};
  const base = backendUrl ? (backendUrl.endsWith('/') ? backendUrl.slice(0, -1) : backendUrl) : 'https://da-5f4c85c6edef485aae966f71f553a8f0.ecs.us-east-1.on.aws';

  const copy = () => {
    navigator.clipboard.writeText(plan.plan);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="overflow-hidden rounded-xl border border-gold-500/30 bg-gold-500/5"
    >
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-2 px-4 py-3"
      >
        <div className="flex items-center gap-2 text-sm font-semibold">
          <ListChecks className="h-4 w-4 text-gold-400" />
          Execution Plan
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              copy();
            }}
            className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            aria-label="Copy plan"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
          </button>
          <motion.span animate={{ rotate: open ? 180 : 0 }}>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </motion.span>
        </div>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="border-t border-gold-500/20 px-4 py-3 text-sm">
              {/* 2. Pass the base URL prop here */}
              <MarkdownContent content={plan.plan} base={base} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}