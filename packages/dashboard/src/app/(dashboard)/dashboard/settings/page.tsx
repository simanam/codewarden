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
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/auth-context';
import { AlertTriangle, Mail, CheckCircle } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';

export default function SettingsPage() {
  const { user } = useAuth();
  const [saving, setSaving] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [emailSaving, setEmailSaving] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [emailSuccess, setEmailSuccess] = useState(false);

  const hasEmail = !!user?.email;

  useEffect(() => {
    // Load display name from user metadata
    if (user?.user_metadata?.display_name) {
      setDisplayName(user.user_metadata.display_name);
    } else if (user?.user_metadata?.full_name) {
      setDisplayName(user.user_metadata.full_name);
    } else if (user?.user_metadata?.name) {
      setDisplayName(user.user_metadata.name);
    }
  }, [user]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const supabase = createClient();
      await supabase.auth.updateUser({
        data: { display_name: displayName },
      });
    } catch {
      // Handle error silently for now
    }
    setSaving(false);
  };

  const handleAddEmail = async () => {
    if (!newEmail) return;

    setEmailSaving(true);
    setEmailError(null);
    setEmailSuccess(false);

    try {
      const supabase = createClient();
      const { error } = await supabase.auth.updateUser({
        email: newEmail,
      });

      if (error) {
        setEmailError(error.message);
      } else {
        setEmailSuccess(true);
        setNewEmail('');
      }
    } catch {
      setEmailError('Failed to update email. Please try again.');
    }

    setEmailSaving(false);
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title="Settings"
        description="Manage your account and preferences"
      />

      <div className="flex-1 p-6 space-y-6 max-w-2xl">
        {/* Email Missing Banner */}
        {!hasEmail && (
          <Card className="border-yellow-500/30 bg-yellow-500/5">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="p-2 rounded-full bg-yellow-500/10">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-yellow-400">
                    Add your email address
                  </h3>
                  <p className="text-sm text-secondary-400 mt-1">
                    You signed in without an email address. Add one to receive
                    important notifications about errors and security alerts.
                  </p>
                  <div className="flex items-center gap-2 mt-4">
                    <Input
                      type="email"
                      placeholder="you@example.com"
                      value={newEmail}
                      onChange={(e) => setNewEmail(e.target.value)}
                      className="max-w-xs"
                    />
                    <Button
                      onClick={handleAddEmail}
                      loading={emailSaving}
                      disabled={!newEmail}
                    >
                      <Mail className="h-4 w-4 mr-2" />
                      Add Email
                    </Button>
                  </div>
                  {emailError && (
                    <p className="text-sm text-red-400 mt-2">{emailError}</p>
                  )}
                  {emailSuccess && (
                    <div className="flex items-center gap-2 mt-2 text-green-400">
                      <CheckCircle className="h-4 w-4" />
                      <p className="text-sm">
                        Verification email sent! Check your inbox.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Profile Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
            <CardDescription>
              Manage your account information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              {hasEmail ? (
                <>
                  <Input
                    id="email"
                    type="email"
                    value={user?.email || ''}
                    disabled
                  />
                  <p className="text-xs text-secondary-500">
                    Your email cannot be changed
                  </p>
                </>
              ) : (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-secondary-800/50 border border-secondary-700">
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  <span className="text-sm text-secondary-400">
                    No email address - add one above to receive notifications
                  </span>
                </div>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="name">Display Name</Label>
              <Input
                id="name"
                placeholder="Your name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            </div>
            <Button onClick={handleSave} loading={saving}>
              Save Changes
            </Button>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>
              Configure how you receive alerts
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Email Notifications</p>
                <p className="text-sm text-secondary-400">
                  Receive email alerts for critical errors
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-secondary-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Telegram Notifications</p>
                <p className="text-sm text-secondary-400">
                  Get instant alerts via Telegram bot
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" />
                <div className="w-11 h-6 bg-secondary-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Weekly Digest</p>
                <p className="text-sm text-secondary-400">
                  Receive a weekly summary of events
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-secondary-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="border-red-500/20">
          <CardHeader>
            <CardTitle className="text-red-400">Danger Zone</CardTitle>
            <CardDescription>
              Irreversible actions for your account
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-lg bg-red-500/5 border border-red-500/20">
              <div>
                <p className="font-medium">Delete Account</p>
                <p className="text-sm text-secondary-400">
                  Permanently delete your account and all data
                </p>
              </div>
              <Button variant="destructive">Delete Account</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
