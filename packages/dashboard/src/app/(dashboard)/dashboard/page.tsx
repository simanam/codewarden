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
import { AlertTriangle, CheckCircle, Clock, TrendingUp, Loader2 } from 'lucide-react';
import { getDashboardStats, getEvents, type DashboardStats, type Event } from '@/lib/api/client';
import Link from 'next/link';

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

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [statsData, eventsData] = await Promise.all([
          getDashboardStats(),
          getEvents({ limit: 5 }),
        ]);
        setStats(statsData);
        setEvents(eventsData);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const statCards = [
    {
      title: 'Total Apps',
      value: stats?.total_apps ?? 0,
      icon: TrendingUp,
      color: 'text-blue-400',
    },
    {
      title: 'Events (24h)',
      value: stats?.total_events_24h ?? 0,
      icon: TrendingUp,
      color: 'text-blue-400',
    },
    {
      title: 'Errors (24h)',
      value: stats?.total_errors_24h ?? 0,
      icon: AlertTriangle,
      color: stats?.total_errors_24h ? 'text-red-400' : 'text-green-400',
    },
    {
      title: 'Apps Healthy',
      value: stats?.apps_healthy ?? 0,
      icon: CheckCircle,
      color: 'text-green-400',
    },
  ];

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <Header
          title="Dashboard"
          description="Monitor your application health and security"
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
        title="Dashboard"
        description="Monitor your application health and security"
      />

      <div className="flex-1 p-6 space-y-6">
        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
            {error}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {statCards.map((stat) => (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-secondary-400">
                  {stat.title}
                </CardTitle>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Recent Events */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Events</CardTitle>
            <CardDescription>
              Latest events from your connected projects
            </CardDescription>
          </CardHeader>
          <CardContent>
            {events.length === 0 ? (
              <div className="text-center py-8 text-secondary-500">
                <p>No events yet.</p>
                <p className="text-sm mt-1">
                  Events will appear here once your SDK starts sending data.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {events.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-start gap-4 p-4 rounded-lg bg-secondary-800/50 hover:bg-secondary-800 transition-colors cursor-pointer"
                  >
                    <div
                      className={`mt-0.5 h-2 w-2 rounded-full ${
                        event.severity === 'critical' || event.severity === 'high'
                          ? 'bg-red-500'
                          : event.severity === 'medium'
                          ? 'bg-yellow-500'
                          : 'bg-blue-500'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {event.error_message || event.error_type || event.event_type}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs px-1.5 py-0.5 rounded ${
                          event.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                          event.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                          event.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {event.severity}
                        </span>
                        {event.file_path && (
                          <>
                            <span className="text-xs text-secondary-600">•</span>
                            <span className="text-xs text-secondary-500 truncate">
                              {event.file_path}
                              {event.line_number && `:${event.line_number}`}
                            </span>
                          </>
                        )}
                        <span className="text-xs text-secondary-600">•</span>
                        <span className="text-xs text-secondary-500">
                          {formatTime(event.occurred_at)}
                        </span>
                      </div>
                      {event.analysis_summary && (
                        <p className="text-xs text-secondary-400 mt-2">
                          AI: {event.analysis_summary}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-3">
          <Link href="/dashboard/projects">
            <Card className="hover:border-primary-500/50 transition-colors cursor-pointer h-full">
              <CardContent className="pt-6">
                <h3 className="font-medium mb-1">Create New Project</h3>
                <p className="text-sm text-secondary-400">
                  Set up a new project and get your SDK key
                </p>
              </CardContent>
            </Card>
          </Link>
          <a href="https://docs.codewarden.io" target="_blank" rel="noopener noreferrer">
            <Card className="hover:border-primary-500/50 transition-colors cursor-pointer h-full">
              <CardContent className="pt-6">
                <h3 className="font-medium mb-1">View Documentation</h3>
                <p className="text-sm text-secondary-400">
                  Learn how to integrate CodeWarden
                </p>
              </CardContent>
            </Card>
          </a>
          <Link href="/dashboard/settings">
            <Card className="hover:border-primary-500/50 transition-colors cursor-pointer h-full">
              <CardContent className="pt-6">
                <h3 className="font-medium mb-1">Configure Notifications</h3>
                <p className="text-sm text-secondary-400">
                  Set up alerts for your team
                </p>
              </CardContent>
            </Card>
          </Link>
        </div>
      </div>
    </div>
  );
}
