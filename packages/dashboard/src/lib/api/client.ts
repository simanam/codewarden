/**
 * CodeWarden API Client
 *
 * Handles all API calls from the dashboard to the backend.
 * Uses Supabase session for authentication.
 */

import { createClient } from '@/lib/supabase/client';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface App {
  id: string;
  name: string;
  slug: string;
  description?: string;
  environment: string;
  framework?: string;
  status: string;
  created_at: string;
  last_event_at?: string;
  event_count_24h: number;
  error_count_24h: number;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  key_type: string;
  full_key?: string; // Only on creation
  permissions: string[];
  created_at: string;
  last_used_at?: string;
}

export interface Event {
  id: string;
  event_type: string;
  severity: string;
  error_type?: string;
  error_message?: string;
  file_path?: string;
  line_number?: number;
  status: string;
  occurred_at: string;
  analysis_status: string;
  analysis_summary?: string;
}

export interface DashboardStats {
  total_apps: number;
  total_events_24h: number;
  total_errors_24h: number;
  critical_count: number;
  warning_count: number;
  apps_healthy: number;
  apps_warning: number;
  apps_critical: number;
}

// Get auth token from Supabase session
async function getAuthToken(): Promise<string | null> {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || null;
}

// API request helper
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();

  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.detail || error.message || `HTTP ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// API Functions

// Dashboard Stats
export async function getDashboardStats(): Promise<DashboardStats> {
  return apiRequest<DashboardStats>('/api/dashboard/stats');
}

// Apps
export async function getApps(): Promise<App[]> {
  return apiRequest<App[]>('/api/dashboard/apps');
}

export async function getApp(appId: string): Promise<App> {
  return apiRequest<App>(`/api/dashboard/apps/${appId}`);
}

export async function createApp(data: {
  name: string;
  description?: string;
  environment?: string;
  framework?: string;
}): Promise<App> {
  return apiRequest<App>('/api/dashboard/apps', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteApp(appId: string): Promise<void> {
  await apiRequest<void>(`/api/dashboard/apps/${appId}`, {
    method: 'DELETE',
  });
}

// API Keys
export async function getApiKeys(appId: string): Promise<ApiKey[]> {
  return apiRequest<ApiKey[]>(`/api/dashboard/apps/${appId}/keys`);
}

export async function createApiKey(
  appId: string,
  name: string = 'Default Key',
  keyType: string = 'live'
): Promise<ApiKey> {
  return apiRequest<ApiKey>(
    `/api/dashboard/apps/${appId}/keys?name=${encodeURIComponent(name)}&key_type=${keyType}`,
    { method: 'POST' }
  );
}

export async function revokeApiKey(keyId: string): Promise<void> {
  await apiRequest<void>(`/api/dashboard/keys/${keyId}`, {
    method: 'DELETE',
  });
}

// Events
export async function getEvents(options?: {
  appId?: string;
  limit?: number;
  severity?: string;
}): Promise<Event[]> {
  const params = new URLSearchParams();
  if (options?.limit) params.set('limit', options.limit.toString());
  if (options?.severity) params.set('severity', options.severity);

  const query = params.toString() ? `?${params.toString()}` : '';

  if (options?.appId) {
    return apiRequest<Event[]>(`/api/dashboard/apps/${options.appId}/events${query}`);
  }
  return apiRequest<Event[]>(`/api/dashboard/events${query}`);
}

export async function getAppEvents(
  appId: string,
  options?: {
    limit?: number;
    offset?: number;
    severity?: string;
    status?: string;
  }
): Promise<Event[]> {
  const params = new URLSearchParams();
  if (options?.limit) params.set('limit', options.limit.toString());
  if (options?.offset) params.set('offset', options.offset.toString());
  if (options?.severity) params.set('severity', options.severity);
  if (options?.status) params.set('status_filter', options.status);

  const query = params.toString() ? `?${params.toString()}` : '';
  return apiRequest<Event[]>(`/api/dashboard/apps/${appId}/events${query}`);
}

// Settings
export interface PlanLimits {
  events_per_month: number;
  apps_limit: number;
  retention_days: number;
  ai_analysis: boolean;
  security_scans: boolean | string;
  evidence_locker: boolean;
  team_members: number;
  sso?: boolean;
  dedicated_support?: boolean;
  priority_support?: boolean;
  partner_badge?: boolean;
  admin_access?: boolean;
  bypass_rate_limits?: boolean;
  system_admin?: boolean;
  is_paid: boolean;
}

export interface PlanInfo {
  plan: 'hobbyist' | 'builder' | 'pro' | 'team' | 'enterprise' | 'partner' | 'admin';
  plan_limits: PlanLimits;
  is_paid: boolean;
  is_partner: boolean;
  is_admin: boolean;
}

export interface OrganizationSettings {
  name: string;
  plan_info?: PlanInfo;
  notification_email?: string;
  telegram_chat_id?: string;
  slack_webhook?: string;
  notify_on_critical: boolean;
  notify_on_warning: boolean;
  weekly_digest: boolean;
}

export async function getSettings(): Promise<OrganizationSettings> {
  return apiRequest<OrganizationSettings>('/api/dashboard/settings');
}

export async function updateSettings(settings: Partial<OrganizationSettings>): Promise<OrganizationSettings> {
  return apiRequest<OrganizationSettings>('/api/dashboard/settings', {
    method: 'PATCH',
    body: JSON.stringify(settings),
  });
}

// Architecture Map
export interface ServiceNode {
  id: string;
  type: 'database' | 'api' | 'external' | 'cache' | 'frontend' | 'storage';
  name: string;
  status: 'healthy' | 'warning' | 'critical';
  latency?: number;
  error_rate?: number;
  url?: string;
  last_checked?: string;
}

export interface ServiceEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

export interface ArchitectureMap {
  nodes: ServiceNode[];
  edges: ServiceEdge[];
}

export async function getArchitectureMap(appId: string): Promise<ArchitectureMap> {
  return apiRequest<ArchitectureMap>(`/api/dashboard/apps/${appId}/architecture`);
}

// AI Status
export interface AIStatus {
  available: boolean;
  models: string[];
  message: string;
}

export async function getAIStatus(): Promise<AIStatus> {
  return apiRequest<AIStatus>('/api/dashboard/ai/status');
}

// Notification Status
export interface NotificationStatus {
  available: boolean;
  channels: string[];
  message: string;
}

export async function getNotificationStatus(): Promise<NotificationStatus> {
  return apiRequest<NotificationStatus>('/api/dashboard/notifications/status');
}

// Compliance
export interface ComplianceCheck {
  id: string;
  name: string;
  description: string;
  status: 'passing' | 'failing' | 'not_configured';
  last_checked: string | null;
  category: string;
  details?: string;
}

export interface ComplianceStatus {
  score: number;
  passing_count: number;
  failing_count: number;
  not_configured_count: number;
  checks: ComplianceCheck[];
}

export async function getComplianceStatus(): Promise<ComplianceStatus> {
  return apiRequest<ComplianceStatus>('/api/dashboard/compliance');
}

// Evidence
export interface EvidenceEvent {
  id: string;
  event_type: string;
  title?: string;
  description?: string;
  severity: string;
  actor_email?: string;
  ip_address?: string;
  created_at: string;
}

export interface EvidenceListResponse {
  events: EvidenceEvent[];
  total: number;
}

export async function getEvidenceEvents(
  appId: string,
  options?: {
    limit?: number;
    offset?: number;
    event_type?: string;
  }
): Promise<EvidenceListResponse> {
  const params = new URLSearchParams();
  if (options?.limit) params.set('limit', options.limit.toString());
  if (options?.offset) params.set('offset', options.offset.toString());
  if (options?.event_type) params.set('event_type', options.event_type);

  const query = params.toString() ? `?${params.toString()}` : '';
  return apiRequest<EvidenceListResponse>(`/api/dashboard/apps/${appId}/evidence${query}`);
}

export async function getAllEvidenceEvents(
  options?: {
    limit?: number;
  }
): Promise<EvidenceEvent[]> {
  // Get evidence from all apps by fetching apps first then their evidence
  const apps = await getApps();
  const allEvents: EvidenceEvent[] = [];

  for (const app of apps.slice(0, 5)) { // Limit to first 5 apps
    try {
      const response = await getEvidenceEvents(app.id, { limit: options?.limit || 10 });
      allEvents.push(...response.events);
    } catch {
      // Skip apps with no evidence
    }
  }

  // Sort by created_at desc and limit
  return allEvents
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, options?.limit || 20);
}

export interface ExportRequest {
  format: 'json' | 'csv' | 'pdf';
  start_date?: string;
  end_date?: string;
  event_types?: string[];
}

export interface ExportResponse {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  format: string;
  download_url?: string;
  record_count?: number;
  error?: string;
}

export async function requestEvidenceExport(
  appId: string,
  request: ExportRequest
): Promise<ExportResponse> {
  return apiRequest<ExportResponse>(`/api/dashboard/apps/${appId}/evidence/export`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getExportStatus(exportId: string): Promise<ExportResponse> {
  return apiRequest<ExportResponse>(`/api/dashboard/exports/${exportId}`);
}

// Security
export interface SecurityStats {
  total_apps: number;
  apps_scanned: number;
  total_vulnerabilities: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  last_scan_at: string | null;
  scans_this_week: number;
}

export interface SecurityScan {
  id: string;
  app_id: string;
  scan_type: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  duration_ms?: number;
  vulnerability_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
}

export interface SecurityScanList {
  scans: SecurityScan[];
  total: number;
}

export async function getSecurityStats(): Promise<SecurityStats> {
  return apiRequest<SecurityStats>('/api/dashboard/security/stats');
}

export async function getRecentScans(limit: number = 10): Promise<SecurityScanList> {
  return apiRequest<SecurityScanList>(`/api/dashboard/security/scans?limit=${limit}`);
}

export async function getAppScans(appId: string, options?: {
  limit?: number;
  offset?: number;
}): Promise<SecurityScanList> {
  const params = new URLSearchParams();
  if (options?.limit) params.set('limit', options.limit.toString());
  if (options?.offset) params.set('offset', options.offset.toString());

  const query = params.toString() ? `?${params.toString()}` : '';
  return apiRequest<SecurityScanList>(`/api/dashboard/apps/${appId}/scans${query}`);
}

export async function triggerSecurityScan(appId: string, scanType: string = 'full'): Promise<SecurityScan> {
  return apiRequest<SecurityScan>(`/api/dashboard/apps/${appId}/scan`, {
    method: 'POST',
    body: JSON.stringify({ scan_type: scanType }),
  });
}

// Profile Repair (for users who signed up before the trigger fix)
export interface RepairProfileResponse {
  status: 'already_configured' | 'repaired';
  org_id: string;
  message: string;
}

export async function repairProfile(): Promise<RepairProfileResponse> {
  return apiRequest<RepairProfileResponse>('/api/dashboard/repair-profile', {
    method: 'POST',
  });
}
