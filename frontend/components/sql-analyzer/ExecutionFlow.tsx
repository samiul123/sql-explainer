'use client';

import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

interface ExecutionStep {
  step: number;
  clause: string;
  description: string;
  sql?: string;
}

interface ExecutionFlowProps {
  steps: ExecutionStep[];
}

export function ExecutionFlow({ steps }: ExecutionFlowProps) {
  const initialNodes: Node[] = steps.map((step, index) => ({
    id: step.step.toString(),
    type: 'default',
    data: { 
      label: (
        <div className="text-xs py-1 px-2">
          <div className="font-bold text-sm mb-1">{step.step}. {step.clause}</div>
          <div className="text-white text-xs mb-1">{step.description}</div>
          {step.sql && (
            <div className="text-white text-xs font-mono mt-1 max-w-[200px] truncate">
              {step.sql}
            </div>
          )}
        </div>
      ) 
    },
    position: { x: 250, y: index * 120 },
    style: {
      background: getStepColor(step.clause),
      border: '2px solid rgba(255, 255, 255, 0.2)',
      borderRadius: '12px',
      padding: '12px',
      width: 280,
      color: '#fff',
    },
  }));

  const initialEdges: Edge[] = steps.slice(0, -1).map((step, index) => ({
    id: `e${index}`,
    source: step.step.toString(),
    target: steps[index + 1].step.toString(),
    animated: true,
    style: { 
      stroke: 'rgba(255, 255, 255, 0.3)',
      strokeWidth: 2,
    },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: 'rgba(255, 255, 255, 0.3)',
    },
  }));

  const [nodes] = useNodesState(initialNodes);
  const [edges] = useEdgesState(initialEdges);

  return (
    <div style={{ height: '600px', width: '100%' }} className="bg-slate-900 rounded-xl border border-white/10">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        minZoom={0.5}
        maxZoom={1.5}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
      >
        <Background 
          color="rgba(255, 255, 255, 0.1)" 
          variant={BackgroundVariant.Dots}
          gap={16}
        />
        <Controls 
          style={{
            backgroundColor: 'rgba(30, 41, 59, 0.8)',
            color: '#fff',
            borderColor: 'rgba(255, 255, 255, 0.2)',
          }}
        />
      </ReactFlow>
    </div>
  );
}

function getStepColor(clause: string): string {
  const colors: Record<string, string> = {
    'WITH (CTE)': '#3b82f6',  // blue
    'FROM': '#10b981',        // green
    'JOIN': '#f59e0b',        // amber
    'WHERE': '#ef4444',       // red
    'GROUP BY': '#8b5cf6',    // purple
    'HAVING': '#ec4899',      // pink
    'SELECT': '#06b6d4',      // cyan
    'DISTINCT': '#14b8a6',    // teal
    'ORDER BY': '#a855f7',    // purple
    'LIMIT': '#6366f1',       // indigo
  };
  return colors[clause] || 'rgba(51, 65, 85, 0.8)';  // slate
}
