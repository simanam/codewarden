'use client';

export const dynamic = 'force-dynamic';

import { useState, useEffect } from 'react';
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
import {
  Copy,
  Check,
  Key,
  Loader2,
  AlertCircle,
  Terminal,
  GitBranch,
  Shield,
  ChevronRight,
  ExternalLink,
  RefreshCw,
} from 'lucide-react';
import { getApps, getApiKeys, createApiKey, type App, type ApiKey } from '@/lib/api/client';

// CI/CD Platform types
type CIPlatform = 'github' | 'gitlab' | 'circleci' | 'azure' | 'bitbucket';

interface CIPlatformInfo {
  id: CIPlatform;
  name: string;
  icon: string;
  docsUrl: string;
  fileName: string;
}

const CI_PLATFORMS: CIPlatformInfo[] = [
  {
    id: 'github',
    name: 'GitHub Actions',
    icon: '/icons/github.svg',
    docsUrl: 'https://docs.github.com/en/actions',
    fileName: '.github/workflows/security-scan.yml',
  },
  {
    id: 'gitlab',
    name: 'GitLab CI',
    icon: '/icons/gitlab.svg',
    docsUrl: 'https://docs.gitlab.com/ee/ci/',
    fileName: '.gitlab-ci.yml',
  },
  {
    id: 'circleci',
    name: 'CircleCI',
    icon: '/icons/circleci.svg',
    docsUrl: 'https://circleci.com/docs/',
    fileName: '.circleci/config.yml',
  },
  {
    id: 'azure',
    name: 'Azure DevOps',
    icon: '/icons/azure.svg',
    docsUrl: 'https://docs.microsoft.com/en-us/azure/devops/pipelines/',
    fileName: 'azure-pipelines.yml',
  },
  {
    id: 'bitbucket',
    name: 'Bitbucket Pipelines',
    icon: '/icons/bitbucket.svg',
    docsUrl: 'https://support.atlassian.com/bitbucket-cloud/docs/get-started-with-bitbucket-pipelines/',
    fileName: 'bitbucket-pipelines.yml',
  },
];

function generateCIConfig(platform: CIPlatform, dsn: string): string {
  const configs: Record<CIPlatform, string> = {
    github: `# .github/workflows/security-scan.yml
name: CodeWarden Security Scan

on:
  push:
    branches: [main, master, develop]
  pull_request:
    branches: [main, master]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install CodeWarden SDK
        run: pip install codewarden

      - name: Run Security Scan
        env:
          CODEWARDEN_DSN: \${{ secrets.CODEWARDEN_DSN }}
        run: |
          python -c "
          import codewarden
          codewarden.init('\${{ secrets.CODEWARDEN_DSN }}')
          result = codewarden.run_and_report_scan('.')
          print(f'Found {result.total_count} security issues')
          # Fail if critical issues found
          if result.severity_counts.get('critical', 0) > 0:
              exit(1)
          "

# Add CODEWARDEN_DSN to your repository secrets:
# Settings > Secrets and variables > Actions > New repository secret
# Name: CODEWARDEN_DSN
# Value: ${dsn}`,

    gitlab: `# .gitlab-ci.yml
stages:
  - security

security-scan:
  stage: security
  image: python:3.11-slim
  before_script:
    - pip install codewarden
  script:
    - |
      python -c "
      import codewarden
      codewarden.init('\$CODEWARDEN_DSN')
      result = codewarden.run_and_report_scan('.')
      print(f'Found {result.total_count} security issues')
      if result.severity_counts.get('critical', 0) > 0:
          exit(1)
      "
  variables:
    CODEWARDEN_DSN: ${dsn}
  rules:
    - if: \$CI_PIPELINE_SOURCE == "merge_request_event"
    - if: \$CI_COMMIT_BRANCH == "main"
    - if: \$CI_COMMIT_BRANCH == "master"

# Add CODEWARDEN_DSN to your CI/CD variables:
# Settings > CI/CD > Variables > Add variable
# Key: CODEWARDEN_DSN
# Value: ${dsn}
# Protect variable: Yes (recommended)
# Mask variable: Yes`,

    circleci: `# .circleci/config.yml
version: 2.1

jobs:
  security-scan:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run:
          name: Install CodeWarden SDK
          command: pip install codewarden
      - run:
          name: Run Security Scan
          command: |
            python -c "
            import codewarden
            import os
            codewarden.init(os.environ['CODEWARDEN_DSN'])
            result = codewarden.run_and_report_scan('.')
            print(f'Found {result.total_count} security issues')
            if result.severity_counts.get('critical', 0) > 0:
                exit(1)
            "

workflows:
  security:
    jobs:
      - security-scan:
          context:
            - codewarden-context

# Add CODEWARDEN_DSN to a CircleCI context:
# Organization Settings > Contexts > Create Context
# Name: codewarden-context
# Add Environment Variable:
#   CODEWARDEN_DSN: ${dsn}`,

    azure: `# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
      - master

pr:
  branches:
    include:
      - main
      - master

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: pip install codewarden
    displayName: 'Install CodeWarden SDK'

  - script: |
      python -c "
      import codewarden
      import os
      codewarden.init(os.environ['CODEWARDEN_DSN'])
      result = codewarden.run_and_report_scan('.')
      print(f'Found {result.total_count} security issues')
      if result.severity_counts.get('critical', 0) > 0:
          exit(1)
      "
    displayName: 'Run Security Scan'
    env:
      CODEWARDEN_DSN: $(CODEWARDEN_DSN)

# Add CODEWARDEN_DSN to your pipeline variables:
# Pipelines > Edit > Variables > Add
# Name: CODEWARDEN_DSN
# Value: ${dsn}
# Keep this value secret: Yes`,

    bitbucket: `# bitbucket-pipelines.yml
image: python:3.11-slim

pipelines:
  default:
    - step:
        name: Security Scan
        script:
          - pip install codewarden
          - |
            python -c "
            import codewarden
            import os
            codewarden.init(os.environ['CODEWARDEN_DSN'])
            result = codewarden.run_and_report_scan('.')
            print(f'Found {result.total_count} security issues')
            if result.severity_counts.get('critical', 0) > 0:
                exit(1)
            "

  pull-requests:
    '**':
      - step:
          name: Security Scan
          script:
            - pip install codewarden
            - |
              python -c "
              import codewarden
              import os
              codewarden.init(os.environ['CODEWARDEN_DSN'])
              result = codewarden.run_and_report_scan('.')
              print(f'Found {result.total_count} security issues')
              if result.severity_counts.get('critical', 0) > 0:
                  exit(1)
              "

# Add CODEWARDEN_DSN to repository variables:
# Repository settings > Repository variables > Add
# Name: CODEWARDEN_DSN
# Value: ${dsn}
# Secured: Yes`,
  };

  return configs[platform];
}

