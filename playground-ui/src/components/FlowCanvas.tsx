import { useCallback, useRef, useState, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type ReactFlowInstance,
  type Connection,
  type EdgeChange,
  type NodeChange,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  ReactFlowProvider,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { PlaygroundNode } from './nodes/PlaygroundNode';
import { NodePalette } from './NodePalette';
import { PropertiesPanel } from './PropertiesPanel';
import { ExecutionTrace } from './ExecutionTrace';
import {
  PALETTE_NODES,
  CATEGORIES,
  runFlow as apiRunFlow,
  connectExecutionStream,
  listTemplates as apiListTemplates,
  loadTemplate as apiLoadTemplate,
  autoAgents as apiAutoAgents,
  validateFlow,
} from '../api/playground';
import type {
  PlaygroundNode as PlaygroundNodeType,
  PlaygroundEdge as PlaygroundEdgeType,
  PaletteNodeType,
  ExecutionLogEntry,
  FlowTemplate,
  FlowRunEvent,
} from '../types/workflow';

const nodeTypes = {
  trigger: PlaygroundNode,
  action: PlaygroundNode,
  ai: PlaygroundNode,
  flow: PlaygroundNode,
};

const defaultEdgeOptions = {
  style: { stroke: 'rgba(255,255,255,0.08)', strokeWidth: 2 },
  type: 'smoothstep',
  animated: false,
};

let nodeCounter = 0;
let logCounter = 0;
// eslint-disable-next-line prefer-const

function FlowCanvasInner() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const [nodes, setNodes] = useState<PlaygroundNodeType[]>([]);
  const [edges, setEdges] = useState<PlaygroundEdgeType[]>([]);
  const [selectedNode, setSelectedNode] = useState<PlaygroundNodeType | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [executionLogs, setExecutionLogs] = useState<ExecutionLogEntry[]>([]);
  const [templateMenuOpen, setTemplateMenuOpen] = useState(false);
  const [templates, setTemplates] = useState<FlowTemplate[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  /* ─── Load templates on mount ─── */
  useEffect(() => {
    async function load() {
      setTemplatesLoading(true);
      try {
        const data = await apiListTemplates();
        setTemplates(data.templates || []);
      } catch {
        // Templates endpoint may not be available — use sample data
        setTemplates([]);
      }
      setTemplatesLoading(false);
    }
    load();
  }, []);

  /* ─── Cleanup WebSocket on unmount ─── */
  useEffect(() => {
    return () => {
      cleanupRef.current?.();
    };
  }, []);

  /* ─── Node/Edge Changes ─── */
  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setNodes(nds => applyNodeChanges(changes, nds) as PlaygroundNodeType[]);
    },
    [],
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      setEdges(eds => applyEdgeChanges(changes, eds) as PlaygroundEdgeType[]);
    },
    [],
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges(eds => addEdge({
        ...connection,
        style: { stroke: 'rgba(255,255,255,0.08)', strokeWidth: 2 },
        type: 'smoothstep',
      }, eds) as PlaygroundEdgeType[]);
    },
    [],
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: PlaygroundNodeType) => {
      setSelectedNode(node);
    },
    [],
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  /* ─── Drag & Drop from Palette ─── */
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      if (!reactFlowInstance) return;

      const dataStr = event.dataTransfer.getData('application/hiveos-node');
      if (!dataStr) return;

      try {
        const paletteNode: PaletteNodeType = JSON.parse(dataStr);
        const position = reactFlowInstance.screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });

        nodeCounter++;
        const newNode: PlaygroundNodeType = {
          id: `node_${Date.now()}_${nodeCounter}`,
          type: paletteNode.type,
          position,
          data: {
            label: `${paletteNode.label} ${nodeCounter}`,
            description: paletteNode.description,
            category: paletteNode.category,
            icon: paletteNode.icon,
            config: paletteNode.defaultConfig || {},
            executionStatus: 'idle',
          },
        };

        setNodes(nds => [...nds, newNode]);
      } catch {
        // failed to parse — silently ignore
      }
    },
    [reactFlowInstance],
  );

  /* ─── Update / Delete Node ─── */
  const onUpdateNode = useCallback(
    (nodeId: string, data: Partial<PlaygroundNodeType['data']>) => {
      setNodes(nds =>
        nds.map(n =>
          n.id === nodeId
            ? { ...n, data: { ...n.data, ...data } }
            : n,
        ),
      );
      setSelectedNode(prev =>
        prev?.id === nodeId
          ? { ...prev, data: { ...prev.data, ...data } }
          : prev,
      );
    },
    [],
  );

  const onDeleteNode = useCallback(
    (nodeId: string) => {
      setNodes(nds => nds.filter(n => n.id !== nodeId));
      setEdges(eds => eds.filter(e => e.source !== nodeId && e.target !== nodeId));
      setSelectedNode(null);
    },
    [],
  );

  const onClearCanvas = useCallback(() => {
    cleanupRef.current?.();
    setNodes([]);
    setEdges([]);
    setSelectedNode(null);
    setExecutionLogs([]);
    setIsRunning(false);
    setCurrentRunId(null);
  }, []);

  /* ─── Add Log ─── */
  const addLogEntry = useCallback((log: ExecutionLogEntry) => {
    setExecutionLogs(prev => [...prev, log]);
  }, []);

  /* ─── Handle WebSocket Events ─── */
  const handleFlowEvent = useCallback((event: FlowRunEvent) => {
    logCounter++;

    // Update node execution status
    if (event.node_id) {
      setNodes(nds =>
        nds.map(n => {
          if (n.id !== event.node_id) return n;
          let status: PlaygroundNodeType['data']['executionStatus'] = 'idle';
          if (event.type === 'node_start') status = 'running';
          else if (event.type === 'node_complete') status = 'completed';
          else if (event.type === 'node_error') status = 'error';

          return {
            ...n,
            data: {
              ...n.data,
              executionStatus: status,
              executionDuration: event.duration,
              executionError: event.type === 'node_error' ? event.message : undefined,
            },
          };
        }),
      );

      // Update edges
      if (event.type === 'node_start' || event.type === 'node_complete') {
        setEdges(eds =>
          eds.map(e =>
            e.source === event.node_id
              ? {
                  ...e,
                  data: { ...e.data, executionStatus: event.type === 'node_start' ? 'running' as const : 'completed' as const },
                  animated: event.type === 'node_start',
                }
              : e,
          ),
        );
      }

      if (event.type === 'node_error') {
        setEdges(eds =>
          eds.map(e =>
            e.source === event.node_id
              ? { ...e, data: { ...e.data, executionStatus: 'error' as const }, animated: false }
              : e,
          ),
        );
      }
    }

    // Map event type to log event
    const logEventMap: Record<string, ExecutionLogEntry['event']> = {
      node_start: 'start',
      node_complete: 'complete',
      node_error: 'error',
      log: 'step',
      complete: 'complete',
      error: 'error',
    };

    addLogEntry({
      id: `log_${logCounter}`,
      nodeId: event.node_id || 'system',
      nodeLabel: event.node_label || 'Flow',
      event: logEventMap[event.type] || 'step',
      timestamp: event.timestamp || new Date().toISOString(),
      message: event.message || event.type,
      duration: event.duration,
      data: event.data,
    });
  }, [addLogEntry]);

  /* ─── Run Flow (Real Backend) ─── */
  const onRunFlow = useCallback(async () => {
    if (nodes.length === 0) return;

    // Cleanup previous run
    cleanupRef.current?.();

    setIsRunning(true);
    setExecutionLogs([]);
    setCurrentRunId(null);

    // Reset all nodes
    setNodes(nds =>
      nds.map(n => ({
        ...n,
        data: { ...n.data, executionStatus: 'idle' as const, executionDuration: undefined, executionOutput: undefined, executionError: undefined },
      })),
    );
    setEdges(eds =>
      eds.map(e => ({ ...e, data: { ...e.data, executionStatus: 'idle' as const }, animated: false })),
    );

    try {
      // 1. Validate first
      logCounter++;
      addLogEntry({
        id: `log_${logCounter}`,
        nodeId: 'system',
        nodeLabel: 'System',
        event: 'step',
        timestamp: new Date().toISOString(),
        message: 'Validating flow...',
      });

      const validation = await validateFlow(nodes, edges);
      if (!validation.valid) {
        logCounter++;
        addLogEntry({
          id: `log_${logCounter}`,
          nodeId: 'system',
          nodeLabel: 'System',
          event: 'error',
          timestamp: new Date().toISOString(),
          message: `Validation failed: ${(validation.errors || []).join(', ')}`,
        });
        setIsRunning(false);
        return;
      }

      // 2. Submit run
      logCounter++;
      addLogEntry({
        id: `log_${logCounter}`,
        nodeId: 'system',
        nodeLabel: 'System',
        event: 'step',
        timestamp: new Date().toISOString(),
        message: 'Submitting flow for execution...',
      });

      const { execution_id } = await apiRunFlow(nodes, edges);
      setCurrentRunId(execution_id);

      logCounter++;
      addLogEntry({
        id: `log_${logCounter}`,
        nodeId: 'system',
        nodeLabel: 'System',
        event: 'start',
        timestamp: new Date().toISOString(),
        message: `Execution started (ID: ${execution_id.slice(0, 8)}...)`,
      });

      // 3. Connect to WebSocket stream
      cleanupRef.current = connectExecutionStream(
        execution_id,
        handleFlowEvent,
        (error) => {
          logCounter++;
          addLogEntry({
            id: `log_${logCounter}`,
            nodeId: 'system',
            nodeLabel: 'System',
            event: 'error',
            timestamp: new Date().toISOString(),
            message: `Stream error: ${error}`,
          });
          setIsRunning(false);
        },
        () => {
          logCounter++;
          addLogEntry({
            id: `log_${logCounter}`,
            nodeId: 'system',
            nodeLabel: 'Flow',
            event: 'complete',
            timestamp: new Date().toISOString(),
            message: 'Execution completed',
          });
          setIsRunning(false);
          setCurrentRunId(null);
        },
      );
    } catch (err) {
      logCounter++;
      addLogEntry({
        id: `log_${logCounter}`,
        nodeId: 'system',
        nodeLabel: 'System',
        event: 'error',
        timestamp: new Date().toISOString(),
        message: `Failed to start execution: ${err instanceof Error ? err.message : String(err)}`,
      });
      setIsRunning(false);
    }
  }, [nodes, edges, addLogEntry, handleFlowEvent]);

  /* ─── Load Template ─── */
  const onLoadTemplate = useCallback(async (templateName: string) => {
    setTemplateMenuOpen(false);
    cleanupRef.current?.();
    setExecutionLogs([]);
    setIsRunning(false);

    try {
      logCounter++;
      addLogEntry({
        id: `log_${logCounter}`,
        nodeId: 'system',
        nodeLabel: 'System',
        event: 'step',
        timestamp: new Date().toISOString(),
        message: `Loading template: ${templateName}`,
      });

      const { nodes: tmplNodes, edges: tmplEdges } = await apiLoadTemplate(templateName);
      if (tmplNodes.length === 0) {
        // Fallback: try the sample templates
        addLogEntry({
          id: `log_${logCounter + 1}`,
          nodeId: 'system',
          nodeLabel: 'System',
          event: 'error',
          timestamp: new Date().toISOString(),
          message: `Template "${templateName}" not found on backend — using sample`,
        });
        return;
      }

      setNodes(tmplNodes);
      setEdges(tmplEdges);
      setSelectedNode(null);

      addLogEntry({
        id: `log_${logCounter + 1}`,
        nodeId: 'system',
        nodeLabel: 'System',
        event: 'complete',
        timestamp: new Date().toISOString(),
        message: `Template "${templateName}" loaded (${tmplNodes.length} nodes)`,
      });
    } catch {
      addLogEntry({
        id: `log_${logCounter + 1}`,
        nodeId: 'system',
        nodeLabel: 'System',
        event: 'error',
        timestamp: new Date().toISOString(),
        message: `Failed to load template "${templateName}"`,
      });
    }
  }, [addLogEntry]);

  /* ─── Auto-Agents ─── */
  const onAutoAgents = useCallback(async () => {
    const task = prompt('Describe your workflow task:');
    if (!task || !task.trim()) return;

    const domain = prompt('Domain (e.g. accounting, research, general):', 'general') || 'general';

    logCounter++;
    addLogEntry({
      id: `log_${logCounter}`,
      nodeId: 'system',
      nodeLabel: 'AI',
      event: 'start',
      timestamp: new Date().toISOString(),
      message: `Analyzing task: "${task.slice(0, 60)}..."`,
    });

    try {
      const result = await apiAutoAgents(task, domain);
      logCounter++;
      addLogEntry({
        id: `log_${logCounter + 1}`,
        nodeId: 'system',
        nodeLabel: 'AI',
        event: 'complete',
        timestamp: new Date().toISOString(),
        message: `Found ${result.agents.length} agents for "${result.domain}" domain`,
        data: result,
      });

      // Auto-create AI node for each suggested agent
      const startPos = { x: 100, y: 100 };
      const newNodes: PlaygroundNodeType[] = result.agents.map((agent, i) => ({
        id: `auto_agent_${Date.now()}_${i}`,
        type: 'ai' as const,
        position: { x: startPos.x + (i * 220), y: startPos.y + (i % 3) * 120 },
        data: {
          label: agent.name,
          category: 'ai',
          icon: '🧠',
          config: { agent_id: agent.id, type: agent.type },
          executionStatus: 'idle',
        },
      }));

      setNodes(nds => [...nds, ...newNodes]);
    } catch (err) {
      addLogEntry({
        id: `log_${logCounter + 1}`,
        nodeId: 'system',
        nodeLabel: 'AI',
        event: 'error',
        timestamp: new Date().toISOString(),
        message: `Auto-agents failed: ${err instanceof Error ? err.message : String(err)}`,
      });
    }
  }, [addLogEntry]);

  /* ─── Sample templates as fallback ─── */
  const sampleFlows: FlowTemplate[] = templates.length > 0 ? templates : [
    { name: 'Financial Report', description: 'Generate a financial report with AI analysis', agents: 4, trigger: 'Manual' },
    { name: 'Web Research', description: 'Search, extract, and summarize web content', agents: 3, trigger: 'Manual' },
    { name: 'Data Pipeline', description: 'Extract, transform, and load data', agents: 5, trigger: 'Schedule' },
  ];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        height: '100%',
      }}
    >
      {/* Toolbar */}
      <div
        style={{
          height: 44,
          background: 'var(--bg-panel)',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Templates menu */}
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setTemplateMenuOpen(!templateMenuOpen)}
              style={toolbarButtonStyle}
            >
              📋 Templates
              {templatesLoading && (
                <span style={{ fontSize: 10, color: 'var(--text-quaternary)', marginLeft: 4 }}>loading...</span>
              )}
            </button>
            {templateMenuOpen && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  marginTop: 4,
                  width: 260,
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                  zIndex: 100,
                  overflow: 'hidden',
                  maxHeight: 320,
                  overflowY: 'auto',
                }}
              >
                <div style={{ padding: '8px 12px', fontSize: 11, color: 'var(--text-quaternary)', borderBottom: '1px solid var(--border-subtle)' }}>
                  {templates.length > 0 ? `${templates.length} templates available` : 'Using sample templates'}
                </div>
                {sampleFlows.map(flow => (
                  <button
                    key={flow.name}
                    onClick={() => onLoadTemplate(flow.name)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      width: '100%',
                      padding: '10px 12px',
                      background: 'transparent',
                      border: 'none',
                      borderBottom: '1px solid var(--border-subtle)',
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      fontFamily: 'var(--font-sans)',
                      fontSize: 12,
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-surface-hover)'; }}
                    onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 510, lineHeight: 1.3 }}>{flow.name}</div>
                      <div style={{ fontSize: 10, color: 'var(--text-quaternary)', lineHeight: 1.3, marginTop: 1 }}>
                        {flow.description}
                      </div>
                    </div>
                    {flow.agents && (
                      <span style={{ fontSize: 10, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
                        {flow.agents} agents
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          <button onClick={onClearCanvas} style={toolbarButtonStyle}>
            🗑 New
          </button>

          {/* Auto-Agents */}
          <button onClick={onAutoAgents} style={toolbarButtonStyle}>
            🤖 Auto-Agents
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Status */}
          <span
            style={{
              fontSize: 11,
              color: 'var(--text-quaternary)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {nodes.length} nodes · {edges.length} connections
          </span>

          {/* Run button */}
          <button
            onClick={onRunFlow}
            disabled={isRunning || nodes.length === 0}
            style={{
              ...toolbarButtonStyle,
              background: isRunning
                ? 'rgba(113,112,255,0.1)'
                : 'rgba(16,185,129,0.1)',
              border: `1px solid ${
                isRunning ? 'rgba(113,112,255,0.3)' : 'rgba(16,185,129,0.3)'
              }`,
              color: isRunning ? '#7170ff' : '#10b981',
              fontWeight: 510,
              cursor: isRunning ? 'not-allowed' : 'pointer',
            }}
          >
            {isRunning ? '⏳ Running...' : '▶ Run Flow'}
          </button>
        </div>
      </div>

      {/* Main area: Palette + Canvas + Properties */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left: Node Palette */}
        <NodePalette onDragStart={() => {}} />

        {/* Center: Flow Canvas */}
        <div ref={reactFlowWrapper} style={{ flex: 1, position: 'relative' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            defaultEdgeOptions={defaultEdgeOptions}
            fitView
            colorMode="dark"
            deleteKeyCode="Backspace"
            snapToGrid
            snapGrid={[16, 16]}
            style={{ background: 'var(--bg-deep)' }}
          >
            <Background color="rgba(255,255,255,0.04)" gap={24} size={1} />
            <Controls
              showInteractive={false}
              style={{ bottom: 12, left: 12 }}
            />
            <MiniMap
              nodeColor={(node) => {
                const cat = (node.data as any)?.category;
                const typeColors: Record<string, string> = {
                  trigger: '#10b981',
                  action: '#7170ff',
                  ai: '#f59e0b',
                  flow: '#8a8f98',
                };
                return typeColors[cat] || '#62666d';
              }}
              maskColor="rgba(0,0,0,0.7)"
              style={{ bottom: 48, right: 12, width: 160, height: 100 }}
            />
          </ReactFlow>
        </div>

        {/* Right: Properties Panel */}
        <PropertiesPanel
          node={selectedNode}
          onUpdateNode={onUpdateNode}
          onDeleteNode={onDeleteNode}
        />
      </div>

      {/* Bottom: Execution Trace */}
      <ExecutionTrace
        logs={executionLogs}
        isRunning={isRunning}
        onClear={() => setExecutionLogs([])}
      />
    </div>
  );
}

export function FlowCanvas() {
  return (
    <ReactFlowProvider>
      <FlowCanvasInner />
    </ReactFlowProvider>
  );
}

const toolbarButtonStyle: React.CSSProperties = {
  background: 'rgba(255,255,255,0.03)',
  border: '1px solid var(--border)',
  borderRadius: 6,
  color: 'var(--text-secondary)',
  padding: '6px 12px',
  fontSize: 12,
  fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  gap: 6,
  transition: 'all 0.15s ease',
};
