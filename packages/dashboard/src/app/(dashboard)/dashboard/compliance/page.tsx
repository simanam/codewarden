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
import {
  FileCheck,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  FileJson,
  FileText,
  FileType,
  ShieldCheck,
  Activity,
  Users,
  Settings,
  AlertCircle,
  Info,
  ChevronDown,
  FolderKanban,
} from 'lucide-react';
import {
  getComplianceStatus,
  getEvidenceEvents,
  getApps,
  requestEvidenceExport,
  type ComplianceCheck,
  type EvidenceEvent,
  type App,
} from '@/lib/api/client';

function formatTime(timestamp: string | null) {
  if (!timestamp) return 'Never';
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);

  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString();
}

export default function CompliancePage() {
  const [checks, setChecks] = useState<ComplianceCheck[]>([]);
  const [events, setEvents] = useState<EvidenceEvent[]>([]);
  const [complianceScore, setComplianceScore] = useState(0);
  const [passingCount, setPassingCount] = useState(0);
  const [failingCount, setFailingCount] = useState(0);
  const [notConfiguredCount, setNotConfiguredCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [apps, setApps] = useState<App[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);
  const [showAppSelector, setShowAppSelector] = useState(false);

  const selectedApp = apps.find(app => app.id === selectedAppId);
  const hasApps = apps.length > 0;

  useEffect(() => {
    async function loadApps() {
      try {
        const appsData = await getApps();
        setApps(appsData);
        if (appsData.length > 0 && !selectedAppId) {
          setSelectedAppId(appsData[0].id);
        }
      } catch (err) {
        console.error('Failed to load apps:', err);
        setError(err instanceof Error ? err.message : 'Failed to load apps');
      }
    }
    loadApps();
  }, []);

  useEffect(() => {
    async function loadData() {
      if (!selectedAppId) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Fetch compliance status for selected app
        const complianceData = await getComplianceStatus(selectedAppId);

        // Map API response to component state
        setChecks(complianceData.checks.map(check => ({
          ...check,
          last_checked: check.last_checked,
        })));
        setComplianceScore(complianceData.score);
        setPassingCount(complianceData.passing_count);
        setFailingCount(complianceData.failing_count);
        setNotConfiguredCount(complianceData.not_configured_count);

        // Fetch evidence events for selected app
        try {
          const evidenceData = await getEvidenceEvents(selectedAppId, { limit: 10 });
          setEvents(evidenceData.events);
        } catch {
          setEvents([]);
        }
      } catch (err) {
        console.error('Failed to load compliance data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [selectedAppId]);

  const handleExport = async (format: 'json' | 'csv' | 'pdf') => {
    if (!selectedAppId) {
      alert('No project selected. Select a project first to export evidence.');
      return;
    }

    setExporting(format);
    try {
      const result = await requestEvidenceExport(selectedAppId, { format });
      alert(`Export started (ID: ${result.id}). You'll receive a download link when it's ready.`);
    } catch (err) {
      console.error('Export failed:', err);
      alert(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setExporting(null);
    }
  };

  const eventTypeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    'AUDIT_DEPLOY': Activity,
    'AUDIT_SCAN': ShieldCheck,
    'AUDIT_ACCESS': Users,
    'AUDIT_CONFIG': Settings,
  };

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <Header
          title="Compliance"
          description="SOC 2 readiness and evidence management"
        />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header
        title="Compliance"
        description="SOC 2 readiness and evidence management"
        action={
          apps.length > 0 ? (
            <div className="relative">
              <button
                onClick={() => setShowAppSelector(!showAppSelector)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-secondary-800 hover:bg-secondary-700 transition-colors border border-secondary-700"
              >
                <FolderKanban className="h-4 w-4 text-secondary-400" />
                <span className="text-sm font-medium max-w-[150px] truncate">
                  {selectedApp?.name || 'Select Project'}
                </span>
                <ChevronDown className="h-4 w-4 text-secondary-400" />
              </button>
              {showAppSelector && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowAppSelector(false)}
                  />
                  <div className="absolute right-0 top-full mt-1 w-64 bg-secondary-800 border border-secondary-700 rounded-lg shadow-lg z-20 py-1 max-h-64 overflow-auto">
                    {apps.map(app => (
                      <button
                        key={app.id}
                        onClick={() => {
                          setSelectedAppId(app.id);
                          setShowAppSelector(false);
                        }}
                        className={`w-full text-left px-3 py-2 text-sm hover:bg-secondary-700 transition-colors flex items-center gap-2 ${
                          app.id === selectedAppId ? 'bg-primary-500/10 text-primary-400' : ''
                        }`}
                      >
                        <FolderKanban className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate">{app.name}</span>
                        {app.framework && (
                          <span className="text-xs text-secondary-500 ml-auto">{app.framework}</span>
                        )}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          ) : undefined
        }
      />

      <div className="flex-1 p-6 space-y-6 overflow-auto">
        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
            {error}
          </div>
        )}

        {/* Info banner if no apps */}
        {!hasApps && (
          <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-start gap-3">
            <Info className="h-5 w-5 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium">No apps configured yet</p>
              <p className="text-sm mt-1">
                Create an app and install the SDK to start tracking compliance data.
                All checks will show as &quot;Not Configured&quot; until then.
              </p>
            </div>
          </div>
        )}

        {/* Overview */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-secondary-400">
                Compliance Score
              </CardTitle>
              <FileCheck className="h-4 w-4 text-primary-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {checks.length > 0 ? `${complianceScore}%` : 'N/A'}
              </div>
              <div className="w-full h-2 bg-secondary-800 rounded-full mt-2">
                <div
                  className={`h-2 rounded-full ${
                    complianceScore >= 80 ? 'bg-green-500' :
                    complianceScore >= 50 ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`}
                  style={{ width: `${complianceScore}%` }}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-secondary-400">
                Passing
              </CardTitle>
              <CheckCircle className="h-4 w-4 text-green-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{passingCount}</div>
              <p className="text-xs text-secondary-500 mt-1">
                of {checks.length} checks
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-secondary-400">
                Failing
              </CardTitle>
              <XCircle className="h-4 w-4 text-red-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{failingCount}</div>
              <p className="text-xs text-secondary-500 mt-1">
                requires attention
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-secondary-400">
                Not Configured
              </CardTitle>
              <Clock className="h-4 w-4 text-yellow-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{notConfiguredCount}</div>
              <p className="text-xs text-secondary-500 mt-1">
                needs setup
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Compliance Checks */}
        <Card>
          <CardHeader>
            <CardTitle>SOC 2 Readiness Checklist</CardTitle>
            <CardDescription>
              Key controls and their current status based on your actual data
            </CardDescription>
          </CardHeader>
          <CardContent>
            {checks.length === 0 ? (
              <div className="text-center py-8 text-secondary-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No compliance checks available.</p>
                <p className="text-sm mt-1">
                  Create an app to start tracking compliance.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {checks.map((check) => (
                  <div
                    key={check.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-secondary-800/50"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={`p-2 rounded-lg ${
                          check.status === 'passing' ? 'bg-green-500/10' :
                          check.status === 'failing' ? 'bg-red-500/10' :
                          'bg-yellow-500/10'
                        }`}
                      >
                        {check.status === 'passing' ? (
                          <CheckCircle className="h-5 w-5 text-green-400" />
                        ) : check.status === 'failing' ? (
                          <XCircle className="h-5 w-5 text-red-400" />
                        ) : (
                          <Clock className="h-5 w-5 text-yellow-400" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium">{check.name}</p>
                        <p className="text-sm text-secondary-500">
                          {check.description}
                        </p>
                        {check.details && (
                          <p className="text-xs text-secondary-400 mt-1">
                            {check.details}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`text-xs px-2 py-1 rounded ${
                        check.status === 'passing' ? 'bg-green-500/20 text-green-400' :
                        check.status === 'failing' ? 'bg-red-500/20 text-red-400' :
                        'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {check.status === 'not_configured' ? 'Not Configured' : check.status}
                      </span>
                      {check.last_checked && (
                        <p className="text-xs text-secondary-500 mt-1">
                          {formatTime(check.last_checked)}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Evidence Export */}
        <Card>
          <CardHeader>
            <CardTitle>Export Evidence</CardTitle>
            <CardDescription>
              Download audit logs and compliance evidence for reporting
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-center gap-2"
                onClick={() => handleExport('json')}
                disabled={exporting !== null || !hasApps}
              >
                {exporting === 'json' ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  <FileJson className="h-6 w-6 text-blue-400" />
                )}
                <span className="font-medium">JSON Export</span>
                <span className="text-xs text-secondary-500">
                  Full structured data
                </span>
              </Button>

              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-center gap-2"
                onClick={() => handleExport('csv')}
                disabled={exporting !== null || !hasApps}
              >
                {exporting === 'csv' ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  <FileText className="h-6 w-6 text-green-400" />
                )}
                <span className="font-medium">CSV Export</span>
                <span className="text-xs text-secondary-500">
                  Spreadsheet compatible
                </span>
              </Button>

              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-center gap-2"
                onClick={() => handleExport('pdf')}
                disabled={exporting !== null || !hasApps}
              >
                {exporting === 'pdf' ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  <FileType className="h-6 w-6 text-red-400" />
                )}
                <span className="font-medium">PDF Report</span>
                <span className="text-xs text-secondary-500">
                  Formatted compliance report
                </span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Recent Evidence */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Evidence Events</CardTitle>
            <CardDescription>
              Latest audit log entries from your applications
            </CardDescription>
          </CardHeader>
          <CardContent>
            {events.length === 0 ? (
              <div className="text-center py-8 text-secondary-500">
                <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No evidence events yet.</p>
                <p className="text-sm mt-1">
                  {hasApps
                    ? 'Events will appear here as your application runs and logs evidence.'
                    : 'Create an app and install the SDK to start collecting evidence.'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {events.map((event) => {
                  const Icon = eventTypeIcons[event.event_type] || Activity;
                  const title = event.title || `${event.event_type.replace('AUDIT_', '')} event`;
                  return (
                    <div
                      key={event.id}
                      className="flex items-center gap-4 p-4 rounded-lg bg-secondary-800/50"
                    >
                      <div className="p-2 rounded-lg bg-primary-500/10">
                        <Icon className="h-4 w-4 text-primary-400" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">{title}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-secondary-500">
                            {event.event_type.replace('AUDIT_', '')}
                          </span>
                          {event.actor_email && (
                            <>
                              <span className="text-xs text-secondary-600">•</span>
                              <span className="text-xs text-secondary-500">
                                {event.actor_email}
                              </span>
                            </>
                          )}
                          <span className="text-xs text-secondary-600">•</span>
                          <span className="text-xs text-secondary-500">
                            {formatTime(event.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
