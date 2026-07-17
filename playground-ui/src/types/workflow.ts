import type { Node, Edge } from '@xyflow/react';

/* ─── Node Types ─── */
export type NodeCategory = 'trigger' | 'action' | 'ai' | 'flow';

export type NodeTypeLabel = 'trigger' | 'action' | 'ai' | 'flow';

/* ─── Node Data ─── */
export interface PlaygroundNodeData {
  label: string;
  description?: string;
  category: NodeCategory;
  icon?: string;
  config?: Record<string, unknown>;
  // Execution state
  executionStatus?: 'idle' | 'running' | 'completed' | 'error' | 'skipped';
  executionDuration?: number;
  executionOutput?: string;
  executionError?: string;
}

export type PlaygroundNode = Node<PlaygroundNodeData, NodeTypeLabel>;

/* ─── Edge Data ─── */
export interface PlaygroundEdgeData {
  condition?: string;
  executionStatus?: 'idle' | 'running' | 'completed' | 'error';
}

export type PlaygroundEdge = Edge<PlaygroundEdgeData>;

/* ─── Workflow State ─── */
export interface WorkflowState {
  nodes: PlaygroundNode[];
  edges: PlaygroundEdge[];
  selectedNode: PlaygroundNode | null;
  isRunning: boolean;
  executionLog: ExecutionLogEntry[];
  templates: FlowTemplate[];
  agents: AgentInfo[];
}

/* ─── Execution Log ─── */
export interface ExecutionLogEntry {
  id: string;
  nodeId: string;
  nodeLabel: string;
  event: 'start' | 'complete' | 'error' | 'step';
  timestamp: string;
  duration?: number;
  message: string;
  data?: unknown;
}

/* ─── Flow Template ─── */
export interface FlowTemplate {
  name: string;
  description: string;
  domain?: string;
  version?: string;
  agents?: number;
  trigger?: string;
  nodes?: PlaygroundNode[];
  edges?: PlaygroundEdge[];
}

/* ─── Agent Info ─── */
export interface AgentInfo {
  id: string;
  name: string;
  type: string;
  match_score?: number;
}

/* ─── Palette Node Template ─── */
export interface PaletteNodeType {
  type: NodeTypeLabel;
  category: NodeCategory;
  label: string;
  description: string;
  icon: string;
  color: string;
  bgColor: string;
  defaultConfig?: Record<string, unknown>;
}

/* ─── API Responses ─── */
export interface ValidateResponse {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}

export interface AutoAgentsResponse {
  task: string;
  domain: string;
  agents: AgentInfo[];
  recommended_orchestrator?: string;
}

export interface TemplatesResponse {
  domain: string;
  templates: FlowTemplate[];
}

/* ─── Run Flow Response ─── */
export interface RunFlowResponse {
  execution_id: string;
  status: string;
}

export interface FlowRunEvent {
  type: 'log' | 'node_start' | 'node_complete' | 'node_error' | 'complete' | 'error';
  node_id?: string;
  node_label?: string;
  message?: string;
  duration?: number;
  data?: unknown;
  timestamp?: string;
}
