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
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Bug,
  Key,
  Code,
  Loader2,
  RefreshCw,
  ArrowRight,
  Info,
} from 'lucide-react';
import {
  getSecurityStats,
  getRecentScans,
  getApps,
  triggerSecurityScan,
  type SecurityStats,
  type SecurityScan,
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
  return date.toLocaleDateString();
}

export default function SecurityPage() {
  const [stats, setStats] = useState<SecurityStats | null>(null);
  const [recentScans, setRecentScans] = useState<SecurityScan[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasApps, setHasApps] = useState(false);
  const [firstAppId, setFirstAppId] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        // Fetch security stats and recent scans from API
        const [statsData, scansData, apps] = await Promise.all([
          getSecurityStats(),
          getRecentScans(10),
          getApps(),
        ]);

        setStats(statsData);
        setRecentScans(scansData.scans);
        setHasApps(apps.length > 0);
        if (apps.length > 0) {
          setFirstAppId(apps[0].id);
        }
      } catch (err) {
        console.error('Failed to load security data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const handleRunScan = async (scanType: string = 'full') => {
    if (!firstAppId) {
      alert('No apps configured. Create an app first to run security scans.');
      return;
    }

    setScanning(true);
    try {
      await triggerSecurityScan(firstAppId, scanType);
      // Refresh data after scan completes
      const [statsData, scansData] = await Promise.all([
        getSecurityStats(),
        getRecentScans(10),
      ]);
      setStats(statsData);
      setRecentScans(scansData.scans);
    } catch (err) {
      console.error('Failed to trigger scan:', err);
      alert(`Scan failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setScanning(false);
    }
  };

  const severityColors = {
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  };

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <Header
          title="Security"
          description="Security scanning and vulnerability management"
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
        title="Security"
        description="Security scanning and vulnerability management"
        action={
          <Button
            onClick={() => handleRunScan('full')}
            disabled={scanning || !hasApps}
            className="gap-2"
          >
            {scanning ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Run Full Scan
          </Button>
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
                Create an app and install the SDK to start running security scans.
                All stats will show as zero until then.
              </p>
            </div>
          </div>
        )}

        {/* Overview Stats */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-secondary-400">
                Total Vulnerabilities
              </CardTitle>
              <Shield className="h-4 w-4 text-red-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_vulnerabilities ?? 0}</div>
              <p className="text-xs text-secondary-500 mt-1">
                Across {stats?.apps_scanned ?? 0} scanned apps
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-secondary-400">
                Critical/High
              </CardTitle>
              <AlertTriangle className="h-4 w-4 text-orange-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(stats?.critical_count ?? 0) + (stats?.high_count ?? 0)}
              </div>
              <p className="text-xs text-secondary-500 mt-1">
                {stats?.critical_count ?? 0} critical, {stats?.high_count ?? 0} high
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-secondary-400">
                Last Scan
              </CardTitle>
              <Clock className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatTime(stats?.last_scan_at ?? null)}</div>
              <p className="text-xs text-secondary-500 mt-1">
                {stats?.scans_this_week ?? 0} scans this week
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-secondary-400">
                Coverage
              </CardTitle>
              <CheckCircle className="h-4 w-4 text-green-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.total_apps ? Math.round((stats.apps_scanned / stats.total_apps) * 100) : 0}%
              </div>
              <p className="text-xs text-secondary-500 mt-1">
                {stats?.apps_scanned ?? 0} of {stats?.total_apps ?? 0} apps scanned
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Vulnerability Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Vulnerability Breakdown</CardTitle>
            <CardDescription>
              Distribution of findings by severity
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div className={`p-4 rounded-lg border ${severityColors.critical}`}>
                <div className="text-2xl font-bold">{stats?.critical_count ?? 0}</div>
                <div className="text-sm font-medium mt-1">Critical</div>
              </div>
              <div className={`p-4 rounded-lg border ${severityColors.high}`}>
                <div className="text-2xl font-bold">{stats?.high_count ?? 0}</div>
                <div className="text-sm font-medium mt-1">High</div>
              </div>
              <div className={`p-4 rounded-lg border ${severityColors.medium}`}>
                <div className="text-2xl font-bold">{stats?.medium_count ?? 0}</div>
                <div className="text-sm font-medium mt-1">Medium</div>
              </div>
              <div className={`p-4 rounded-lg border ${severityColors.low}`}>
                <div className="text-2xl font-bold">{stats?.low_count ?? 0}</div>
                <div className="text-sm font-medium mt-1">Low</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Scan Types */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="hover:border-primary-500/50 transition-colors">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-purple-500/10">
                  <Bug className="h-5 w-5 text-purple-400" />
                </div>
                <div>
                  <h3 className="font-medium">Dependency Scan</h3>
                  <p className="text-xs text-secondary-400">pip-audit / npm audit</p>
                </div>
              </div>
              <p className="text-sm text-secondary-400 mb-4">
                Scan dependencies for known vulnerabilities and CVEs
              </p>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => handleRunScan('dependencies')}
                disabled={scanning || !hasApps}
              >
                {scanning ? 'Scanning...' : 'Run Dependency Scan'}
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:border-primary-500/50 transition-colors">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-red-500/10">
                  <Key className="h-5 w-5 text-red-400" />
                </div>
                <div>
                  <h3 className="font-medium">Secret Scan</h3>
                  <p className="text-xs text-secondary-400">Gitleaks patterns</p>
                </div>
              </div>
              <p className="text-sm text-secondary-400 mb-4">
                Detect hardcoded secrets, API keys, and credentials
              </p>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => handleRunScan('secrets')}
                disabled={scanning || !hasApps}
              >
                {scanning ? 'Scanning...' : 'Run Secret Scan'}
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:border-primary-500/50 transition-colors">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-blue-500/10">
                  <Code className="h-5 w-5 text-blue-400" />
                </div>
                <div>
                  <h3 className="font-medium">Code Scan</h3>
                  <p className="text-xs text-secondary-400">Bandit SAST</p>
                </div>
              </div>
              <p className="text-sm text-secondary-400 mb-4">
                Static analysis for security issues and vulnerabilities
              </p>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => handleRunScan('code')}
                disabled={scanning || !hasApps}
              >
                {scanning ? 'Scanning...' : 'Run Code Scan'}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Recent Scans */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Scans</CardTitle>
            <CardDescription>
              Latest security scan results
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recentScans.length === 0 ? (
              <div className="text-center py-8 text-secondary-500">
                <Shield className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No scans yet.</p>
                <p className="text-sm mt-1">
                  {hasApps
                    ? 'Run a security scan to see results here.'
                    : 'Create an app and install the SDK to start running security scans.'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentScans.map((scan) => (
                  <div
                    key={scan.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-secondary-800/50 hover:bg-secondary-800 transition-colors cursor-pointer"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={`h-2 w-2 rounded-full ${
                          scan.status === 'passed' ? 'bg-green-500' :
                          scan.status === 'failed' ? 'bg-red-500' :
                          scan.status === 'running' ? 'bg-yellow-500' :
                          'bg-gray-500'
                        }`}
                      />
                      <div>
                        <p className="font-medium capitalize">
                          {scan.scan_type} Scan
                        </p>
                        <p className="text-sm text-secondary-500">
                          {formatTime(scan.completed_at ?? scan.started_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {scan.vulnerability_count > 0 && (
                        <div className="flex gap-2">
                          {scan.critical_count > 0 && (
                            <span className={`text-xs px-2 py-1 rounded ${severityColors.critical}`}>
                              {scan.critical_count} critical
                            </span>
                          )}
                          {scan.high_count > 0 && (
                            <span className={`text-xs px-2 py-1 rounded ${severityColors.high}`}>
                              {scan.high_count} high
                            </span>
                          )}
                        </div>
                      )}
                      <span className={`text-xs px-2 py-1 rounded ${
                        scan.status === 'passed' ? 'bg-green-500/20 text-green-400' :
                        scan.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                        'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {scan.status}
                      </span>
                      <ArrowRight className="h-4 w-4 text-secondary-500" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
