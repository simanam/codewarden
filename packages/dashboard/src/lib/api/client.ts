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
export interface OrganizationSettings {
  name: string;
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
