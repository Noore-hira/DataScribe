export type NodeName =
  | 'conversation'
  | 'initialize'
  | 'supervisor'
  | 'planner'
  | 'programmer'
  | 'executor'
  | 'critic'
  | 'reporter';

export const NODE_ORDER: NodeName[] = [
  'conversation',
  'initialize',
  'supervisor',
  'planner',
  'programmer',
  'executor',
  'critic',
  'reporter',
];

export const NODE_LABELS: Record<NodeName, string> = {
  conversation: 'Conversation',
  initialize: 'Initialize',
  supervisor: 'Supervisor',
  planner: 'Planner',
  programmer: 'Programmer',
  executor: 'Executor',
  critic: 'Critic',
  reporter: 'Reporter',
};

export const NODE_DESCRIPTIONS: Record<NodeName, string> = {
  conversation: 'Receives your question and prepares the dataset context.',
  initialize: 'Loads the uploaded dataset and sets up the session.',
  supervisor: 'Routes the task and decides which agent runs next.',
  planner: 'Builds an execution plan from your request.',
  programmer: 'Generates Python code to analyse the data.',
  executor: 'Runs the code and produces charts and metrics.',
  critic: 'Reviews results and may request another iteration.',
  reporter: 'Assembles the final report and charts.',
};

export type NodeStatus =
  | 'waiting'
  | 'running'
  | 'completed'
  | 'failed'
  | 'retrying';

export interface NodeMetrics {
  analysis_tasks?: number;
  visualization_tasks?: number;
  lines_of_code?: number;
  charts_generated?: number;
  execution_status?: 'pass' | 'fail' | 'running' | 'pending';
  critic_verdict?: 'pass' | 'fail';
  retry_count?: number;
  report_generated?: boolean;
  [key: string]: unknown;
}

export interface WorkflowNodeState {
  node: NodeName;
  status: NodeStatus;
  message?: string;
  metrics?: NodeMetrics;
  progress?: number;
  startedAt?: number;
  endedAt?: number;
  durationMs?: number;
  retries?: number;
}

export type SSEEvent =
  | { event: 'node_start'; node: NodeName; progress: number; message: string; timestamp: string }
  | { event: 'node_end'; node: NodeName; metrics: NodeMetrics; progress: number; message: string; timestamp: string }
  | { event: 'decision'; decision: string }
  | { event: 'plan'; plan: string }
  | { event: 'retry'; retry_count: number; next_node: NodeName; message: string }
  | { event: 'warning'; message: string; node?: NodeName }
  | { event: 'code'; code: string }
  | { event: 'execution'; output: string }
  | { event: 'charts'; charts: string[] }
  | { event: 'critic'; verdict: string; retry: number }
  | { event: 'report'; report: string; charts: string[] }
  | { event: 'message'; content: string } 
  | { event: 'text'; content: string }    
  | { event: 'token'; content: string } // 🛠️ ADDED: The new streaming token event
  | { event: 'error'; message: string; node?: NodeName }
  | { event: 'complete'; duration: number };

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  charts?: string[];
  createdAt: number;
}

export interface TimelineEntry {
  id: string;
  node: NodeName;
  status: 'start' | 'end' | 'info' | 'retry' | 'warning' | 'decision' | 'report' | 'complete' | 'error';
  message: string;
  createdAt: number;
}

export interface DatasetMeta {
  filename: string;
  rows: number;
  columns: number;
  threadId: string;
  uploadedAt: number;
  path: string;
}

export interface WorkflowReport {
  report: string;
  charts: string[];
  generatedAt: number;
  durationMs?: number;
}

export interface PlanSummary {
  plan: string;
  createdAt: number;
}

export interface SessionRecord {
  id: string;
  threadId: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  filename?: string;
}

export const GROQ_MODELS = [
  { value: 'llama-3.3-70b-versatile', label: 'llama-3.3-70b-versatile' },
  { value: 'llama-3.1-8b-instant', label: 'llama-3.1-8b-instant' },
  { value: 'openai/gpt-oss-120b', label: 'openai/gpt-oss-120b' },
] as const;

export type GroqModel = (typeof GROQ_MODELS)[number]['value'];

export const DEFAULT_BACKEND_URL = 'https://da-5f4c85c6edef485aae966f71f553a8f0.ecs.us-east-1.on.aws';

export const SSE_RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 12000];