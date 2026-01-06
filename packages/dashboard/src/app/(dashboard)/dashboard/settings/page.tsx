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
import {
  AlertTriangle,
  Mail,
  CheckCircle,
  Bell,
  MessageCircle,
  Loader2,
  Save,
  Sparkles,
} from 'lucide-react';
import { createClient } from '@/lib/supabase/client';
import {
  getSettings,
  updateSettings,
  getAIStatus,
  getNotificationStatus,
  OrganizationSettings,
  AIStatus,
  NotificationStatus,
} from '@/lib/api/client';

export default function SettingsPage() {
  const { user } = useAuth();
  const [saving, setSaving] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [emailSaving, setEmailSaving] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [emailSuccess, setEmailSuccess] = useState(false);

  // Organization settings
  const [settings, setSettings] = useState<OrganizationSettings | null>(null);
  const [settingsLoading, setSettingsLoading] = useState(true);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [settingsSuccess, setSettingsSuccess] = useState(false);

  // Notification email input
  const [notificationEmail, setNotificationEmail] = useState('');
  const [telegramChatId, setTelegramChatId] = useState('');

  // Service status
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [notificationStatus, setNotificationStatus] =
    useState<NotificationStatus | null>(null);

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

  useEffect(() => {
    // Load organization settings
    async function loadSettings() {
      try {
        const [orgSettings, ai, notifications] = await Promise.all([
          getSettings(),
          getAIStatus(),
          getNotificationStatus(),
        ]);
        setSettings(orgSettings);
        setNotificationEmail(orgSettings.notification_email || '');
        setTelegramChatId(orgSettings.telegram_chat_id || '');
        setAiStatus(ai);
        setNotificationStatus(notifications);
      } catch (err) {
        console.error('Failed to load settings:', err);
        setSettingsError('Failed to load settings');
      } finally {
        setSettingsLoading(false);
      }
    }

    loadSettings();
  }, []);

  const handleSaveProfile = async () => {
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

  const handleSaveNotifications = async () => {
    if (!settings) return;

    setSettingsSaving(true);
    setSettingsError(null);
    setSettingsSuccess(false);

    try {
      const updated = await updateSettings({
        notification_email: notificationEmail || undefined,
        telegram_chat_id: telegramChatId || undefined,
        notify_on_critical: settings.notify_on_critical,
        notify_on_warning: settings.notify_on_warning,
        weekly_digest: settings.weekly_digest,
      });
      setSettings(updated);
      setSettingsSuccess(true);
      setTimeout(() => setSettingsSuccess(false), 3000);
    } catch (err) {
      setSettingsError('Failed to save settings');
    } finally {
      setSettingsSaving(false);
    }
  };

  const toggleSetting = (key: keyof OrganizationSettings) => {
    if (!settings) return;
    setSettings({
      ...settings,
      [key]: !settings[key],
    });
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
                      disabled={!newEmail || emailSaving}
                    >
                      {emailSaving ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Mail className="h-4 w-4 mr-2" />
                      )}
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

        {/* Service Status Cards */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* AI Status */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div
                  className={`p-2 rounded-full ${
                    aiStatus?.available
                      ? 'bg-green-500/10'
                      : 'bg-secondary-700'
                  }`}
                >
                  <Sparkles
                    className={`h-5 w-5 ${
                      aiStatus?.available
                        ? 'text-green-400'
                        : 'text-secondary-400'
                    }`}
                  />
                </div>
                <div>
                  <h3 className="font-medium">AI Analysis</h3>
                  <p className="text-sm text-secondary-400">
                    {aiStatus?.available
                      ? `Using ${aiStatus.models[0]}`
                      : 'Not configured'}
                  </p>
                </div>
                <div
                  className={`ml-auto px-2 py-1 rounded text-xs ${
                    aiStatus?.available
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-secondary-700 text-secondary-400'
                  }`}
                >
                  {aiStatus?.available ? 'Active' : 'Inactive'}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Notifications Status */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div
                  className={`p-2 rounded-full ${
                    notificationStatus?.available
                      ? 'bg-green-500/10'
                      : 'bg-secondary-700'
                  }`}
                >
                  <Bell
                    className={`h-5 w-5 ${
                      notificationStatus?.available
                        ? 'text-green-400'
                        : 'text-secondary-400'
                    }`}
                  />
                </div>
                <div>
                  <h3 className="font-medium">Notifications</h3>
                  <p className="text-sm text-secondary-400">
                    {notificationStatus?.available
                      ? `Via ${notificationStatus.channels.join(', ')}`
                      : 'Not configured'}
                  </p>
                </div>
                <div
                  className={`ml-auto px-2 py-1 rounded text-xs ${
                    notificationStatus?.available
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-secondary-700 text-secondary-400'
                  }`}
                >
                  {notificationStatus?.available ? 'Active' : 'Inactive'}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Profile Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
            <CardDescription>Manage your account information</CardDescription>
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
            <Button onClick={handleSaveProfile} disabled={saving}>
              {saving ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Save Changes
            </Button>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>
              Configure how you receive alerts for errors and security events
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {settingsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
              </div>
            ) : (
              <>
                {/* Notification Email */}
                <div className="space-y-2">
                  <Label htmlFor="notification-email">
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4" />
                      Notification Email
                    </div>
                  </Label>
                  <Input
                    id="notification-email"
                    type="email"
                    placeholder="alerts@yourcompany.com"
                    value={notificationEmail}
                    onChange={(e) => setNotificationEmail(e.target.value)}
                  />
                  <p className="text-xs text-secondary-500">
                    Receive error alerts at this email (can be different from
                    your account email)
                  </p>
                </div>

                {/* Telegram Chat ID */}
                <div className="space-y-2">
                  <Label htmlFor="telegram-chat-id">
                    <div className="flex items-center gap-2">
                      <MessageCircle className="h-4 w-4" />
                      Telegram Chat ID
                    </div>
                  </Label>
                  <Input
                    id="telegram-chat-id"
                    placeholder="123456789"
                    value={telegramChatId}
                    onChange={(e) => setTelegramChatId(e.target.value)}
                  />
                  <p className="text-xs text-secondary-500">
                    Get instant alerts via Telegram. Message @CodeWardenBot to
                    get your chat ID.
                  </p>
                </div>

                <hr className="border-secondary-700" />

                {/* Toggle Options */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Critical Error Alerts</p>
                      <p className="text-sm text-secondary-400">
                        Immediate notification for critical and high severity
                        errors
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={settings?.notify_on_critical ?? true}
                        onChange={() => toggleSetting('notify_on_critical')}
                      />
                      <div className="w-11 h-6 bg-secondary-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Warning Alerts</p>
                      <p className="text-sm text-secondary-400">
                        Get notified about warnings and potential issues
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={settings?.notify_on_warning ?? true}
                        onChange={() => toggleSetting('notify_on_warning')}
                      />
                      <div className="w-11 h-6 bg-secondary-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Weekly Digest</p>
                      <p className="text-sm text-secondary-400">
                        Receive a weekly summary of events and metrics
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={settings?.weekly_digest ?? true}
                        onChange={() => toggleSetting('weekly_digest')}
                      />
                      <div className="w-11 h-6 bg-secondary-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>
                </div>

                <div className="flex items-center gap-4 pt-4">
                  <Button
                    onClick={handleSaveNotifications}
                    disabled={settingsSaving}
                  >
                    {settingsSaving ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4 mr-2" />
                    )}
                    Save Notification Settings
                  </Button>
                  {settingsSuccess && (
                    <div className="flex items-center gap-2 text-green-400">
                      <CheckCircle className="h-4 w-4" />
                      <span className="text-sm">Saved!</span>
                    </div>
                  )}
                  {settingsError && (
                    <p className="text-sm text-red-400">{settingsError}</p>
                  )}
                </div>
              </>
            )}
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
