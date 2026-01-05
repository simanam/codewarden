'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState } from 'react';
import { Header } from '@/components/layout/header';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Copy, Check, MoreVertical, Key, Loader2, AlertCircle } from 'lucide-react';
import { getApps, createApp, getApiKeys, createApiKey, type App, type ApiKey } from '@/lib/api/client';

export default function ProjectsPage() {
  const [apps, setApps] = useState<App[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createEnv, setCreateEnv] = useState('production');
  const [createFramework, setCreateFramework] = useState('');
  const [creating, setCreating] = useState(false);

  // API Key modal state
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [selectedApp, setSelectedApp] = useState<App | null>(null);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [newKey, setNewKey] = useState<ApiKey | null>(null);
  const [loadingKeys, setLoadingKeys] = useState(false);
  const [creatingKey, setCreatingKey] = useState(false);

  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    loadApps();
  }, []);

  async function loadApps() {
    try {
      setLoading(true);
      const data = await getApps();
      setApps(data);
    } catch (err) {
      console.error('Failed to load apps:', err);
      setError(err instanceof Error ? err.message : 'Failed to load apps');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateApp() {
    if (!createName.trim()) return;

    try {
      setCreating(true);
      const app = await createApp({
        name: createName,
        environment: createEnv,
        framework: createFramework || undefined,
      });
      setApps((prev) => [app, ...prev]);
      setShowCreateModal(false);
      setCreateName('');
      setCreateEnv('production');
      setCreateFramework('');

      // Show API key modal for the new app
      setSelectedApp(app);
      setShowKeyModal(true);
      await loadApiKeys(app.id);
    } catch (err) {
      console.error('Failed to create app:', err);
      setError(err instanceof Error ? err.message : 'Failed to create app');
    } finally {
      setCreating(false);
    }
  }

  async function loadApiKeys(appId: string) {
    try {
      setLoadingKeys(true);
      const keys = await getApiKeys(appId);
      setApiKeys(keys);
    } catch (err) {
      console.error('Failed to load API keys:', err);
    } finally {
      setLoadingKeys(false);
    }
  }

  async function handleCreateKey() {
    if (!selectedApp) return;

    try {
      setCreatingKey(true);
      const key = await createApiKey(selectedApp.id, 'Default Key', 'live');
      setNewKey(key);
      setApiKeys((prev) => [key, ...prev]);
    } catch (err) {
      console.error('Failed to create API key:', err);
      setError(err instanceof Error ? err.message : 'Failed to create API key');
    } finally {
      setCreatingKey(false);
    }
  }

  function copyToClipboard(text: string, id: string) {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  }

  function openKeyModal(app: App) {
    setSelectedApp(app);
    setShowKeyModal(true);
    setNewKey(null);
    loadApiKeys(app.id);
  }

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <Header title="Projects" description="Manage your projects and SDK configurations" />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header title="Projects" description="Manage your projects and SDK configurations" />

      <div className="flex-1 p-6 space-y-6">
        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            {error}
            <button onClick={() => setError(null)} className="ml-auto text-xs underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Header Actions */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-secondary-400">
              {apps.length} project{apps.length !== 1 && 's'}
            </p>
          </div>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Project
          </Button>
        </div>

        {/* Projects Grid */}
        {apps.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="h-12 w-12 rounded-full bg-primary-500/10 flex items-center justify-center mb-4">
                <Plus className="h-6 w-6 text-primary-500" />
              </div>
              <h3 className="font-medium mb-1">No projects yet</h3>
              <p className="text-sm text-secondary-400 mb-4">
                Create your first project to start monitoring
              </p>
              <Button onClick={() => setShowCreateModal(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Project
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {apps.map((app) => (
              <Card key={app.id} className="relative">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{app.name}</CardTitle>
                      <CardDescription>
                        {app.environment}
                        {app.framework && ` • ${app.framework}`}
                      </CardDescription>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => openKeyModal(app)}
                    >
                      <Key className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-2xl font-bold">{app.event_count_24h}</p>
                      <p className="text-xs text-secondary-500">Events (24h)</p>
                    </div>
                    <div>
                      <p className={`text-2xl font-bold ${app.error_count_24h > 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {app.error_count_24h}
                      </p>
                      <p className="text-xs text-secondary-500">Errors (24h)</p>
                    </div>
                  </div>

                  {/* Status */}
                  <div className="flex items-center gap-2">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        app.error_count_24h > 0
                          ? 'bg-red-500'
                          : app.event_count_24h > 0
                          ? 'bg-green-500'
                          : 'bg-secondary-500'
                      }`}
                    />
                    <span className="text-xs text-secondary-400">
                      {app.last_event_at
                        ? `Last event: ${new Date(app.last_event_at).toLocaleString()}`
                        : 'No events yet'}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create Project Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md mx-4">
              <CardHeader>
                <CardTitle>Create New Project</CardTitle>
                <CardDescription>Set up a new project to start tracking events</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="projectName">Project Name</Label>
                  <Input
                    id="projectName"
                    placeholder="my-awesome-app"
                    value={createName}
                    onChange={(e) => setCreateName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="environment">Environment</Label>
                  <select
                    id="environment"
                    value={createEnv}
                    onChange={(e) => setCreateEnv(e.target.value)}
                    className="w-full h-10 rounded-lg border border-secondary-700 bg-secondary-900 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="production">Production</option>
                    <option value="staging">Staging</option>
                    <option value="development">Development</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="framework">Framework (optional)</Label>
                  <select
                    id="framework"
                    value={createFramework}
                    onChange={(e) => setCreateFramework(e.target.value)}
                    className="w-full h-10 rounded-lg border border-secondary-700 bg-secondary-900 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select framework...</option>
                    <option value="fastapi">FastAPI (Python)</option>
                    <option value="flask">Flask (Python)</option>
                    <option value="django">Django (Python)</option>
                    <option value="nextjs">Next.js</option>
                    <option value="express">Express.js</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button variant="outline" onClick={() => setShowCreateModal(false)} disabled={creating}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateApp} disabled={creating || !createName.trim()}>
                    {creating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    Create Project
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* API Keys Modal */}
        {showKeyModal && selectedApp && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-lg mx-4">
              <CardHeader>
                <CardTitle>API Keys - {selectedApp.name}</CardTitle>
                <CardDescription>Manage API keys for SDK authentication</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* New Key Alert */}
                {newKey?.full_key && (
                  <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                    <p className="text-sm font-medium text-green-400 mb-2">
                      New API key created! Copy it now - you won&apos;t see it again.
                    </p>
                    <div className="flex items-center gap-2">
                      <Input
                        value={newKey.full_key}
                        readOnly
                        className="font-mono text-xs"
                      />
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => copyToClipboard(newKey.full_key!, 'new')}
                      >
                        {copiedKey === 'new' ? (
                          <Check className="h-4 w-4 text-green-500" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                )}

                {/* Existing Keys */}
                {loadingKeys ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
                  </div>
                ) : apiKeys.length === 0 ? (
                  <div className="text-center py-8 text-secondary-500">
                    <p>No API keys yet.</p>
                    <p className="text-sm mt-1">Create one to start using the SDK.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {apiKeys.map((key) => (
                      <div
                        key={key.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-secondary-800/50"
                      >
                        <div>
                          <p className="text-sm font-medium">{key.name}</p>
                          <p className="text-xs text-secondary-500 font-mono">
                            {key.key_prefix}...
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-secondary-400">{key.key_type}</p>
                          {key.last_used_at && (
                            <p className="text-xs text-secondary-500">
                              Last used: {new Date(key.last_used_at).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex justify-between pt-4 border-t border-secondary-800">
                  <Button variant="outline" onClick={handleCreateKey} disabled={creatingKey}>
                    {creatingKey ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
                    Generate New Key
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setShowKeyModal(false);
                      setNewKey(null);
                    }}
                  >
                    Close
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
