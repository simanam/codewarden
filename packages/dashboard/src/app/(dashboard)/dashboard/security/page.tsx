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
  ChevronDown,
  FolderKanban,
  X,
  FileCode,
  Package,
  Terminal,
  Copy,
  Check,
} from 'lucide-react';
import {
  getSecurityStats,
  getRecentScans,
  getApps,
  triggerSecurityScan,
  getScanDetails,
  type SecurityStats,
  type SecurityScan,
  type SecurityScanDetail,
  type SecurityFinding,
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
  return date.toLocaleDateString();
}

export default function SecurityPage() {
  const [stats, setStats] = useState<SecurityStats | null>(null);
  const [recentScans, setRecentScans] = useState<SecurityScan[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apps, setApps] = useState<App[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);
  const [showAppSelector, setShowAppSelector] = useState(false);
  const [selectedScan, setSelectedScan] = useState<SecurityScanDetail | null>(null);
  const [loadingScan, setLoadingScan] = useState(false);
  const [copiedCommand, setCopiedCommand] = useState<string | null>(null);

  const selectedApp = apps.find(app => app.id === selectedAppId);
  const hasApps = apps.length > 0;

  const handleScanClick = async (scanId: string) => {
    setLoadingScan(true);
    try {
      const details = await getScanDetails(scanId);
      setSelectedScan(details);
    } catch (err) {
      console.error('Failed to load scan details:', err);
      alert(`Failed to load scan details: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoadingScan(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCommand(text);
    setTimeout(() => setCopiedCommand(null), 2000);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'dependency':
        return <Package className="h-4 w-4" />;
      case 'secret':
        return <Key className="h-4 w-4" />;
      case 'code':
        return <FileCode className="h-4 w-4" />;
      default:
        return <Bug className="h-4 w-4" />;
    }
  };

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

        // Fetch security stats and recent scans for selected app
        const [statsData, scansData] = await Promise.all([
          getSecurityStats(selectedAppId),
          getRecentScans(10, selectedAppId),
        ]);

        setStats(statsData);
        setRecentScans(scansData.scans);
      } catch (err) {
        console.error('Failed to load security data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [selectedAppId]);

  const handleRunScan = async (scanType: string = 'full') => {
    if (!selectedAppId) {
      alert('No project selected. Select a project first to run security scans.');
      return;
    }

    setScanning(true);
    try {
      await triggerSecurityScan(selectedAppId, scanType);
      // Refresh data after scan completes
      const [statsData, scansData] = await Promise.all([
        getSecurityStats(selectedAppId),
        getRecentScans(10, selectedAppId),
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
          <div className="flex items-center gap-3">
            {/* Project Selector */}
            {apps.length > 0 && (
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
            )}
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
          </div>
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
                    onClick={() => handleScanClick(scan.id)}
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

      {/* Scan Details Modal */}
      {(selectedScan || loadingScan) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => !loadingScan && setSelectedScan(null)}
          />
          <div className="relative w-full max-w-4xl max-h-[85vh] bg-secondary-900 border border-secondary-700 rounded-xl shadow-2xl overflow-hidden flex flex-col m-4">
            {loadingScan ? (
              <div className="flex items-center justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
              </div>
            ) : selectedScan && (
              <>
                {/* Modal Header */}
                <div className="flex items-center justify-between p-6 border-b border-secondary-700">
                  <div>
                    <h2 className="text-xl font-semibold capitalize">
                      {selectedScan.scan_type} Scan Results
                    </h2>
                    <p className="text-sm text-secondary-400 mt-1">
                      {formatTime(selectedScan.completed_at ?? selectedScan.started_at)}
                      {selectedScan.duration_ms && ` • ${(selectedScan.duration_ms / 1000).toFixed(1)}s`}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-sm px-3 py-1 rounded-full ${
                      selectedScan.status === 'passed' ? 'bg-green-500/20 text-green-400' :
                      selectedScan.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {selectedScan.status}
                    </span>
                    <button
                      onClick={() => setSelectedScan(null)}
                      className="p-2 rounded-lg hover:bg-secondary-800 transition-colors"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-4 gap-4 p-6 border-b border-secondary-700">
                  <div className={`p-3 rounded-lg ${severityColors.critical}`}>
                    <div className="text-lg font-bold">{selectedScan.critical_count}</div>
                    <div className="text-xs">Critical</div>
                  </div>
                  <div className={`p-3 rounded-lg ${severityColors.high}`}>
                    <div className="text-lg font-bold">{selectedScan.high_count}</div>
                    <div className="text-xs">High</div>
                  </div>
                  <div className={`p-3 rounded-lg ${severityColors.medium}`}>
                    <div className="text-lg font-bold">{selectedScan.medium_count}</div>
                    <div className="text-xs">Medium</div>
                  </div>
                  <div className={`p-3 rounded-lg ${severityColors.low}`}>
                    <div className="text-lg font-bold">{selectedScan.low_count}</div>
                    <div className="text-xs">Low</div>
                  </div>
                </div>

                {/* Findings List */}
                <div className="flex-1 overflow-auto p-6">
                  {selectedScan.findings.length === 0 ? (
                    <div className="text-center py-12 text-secondary-500">
                      <CheckCircle className="h-12 w-12 mx-auto mb-3 text-green-500" />
                      <p className="font-medium">No vulnerabilities found!</p>
                      <p className="text-sm mt-1">Your code passed all security checks.</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <h3 className="text-sm font-medium text-secondary-400 uppercase tracking-wide">
                        {selectedScan.findings.length} Finding{selectedScan.findings.length !== 1 ? 's' : ''}
                      </h3>
                      {selectedScan.findings.map((finding) => (
                        <div
                          key={finding.id}
                          className="p-4 rounded-lg bg-secondary-800/50 border border-secondary-700"
                        >
                          <div className="flex items-start gap-3">
                            <div className={`p-2 rounded-lg ${
                              finding.type === 'dependency' ? 'bg-purple-500/10 text-purple-400' :
                              finding.type === 'secret' ? 'bg-red-500/10 text-red-400' :
                              'bg-blue-500/10 text-blue-400'
                            }`}>
                              {getTypeIcon(finding.type)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <h4 className="font-medium">{finding.title}</h4>
                                <span className={`text-xs px-2 py-0.5 rounded ${
                                  severityColors[finding.severity as keyof typeof severityColors] || severityColors.medium
                                }`}>
                                  {finding.severity}
                                </span>
                                {finding.cve_id && (
                                  <span className="text-xs px-2 py-0.5 rounded bg-secondary-700 text-secondary-300">
                                    {finding.cve_id}
                                  </span>
                                )}
                                {finding.cwe_id && (
                                  <span className="text-xs px-2 py-0.5 rounded bg-secondary-700 text-secondary-300">
                                    {finding.cwe_id}
                                  </span>
                                )}
                              </div>
                              {finding.description && (
                                <p className="text-sm text-secondary-400 mt-2">
                                  {finding.description}
                                </p>
                              )}
                              {(finding.file_path || finding.package_name) && (
                                <div className="flex items-center gap-4 mt-3 text-sm">
                                  {finding.file_path && (
                                    <span className="text-secondary-500">
                                      <FileCode className="h-3.5 w-3.5 inline mr-1" />
                                      {finding.file_path}
                                      {finding.line_number && `:${finding.line_number}`}
                                    </span>
                                  )}
                                  {finding.package_name && (
                                    <span className="text-secondary-500">
                                      <Package className="h-3.5 w-3.5 inline mr-1" />
                                      {finding.package_name}
                                      {finding.package_version && `@${finding.package_version}`}
                                      {finding.fixed_version && (
                                        <span className="text-green-400 ml-1">
                                          → {finding.fixed_version}
                                        </span>
                                      )}
                                    </span>
                                  )}
                                </div>
                              )}
                              {finding.remediation && (
                                <div className="mt-3 p-3 rounded bg-secondary-900 border border-secondary-700">
                                  <p className="text-xs font-medium text-secondary-400 mb-1">Remediation</p>
                                  <p className="text-sm">{finding.remediation}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Fix Commands */}
                  {selectedScan.fix_commands && selectedScan.fix_commands.length > 0 && (
                    <div className="mt-6 pt-6 border-t border-secondary-700">
                      <h3 className="text-sm font-medium text-secondary-400 uppercase tracking-wide mb-3">
                        Quick Fix Commands
                      </h3>
                      <div className="space-y-2">
                        {selectedScan.fix_commands.map((cmd, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-3 rounded-lg bg-secondary-800 font-mono text-sm"
                          >
                            <div className="flex items-center gap-2">
                              <Terminal className="h-4 w-4 text-secondary-500" />
                              <code>{cmd}</code>
                            </div>
                            <button
                              onClick={() => copyToClipboard(cmd)}
                              className="p-1.5 rounded hover:bg-secondary-700 transition-colors"
                              title="Copy to clipboard"
                            >
                              {copiedCommand === cmd ? (
                                <Check className="h-4 w-4 text-green-400" />
                              ) : (
                                <Copy className="h-4 w-4 text-secondary-400" />
                              )}
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
