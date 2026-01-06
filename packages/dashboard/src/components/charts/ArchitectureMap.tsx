'use client';

import { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionLineType,
  MarkerType,
  NodeProps,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Database,
  Server,
  Globe,
  HardDrive,
  MonitorSmartphone,
  Cloud,
  Wifi,
  AlertCircle,
} from 'lucide-react';
import { ServiceNode as ServiceNodeType, ServiceEdge } from '@/lib/api/client';

// Node status colors
const statusColors = {
  healthy: {
    background: 'rgba(16, 185, 129, 0.15)',
    border: '#10B981',
    text: '#10B981',
  },
  warning: {
    background: 'rgba(245, 158, 11, 0.15)',
    border: '#F59E0B',
    text: '#F59E0B',
  },
  critical: {
    background: 'rgba(239, 68, 68, 0.15)',
    border: '#EF4444',
    text: '#EF4444',
  },
};

// Node type icons
const nodeIcons: Record<string, React.ElementType> = {
  database: Database,
  api: Server,
  external: Globe,
  cache: HardDrive,
  frontend: MonitorSmartphone,
  storage: Cloud,
};

// Custom node data type
interface ServiceNodeData extends Record<string, unknown> {
  name: string;
  type: string;
  status: string;
  latency?: number;
  error_rate?: number;
  url?: string;
}

