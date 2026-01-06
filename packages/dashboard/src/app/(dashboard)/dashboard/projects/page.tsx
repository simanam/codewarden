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
import { Plus, Copy, Check, Key, Loader2, AlertCircle, Network, Trash2, FolderKanban } from 'lucide-react';
import Link from 'next/link';
import { getApps, createApp, getApiKeys, createApiKey, deleteApp, type App, type ApiKey } from '@/lib/api/client';

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

  // Delete confirmation state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [appToDelete, setAppToDelete] = useState<App | null>(null);
  const [deleting, setDeleting] = useState(false);

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

  function confirmDelete(app: App) {
    setAppToDelete(app);
    setShowDeleteModal(true);
  }

  async function handleDeleteApp() {
    if (!appToDelete) return;

    try {
      setDeleting(true);
      await deleteApp(appToDelete.id);
      setApps((prev) => prev.filter((a) => a.id !== appToDelete.id));
      setShowDeleteModal(false);
      setAppToDelete(null);
    } catch (err) {
      console.error('Failed to delete app:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete project');
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <Header title="Projects" description="Manage your projects and SDK configurations" />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header title="Projects" description="Manage your projects and SDK configurations" />

      <div className="flex-1 p-4 md:p-6 space-y-6 overflow-auto">
        {error && (
          <div className="p-4 rounded-lg bg-danger/10 border border-danger/20 text-danger flex items-center gap-2 text-sm">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span className="flex-1">{error}</span>
            <button onClick={() => setError(null)} className="text-xs font-medium hover:underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Header Actions */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {apps.length} project{apps.length !== 1 && 's'}
          </p>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Project
          </Button>
        </div>

        {/* Projects Grid */}
        {apps.length === 0 ? (
          <Card className="border-dashed border-2">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="h-14 w-14 rounded-full bg-muted flex items-center justify-center mb-4">
                <FolderKanban className="h-7 w-7 text-muted-foreground" />
              </div>
              <h3 className="font-semibold mb-1">No projects yet</h3>
              <p className="text-sm text-muted-foreground mb-4 text-center max-w-sm">
                Create your first project to start monitoring your application
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
              <Card key={app.id} className="card-interactive group">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-base truncate">{app.name}</CardTitle>
                      <CardDescription className="mt-0.5">
                        <span className="badge badge-info mr-1.5">{app.environment}</span>
                        {app.framework && <span className="text-muted-foreground">{app.framework}</span>}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Link href={`/dashboard/projects/${app.id}/architecture`}>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          title="View Architecture"
                        >
                          <Network className="h-4 w-4" />
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => openKeyModal(app)}
                        title="API Keys"
                      >
                        <Key className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-danger"
                        onClick={() => confirmDelete(app)}
                        title="Delete Project"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-muted/50">
                      <p className="stat-value text-xl">{app.event_count_24h}</p>
                      <p className="stat-label text-xs">Events (24h)</p>
                    </div>
                    <div className="p-3 rounded-lg bg-muted/50">
                      <p className={`stat-value text-xl ${app.error_count_24h > 0 ? 'text-danger' : 'text-success'}`}>
                        {app.error_count_24h}
                      </p>
                      <p className="stat-label text-xs">Errors (24h)</p>
                    </div>
                  </div>

                  {/* Status */}
                  <div className="flex items-center gap-2 pt-2 border-t border-border">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        app.error_count_24h > 0
                          ? 'bg-danger'
                          : app.event_count_24h > 0
                          ? 'bg-success'
                          : 'bg-muted-foreground'
                      }`}
                    />
                    <span className="text-xs text-muted-foreground">
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
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-md animate-scale-in">
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
                    className="w-full h-9 rounded-lg border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
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
                    className="w-full h-9 rounded-lg border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
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
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-lg animate-scale-in">
              <CardHeader>
                <CardTitle>API Keys - {selectedApp.name}</CardTitle>
                <CardDescription>Manage API keys for SDK authentication</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* New Key Alert */}
                {newKey?.full_key && (
                  <div className="p-4 rounded-lg bg-success/10 border border-success/20">
                    <p className="text-sm font-medium text-success mb-2">
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
                          <Check className="h-4 w-4 text-success" />
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
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                ) : apiKeys.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto mb-3">
                      <Key className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <p className="font-medium text-sm">No API keys yet</p>
                    <p className="text-xs text-muted-foreground mt-1">Create one to start using the SDK.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {apiKeys.map((key) => (
                      <div
                        key={key.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                      >
                        <div>
                          <p className="text-sm font-medium">{key.name}</p>
                          <p className="text-xs text-muted-foreground font-mono">
                            {key.key_prefix}...
                          </p>
                        </div>
                        <div className="text-right">
                          <span className="badge badge-info text-xs">{key.key_type}</span>
                          {key.last_used_at && (
                            <p className="text-xs text-muted-foreground mt-1">
                              Last used: {new Date(key.last_used_at).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex justify-between pt-4 border-t border-border">
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

        {/* Delete Confirmation Modal */}
        {showDeleteModal && appToDelete && (
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-md animate-scale-in">
              <CardHeader>
                <CardTitle className="text-danger">Delete Project</CardTitle>
                <CardDescription>
                  Are you sure you want to delete &quot;{appToDelete.name}&quot;?
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm">
                  <p className="font-medium mb-1">This action cannot be undone.</p>
                  <p className="text-danger/80">All events, API keys, and data associated with this project will be permanently deleted.</p>
                </div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowDeleteModal(false);
                      setAppToDelete(null);
                    }}
                    disabled={deleting}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleDeleteApp}
                    disabled={deleting}
                  >
                    {deleting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Trash2 className="h-4 w-4 mr-2" />}
                    Delete Project
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
