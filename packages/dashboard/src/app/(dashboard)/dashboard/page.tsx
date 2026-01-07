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
import { AlertTriangle, CheckCircle, Layers, TrendingUp, Loader2, ArrowRight, BookOpen, Bell, FolderPlus } from 'lucide-react';
import { getDashboardStats, getEvents, repairProfile, type DashboardStats, type Event } from '@/lib/api/client';
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
  const [repairing, setRepairing] = useState(false);

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
        const errorMessage = err instanceof Error ? err.message : 'Failed to load data';

        // If the error is about missing organization, try to repair the profile
        if (errorMessage.includes('not linked to an organization') || errorMessage.includes('Organization not found')) {
          setRepairing(true);
          try {
            const result = await repairProfile();
            if (result.status === 'repaired') {
              // Profile repaired, reload the page
              window.location.reload();
              return;
            }
          } catch (repairErr) {
            console.error('Failed to repair profile:', repairErr);
          } finally {
            setRepairing(false);
          }
        }

        setError(errorMessage);
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
      icon: Layers,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      title: 'Events (24h)',
      value: stats?.total_events_24h ?? 0,
      icon: TrendingUp,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      title: 'Errors (24h)',
      value: stats?.total_errors_24h ?? 0,
      icon: AlertTriangle,
      color: stats?.total_errors_24h ? 'text-danger' : 'text-success',
      bgColor: stats?.total_errors_24h ? 'bg-danger/10' : 'bg-success/10',
    },
    {
      title: 'Apps Healthy',
      value: stats?.apps_healthy ?? 0,
      icon: CheckCircle,
      color: 'text-success',
      bgColor: 'bg-success/10',
    },
  ];

  if (loading || repairing) {
    return (
      <div className="flex flex-col h-full">
        <Header
          title="Dashboard"
          description="Monitor your application health and security"
        />
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          {repairing && (
            <p className="text-sm text-muted-foreground">Setting up your account...</p>
          )}
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

      <div className="flex-1 p-4 md:p-6 space-y-6 overflow-auto">
        {error && (
          <div className="p-4 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm">
            {error}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid gap-3 md:gap-4 grid-cols-2 lg:grid-cols-4">
          {statCards.map((stat) => (
            <Card key={stat.title} className="card-interactive">
              <CardContent className="p-4 md:p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs md:text-sm font-medium text-muted-foreground">
                      {stat.title}
                    </p>
                    <p className="stat-value mt-1">{stat.value}</p>
                  </div>
                  <div className={`p-2.5 rounded-lg ${stat.bgColor}`}>
                    <stat.icon className={`h-5 w-5 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Recent Events */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Events</CardTitle>
                <CardDescription className="mt-1">
                  Latest events from your connected projects
                </CardDescription>
              </div>
              {events.length > 0 && (
                <Link
                  href="/dashboard/events"
                  className="text-sm text-primary hover:text-primary/80 font-medium flex items-center gap-1 transition-colors"
                >
                  View all
                  <ArrowRight className="h-4 w-4" />
                </Link>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {events.length === 0 ? (
              <div className="text-center py-10">
                <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="h-7 w-7 text-muted-foreground" />
                </div>
                <p className="font-medium">No events yet</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Events will appear here once your SDK starts sending data.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {events.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-start gap-3 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors cursor-pointer group"
                  >
                    <div className={`mt-1 p-1.5 rounded-full shrink-0 ${
                      event.severity === 'critical' || event.severity === 'high'
                        ? 'bg-danger/10'
                        : event.severity === 'medium'
                        ? 'bg-warning/10'
                        : 'bg-primary/10'
                    }`}>
                      <div
                        className={`h-2 w-2 rounded-full ${
                          event.severity === 'critical' || event.severity === 'high'
                            ? 'bg-danger'
                            : event.severity === 'medium'
                            ? 'bg-warning'
                            : 'bg-primary'
                        }`}
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                        {event.error_message || event.error_type || event.event_type}
                      </p>
                      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-1.5">
                        <span className={`badge ${
                          event.severity === 'critical' ? 'badge-danger' :
                          event.severity === 'high' ? 'badge-danger' :
                          event.severity === 'medium' ? 'badge-warning' :
                          'badge-info'
                        }`}>
                          {event.severity}
                        </span>
                        {event.file_path && (
                          <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                            {event.file_path}
                            {event.line_number && `:${event.line_number}`}
                          </span>
                        )}
                        <span className="text-xs text-muted-foreground">
                          {formatTime(event.occurred_at)}
                        </span>
                      </div>
                      {event.analysis_summary && (
                        <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                          <span className="font-medium text-primary">AI:</span> {event.analysis_summary}
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
        <div className="grid gap-3 md:gap-4 grid-cols-1 md:grid-cols-3">
          <Link href="/dashboard/projects">
            <Card className="card-interactive h-full group">
              <CardContent className="p-5">
                <div className="flex items-start gap-4">
                  <div className="p-2.5 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                    <FolderPlus className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium group-hover:text-primary transition-colors">Create New Project</h3>
                    <p className="text-sm text-muted-foreground mt-0.5">
                      Set up a new project and get your SDK key
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
          <a href="https://docs.codewarden.io" target="_blank" rel="noopener noreferrer">
            <Card className="card-interactive h-full group">
              <CardContent className="p-5">
                <div className="flex items-start gap-4">
                  <div className="p-2.5 rounded-lg bg-accent/10 group-hover:bg-accent/20 transition-colors">
                    <BookOpen className="h-5 w-5 text-accent" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium group-hover:text-accent transition-colors">View Documentation</h3>
                    <p className="text-sm text-muted-foreground mt-0.5">
                      Learn how to integrate CodeWarden
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </a>
          <Link href="/dashboard/settings">
            <Card className="card-interactive h-full group">
              <CardContent className="p-5">
                <div className="flex items-start gap-4">
                  <div className="p-2.5 rounded-lg bg-success/10 group-hover:bg-success/20 transition-colors">
                    <Bell className="h-5 w-5 text-success" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium group-hover:text-success transition-colors">Configure Notifications</h3>
                    <p className="text-sm text-muted-foreground mt-0.5">
                      Set up alerts for your team
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        </div>
      </div>
    </div>
  );
}
