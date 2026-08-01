import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Send, Paperclip, Sparkles, Square } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { UploadCard } from '@/components/upload/UploadCard';
import { useSession } from '@/contexts/SessionContext';
import { useWorkflow } from '@/contexts/WorkflowContext';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder,
}: ChatInputProps) {
  const { dataset } = useSession();
  const { isStreaming, stopStream } = useWorkflow();

  const [value, setValue] = useState('');
  const [showUpload, setShowUpload] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const canSend =
    value.trim().length > 0 &&
    !disabled &&
    !isStreaming;

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;

    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [value]);

  const handleSend = () => {
    if (!canSend) return;

    onSend(value.trim());
    setValue('');
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="relative">

      <AnimatePresence>
        {showUpload && (
          <motion.div
            initial={{ opacity: 0, y: 8, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: 8, height: 0 }}
            className="mb-3"
          >
            <UploadCard compact />
          </motion.div>
        )}
      </AnimatePresence>

      <div
        className={cn(
          "flex items-end gap-2 rounded-2xl border bg-card/60 p-2 backdrop-blur transition-all",
          dataset
            ? "border-border/70"
            : "border-gold-500/30"
        )}
      >
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 shrink-0 text-muted-foreground"
          onClick={() => setShowUpload((v) => !v)}
          title="Upload dataset"
        >
          <Paperclip className="h-4 w-4" />
        </Button>

        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          rows={1}
          placeholder={
            placeholder ??
            "Ask anything about your data..."
          }
          className="flex-1 resize-none bg-transparent py-2 text-sm outline-none placeholder:text-muted-foreground/60 scrollbar-thin"
        />

        <AnimatePresence mode="wait">
          {isStreaming ? (
            <Button
              key="stop"
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={stopStream}
            >
              <Square className="h-3 w-3 fill-current" />
              Stop
            </Button>
          ) : (
            <Button
              key="send"
              size="icon"
              className="h-9 w-9 bg-gradient-gold text-black hover:opacity-90"
              disabled={!canSend}
              onClick={handleSend}
            >
              {canSend ? (
                <Send className="h-4 w-4" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
            </Button>
          )}
        </AnimatePresence>
      </div>

      <div className="mt-2 flex items-center justify-between px-2 text-[11px] text-muted-foreground/70">
        <span>
          {dataset ? (
            <>
              <span className="text-gold-400">●</span>{" "}
              {dataset.filename}
            </>
          ) : (
            "No dataset uploaded"
          )}
        </span>

        <span>
          <kbd className="rounded bg-secondary px-1.5 py-0.5 font-mono">
            Enter
          </kbd>{" "}
          send ·{" "}
          <kbd className="rounded bg-secondary px-1.5 py-0.5 font-mono">
            Shift+Enter
          </kbd>{" "}
          newline
        </span>
      </div>
    </div>
  );
}