// Custom node component
function ServiceNodeComponent({ data }: NodeProps<Node<ServiceNodeData>>) {
  const nodeData = data as unknown as ServiceNodeData;
  const Icon = nodeIcons[nodeData.type] || Server;
  const colors = statusColors[nodeData.status as keyof typeof statusColors] || statusColors.healthy;

  return (
    <div
      className="px-4 py-3 rounded-xl shadow-lg min-w-[160px] transition-all duration-200 hover:scale-105"
      style={{
        background: colors.background,
        border: `2px solid ${colors.border}`,
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-secondary-500 !border-secondary-400"
      />

      <div className="flex items-center gap-3">
        <div
          className="p-2 rounded-lg"
          style={{ background: `${colors.border}20` }}
        >
          <Icon className="h-5 w-5" style={{ color: colors.border }} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">{nodeData.name}</p>
          <p className="text-xs text-secondary-400 capitalize">{nodeData.type}</p>
        </div>
      </div>

      {/* Status indicator */}
      <div className="mt-2 flex items-center justify-between text-xs">
        <div className="flex items-center gap-1">
          <span
            className="h-2 w-2 rounded-full animate-pulse"
            style={{ background: colors.border }}
          />
          <span style={{ color: colors.text }} className="capitalize">
            {nodeData.status}
          </span>
        </div>
        {nodeData.latency && (
          <span className="text-secondary-400">{nodeData.latency}ms</span>
        )}
      </div>

      {/* Error rate if critical */}
      {nodeData.error_rate && nodeData.error_rate > 0 && (
        <div className="mt-1 flex items-center gap-1 text-xs text-red-400">
          <AlertCircle className="h-3 w-3" />
          <span>{(nodeData.error_rate * 100).toFixed(1)}% errors</span>
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-secondary-500 !border-secondary-400"
      />
    </div>
  );
}

// Node types for ReactFlow
const nodeTypes = {
  serviceNode: ServiceNodeComponent,
};

// Default edge options
const defaultEdgeOptions = {
  type: 'smoothstep',
  animated: true,
  style: { stroke: '#6B7280', strokeWidth: 2 },
  markerEnd: {
    type: MarkerType.ArrowClosed,
    color: '#6B7280',
  },
};

interface ArchitectureMapProps {
  nodes: ServiceNodeType[];
  edges: ServiceEdge[];
  className?: string;
}

export function ArchitectureMap({ nodes: serviceNodes, edges: serviceEdges, className }: ArchitectureMapProps) {
  // Convert API nodes to ReactFlow nodes with layout
  const initialNodes: Node[] = useMemo(() => {
    // Group nodes by type for layout
    const typeGroups: Record<string, ServiceNodeType[]> = {};
    serviceNodes.forEach((node) => {
      if (!typeGroups[node.type]) typeGroups[node.type] = [];
      typeGroups[node.type].push(node);
    });

    // Define vertical positions for each type
    const typeYPositions: Record<string, number> = {
      frontend: 0,
      api: 150,
      cache: 300,
      database: 300,
      external: 450,
      storage: 450,
    };

    // Calculate positions
    const positioned: Node[] = [];
    const typeIndexes: Record<string, number> = {};

    serviceNodes.forEach((node) => {
      const type = node.type;
      if (typeIndexes[type] === undefined) typeIndexes[type] = 0;

      const countOfType = typeGroups[type]?.length || 1;
      const index = typeIndexes[type]++;

      // Calculate x position to center nodes of same type
      const spacing = 220;
      const totalWidth = (countOfType - 1) * spacing;
      const startX = 400 - totalWidth / 2;
      const x = startX + index * spacing;

      const y = typeYPositions[type] ?? 300;

      positioned.push({
        id: node.id,
        type: 'serviceNode',
        position: { x, y },
        data: {
          name: node.name,
          type: node.type,
          status: node.status,
          latency: node.latency,
          error_rate: node.error_rate,
          url: node.url,
        },
      });
    });

    return positioned;
  }, [serviceNodes]);

  // Convert API edges to ReactFlow edges
  const initialEdges: Edge[] = useMemo(() => {
    return serviceEdges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#6B7280', strokeWidth: 2 },
      labelStyle: { fill: '#9CA3AF', fontSize: 12 },
      labelBgStyle: { fill: '#1F2937', fillOpacity: 0.8 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#6B7280',
      },
    }));
  }, [serviceEdges]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes when props change
  useMemo(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  if (serviceNodes.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center h-full min-h-[400px] ${className}`}>
        <Wifi className="h-12 w-12 text-secondary-500 mb-4" />
        <h3 className="text-lg font-medium text-secondary-300 mb-2">No Services Connected</h3>
        <p className="text-sm text-secondary-500 text-center max-w-md">
          Connect your services to see your architecture map. The SDK will automatically detect
          and map your database, cache, and external API connections.
        </p>
      </div>
    );
  }

  return (
    <div className={`h-full min-h-[500px] ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        connectionLineType={ConnectionLineType.SmoothStep}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.5}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#374151" gap={20} size={1} />
        <Controls
          className="!bg-secondary-800 !border-secondary-700 !rounded-lg [&>button]:!bg-secondary-800 [&>button]:!border-secondary-700 [&>button]:!text-secondary-300 [&>button:hover]:!bg-secondary-700"
        />
        <MiniMap
          nodeColor={(node) => {
            const status = node.data?.status || 'healthy';
            return statusColors[status as keyof typeof statusColors]?.border || '#6B7280';
          }}
          maskColor="rgba(0, 0, 0, 0.8)"
          className="!bg-secondary-900 !border-secondary-700 !rounded-lg"
        />
      </ReactFlow>
    </div>
  );
}

// Legend component for the map
export function ArchitectureMapLegend() {
  const legendItems = [
    { type: 'frontend', icon: MonitorSmartphone, label: 'Frontend' },
    { type: 'api', icon: Server, label: 'API Server' },
    { type: 'database', icon: Database, label: 'Database' },
    { type: 'cache', icon: HardDrive, label: 'Cache' },
    { type: 'external', icon: Globe, label: 'External API' },
    { type: 'storage', icon: Cloud, label: 'Storage' },
  ];

  const statusItems = [
    { status: 'healthy', label: 'Healthy' },
    { status: 'warning', label: 'Warning' },
    { status: 'critical', label: 'Critical' },
  ];

  return (
    <div className="flex flex-wrap gap-4 p-4 bg-secondary-800/50 rounded-lg">
      <div className="flex flex-wrap gap-3">
        <span className="text-xs text-secondary-400 font-medium">Types:</span>
        {legendItems.map((item) => (
          <div key={item.type} className="flex items-center gap-1.5">
            <item.icon className="h-3.5 w-3.5 text-secondary-400" />
            <span className="text-xs text-secondary-300">{item.label}</span>
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-3">
        <span className="text-xs text-secondary-400 font-medium">Status:</span>
        {statusItems.map((item) => (
          <div key={item.status} className="flex items-center gap-1.5">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ background: statusColors[item.status as keyof typeof statusColors].border }}
            />
            <span className="text-xs text-secondary-300">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
