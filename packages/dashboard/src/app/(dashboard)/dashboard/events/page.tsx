'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState } from 'react';
import { Header } from '@/components/layout/header';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Filter, Download, Loader2, RefreshCw } from 'lucide-react';
import { getEvents, getApps, type Event, type App } from '@/lib/api/client';

function getLevelStyles(severity: string) {
  switch (severity) {
    case 'critical':
      return 'bg-red-500/10 text-red-400 border-red-500/20';
    case 'high':
      return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
    case 'medium':
      return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
    case 'low':
      return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    case 'info':
      return 'bg-secondary-500/10 text-secondary-400 border-secondary-500/20';
    default:
      return 'bg-secondary-500/10 text-secondary-400 border-secondary-500/20';
  }
}

function formatTime(timestamp: string) {
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

export default function EventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [apps, setApps] = useState<App[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [appFilter, setAppFilter] = useState<string>('all');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [eventsData, appsData] = await Promise.all([
        getEvents({ limit: 100 }),
        getApps(),
      ]);
      setEvents(eventsData);
      setApps(appsData);
    } catch (err) {
      console.error('Failed to load events:', err);
      setError(err instanceof Error ? err.message : 'Failed to load events');
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    await loadData();
  }

  // Filter events
  const filteredEvents = events.filter((event) => {
    if (severityFilter !== 'all' && event.severity !== severityFilter) {
      return false;
    }
    // App filter would require app_id on event, which we can add later
    return true;
  });

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <Header title="Events" description="View and manage application events and errors" />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header title="Events" description="View and manage application events and errors" />

      <div className="flex-1 p-6 space-y-6">
        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
            {error}
          </div>
        )}

        {/* Filters */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="h-9 rounded-lg border border-secondary-700 bg-secondary-900 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="info">Info</option>
            </select>
            {apps.length > 0 && (
              <select
                value={appFilter}
                onChange={(e) => setAppFilter(e.target.value)}
                className="h-9 rounded-lg border border-secondary-700 bg-secondary-900 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">All Projects</option>
                {apps.map((app) => (
                  <option key={app.id} value={app.id}>
                    {app.name}
                  </option>
                ))}
              </select>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Events List */}
        <Card>
          <CardHeader>
            <CardTitle>
              {filteredEvents.length === 0
                ? 'No Events'
                : `${filteredEvents.length} Event${filteredEvents.length !== 1 ? 's' : ''}`}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredEvents.length === 0 ? (
              <div className="text-center py-12 text-secondary-500">
                <p className="text-lg mb-2">No events yet</p>
                <p className="text-sm">
                  Events will appear here once your SDK starts sending data.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredEvents.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-center gap-4 p-4 rounded-lg bg-secondary-800/50 hover:bg-secondary-800 transition-colors cursor-pointer"
                  >
                    {/* Severity Badge */}
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium border ${getLevelStyles(
                        event.severity
                      )}`}
                    >
                      {event.severity?.toUpperCase() || 'UNKNOWN'}
                    </span>

                    {/* Message */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {event.error_message || event.error_type || event.event_type}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-secondary-500">
                          {event.event_type}
                        </span>
                        {event.file_path && (
                          <>
                            <span className="text-xs text-secondary-600">•</span>
                            <span className="text-xs text-secondary-500 font-mono truncate max-w-[200px]">
                              {event.file_path}
                              {event.line_number && `:${event.line_number}`}
                            </span>
                          </>
                        )}
                      </div>
                      {event.analysis_summary && (
                        <p className="text-xs text-primary-400 mt-1">
                          AI: {event.analysis_summary}
                        </p>
                      )}
                    </div>

                    {/* Status */}
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        event.status === 'resolved'
                          ? 'bg-green-500/10 text-green-400'
                          : event.status === 'acknowledged'
                          ? 'bg-yellow-500/10 text-yellow-400'
                          : 'bg-secondary-500/10 text-secondary-400'
                      }`}
                    >
                      {event.status}
                    </span>

                    {/* Analysis Status */}
                    {event.analysis_status === 'pending' && (
                      <span className="text-xs text-secondary-500 flex items-center gap-1">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Analyzing
                      </span>
                    )}

                    {/* Time */}
                    <span className="text-xs text-secondary-500 whitespace-nowrap">
                      {formatTime(event.occurred_at)}
                    </span>
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
