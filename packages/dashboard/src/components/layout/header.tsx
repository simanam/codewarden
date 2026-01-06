'use client';

import { useState, useEffect } from 'react';
import { Bell, Search, AlertTriangle, CheckCircle, Info, X } from 'lucide-react';
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
    <header className="flex h-16 items-center justify-between border-b border-secondary-800 px-6">
      <div>
        <h1 className="text-xl font-semibold">{title}</h1>
        {description && (
          <p className="text-sm text-secondary-400">{description}</p>
        )}
      </div>
      <div className="flex items-center gap-4">
        {action}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-secondary-500" />
          <Input
            placeholder="Search events..."
            className="w-64 pl-9"
          />
        </div>
        <div className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="relative"
            onClick={() => setShowNotifications(!showNotifications)}
          >
            <Bell className="h-5 w-5" />
            {criticalCount > 0 && (
              <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 text-[10px] font-medium flex items-center justify-center">
                {criticalCount > 9 ? '9+' : criticalCount}
              </span>
            )}
          </Button>

          {/* Notification Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 top-full mt-2 w-80 rounded-lg border border-secondary-700 bg-secondary-900 shadow-xl z-50">
              <div className="flex items-center justify-between p-3 border-b border-secondary-800">
                <h3 className="font-medium">Notifications</h3>
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
                  <div className="p-4 text-center text-secondary-500">
                    Loading...
                  </div>
                ) : notifications.length === 0 ? (
                  <div className="p-4 text-center text-secondary-500">
                    <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500 opacity-50" />
                    <p>All clear!</p>
                    <p className="text-xs mt-1">No recent events</p>
                  </div>
                ) : (
                  <div className="divide-y divide-secondary-800">
                    {notifications.map((event) => (
                      <div
                        key={event.id}
                        className="p-3 hover:bg-secondary-800/50 cursor-pointer"
                      >
                        <div className="flex items-start gap-3">
                          <div className={`mt-0.5 ${
                            event.severity === 'critical' ? 'text-red-400' :
                            event.severity === 'warning' ? 'text-yellow-400' :
                            'text-blue-400'
                          }`}>
                            {event.severity === 'critical' ? (
                              <AlertTriangle className="h-4 w-4" />
                            ) : (
                              <Info className="h-4 w-4" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">
                              {event.error_type || event.event_type}
                            </p>
                            <p className="text-xs text-secondary-400 truncate">
                              {event.error_message || 'No details'}
                            </p>
                            <p className="text-xs text-secondary-500 mt-1">
                              {formatTime(event.occurred_at)}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="p-2 border-t border-secondary-800">
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
