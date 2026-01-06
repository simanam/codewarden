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
  FileCheck,
  Menu,
  X,
  Star,
  Crown,
} from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { useState, useEffect } from 'react';
import { getSettings, PlanInfo } from '@/lib/api/client';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Events', href: '/dashboard/events', icon: AlertTriangle },
  { name: 'Projects', href: '/dashboard/projects', icon: FolderKanban },
  { name: 'Security', href: '/dashboard/security', icon: Shield },
  { name: 'Compliance', href: '/dashboard/compliance', icon: FileCheck },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [planInfo, setPlanInfo] = useState<PlanInfo | null>(null);

  const hasEmail = !!user?.email;

  // Fetch plan info
  useEffect(() => {
    if (user) {
      getSettings()
        .then((settings) => {
          if (settings.plan_info) {
            setPlanInfo(settings.plan_info);
          }
        })
        .catch(() => {
          // Silently fail - plan info is not critical
        });
    }
  }, [user]);
  const displayName =
    user?.user_metadata?.display_name ||
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email ||
    'User';

  const avatarInitial = displayName.charAt(0).toUpperCase();

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 px-4 border-b border-border">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary text-primary-foreground">
          <Shield className="h-5 w-5" />
        </div>
        <span className="text-lg font-semibold tracking-tight">
          CodeWarden
        </span>
      </div>

      {/* Email Missing Alert */}
      {!hasEmail && (
        <Link
          href="/dashboard/settings"
          className="mx-3 mt-3 p-3 rounded-lg bg-accent/10 border border-accent/20 hover:bg-accent/15 transition-colors group"
          onClick={() => setMobileOpen(false)}
        >
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-accent/20">
              <Mail className="h-4 w-4 text-accent" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-accent">
                Add your email
              </p>
              <p className="text-xs text-muted-foreground truncate">
                Get notified about errors
              </p>
            </div>
          </div>
        </Link>
      )}

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              <item.icon className={cn('h-4.5 w-4.5', isActive && 'text-primary-foreground')} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className="border-t border-border p-3 space-y-3">
        {/* Theme Toggle */}
        <div className="flex items-center justify-between px-1">
          <span className="text-xs font-medium text-muted-foreground">Theme</span>
          <ThemeToggle />
        </div>

        {/* User Section */}
        <div className="p-2 rounded-lg bg-muted/50">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center text-sm font-semibold text-primary-foreground shadow-sm">
              {avatarInitial}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">
                {displayName}
              </p>
              <div className="flex items-center gap-1.5">
                {planInfo?.is_admin ? (
                  <>
                    <Shield className="h-3 w-3 text-danger" />
                    <span className="text-xs font-medium text-danger">Admin</span>
                  </>
                ) : planInfo?.is_partner ? (
                  <>
                    <Star className="h-3 w-3 text-accent" />
                    <span className="text-xs font-medium text-accent">Partner</span>
                  </>
                ) : planInfo ? (
                  <>
                    <Crown className="h-3 w-3 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">
                      {planInfo.plan.charAt(0).toUpperCase() + planInfo.plan.slice(1)} Plan
                    </span>
                  </>
                ) : (
                  <span className="text-xs text-muted-foreground">Loading...</span>
                )}
              </div>
            </div>
          </div>
        </div>

        <button
          onClick={() => signOut()}
          className="flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed top-3 left-3 z-40 p-2 rounded-lg bg-card border border-border shadow-sm lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Mobile Sidebar Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 transform bg-card border-r border-border transition-transform duration-300 ease-out lg:hidden',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute top-3 right-3 p-2 rounded-lg hover:bg-muted"
        >
          <X className="h-5 w-5" />
        </button>
        <div className="flex h-full flex-col">
          <SidebarContent />
        </div>
      </div>

      {/* Desktop Sidebar */}
      <div className="hidden lg:flex h-full w-64 flex-col bg-card border-r border-border">
        <SidebarContent />
      </div>
    </>
  );
}
