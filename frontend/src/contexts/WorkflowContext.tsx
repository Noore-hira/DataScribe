// @refresh reset
import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from 'react';
import {
  NODE_ORDER,
  type ChatMessage,
  type NodeName,
  type NodeStatus,
  type PlanSummary,
  type SSEEvent,
  type TimelineEntry,
  type WorkflowNodeState,
  type WorkflowReport,
} from '@/types';
import { streamChat, type StreamController } from '@/services/sse';

interface WorkflowContextValue {
  nodes: Record<NodeName, WorkflowNodeState>;
  timeline: TimelineEntry[];
  messages: ChatMessage[];
  plan: PlanSummary | null;
  reports: WorkflowReport[];
  decision: string | null;
  retryCount: number;
  isStreaming: boolean;
  lastError: string | null;

  startStream: (params: { message: string; threadId: string; baseUrl?: string | null; apiKey?: string; model?: string; datasetPath?: string }, hooks?: { onReport?: (r: WorkflowReport) => void; onComplete?: (durationMs: number) => void }) => void;
  stopStream: () => void;
  resetWorkflow: () => void;
  clearMessages: () => void;
  loadChatHistory: (history: ChatMessage[]) => void;
}

const WorkflowContext = createContext<WorkflowContextValue | null>(null);

function emptyNodes(): Record<NodeName, WorkflowNodeState> {
  const out = {} as Record<NodeName, WorkflowNodeState>;
  for (const n of NODE_ORDER) {
    out[n] = { node: n, status: 'waiting' as NodeStatus, retries: 0 };
  }
  return out;
}

let idCounter = 0;
function uid(prefix: string): string {
  idCounter += 1;
  return `${prefix}-${Date.now().toString(36)}-${idCounter}`;
}

