'use client'
import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import {
  User,
  Bell,
  Shield,
  Palette,
  Database,
  LogOut,
  Save,
  ChevronRight,
  Settings as SettingsIcon,
  Instagram,
  CheckCircle,
  AlertCircle,
  Moon,
  Sun,
  Monitor
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"

interface SettingsSectionProps {
  icon: React.ElementType
  title: string
  description: string
  onClick?: () => void
  showChevron?: boolean
}

const SettingsSection: React.FC<SettingsSectionProps> = ({
  icon: Icon,
  title,
  description,
  onClick,
  showChevron = true
}) => (
  <div
    onClick={onClick}
    className={`p-4 bg-gray-900 border border-gray-800 rounded-xl transition-all duration-200 ${onClick ? 'cursor-pointer hover:bg-gray-800/50 hover:border-gray-700' : ''
      }`}
  >
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="p-3 rounded-lg bg-blue-500/10">
          <Icon className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h3 className="font-medium text-white">{title}</h3>
          <p className="text-sm text-gray-400">{description}</p>
        </div>
      </div>
      {showChevron && onClick && (
        <ChevronRight className="w-5 h-5 text-gray-400" />
      )}
    </div>
  </div>
)

export default function Settings() {
  const navigate = useNavigate()
  const [user, setUser] = useState({ name: '', email: '' })
  const [notifications, setNotifications] = useState({
    emailNotifications: true,
    pushNotifications: false,
    weeklyDigest: true,
    postReminders: true
  })
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('dark')
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

  useEffect(() => {
    // Load user data from localStorage or API
    const userEmail = localStorage.getItem('email') || 'user@example.com'
    const userName = localStorage.getItem('userName') || 'User'
    setUser({ name: userName, email: userEmail })
  }, [])

  const handleSaveNotifications = () => {
    setSaveStatus('saving')
    setTimeout(() => {
      localStorage.setItem('notifications', JSON.stringify(notifications))
      setSaveStatus('saved')
      setTimeout(() => setSaveStatus('idle'), 2000)
    }, 500)
  }

  const handleLogout = () => {
    localStorage.clear()
    navigate('/login')
  }

  const getSaveButtonContent = () => {
    switch (saveStatus) {
      case 'saving':
        return (
          <>
            <div className="w-4 h-4 border-b-2 border-white rounded-full animate-spin" />
            Saving...
          </>
        )
      case 'saved':
        return (
          <>
            <CheckCircle className="w-4 h-4" />
            Saved!
          </>
        )
      case 'error':
        return (
          <>
            <AlertCircle className="w-4 h-4" />
            Error
          </>
        )
      default:
        return (
          <>
            <Save className="w-4 h-4" />
            Save Changes
          </>
        )
    }
  }

  return (
    <div className="h-[100vh] text-white ">
      <div className="container px-6 py-8 mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-3 rounded-lg bg-blue-500/10">
              <SettingsIcon className="w-6 h-6 text-blue-400" />
            </div>
            <h1 className="text-3xl font-semibold text-white">Settings</h1>
          </div>
          <p className="text-lg text-gray-400">
            Manage your account preferences and application settings
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Main Settings */}
          <div className="space-y-6 lg:col-span-2">
            {/* Quick Access Cards */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <SettingsSection
                icon={User}
                title="Account Settings"
                description="Manage your account details"
                onClick={() => { }}
                showChevron={false}
              />
              <SettingsSection
                icon={Instagram}
                title="Social Media"
                description="Connect your social accounts"
                onClick={() => navigate('/dashboard/settings/socialmedia')}
              />
            </div>

            {/* Notification Settings */}
            {/* <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-lg bg-emerald-500/10">
                    <Bell className="w-5 h-5 text-emerald-400" />
                  </div>
                  <div>
                    <CardTitle className="text-white">Notifications</CardTitle>
                    <CardDescription className="text-gray-400">
                      Configure how you receive updates
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 border border-gray-800 rounded-lg bg-gray-800/30">
                  <div className="flex-1">
                    <Label htmlFor="email-notif" className="text-white">Email Notifications</Label>
                    <p className="text-sm text-gray-400">Receive updates via email</p>
                  </div>
                  <Switch
                    id="email-notif"
                    checked={notifications.emailNotifications}
                    onCheckedChange={(checked: boolean) =>
                      setNotifications({ ...notifications, emailNotifications: checked })
                    }
                  />
                </div>

                <div className="flex items-center justify-between p-4 border border-gray-800 rounded-lg bg-gray-800/30">
                  <div className="flex-1">
                    <Label htmlFor="push-notif" className="text-white">Push Notifications</Label>
                    <p className="text-sm text-gray-400">Get browser notifications</p>
                  </div>
                  <Switch
                    id="push-notif"
                    checked={notifications.pushNotifications}
                    onCheckedChange={(checked: boolean) =>
                      setNotifications({ ...notifications, pushNotifications: checked })
                    }
                  />
                </div>

                <div className="flex items-center justify-between p-4 border border-gray-800 rounded-lg bg-gray-800/30">
                  <div className="flex-1">
                    <Label htmlFor="weekly-digest" className="text-white">Weekly Digest</Label>
                    <p className="text-sm text-gray-400">Weekly summary of your activity</p>
                  </div>
                  <Switch
                    id="weekly-digest"
                    checked={notifications.weeklyDigest}
                    onCheckedChange={(checked: boolean) =>
                      setNotifications({ ...notifications, weeklyDigest: checked })
                    }
                  />
                </div>

                <div className="flex items-center justify-between p-4 border border-gray-800 rounded-lg bg-gray-800/30">
                  <div className="flex-1">
                    <Label htmlFor="post-reminders" className="text-white">Post Reminders</Label>
                    <p className="text-sm text-gray-400">Reminders for scheduled posts</p>
                  </div>
                  <Switch
                    id="post-reminders"
                    checked={notifications.postReminders}
                    onCheckedChange={(checked: boolean) =>
                      setNotifications({ ...notifications, postReminders: checked })
                    }
                  />
                </div>

                <Button
                  onClick={handleSaveNotifications}
                  disabled={saveStatus === 'saving' || saveStatus === 'saved'}
                  className={`w-full ${saveStatus === 'saved'
                      ? 'bg-emerald-600 hover:bg-emerald-700'
                      : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                >
                  <div className="flex items-center gap-2">
                    {getSaveButtonContent()}
                  </div>
                </Button>
              </CardContent>
            </Card> */}

            {/* Appearance Settings */}
            {/* <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-lg bg-purple-500/10">
                    <Palette className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <CardTitle className="text-white">Appearance</CardTitle>
                    <CardDescription className="text-gray-400">
                      Customize how the app looks
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <button
                    onClick={() => setTheme('light')}
                    className={`p-4 border rounded-xl transition-all ${theme === 'light'
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-gray-800 bg-gray-800/30 hover:border-gray-700'
                      }`}
                  >
                    <Sun className={`w-6 h-6 mx-auto mb-2 ${theme === 'light' ? 'text-blue-400' : 'text-gray-400'
                      }`} />
                    <p className={`text-sm ${theme === 'light' ? 'text-blue-300' : 'text-gray-400'
                      }`}>Light</p>
                  </button>

                  <button
                    onClick={() => setTheme('dark')}
                    className={`p-4 border rounded-xl transition-all ${theme === 'dark'
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-gray-800 bg-gray-800/30 hover:border-gray-700'
                      }`}
                  >
                    <Moon className={`w-6 h-6 mx-auto mb-2 ${theme === 'dark' ? 'text-blue-400' : 'text-gray-400'
                      }`} />
                    <p className={`text-sm ${theme === 'dark' ? 'text-blue-300' : 'text-gray-400'
                      }`}>Dark</p>
                  </button>

                  <button
                    onClick={() => setTheme('system')}
                    className={`p-4 border rounded-xl transition-all ${theme === 'system'
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-gray-800 bg-gray-800/30 hover:border-gray-700'
                      }`}
                  >
                    <Monitor className={`w-6 h-6 mx-auto mb-2 ${theme === 'system' ? 'text-blue-400' : 'text-gray-400'
                      }`} />
                    <p className={`text-sm ${theme === 'system' ? 'text-blue-300' : 'text-gray-400'
                      }`}>System</p>
                  </button>
                </div>
              </CardContent>
            </Card> */}

            {/* More Settings */}
            {/* <div className="space-y-4">
              <SettingsSection
                icon={Shield}
                title="Privacy & Security"
                description="Manage your privacy and security settings"
                onClick={() => { }}
                showChevron={false}
              />
              <SettingsSection
                icon={Database}
                title="Data Management"
                description="Export or delete your data"
                onClick={() => { }}
                showChevron={false}
              />
            </div> */}
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  variant="outline"
                  className="w-full text-white bg-gray-800 border-gray-700 hover:bg-gray-700"
                  onClick={() => navigate('/dashboard/settings/socialmedia')}
                >
                  <Instagram className="w-4 h-4 mr-2" />
                  Manage Social Media
                </Button>
                <Button
                  variant="outline"
                  className="w-full text-white bg-gray-800 border-gray-700 hover:bg-gray-700"
                >
                  <Bell className="w-4 h-4 mr-2" />
                  Notification Center
                </Button>
                <Separator className="bg-gray-800" />
                <Button
                  variant="destructive"
                  className="w-full bg-red-600 hover:bg-red-700"
                  onClick={handleLogout}
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Log Out
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Account Info */}
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-12 h-12 text-lg font-semibold text-white bg-blue-600 rounded-full">
                    {user.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-white truncate">{user.name}</CardTitle>
                    <CardDescription className="text-gray-400 truncate">
                      {user.email}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Button
                  variant="outline"
                  className="w-full text-white bg-gray-800 border-gray-700 hover:bg-gray-700"
                >
                  Edit Profile
                </Button>
              </CardContent>
            </Card>

            {/* Quick Actions */}


            {/* Help & Support */}
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">Help & Support</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <a href="#" className="block text-blue-400 transition-colors hover:text-blue-300">
                  Documentation
                </a>
                <a href="#" className="block text-blue-400 transition-colors hover:text-blue-300">
                  Contact Support
                </a>
                <a href="#" className="block text-blue-400 transition-colors hover:text-blue-300">
                  Report a Bug
                </a>
                <Separator className="my-3 bg-gray-800" />
                <p className="text-gray-500">Version 1.0.0</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
