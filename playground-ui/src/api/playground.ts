import type {
  PlaygroundNode,
  PlaygroundEdge,
  ValidateResponse,
  TemplatesResponse,
  RunFlowResponse,
  AutoAgentsResponse,
  FlowRunEvent,
} from '../types/workflow';

const API_BASE = '/api';

/* ─── API Calls ─── */

export async function validateFlow(nodes: PlaygroundNode[], edges: PlaygroundEdge[]): Promise<ValidateResponse> {
  const flowYaml = JSON.stringify({ nodes, edges });
  const res = await fetch(`${API_BASE}/playground/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ yaml_content: flowYaml }),
  });
  return res.json();
}

export async function listTemplates(domain = 'accounting'): Promise<TemplatesResponse> {
  const res = await fetch(`${API_BASE}/playground/templates?domain=${domain}`);
  return res.json();
}

export async function loadTemplate(templateName: string): Promise<{ nodes: PlaygroundNode[]; edges: PlaygroundEdge[] }> {
  const res = await fetch(`${API_BASE}/playground/templates?name=${encodeURIComponent(templateName)}`);
  const data = await res.json();
  // Backend returns { domain, templates: [...] } — find the matching template
  if (data.templates) {
    const tmpl = data.templates.find((t: any) => t.name === templateName);
    if (tmpl?.nodes && tmpl?.edges) return { nodes: tmpl.nodes, edges: tmpl.edges };
  }
  return { nodes: [], edges: [] };
}

export async function runFlow(nodes: PlaygroundNode[], edges: PlaygroundEdge[]): Promise<RunFlowResponse> {
  const res = await fetch(`${API_BASE}/playground/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.type,
        label: n.data.label,
        config: n.data.config,
      })),
      edges: edges.map(e => ({
        source: e.source,
        target: e.target,
      })),
    }),
  });
  return res.json();
}

export async function autoAgents(task: string, domain: string): Promise<AutoAgentsResponse> {
  const res = await fetch(`${API_BASE}/playground/auto-agents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task, domain }),
  });
  return res.json();
}

/* ─── WebSocket Execution Stream ─── */

type StreamCallback = (event: FlowRunEvent) => void;
type StreamError = (error: string) => void;
type StreamDone = () => void;

export function connectExecutionStream(
  runId: string,
  onEvent: StreamCallback,
  onError: StreamError,
  onDone: StreamDone,
): () => void {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}${API_BASE}/playground/runs/${runId}/stream`;

  let ws: WebSocket | null = null;
  let reconnectAttempts = 0;
  const maxReconnect = 3;

  function connect() {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      reconnectAttempts = 0;
    };

    ws.onmessage = (msg) => {
      try {
        const event: FlowRunEvent = JSON.parse(msg.data);
        onEvent(event);

        if (event.type === 'complete' || event.type === 'error') {
          ws?.close();
          if (event.type === 'complete') onDone();
          if (event.type === 'error') onError(event.message || 'Execution failed');
        }
      } catch {
        // Partial message — ignore
      }
    };

    ws.onerror = () => {
      if (reconnectAttempts < maxReconnect) {
        reconnectAttempts++;
        setTimeout(connect, 1000 * reconnectAttempts);
      } else {
        onError('WebSocket connection failed after retries');
      }
    };

    ws.onclose = () => {
      // If not closed by us, try once more
      if (reconnectAttempts < maxReconnect) {
        reconnectAttempts++;
        setTimeout(connect, 1000);
      }
    };
  }

  connect();

  // Return cleanup function
  return () => {
    ws?.close();
    ws = null;
  };
}

/* ─── Palette Node Definitions ─── */

import type { PaletteNodeType, NodeCategory } from '../types/workflow';