export function WorkflowProvider({ children }: { children: ReactNode }) {
  const [nodes, setNodes] = useState<Record<NodeName, WorkflowNodeState>>(emptyNodes);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [plan, setPlan] = useState<PlanSummary | null>(null);
  const [reports, setReports] = useState<WorkflowReport[]>([]);
  const [decision, setDecision] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [isStreaming, setIsStreaming] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);

  const controllerRef = useRef<StreamController | null>(null);
  const onReportRef = useRef<((r: WorkflowReport) => void) | null>(null);
  const onCompleteRef = useRef<((durationMs: number) => void) | null>(null);
  
  // 🛑 Prevent duplicate reports from LangGraph double-yields or network retries
  const lastReportRef = useRef<string | null>(null);

  const pushTimeline = useCallback((entry: Omit<TimelineEntry, 'id' | 'createdAt'>) => {
    setTimeline((t) => [...t, { ...entry, id: uid('tl'), createdAt: Date.now() }]);
  }, []);

  const handleEvent = useCallback(
    (event: SSEEvent) => {
      switch (event.event) {
        case 'node_start': {
          setNodes((prev) => ({
            ...prev,
            [event.node]: {
              ...prev[event.node],
              node: event.node,
              status: 'running',
              progress: event.progress,
              message: event.message,
              startedAt: prev[event.node].startedAt ?? Date.now(),
            },
          }));
          pushTimeline({ node: event.node, status: 'start', message: event.message || `${event.node} started` });
          break;
        }
        case 'node_end': {
          setNodes((prev) => {
            const prevNode = prev[event.node];
            const startedAt = prevNode.startedAt ?? Date.now();
            const endedAt = Date.now();
            return {
              ...prev,
              [event.node]: {
                ...prevNode,
                status: 'completed',
                metrics: event.metrics,
                progress: event.progress,
                message: event.message,
                startedAt,
                endedAt,
                durationMs: endedAt - startedAt,
              },
            };
          });
          pushTimeline({ node: event.node, status: 'end', message: event.message || `${event.node} completed` });
          break;
        }
        case 'decision': {
          setDecision(event.decision);
          pushTimeline({ node: 'supervisor', status: 'decision', message: event.decision });
          break;
        }
        case 'plan': {
          setPlan({ plan: event.plan, createdAt: Date.now() });
          
          if (event.plan) {
            pushTimeline({ 
              node: 'planner', 
              status: 'info', 
              message: `Execution Plan Created:\n\n${event.plan}` 
            });
          } else {
            pushTimeline({ node: 'planner', status: 'info', message: 'Execution plan generated' });
          }
          break;
        }
        case 'retry': {
          setRetryCount(event.retry_count);
          setNodes((prev) => ({
            ...prev,
            [event.next_node]: {
              ...prev[event.next_node],
              node: event.next_node,
              status: 'retrying',
              message: event.message,
              retries: (prev[event.next_node].retries ?? 0) + 1,
            },
          }));
          pushTimeline({
            node: event.next_node,
            status: 'retry',
            message: `Retry #${event.retry_count}: ${event.message}`,
          });
          break;
        }
        case 'warning': {
          pushTimeline({
            node: event.node ?? 'supervisor',
            status: 'warning',
            message: event.message,
          });
          break;
        }
        
        // 🛠️ ADDED: The new live token stream handler
        case 'token': {
          setMessages((prev) => {
            const updated = [...prev];
            const lastMessageIndex = updated.length - 1;
            const lastMessage = updated[lastMessageIndex];

            // If the active message belongs to the AI, append the word
            if (lastMessage && lastMessage.role === 'assistant') {
              updated[lastMessageIndex] = {
                ...lastMessage,
                content: lastMessage.content + event.content,
              };
            } else {
              // Otherwise, this is the very first token! Create a new AI message.
              updated.push({
                id: uid('msg'),
                role: 'assistant',
                content: event.content,
                createdAt: Date.now(),
              });
            }
            return updated;
          });
          break;
        }

        case 'report': {
          const newReportContent = event.report;
          const newCharts = event.charts || [];
          
          // 🛑 SMART DEDUPLICATION: Silently ignore if it's the exact same report
          if (lastReportRef.current === newReportContent) {
            break;
          }
          lastReportRef.current = newReportContent;

          const newReportObj: WorkflowReport = {
            report: newReportContent,
            charts: newCharts,
            generatedAt: Date.now(),
          };

          setReports((prev) => [...prev, newReportObj]);
          onReportRef.current?.(newReportObj);

          // 🛠️ UPDATED: Prevent duplicate messages!
          // Replace/Update the message we were just streaming into with the final text & charts
          setMessages((prev) => {
            const updated = [...prev];
            const lastMessageIndex = updated.length - 1;
            const lastMessage = updated[lastMessageIndex];

            if (lastMessage && lastMessage.role === 'assistant') {
              updated[lastMessageIndex] = {
                ...lastMessage,
                content: newReportContent,
                charts: newCharts, // Attach the charts to the streamed text!
              };
              return updated;
            }

            // Fallback just in case streaming failed but the report succeeded
            return [
              ...updated,
              {
                id: uid('msg'),
                role: 'assistant',
                content: newReportContent,
                charts: newCharts,
                createdAt: Date.now(),
              },
            ];
          });

          pushTimeline({ node: 'reporter', status: 'report', message: 'Final report generated' });
          break;
        }
        case 'message':
        case 'text': {
          setMessages((m) => [
            ...m,
            {
              id: uid('msg'),
              role: 'assistant',
              content: event.content,
              createdAt: Date.now(),
            },
          ]);
          pushTimeline({ node: 'conversation', status: 'info', message: 'Chat response sent' });
          break;
        }
        case 'error': {
          setLastError(event.message);
          const failedNode = event.node;
          const errorMsg = event.message;
          
          if (failedNode) {
            setNodes((prev) => ({
              ...prev,
              [failedNode]: { ...prev[failedNode], status: 'failed', message: errorMsg },
            }));
          }
          
          pushTimeline({
            node: failedNode ?? 'supervisor',
            status: 'error',
            message: errorMsg,
          });

          let friendlyMessage = "I encountered an unexpected error while processing your request.";
          
          if (errorMsg.includes('429') || errorMsg.toLowerCase().includes('rate limit')) {
            friendlyMessage = "I'm sorry, but your API token limit has been reached. Please wait a few minutes before trying again, or check your API provider's billing dashboard.";
          }
          else if (errorMsg.toLowerCase().includes('upload a dataset')) {
            friendlyMessage = "It looks like you haven't uploaded a dataset yet. Please upload a dataset using the attachment button so I can analyze it for you!";
          }

          setMessages((m) => [
            ...m,
            {
              id: uid('msg'),
              role: 'assistant',
              content: friendlyMessage,
              createdAt: Date.now(),
            },
          ]);

          break;
        }
        case 'complete': {
          onCompleteRef.current?.(event.duration);
          setIsStreaming(false);
          pushTimeline({ node: 'reporter', status: 'complete', message: `Workflow complete (${(event.duration / 1000).toFixed(1)}s)` });
          break;
        }
      }
    },
    [pushTimeline]
  );

  const startStream = useCallback<WorkflowContextValue['startStream']>(
    (params, hooks) => {
      controllerRef.current?.close();
      onReportRef.current = hooks?.onReport ?? null;
      onCompleteRef.current = hooks?.onComplete ?? null;
      
      // Reset the duplicate blocker for the new prompt
      lastReportRef.current = null;

      setMessages((m) => [
        ...m,
        { id: uid('msg'), role: 'user', content: params.message, createdAt: Date.now() },
      ]);
      setNodes(emptyNodes());
      setTimeline([]);
      setPlan(null);
      setDecision(null);
      setRetryCount(0);
      setLastError(null);
      setIsStreaming(true);

      controllerRef.current = streamChat(
        { message: params.message, threadId: params.threadId, apiKey: params.apiKey, model: params.model, datasetPath: params.datasetPath },
        {
          onEvent: handleEvent,
          onClose: () => setIsStreaming(false),
        },
        { baseUrl: params.baseUrl }
      );
    },
    [handleEvent]
  );

  const stopStream = useCallback(() => {
    controllerRef.current?.close();
    controllerRef.current = null;
    setIsStreaming(false);
  }, []);

  const resetWorkflow = useCallback(() => {
    controllerRef.current?.close();
    controllerRef.current = null;
    setNodes(emptyNodes());
    setTimeline([]);
    setPlan(null);
    setReports([]);
    setDecision(null);
    setRetryCount(0);
    setLastError(null);
    setIsStreaming(false);
    lastReportRef.current = null;
  }, []);

  const clearMessages = useCallback(() => {
    controllerRef.current?.close();
    controllerRef.current = null;
    setMessages([]);
    setNodes(emptyNodes());
    setTimeline([]);
    setPlan(null);
    setReports([]);
    setDecision(null);
    setRetryCount(0);
    setLastError(null);
    setIsStreaming(false);
    lastReportRef.current = null;
  }, []);

  const loadChatHistory = useCallback((history: ChatMessage[]) => {
    controllerRef.current?.close();
    controllerRef.current = null;
    setNodes(emptyNodes());
    setTimeline([]);
    setPlan(null);
    
    // Only parse messages that actually look like reports, ignoring conversational filler
    const assistantMessages = history.filter(m => m.role === 'assistant' && (m.content || (m.charts && m.charts.length > 0)));
    const realReports = assistantMessages.filter(m => 
      (m.charts && m.charts.length > 0) || 
      /^#/.test(m.content) || 
      m.content.length > 1200
    );

    const loadedReports: WorkflowReport[] = realReports.map(m => ({
      report: m.content,
      charts: m.charts || [],
      generatedAt: m.createdAt || Date.now(),
    }));
    
    setReports(loadedReports);
    
    // Prime the deduplicator so reloading doesn't allow a duplicate on the next immediate prompt
    if (loadedReports.length > 0) {
      lastReportRef.current = loadedReports[loadedReports.length - 1].report;
    }

    setDecision(null);
    setRetryCount(0);
    setLastError(null);
    setIsStreaming(false);
    
    setMessages(history);
  }, []);

  const value = useMemo<WorkflowContextValue>(
    () => ({
      nodes,
      timeline,
      messages,
      plan,
      reports,
      decision,
      retryCount,
      isStreaming,
      lastError,
      startStream,
      stopStream,
      resetWorkflow,
      clearMessages,
      loadChatHistory,
    }),
    [nodes, timeline, messages, plan, reports, decision, retryCount, isStreaming, lastError, startStream, stopStream, resetWorkflow, clearMessages, loadChatHistory]
  );

  return <WorkflowContext.Provider value={value}>{children}</WorkflowContext.Provider>;
}

export function useWorkflow(): WorkflowContextValue {
  const ctx = useContext(WorkflowContext);
  if (!ctx) throw new Error('useWorkflow must be used within WorkflowProvider');
  return ctx;
}