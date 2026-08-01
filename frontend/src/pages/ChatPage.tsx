import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle } from 'lucide-react';
import { ChatMessage } from '@/components/chat/ChatMessage';
import { ChatInput } from '@/components/chat/ChatInput';
import { RetryNotification, DecisionBanner } from '@/components/workflow/WorkflowEvents';
import { useSession } from '@/contexts/SessionContext';
import { useSettings } from '@/contexts/SettingsContext';
import { useWorkflow } from '@/contexts/WorkflowContext';
// Add this import near your other imports
import { AnimatedBackground } from '@/components/common/AnimatedBackground'; // Adjust path if needed

export default function ChatPage() {
  const { dataset, threadId } = useSession();
  const { backendUrl, apiKey, model } = useSettings();
  const { messages, decision, retryCount, lastError, isStreaming, startStream, timeline } = useWorkflow();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isAtBottom] = useState(true);

  useEffect(() => {
    if (isAtBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length, timeline.length, isAtBottom]);

  const handleSend = (message: string) => {
    if (!threadId) return;

    startStream(
      {
        message,
        threadId,
        baseUrl: backendUrl,
        apiKey,
        model,
        datasetPath: dataset?.path,
      },
      {}
    );
  };

  return (
    <div className="mx-auto flex h-full max-w-4xl flex-col px-4 py-4 sm:px-6">
      <AnimatedBackground />
      {/* Upload + status */}
      <div className="mb-4 space-y-3">
        {decision && <DecisionBanner decision={decision} />}

        {retryCount > 0 && (
          <RetryNotification retryCount={retryCount} />
        )}

        {lastError && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive"
          >
            <AlertCircle className="h-4 w-4 shrink-0" />
            {lastError}
          </motion.div>
        )}
      </div>
      {/* Chat + workflow */}
      <div className="flex-1 space-y-4 overflow-y-auto pb-4 scrollbar-thin">
        {messages.length === 0 && !isStreaming && (
          <EmptyState />
        )}

        <AnimatePresence>
          {messages.map((m) => (
            <ChatMessage key={m.id} message={m} />
          ))}
        </AnimatePresence>

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="pt-2">
        <ChatInput onSend={handleSend} disabled={isStreaming}/>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-20 text-center"
    >
      <h1 className="font-display text-6xl font-black tracking-tight text-foreground sm:text-7xl">
        Ask Anything
      </h1>

      <h2 className="mt-1 bg-gradient-to-r from-yellow-300 via-amber-400 to-yellow-500 bg-clip-text text-6xl font-black tracking-tight text-transparent sm:text-7xl">
        About Your Data
      </h2>

      <p className="mt-8 max-w-2xl text-lg leading-8 text-muted-foreground">
        Start a conversation naturally.
        Upload a dataset anytime using the attachment button to unlock AI-powered analysis, visualisations and code generation.
      </p>

      <div className="mt-12 grid w-full max-w-5xl grid-cols-2 gap-5 lg:grid-cols-4">

        <FeatureCard
          title="Chat Naturally"
          text="Ask questions in plain English."
        />

        <FeatureCard
          title="Smart Analysis"
          text="AI agents analyse your dataset."
        />

        <FeatureCard
          title="Code Generation"
          text="Automatic Python generation."
        />

        <FeatureCard
          title="Visual Insights"
          text="Interactive charts and reports."
        />

      </div>
    </motion.div>
  );
}

function FeatureCard({
  title,
  text,
}: {
  title: string;
  text: string;
}) {
  return (
    <motion.div
      whileHover={{ y: -6 }}
      // 🛠️ White in light mode, dark gradient in dark mode
      className="group rounded-2xl border border-gold-500/20 bg-white dark:bg-gradient-to-br dark:from-zinc-900 dark:to-black p-5 shadow-xl transition-all duration-300 hover:shadow-2xl hover:shadow-gold-500/10"
    >
      {/* 🛠️ Slightly darker gold in light mode for better contrast against white */}
      <h3 className="text-lg font-semibold text-gold-500 dark:text-gold-400">
        {title}
      </h3>

      {/* 🛠️ Dark gray text in light mode, light text in dark mode */}
      <p className="mt-2 text-sm text-zinc-600 dark:text-white/70">
        {text}
      </p>
    </motion.div>
  );
}