export const PALETTE_NODES: PaletteNodeType[] = [
  // ── Triggers ──
  {
    type: 'trigger',
    category: 'trigger' as NodeCategory,
    label: 'Webhook',
    description: 'Listen for incoming HTTP requests',
    icon: '🔗',
    color: '#10b981',
    bgColor: 'rgba(16,185,129,0.12)',
    defaultConfig: { method: 'POST', path: '/webhook' },
  },
  {
    type: 'trigger',
    category: 'trigger' as NodeCategory,
    label: 'Schedule',
    description: 'Run on a cron schedule',
    icon: '⏰',
    color: '#10b981',
    bgColor: 'rgba(16,185,129,0.12)',
    defaultConfig: { cron: '0 9 * * 1' },
  },
  {
    type: 'trigger',
    category: 'trigger' as NodeCategory,
    label: 'Manual',
    description: 'Triggered by user',
    icon: '👆',
    color: '#10b981',
    bgColor: 'rgba(16,185,129,0.12)',
  },
  // ── Actions ──
  {
    type: 'action',
    category: 'action' as NodeCategory,
    label: 'Search Web',
    description: 'Search the web for information',
    icon: '🔍',
    color: '#7170ff',
    bgColor: 'rgba(113,112,255,0.12)',
    defaultConfig: { query: '', max_results: 5 },
  },
  {
    type: 'action',
    category: 'action' as NodeCategory,
    label: 'Read PDF',
    description: 'Extract text from a PDF document',
    icon: '📄',
    color: '#7170ff',
    bgColor: 'rgba(113,112,255,0.12)',
    defaultConfig: { path: '' },
  },
  {
    type: 'action',
    category: 'action' as NodeCategory,
    label: 'Send Email',
    description: 'Send an email notification',
    icon: '📧',
    color: '#7170ff',
    bgColor: 'rgba(113,112,255,0.12)',
    defaultConfig: { to: '', subject: '', body: '' },
  },
  {
    type: 'action',
    category: 'action' as NodeCategory,
    label: 'API Call',
    description: 'Make an HTTP request',
    icon: '🌐',
    color: '#7170ff',
    bgColor: 'rgba(113,112,255,0.12)',
    defaultConfig: { url: '', method: 'GET', headers: {} },
  },
  {
    type: 'action',
    category: 'action' as NodeCategory,
    label: 'Write File',
    description: 'Save output to a file',
    icon: '💾',
    color: '#7170ff',
    bgColor: 'rgba(113,112,255,0.12)',
    defaultConfig: { path: '', content: '' },
  },
  // ── AI / Agents ──
  {
    type: 'ai',
    category: 'ai' as NodeCategory,
    label: 'AI Analyst',
    description: 'Analyze data with an LLM',
    icon: '🤖',
    color: '#f59e0b',
    bgColor: 'rgba(245,158,11,0.12)',
    defaultConfig: { prompt: '', model: 'claude-sonnet-4' },
  },
  {
    type: 'ai',
    category: 'ai' as NodeCategory,
    label: 'AI Writer',
    description: 'Generate text content',
    icon: '✍️',
    color: '#f59e0b',
    bgColor: 'rgba(245,158,11,0.12)',
    defaultConfig: { prompt: '', tone: 'professional' },
  },
  {
    type: 'ai',
    category: 'ai' as NodeCategory,
    label: 'SQL Query',
    description: 'Query a database with AI',
    icon: '🗄️',
    color: '#f59e0b',
    bgColor: 'rgba(245,158,11,0.12)',
    defaultConfig: { query: '', db: '' },
  },
  {
    type: 'ai',
    category: 'ai' as NodeCategory,
    label: 'Agent Team',
    description: 'Orchestrate sub-agents',
    icon: '🧠',
    color: '#f59e0b',
    bgColor: 'rgba(245,158,11,0.12)',
    defaultConfig: { agents: [], strategy: 'sequential' },
  },
  // ── Flow Control ──
  {
    type: 'flow',
    category: 'flow' as NodeCategory,
    label: 'Condition',
    description: 'Branch based on a condition',
    icon: '🔀',
    color: '#8a8f98',
    bgColor: 'rgba(138,143,152,0.12)',
    defaultConfig: { condition: '', true_branch: '', false_branch: '' },
  },
  {
    type: 'flow',
    category: 'flow' as NodeCategory,
    label: 'Merge',
    description: 'Merge parallel branches',
    icon: '🔀',
    color: '#8a8f98',
    bgColor: 'rgba(138,143,152,0.12)',
  },
  {
    type: 'flow',
    category: 'flow' as NodeCategory,
    label: 'Loop',
    description: 'Repeat until condition met',
    icon: '🔄',
    color: '#8a8f98',
    bgColor: 'rgba(138,143,152,0.12)',
    defaultConfig: { max_iterations: 10, condition: '' },
  },
  {
    type: 'flow',
    category: 'flow' as NodeCategory,
    label: 'Delay',
    description: 'Wait before proceeding',
    icon: '⏳',
    color: '#8a8f98',
    bgColor: 'rgba(138,143,152,0.12)',
    defaultConfig: { seconds: 5 },
  },
];

export const CATEGORIES = [
  { id: 'trigger' as const, label: 'Triggers', icon: '⚡' },
  { id: 'action' as const, label: 'Actions', icon: '⚙️' },
  { id: 'ai' as const, label: 'AI & Agents', icon: '🤖' },
  { id: 'flow' as const, label: 'Flow Control', icon: '🔀' },
];
