'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Header } from '@/components/layout/header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArchitectureMap, ArchitectureMapLegend } from '@/components/charts/ArchitectureMap';
import {
  getApp,
  getArchitectureMap,
  type App,
  type ArchitectureMap as ArchitectureMapType,
} from '@/lib/api/client';
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  RefreshCw,
  Download,
  Maximize2,
} from 'lucide-react';

export default function ArchitecturePage() {
  const params = useParams();
  const router = useRouter();
  const appId = params.id as string;

  const [app, setApp] = useState<App | null>(null);
  const [architecture, setArchitecture] = useState<ArchitectureMapType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    loadData();
  }, [appId]);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const [appData, archData] = await Promise.all([
        getApp(appId),
        getArchitectureMap(appId),
      ]);
      setApp(appData);
      setArchitecture(archData);
    } catch (err) {
      console.error('Failed to load architecture:', err);
      setError(err instanceof Error ? err.message : 'Failed to load architecture');
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    try {
      setRefreshing(true);
      const archData = await getArchitectureMap(appId);
      setArchitecture(archData);
    } catch (err) {
      console.error('Failed to refresh architecture:', err);
    } finally {
      setRefreshing(false);
    }
  }

  function toggleFullscreen() {
    setIsFullscreen(!isFullscreen);
  }

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <Header
          title="Architecture Map"
          description="Loading..."
        />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full">
        <Header
          title="Architecture Map"
          description="Error loading architecture"
        />
        <div className="flex-1 p-6">
          <Card className="border-red-500/20 bg-red-500/10">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <AlertCircle className="h-12 w-12 text-red-400 mb-4" />
              <h3 className="text-lg font-medium text-red-400 mb-2">Failed to Load</h3>
              <p className="text-sm text-secondary-400 mb-4">{error}</p>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => router.back()}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Go Back
                </Button>
                <Button onClick={loadData}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Retry
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full ${isFullscreen ? 'fixed inset-0 z-50 bg-secondary-950' : ''}`}>
      <Header
        title={`Architecture - ${app?.name || 'Project'}`}
        description="Visual representation of your service architecture and connections"
      />

      <div className="flex-1 p-6 flex flex-col gap-4">
        {/* Actions Bar */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Projects
          </Button>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={toggleFullscreen}>
              <Maximize2 className="h-4 w-4 mr-2" />
              {isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            </Button>
          </div>
        </div>

        {/* Architecture Map */}
        <Card className="flex-1 overflow-hidden">
          <CardHeader className="py-3 border-b border-secondary-800">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Service Topology</CardTitle>
              <div className="flex items-center gap-4 text-sm text-secondary-400">
                <span>{architecture?.nodes.length || 0} services</span>
                <span>{architecture?.edges.length || 0} connections</span>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0 h-[calc(100%-60px)]">
            {architecture && (
              <ArchitectureMap
                nodes={architecture.nodes}
                edges={architecture.edges}
              />
            )}
          </CardContent>
        </Card>

        {/* Legend */}
        {!isFullscreen && <ArchitectureMapLegend />}

        {/* Service Details Summary */}
        {architecture && architecture.nodes.length > 0 && !isFullscreen && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {['healthy', 'warning', 'critical'].map((status) => {
              const count = architecture.nodes.filter((n) => n.status === status).length;
              if (count === 0) return null;
              const colors = {
                healthy: 'text-green-400 bg-green-500/10 border-green-500/20',
                warning: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
                critical: 'text-red-400 bg-red-500/10 border-red-500/20',
              };
              return (
                <Card key={status} className={`${colors[status as keyof typeof colors]}`}>
                  <CardContent className="p-4">
                    <p className="text-2xl font-bold">{count}</p>
                    <p className="text-sm capitalize">{status} Services</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
