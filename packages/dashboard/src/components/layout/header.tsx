'use client';

import { useState, useEffect } from 'react';
import { Bell, Search, AlertTriangle, CheckCircle, Info, X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { getEvents, type Event } from '@/lib/api/client';

interface HeaderProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
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

export function Header({ title, description, action }: HeaderProps) {
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState<Event[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);

  useEffect(() => {
    if (showNotifications && !hasLoaded) {
      loadNotifications();
    }
  }, [showNotifications, hasLoaded]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as HTMLElement;
      if (!target.closest('[data-notifications]')) {
        setShowNotifications(false);
      }
    }

    if (showNotifications) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showNotifications]);

  async function loadNotifications() {
    try {
      setLoading(true);
      const events = await getEvents({ limit: 10 });
      setNotifications(events);
      setHasLoaded(true);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  }

  const criticalCount = notifications.filter(n => n.severity === 'critical').length;

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 md:px-6">
      <div className="flex-1 min-w-0 pl-10 lg:pl-0">
        <h1 className="text-lg md:text-xl font-semibold tracking-tight truncate">{title}</h1>
        {description && (
          <p className="text-xs md:text-sm text-muted-foreground truncate hidden sm:block">{description}</p>
        )}
      </div>

      <div className="flex items-center gap-2 md:gap-3">
        {action}

        {/* Search - Hidden on mobile */}
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search events..."
            className="w-48 lg:w-64 pl-9 h-9 bg-muted/50"
          />
        </div>

        {/* Notifications */}
        <div className="relative" data-notifications>
          <Button
            variant="ghost"
            size="icon"
            className="relative"
            onClick={(e) => {
              e.stopPropagation();
              setShowNotifications(!showNotifications);
            }}
          >
            <Bell className="h-5 w-5" />
            {criticalCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-danger text-[10px] font-medium flex items-center justify-center text-white animate-pulse">
                {criticalCount > 9 ? '9+' : criticalCount}
              </span>
            )}
          </Button>

          {/* Notification Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 top-full mt-2 w-80 rounded-lg border border-border bg-card shadow-lg z-50 animate-slide-down overflow-hidden">
              <div className="flex items-center justify-between p-3 border-b border-border bg-muted/30">
                <h3 className="font-medium text-sm">Notifications</h3>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => setShowNotifications(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <div className="max-h-80 overflow-auto">
                {loading ? (
                  <div className="p-6 text-center text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2" />
                    <p className="text-sm">Loading...</p>
                  </div>
                ) : notifications.length === 0 ? (
                  <div className="p-6 text-center">
                    <div className="w-12 h-12 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-3">
                      <CheckCircle className="h-6 w-6 text-success" />
                    </div>
                    <p className="font-medium text-sm">All clear!</p>
                    <p className="text-xs text-muted-foreground mt-1">No recent events</p>
                  </div>
                ) : (
                  <div className="divide-y divide-border">
                    {notifications.map((event) => (
                      <div
                        key={event.id}
                        className="p-3 hover:bg-muted/50 cursor-pointer transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <div className={`mt-0.5 p-1.5 rounded-full ${
                            event.severity === 'critical'
                              ? 'bg-danger/10 text-danger'
                              : event.severity === 'warning'
                              ? 'bg-warning/10 text-warning'
                              : 'bg-primary/10 text-primary'
                          }`}>
                            {event.severity === 'critical' ? (
                              <AlertTriangle className="h-3.5 w-3.5" />
                            ) : (
                              <Info className="h-3.5 w-3.5" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">
                              {event.error_type || event.event_type}
                            </p>
                            <p className="text-xs text-muted-foreground truncate mt-0.5">
                              {event.error_message || 'No details'}
                            </p>
                            <p className="text-xs text-muted-foreground/70 mt-1">
                              {formatTime(event.occurred_at)}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="p-2 border-t border-border bg-muted/30">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full text-xs"
                  onClick={() => {
                    setShowNotifications(false);
                    window.location.href = '/dashboard/events';
                  }}
                >
                  View all events
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
