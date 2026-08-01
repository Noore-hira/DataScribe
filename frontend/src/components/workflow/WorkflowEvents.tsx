import { motion, AnimatePresence } from 'framer-motion';
import { RotateCw, MessageSquare } from 'lucide-react';

export function RetryNotification({ retryCount, message }: { retryCount: number; message?: string }) {
  return (
    <AnimatePresence>
      {retryCount > 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="flex items-center gap-3 rounded-xl border border-warning/40 bg-warning/10 px-4 py-2.5"
        >
          <motion.span
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="text-warning"
          >
            <RotateCw className="h-4 w-4" />
          </motion.span>
          <div className="text-xs">
            <span className="font-semibold text-warning">Critic requested another iteration</span>
            <span className="ml-2 text-muted-foreground">Retry #{retryCount}</span>
            {message && <div className="mt-0.5 text-muted-foreground">{message}</div>}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export function DecisionBanner({ decision }: { decision: string }) {
  return (
    <AnimatePresence>
      {decision && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="flex items-center gap-2 rounded-lg border border-border/60 bg-card/50 px-3 py-2 text-xs"
        >
          <span className="font-semibold text-gold-400">Supervisor decision</span>
          <span className="text-muted-foreground">{decision}</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export function ConversationMessageBanner({ content }: { content: string }) {
  return (
    <AnimatePresence>
      {content && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="flex items-center gap-2 rounded-lg border border-gold-500/30 bg-gold-500/5 px-3 py-2 text-xs"
        >
          <MessageSquare className="h-3.5 w-3.5 text-gold-400 shrink-0" />
          <span className="text-foreground">{content}</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}