export default function IntegrationsPage() {
  const [apps, setApps] = useState<App[]>([]);
  const [selectedApp, setSelectedApp] = useState<App | null>(null);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [newKey, setNewKey] = useState<ApiKey | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingKeys, setLoadingKeys] = useState(false);
  const [creatingKey, setCreatingKey] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState<CIPlatform>('github');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    loadApps();
  }, []);

  useEffect(() => {
    if (selectedApp) {
      loadApiKeys(selectedApp.id);
    }
  }, [selectedApp]);

  async function loadApps() {
    try {
      setLoading(true);
      const data = await getApps();
      setApps(data);
      if (data.length > 0) {
        setSelectedApp(data[0]);
      }
    } catch (err) {
      console.error('Failed to load apps:', err);
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  }

  async function loadApiKeys(appId: string) {
    try {
      setLoadingKeys(true);
      const keys = await getApiKeys(appId);
      setApiKeys(keys);
      setNewKey(null);
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
      const key = await createApiKey(selectedApp.id, 'CI/CD Key', 'live');
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
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  }

  function getDSN(): string {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.codewarden.io';
    const apiHost = apiUrl.replace(/^https?:\/\//, '');
    const keyValue = newKey?.full_key || 'YOUR_API_KEY';
    return `https://${keyValue}@${apiHost}`;
  }

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <Header title="CI/CD Integration" description="Set up automated security scanning in your pipeline" />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header title="CI/CD Integration" description="Set up automated security scanning in your pipeline" />

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

        {apps.length === 0 ? (
          <Card className="border-dashed border-2">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="h-14 w-14 rounded-full bg-muted flex items-center justify-center mb-4">
                <GitBranch className="h-7 w-7 text-muted-foreground" />
              </div>
              <h3 className="font-semibold mb-1">No projects yet</h3>
              <p className="text-sm text-muted-foreground mb-4 text-center max-w-sm">
                Create a project first to set up CI/CD integration
              </p>
              <Button onClick={() => window.location.href = '/dashboard/projects'}>
                Go to Projects
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Left Column - Setup Steps */}
            <div className="lg:col-span-1 space-y-4">
              {/* Step 1: Select Project */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <span className="h-6 w-6 rounded-full bg-primary text-primary-foreground text-sm flex items-center justify-center">1</span>
                    Select Project
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <select
                    value={selectedApp?.id || ''}
                    onChange={(e) => {
                      const app = apps.find((a) => a.id === e.target.value);
                      setSelectedApp(app || null);
                    }}
                    className="w-full h-10 rounded-lg border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    {apps.map((app) => (
                      <option key={app.id} value={app.id}>
                        {app.name} ({app.environment})
                      </option>
                    ))}
                  </select>
                </CardContent>
              </Card>

              {/* Step 2: Get API Key */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <span className="h-6 w-6 rounded-full bg-primary text-primary-foreground text-sm flex items-center justify-center">2</span>
                    Get API Key
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {loadingKeys ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    </div>
                  ) : newKey?.full_key ? (
                    <div className="space-y-2">
                      <div className="p-3 rounded-lg bg-success/10 border border-success/20">
                        <p className="text-xs font-medium text-success mb-2">
                          Copy this key now - you won&apos;t see it again!
                        </p>
                        <div className="flex items-center gap-2">
                          <Input
                            value={newKey.full_key}
                            readOnly
                            className="font-mono text-xs h-8"
                          />
                          <Button
                            variant="outline"
                            size="icon"
                            className="h-8 w-8 shrink-0"
                            onClick={() => copyToClipboard(newKey.full_key!, 'apikey')}
                          >
                            {copiedId === 'apikey' ? (
                              <Check className="h-3 w-3 text-success" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )}
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : apiKeys.length > 0 ? (
                    <div className="space-y-2">
                      <div className="p-3 rounded-lg bg-muted/50">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium">{apiKeys[0].name}</p>
                            <p className="text-xs text-muted-foreground font-mono">
                              {apiKeys[0].key_prefix}••••••••
                            </p>
                          </div>
                          <span className="badge badge-info text-xs">{apiKeys[0].key_type}</span>
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Existing keys are masked. Generate a new key to see the full value.
                      </p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleCreateKey}
                        disabled={creatingKey}
                        className="w-full"
                      >
                        {creatingKey ? (
                          <Loader2 className="h-3 w-3 animate-spin mr-2" />
                        ) : (
                          <RefreshCw className="h-3 w-3 mr-2" />
                        )}
                        Generate New Key
                      </Button>
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <Key className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                      <p className="text-sm text-muted-foreground mb-3">No API key yet</p>
                      <Button onClick={handleCreateKey} disabled={creatingKey}>
                        {creatingKey ? (
                          <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        ) : (
                          <Key className="h-4 w-4 mr-2" />
                        )}
                        Generate API Key
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Step 3: Copy DSN */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <span className="h-6 w-6 rounded-full bg-primary text-primary-foreground text-sm flex items-center justify-center">3</span>
                    Your DSN
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Add this as a secret in your CI/CD platform
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    <Input
                      value={getDSN()}
                      readOnly
                      className="font-mono text-xs h-9"
                    />
                    <Button
                      variant="outline"
                      size="icon"
                      className="h-9 w-9 shrink-0"
                      onClick={() => copyToClipboard(getDSN(), 'dsn')}
                      disabled={!newKey?.full_key}
                    >
                      {copiedId === 'dsn' ? (
                        <Check className="h-4 w-4 text-success" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  {!newKey?.full_key && (
                    <p className="text-xs text-muted-foreground mt-2">
                      Generate an API key above to get your DSN
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Right Column - CI Config */}
            <div className="lg:col-span-2">
              <Card className="h-full flex flex-col">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        <span className="h-6 w-6 rounded-full bg-primary text-primary-foreground text-sm flex items-center justify-center">4</span>
                        Add CI/CD Configuration
                      </CardTitle>
                      <CardDescription className="text-xs mt-1">
                        Copy this config to your repository
                      </CardDescription>
                    </div>
                  </div>

                  {/* Platform Tabs */}
                  <div className="flex flex-wrap gap-2 mt-4">
                    {CI_PLATFORMS.map((platform) => (
                      <button
                        key={platform.id}
                        onClick={() => setSelectedPlatform(platform.id)}
                        className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                          selectedPlatform === platform.id
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80'
                        }`}
                      >
                        {platform.name}
                      </button>
                    ))}
                  </div>
                </CardHeader>

                <CardContent className="flex-1 flex flex-col">
                  {/* File path indicator */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Terminal className="h-3 w-3" />
                      <span className="font-mono">
                        {CI_PLATFORMS.find((p) => p.id === selectedPlatform)?.fileName}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <a
                        href={CI_PLATFORMS.find((p) => p.id === selectedPlatform)?.docsUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline flex items-center gap-1"
                      >
                        Docs
                        <ExternalLink className="h-3 w-3" />
                      </a>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs"
                        onClick={() => copyToClipboard(generateCIConfig(selectedPlatform, getDSN()), 'config')}
                      >
                        {copiedId === 'config' ? (
                          <>
                            <Check className="h-3 w-3 mr-1 text-success" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3 mr-1" />
                            Copy
                          </>
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Code block */}
                  <div className="flex-1 relative">
                    <pre className="p-4 rounded-lg bg-muted text-xs font-mono overflow-auto h-full max-h-[500px] whitespace-pre-wrap">
                      {generateCIConfig(selectedPlatform, getDSN())}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* Features Section */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <Shield className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-medium text-sm">Dependency Scanning</h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    Scans your dependencies for known CVEs using pip-audit
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-warning/10">
                  <Key className="h-5 w-5 text-warning" />
                </div>
                <div>
                  <h3 className="font-medium text-sm">Secret Detection</h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    Finds hardcoded API keys, passwords, and tokens
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-danger/10">
                  <Terminal className="h-5 w-5 text-danger" />
                </div>
                <div>
                  <h3 className="font-medium text-sm">Code Analysis</h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    Static analysis for SQL injection, XSS, and more
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
