'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  AlertTriangle,
  FolderKanban,
  Settings,
  LogOut,
  Shield,
  Mail,
} from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Events', href: '/dashboard/events', icon: AlertTriangle },
  { name: 'Projects', href: '/dashboard/projects', icon: FolderKanban },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();

  const hasEmail = !!user?.email;
  const displayName =
    user?.user_metadata?.display_name ||
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email ||
    'User';

  // Get avatar initial from display name or email
  const avatarInitial = displayName.charAt(0).toUpperCase();

  return (
    <div className="flex h-full w-64 flex-col bg-secondary-900 border-r border-secondary-800">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 px-6 border-b border-secondary-800">
        <Shield className="h-8 w-8 text-primary-500" />
        <span className="text-xl font-bold">
          <span className="text-primary-500">Code</span>Warden
        </span>
      </div>

      {/* Email Missing Alert */}
      {!hasEmail && (
        <Link
          href="/dashboard/settings"
          className="mx-3 mt-3 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20 hover:bg-yellow-500/15 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4 text-yellow-500 shrink-0" />
            <div className="min-w-0">
              <p className="text-xs font-medium text-yellow-400">
                Add your email
              </p>
              <p className="text-xs text-secondary-500 truncate">
                Get notified about errors
              </p>
            </div>
          </div>
        </Link>
      )}

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-secondary-400 hover:bg-secondary-800 hover:text-white'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* User Section */}
      <div className="border-t border-secondary-800 p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center text-sm font-medium">
            {avatarInitial}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {displayName}
            </p>
            <p className="text-xs text-secondary-500">Free Plan</p>
          </div>
        </div>
        <button
          onClick={() => signOut()}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-secondary-400 hover:bg-secondary-800 hover:text-white transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </button>
      </div>
    </div>
  );
}
