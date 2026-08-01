import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, User, BarChart3, Image as ImageIcon, Maximize2, Download, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ChatMessage as ChatMessageType } from '@/types';
import { useSettings } from '@/contexts/SettingsContext';

interface ChatMessageProps {
  message: ChatMessageType;
  isLatest?: boolean;
}

export function ChatMessage({ message, isLatest }: ChatMessageProps) {
  const [fullscreen, setFullscreen] = useState<string | null>(null);
  const isUser = message.role === 'user';
  const { backendUrl } = useSettings() ?? {};
  const base = backendUrl ? (backendUrl.endsWith('/') ? backendUrl.slice(0, -1) : backendUrl) : 'https://da-5f4c85c6edef485aae966f71f553a8f0.ecs.us-east-1.on.aws';

  // ==========================================================
  // EXTRACT CHARTS FROM CHAT TEXT & APPLY SMART FILTER
  // ==========================================================
  const extractedCharts = (() => {
    if (isUser) return []; // Don't parse user messages for charts
    const validCharts: string[] = [];
    const matches = message.content.match(/[\w.-]+\.(?:png|html)/gi);
    if (matches) {
      validCharts.push(...matches);
    }
    
    const normalizedCharts = Array.from(new Set(validCharts)).map(filename => {
      const cleanName = filename.split('/').pop()?.replace(/[^a-zA-Z0-9_.-]/g, '') || filename;
      return `charts/${cleanName}`;
    });

    // SMART FILTER: Remove duplicate E2B inline captures if explicitly named charts exist
    const nicelyNamedCharts = normalizedCharts.filter(
      (c) => !/(^|\/)chart_\d+\.(png|html)$/i.test(c)
    );

    return nicelyNamedCharts.length > 0 ? nicelyNamedCharts : normalizedCharts;
  })();

  const imageCharts = extractedCharts.filter(c => c.endsWith('.png'));
  const htmlCharts = extractedCharts.filter(c => c.endsWith('.html'));

  const downloadImage = async (src: string) => {
    const absoluteUrl = `${base}/${src}`;
    const filename = src.split('/').pop() ?? 'chart.png';

    try {
      // Fetch the image as a Blob to bypass cross-origin download restrictions
      const response = await fetch(absoluteUrl);
      const blob = await response.blob();
      
      // Create a local object URL which the browser is allowed to download directly
      const blobUrl = window.URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a); // Required for Firefox compatibility
      a.click();
      
      // Clean up the memory
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("Failed to fetch image for download:", error);
      // Fallback: If the fetch fails, just open it in a new tab like before
      const a = document.createElement('a');
      a.href = absoluteUrl;
      a.download = filename;
      a.target = '_blank';
      a.click();
    }
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={cn('flex w-full gap-3', isUser ? 'justify-end' : 'justify-start')}
      >
        {!isUser && (
          <div className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-gold text-black">
            <Bot className="h-4 w-4" />
          </div>
        )}
        <div
          className={cn(
            'max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed space-y-3',
            isUser
              ? 'bg-gradient-gold text-black'
              : 'glass-panel text-foreground border border-gold-500/20'
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="flex flex-col gap-3">
              {/* Standard Text Rendering */}
              <MarkdownContent content={message.content} base={base} />

              {/* 🛠️ Render Interactive HTML Charts directly in Chat */}
              {htmlCharts.length > 0 && (
                <div className="mt-2 flex flex-col gap-3 border-t border-gold-500/20 pt-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-gold-400">
                    <BarChart3 className="h-4 w-4" /> Interactive Charts
                  </div>
                  {htmlCharts.map((src, i) => (
                    <div key={i} className="overflow-hidden rounded-xl border border-border/60 bg-white shadow-sm">
                      <iframe
                        src={`${base}/${src}`}
                        className="h-[450px] w-full border-0 bg-white"
                        title={`Interactive Chat Chart ${i + 1}`}
                        sandbox="allow-scripts allow-same-origin allow-popups"
                      />
                    </div>
                  ))}
                </div>
              )}

              {/* 🛠️ Render Static PNG Charts with Hover Controls */}
              {imageCharts.length > 0 && (
                <div className="mt-2 flex flex-col gap-3 border-t border-gold-500/20 pt-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-gold-400">
                    <ImageIcon className="h-4 w-4" /> Static Charts
                  </div>
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {imageCharts.map((src, i) => {
                      const absoluteSrc = `${base}/${src}`;
                      return (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: i * 0.08 }}
                          className="group relative overflow-hidden rounded-lg border border-border/60 bg-card/40"
                        >
                          <img
                            src={absoluteSrc}
                            alt={`Generated chart ${i + 1}`}
                            className="w-full cursor-pointer object-contain transition-transform group-hover:scale-105"
                            onClick={() => setFullscreen(absoluteSrc)}
                          />
                          <div className="absolute inset-0 flex items-end justify-end gap-2 bg-gradient-to-t from-black/60 to-transparent p-2 opacity-0 transition-opacity group-hover:opacity-100">
                            <button
                              onClick={() => setFullscreen(absoluteSrc)}
                              className="rounded-md bg-background/80 p-1.5 text-foreground backdrop-blur hover:bg-background/90"
                              aria-label="Open fullscreen"
                            >
                              <Maximize2 className="h-3.5 w-3.5" />
                            </button>
                            <button
                              onClick={() => downloadImage(src)}
                              className="rounded-md bg-background/80 p-1.5 text-foreground backdrop-blur hover:bg-background/90"
                              aria-label="Download chart"
                            >
                              <Download className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        {isUser && (
          <div className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-secondary text-muted-foreground">
            <User className="h-4 w-4" />
          </div>
        )}
      </motion.div>

      {/* Fullscreen Image Modal - Rendered outside the motion.div to prevent layout cropping */}
      <AnimatePresence>
        {fullscreen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 p-6 backdrop-blur"
            onClick={() => setFullscreen(null)}
          >
            <button
              className="absolute right-4 top-4 grid h-10 w-10 place-items-center rounded-full bg-background/80 text-foreground hover:bg-background/100"
              onClick={() => setFullscreen(null)}
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
            <img
              src={fullscreen}
              alt="Chart fullscreen"
              className="max-h-[85vh] max-w-[90vw] h-auto w-auto rounded-lg object-contain shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              className="absolute bottom-6 right-6 flex items-center gap-2 rounded-lg bg-gradient-gold px-4 py-2 text-sm font-semibold text-black hover:opacity-90"
              onClick={(e) => {
                e.stopPropagation();
                const src = fullscreen.split('/charts/')[1];
                downloadImage(`charts/${src}`);
              }}
            >
              <Download className="h-4 w-4" />
              Download
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// ==========================================================
// MARKDOWN PARSER
// ==========================================================
export function MarkdownContent({ content, base }: { content: string; base: string }) {
  const resolveUrl = (src?: string) => {
    if (!src) return '';
    if (src.startsWith('http')) return src;
    const cleanSrc = src.replace(/^(\/?charts\/)+/, '').replace(/^\/+/, '');
    return `${base}/charts/${cleanSrc}`;
  };

  return (
    <div className="prose-chat">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          img({ src, alt, ...props }) {
            return (
              <img
                src={resolveUrl(src)}
                alt={alt || 'Chart'}
                className="my-2 max-h-[300px] max-w-full rounded-lg border border-gold-500/20 object-contain"
                {...props}
              />
            );
          },
          iframe({ src, ...props }) {
            return (
              <iframe
                src={resolveUrl(src)}
                className="my-3 h-[450px] w-full rounded-lg border border-gold-500/30 bg-card shadow-lg"
                sandbox="allow-scripts allow-same-origin"
                {...props}
              />
            );
          },
          code({ className, children, ...props }) {
            const isInline = !className?.includes('language-');
            if (isInline) {
              return (
                <code className="rounded bg-secondary px-1.5 py-0.5 font-mono text-[0.85em] text-gold-400" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className={cn('block font-mono text-[0.85em]', className)} {...props}>
                {children}
              </code>
            );
          },
          pre({ children }) {
            return (
              <pre className="my-2 overflow-x-auto rounded-lg border border-border bg-background/60 p-2 text-xs scrollbar-thin">
                {children}
              </pre>
            );
          },
          table({ children }) {
            return (
              <div className="my-2 overflow-x-auto scrollbar-thin">
                <table className="w-full border-collapse text-xs">{children}</table>
              </div>
            );
          },
          th({ children }) {
            return <th className="border border-border bg-secondary/60 px-2 py-1 text-left font-semibold">{children}</th>;
          },
          td({ children }) {
            return <td className="border border-border px-2 py-1">{children}</td>;
          },
          ul({ children }) {
            return <ul className="my-1 list-disc space-y-0.5 pl-4">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="my-1 list-decimal space-y-0.5 pl-4">{children}</ol>;
          },
          p({ children }) {
            return <p className="my-1 leading-relaxed">{children}</p>;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}