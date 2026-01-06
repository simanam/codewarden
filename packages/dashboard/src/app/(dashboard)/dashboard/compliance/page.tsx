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
  Download,
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
} from 'lucide-react';

// Types
interface EvidenceEvent {
  id: string;
  event_type: string;
  title: string;
  severity: string;
  actor_email: string | null;
  created_at: string;
}

interface ComplianceCheck {
  id: string;
  name: string;
  description: string;
  status: 'passing' | 'failing' | 'not_configured';
  lastChecked: string | null;
  category: string;
}

// Mock data
const mockChecks: ComplianceCheck[] = [
  {
    id: '1',
    name: 'Security Scanning Enabled',
    description: 'Automated security scans are configured and running',
    status: 'passing',
    lastChecked: new Date().toISOString(),
    category: 'security',
  },
  {
    id: '2',
    name: 'Evidence Logging Active',
    description: 'Deployment and access events are being logged',
    status: 'passing',
    lastChecked: new Date().toISOString(),
    category: 'audit',
  },
  {
    id: '3',
    name: 'Error Tracking Configured',
    description: 'Application errors are being captured and tracked',
    status: 'passing',
    lastChecked: new Date().toISOString(),
    category: 'monitoring',
  },
  {
    id: '4',
    name: 'MFA Enabled',
    description: 'Multi-factor authentication is enabled for all users',
    status: 'not_configured',
    lastChecked: null,
    category: 'access',
  },
  {
    id: '5',
    name: 'API Key Rotation',
    description: 'API keys are rotated within the required timeframe',
    status: 'failing',
    lastChecked: new Date(Date.now() - 7 * 86400000).toISOString(),
    category: 'security',
  },
  {
    id: '6',
    name: 'Vulnerability SLA',
    description: 'Critical vulnerabilities addressed within 72 hours',
    status: 'passing',
    lastChecked: new Date().toISOString(),
    category: 'security',
  },
];

const mockEvents: EvidenceEvent[] = [
  {
    id: '1',
    event_type: 'AUDIT_DEPLOY',
    title: 'Deployment: v1.2.3 to production',
    severity: 'info',
    actor_email: 'dev@example.com',
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: '2',
    event_type: 'AUDIT_SCAN',
    title: 'Security Scan: full - passed',
    severity: 'info',
    actor_email: null,
    created_at: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    id: '3',
    event_type: 'AUDIT_ACCESS',
    title: 'Access: login on dashboard',
    severity: 'info',
    actor_email: 'admin@example.com',
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: '4',
    event_type: 'AUDIT_CONFIG',
    title: 'Config Change: notification_email',
    severity: 'info',
    actor_email: 'admin@example.com',
    created_at: new Date(Date.now() - 172800000).toISOString(),
  },
];

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
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        // TODO: Fetch from API
        await new Promise(resolve => setTimeout(resolve, 500));
        setChecks(mockChecks);
        setEvents(mockEvents);
      } catch (err) {
        console.error('Failed to load compliance data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const handleExport = async (format: 'json' | 'csv' | 'pdf') => {
    setExporting(format);
    // TODO: Call export API
    await new Promise(resolve => setTimeout(resolve, 1500));
    setExporting(null);
    // In production, this would trigger a download
    alert(`Export started in ${format.toUpperCase()} format. You'll receive a download link shortly.`);
  };

  const passingCount = checks.filter(c => c.status === 'passing').length;
  const failingCount = checks.filter(c => c.status === 'failing').length;
  const notConfiguredCount = checks.filter(c => c.status === 'not_configured').length;
  const complianceScore = Math.round((passingCount / checks.length) * 100);

  const eventTypeIcons: Record<string, any> = {
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
      />

      <div className="flex-1 p-6 space-y-6 overflow-auto">
        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
            {error}
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
              <div className="text-2xl font-bold">{complianceScore}%</div>
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
              Key controls and their current status
            </CardDescription>
          </CardHeader>
          <CardContent>
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
                    {check.lastChecked && (
                      <p className="text-xs text-secondary-500 mt-1">
                        {formatTime(check.lastChecked)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Evidence Export */}
        <Card>
          <CardHeader>
            <CardTitle>Export Evidence</CardTitle>
            <CardDescription>
              Download audit logs and compliance evidence
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-center gap-2"
                onClick={() => handleExport('json')}
                disabled={exporting !== null}
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
                disabled={exporting !== null}
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
                disabled={exporting !== null}
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
              Latest audit log entries
            </CardDescription>
          </CardHeader>
          <CardContent>
            {events.length === 0 ? (
              <div className="text-center py-8 text-secondary-500">
                <p>No evidence events yet.</p>
                <p className="text-sm mt-1">
                  Events will appear here as your application runs.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {events.map((event) => {
                  const Icon = eventTypeIcons[event.event_type] || Activity;
                  return (
                    <div
                      key={event.id}
                      className="flex items-center gap-4 p-4 rounded-lg bg-secondary-800/50"
                    >
                      <div className="p-2 rounded-lg bg-primary-500/10">
                        <Icon className="h-4 w-4 text-primary-400" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">{event.title}</p>
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
