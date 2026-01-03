"use client";

import * as React from "react";
import { useEffect, useState, useMemo } from "react";
import {
  TrendingUpIcon,
  TrendingDownIcon,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

import {
  EyeClosed,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";

import { useGroup } from './groupContext.tsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AddCompetitorModal } from "@/components/AddCompetitorModal";

// Recharts imports
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Profile {
  id: string;
  platform: string;
  handle: string;
  profile_url: string;
  followers: number;
  engagement_rate: number;
  growth_rate: number;
  posting_frequency: number;
  last_checked: string | null;
}

interface Competitor {
  id: string;
  display_name: string;
  last_checked: string | null;
  total_posts: number;
  profiles: Profile[];
}

interface Campaign {
  id: string;
  user_id: number;
  group_id: number | null;
  name: string;
  goal: string;
  audience: any;
  pillars: string[];
  cadence: {
    platforms: string[];
    posts_per_week: number;
    preferred_days: string[];
    time_windows: string[];
  };
  status: 'draft' | 'active' | 'paused' | 'completed';
  created_at: string;
  updated_at: string;
}

function formatNumber(num: number): string {
  if (num >= 1000000000) return (num / 1000000000).toFixed(1) + "B";
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toLocaleString();
}

interface TrendDataPoint {
  date: string;
  post_count: number;
  total_likes: number;
  total_comments: number;
  avg_engagement: number;
}

interface GroupItem {
  id: number;
  group_id: number;
  platform: string;
  data: {
    username?: string;
    followers?: number;
    following?: number;
    posts?: number;
    engagement_rate?: number;
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export function Dashboard() {
  const { activeGroup } = useGroup();
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [chartData, setChartData] = useState<TrendDataPoint[]>([]);
  const [groupItems, setGroupItems] = useState<GroupItem[]>([]);
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '3m'>('7d');
  const [activeTab, setActiveTab] = useState<'competitors' | 'campaigns'>('competitors');
  const [isAddCompetitorOpen, setIsAddCompetitorOpen] = useState(false);

  // Fetch engagement trends from API
  async function fetchEngagementTrends() {
    if (!activeGroup?.ID) return;
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
    try {
      const res = await fetch(`/api/analytics/engagement-trends?group_id=${activeGroup.ID}&days=${days}`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      });
      if (res.ok) {
        const data = await res.json();
        setChartData(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error("Failed to fetch engagement trends:", err);
    }
  }

  // Refetch when time range changes
  useEffect(() => {
    fetchEngagementTrends();
  }, [activeGroup, timeRange]);

  // Competitor metrics
  const competitorMetrics = useMemo(() => {
    const allProfiles = competitors.flatMap(c => c.profiles || []);
    const totalFollowers = allProfiles.reduce((acc, p) => acc + (p.followers || 0), 0);
    const avgEngagement = allProfiles.length > 0
      ? allProfiles.reduce((acc, p) => acc + (p.engagement_rate || 0), 0) / allProfiles.length
      : 0;
    const avgGrowthRate = allProfiles.length > 0
      ? allProfiles.reduce((acc, p) => acc + (p.growth_rate || 0), 0) / allProfiles.length
      : 0;
    const avgPostingFreq = allProfiles.length > 0
      ? allProfiles.reduce((acc, p) => acc + (p.posting_frequency || 0), 0) / allProfiles.length
      : 0;

    return {
      totalCompetitors: competitors.length,
      totalFollowers,
      avgEngagement,
      avgGrowthRate,
      avgPostingFreq,
      totalPlatforms: allProfiles.length,
    };
  }, [competitors]);

  // Campaign metrics
  const campaignMetrics = useMemo(() => {
    const total = campaigns.length;
    const active = campaigns.filter(c => c.status === 'active').length;
    const completed = campaigns.filter(c => c.status === 'completed').length;
    const successRate = total > 0 ? ((completed / total) * 100) : 0;
    return { total, active, completed, successRate };
  }, [campaigns]);

  // Fetch competitors
  async function fetchCompetitors() {
    if (!activeGroup?.ID) return;
    try {
      const res = await fetch(`/api/competitors/with-profiles?group_id=${activeGroup.ID}`, {
        method: "GET",
        headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${localStorage.getItem('token')}` }
      });
      if (res.ok) {
        const data = await res.json();
        const normalized: Competitor[] = (data || []).map((competitor: any) => ({
          id: competitor.id,
          display_name: competitor.display_name || 'Unknown',
          last_checked: competitor.last_checked ? new Date(competitor.last_checked).toLocaleDateString() : null,
          total_posts: competitor.total_posts || 0,
          profiles: (competitor.profiles || []).map((p: any) => ({
            id: p.id,
            platform: p.platform,
            handle: p.handle,
            profile_url: p.profile_url,
            followers: p.followers || 0,
            engagement_rate: p.engagement_rate || 0,
            growth_rate: p.growth_rate || 0,
            posting_frequency: p.posting_frequency || 0,
            last_checked: p.last_checked ? new Date(p.last_checked).toLocaleDateString() : null,
          })),
        }));
        setCompetitors(normalized);
      }
    } catch (e) {
      console.error("Could not fetch competitors:", e);
    }
  }

  // Fetch campaigns from actual campaigns API
  async function fetchCampaigns() {
    if (!activeGroup?.ID) return;
    try {
      const res = await fetch(`/api/campaigns?group_id=${activeGroup.ID}`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      });
      if (res.ok) {
        const data = await res.json();
        const dataArray = Array.isArray(data) ? data : (data ? [data] : []);
        const transformed: Campaign[] = dataArray.map((item: any) => ({
          id: item.id,
          user_id: item.user_id,
          group_id: item.group_id,
          name: item.name || 'Untitled Campaign',
          goal: item.goal || '',
          audience: item.audience || {},
          pillars: Array.isArray(item.pillars) ? item.pillars : (item.pillars ? JSON.parse(item.pillars) : []),
          cadence: item.cadence || { platforms: [], posts_per_week: 0, preferred_days: [], time_windows: [] },
          status: item.status || 'draft',
          created_at: item.created_at || new Date().toISOString(),
          updated_at: item.updated_at || new Date().toISOString(),
        }));
        setCampaigns(transformed);
      }
    } catch (err) {
      console.error("Fetch campaigns error:", err);
    }
  }

  // Fetch user's group social media platforms
  async function fetchGroupItems() {
    if (!activeGroup?.ID) return;
    try {
      const res = await fetch(`/api/GroupItem?groupID=${activeGroup.ID}`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      });
      if (res.ok) {
        const data = await res.json();
        const items = Array.isArray(data) ? data : [];
        setGroupItems(items);
      }
    } catch (err) {
      console.error("Failed to fetch group items:", err);
    }
  }

  useEffect(() => {
    if (activeGroup?.ID) {
      fetchCompetitors();
      fetchCampaigns();
      fetchGroupItems();
    }
  }, [activeGroup]);

  // Handle row selection
  const toggleRow = (id: string) => {
    setSelectedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const toggleAllRows = () => {
    if (selectedRows.size === competitors.length) {
      setSelectedRows(new Set());
    } else {
      setSelectedRows(new Set(competitors.map(c => c.id)));
    }
  };

  const toggleExpanded = (id: string) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  // Compute user's social media totals from group items
  const userSocialStats = useMemo(() => {
    const totalFollowers = groupItems.reduce((acc, item) => acc + (item.data?.followers || 0), 0);
    const platforms = groupItems.map(item => item.platform);
    const lastUpdated = groupItems.length > 0
      ? new Date(Math.max(...groupItems.map(item => new Date(item.updated_at).getTime()))).toLocaleDateString()
      : null;
    return { totalFollowers, platforms, lastUpdated, count: groupItems.length };
  }, [groupItems]);

  // No active group state - must be AFTER all hooks
  if (!activeGroup) {
    return (
      <div className="flex items-center justify-center h-[400px]">
        <Card className="p-8 text-center bg-card border-border">
          <EyeClosed className="w-16 h-16 mx-auto mb-4 text-amber-500" />
          <h3 className="mb-2 text-xl font-semibold">No Group Selected</h3>
          <p className="text-muted-foreground">Please select a group from the sidebar to view your dashboard.</p>
        </Card>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/30">● Active</Badge>;
      case 'completed':
        return <Badge className="text-blue-400 bg-blue-500/20 border-blue-500/30 hover:bg-blue-500/30">● Done</Badge>;
      case 'draft':
        return <Badge className="bg-zinc-500/20 text-zinc-400 border-zinc-500/30 hover:bg-zinc-500/30">● Draft</Badge>;
      case 'paused':
        return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 hover:bg-amber-500/30">● Paused</Badge>;
      case 'pending':
        return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 hover:bg-amber-500/30">● Pending</Badge>;
      case 'failed':
        return <Badge className="text-red-400 bg-red-500/20 border-red-500/30 hover:bg-red-500/30">● Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="min-h-screen text-foreground bg-background">
      <div className="w-full px-4 py-6 mx-auto">
        {/* Stats Cards Row */}
        <div className="grid gap-4 mb-6 md:grid-cols-2 lg:grid-cols-4">
          {/* Your Social Media */}
          <Card className="relative overflow-hidden bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-zinc-400">Your Social Media</span>
                {userSocialStats.count > 0 && (
                  <Badge variant="outline" className="text-xs text-blue-400 border-blue-500/30 bg-blue-500/10">
                    {userSocialStats.count} platform{userSocialStats.count > 1 ? 's' : ''}
                  </Badge>
                )}
              </div>
              <div className="text-3xl font-bold text-white">{formatNumber(userSocialStats.totalFollowers)}</div>
              <div className="flex flex-wrap gap-1 mt-2">
                {userSocialStats.platforms.map(p => (
                  <Badge key={p} variant="outline" className="text-xs capitalize">{p}</Badge>
                ))}
              </div>
              <p className="mt-1 text-xs text-zinc-500">
                {userSocialStats.lastUpdated ? `Last updated: ${userSocialStats.lastUpdated}` : 'No platforms connected'}
              </p>
            </CardContent>
          </Card>

          {/* Total Followers */}
          <Card className="relative overflow-hidden bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-zinc-400">Total Reach</span>
                <Badge variant="outline" className="text-xs text-rose-400 border-rose-500/30 bg-rose-500/10">
                  <TrendingDownIcon className="w-3 h-3 mr-1" />
                  -2%
                </Badge>
              </div>
              <div className="text-3xl font-bold text-white">{formatNumber(competitorMetrics.totalFollowers)}</div>
              <div className="flex items-center gap-1 mt-2 text-xs">
                <span className="text-rose-400">Down 2% this period</span>
                <TrendingDownIcon className="w-3 h-3 text-rose-400" />
              </div>
              <p className="mt-1 text-xs text-zinc-500">Combined competitor audience</p>
            </CardContent>
          </Card>

          {/* Avg Engagement */}
          <Card className="relative overflow-hidden bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-zinc-400">Avg. Engagement</span>
                <Badge variant="outline" className="text-xs text-emerald-400 border-emerald-500/30 bg-emerald-500/10">
                  <TrendingUpIcon className="w-3 h-3 mr-1" />
                  +8.2%
                </Badge>
              </div>
              <div className="text-3xl font-bold text-white">{competitorMetrics.avgEngagement.toFixed(1)}%</div>
              <div className="flex items-center gap-1 mt-2 text-xs">
                <span className="text-emerald-400">Strong performance</span>
                <TrendingUpIcon className="w-3 h-3 text-emerald-400" />
              </div>
              <p className="mt-1 text-xs text-zinc-500">Engagement exceeds average</p>
            </CardContent>
          </Card>

          {/* Growth Rate */}
          <Card className="relative overflow-hidden bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-zinc-400">Growth Rate</span>
                <Badge variant="outline" className="text-xs text-emerald-400 border-emerald-500/30 bg-emerald-500/10">
                  <TrendingUpIcon className="w-3 h-3 mr-1" />
                  +4.5%
                </Badge>
              </div>
              <div className="text-3xl font-bold text-white">{competitorMetrics.avgGrowthRate.toFixed(1)}%</div>
              <div className="flex items-center gap-1 mt-2 text-xs">
                <span className="text-emerald-400">Steady performance increase</span>
                <TrendingUpIcon className="w-3 h-3 text-emerald-400" />
              </div>
              <p className="mt-1 text-xs text-zinc-500">Meets growth projections</p>
            </CardContent>
          </Card>
        </div>

        {/* Chart Section */}
        <Card className="mb-6 bg-zinc-900/50 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-lg font-semibold text-white">Competitor Activity</CardTitle>
              <CardDescription className="text-zinc-400">Daily likes & engagement from competitor posts</CardDescription>
            </div>
            <div className="flex gap-1 p-1 rounded-lg bg-zinc-800">
              <Button
                variant={timeRange === '3m' ? 'secondary' : 'ghost'}
                size="sm"
                className={timeRange === '3m' ? 'bg-zinc-700' : 'text-zinc-400 hover:text-white'}
                onClick={() => setTimeRange('3m')}
              >
                Last 3 months
              </Button>
              <Button
                variant={timeRange === '30d' ? 'secondary' : 'ghost'}
                size="sm"
                className={timeRange === '30d' ? 'bg-zinc-700' : 'text-zinc-400 hover:text-white'}
                onClick={() => setTimeRange('30d')}
              >
                Last 30 days
              </Button>
              <Button
                variant={timeRange === '7d' ? 'secondary' : 'ghost'}
                size="sm"
                className={timeRange === '7d' ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-white'}
                onClick={() => setTimeRange('7d')}
              >
                Last 7 days
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorFollowers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorEngagement" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke="#71717a"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="#71717a"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(val) => formatNumber(val)}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#18181b',
                    border: '1px solid #27272a',
                    borderRadius: '8px',
                    boxShadow: '0 10px 40px rgba(0,0,0,0.5)',
                  }}
                  labelStyle={{ color: '#a1a1aa' }}
                />
                <Area
                  type="monotone"
                  dataKey="total_likes"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorFollowers)"
                  name="Likes"
                />
                <Area
                  type="monotone"
                  dataKey="avg_engagement"
                  stroke="#22c55e"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorEngagement)"
                  name="Avg Engagement"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Data Table Section */}
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <Tabs value={activeTab} className="w-full" onValueChange={(value) => setActiveTab(value as 'competitors' | 'campaigns')}>
                <div className="flex items-center justify-between mb-4">
                  <TabsList className="p-1 bg-zinc-800">
                    <TabsTrigger value="competitors" className="data-[state=active]:bg-zinc-700">
                      Competitors
                    </TabsTrigger>
                    <TabsTrigger value="campaigns" className="data-[state=active]:bg-zinc-700">
                      Campaigns <Badge variant="outline" className="ml-1 text-xs">{campaignMetrics.total}</Badge>
                    </TabsTrigger>
                  </TabsList>
                  {activeTab === 'campaigns' ? (
                    <a href="dashboard/campaigns">
                      <Button size="sm" className="gap-1">
                        <Plus className="w-4 h-4" />
                        Add Campaign
                      </Button>
                    </a>
                  ) : (
                    <Button size="sm" className="gap-1" onClick={() => setIsAddCompetitorOpen(true)}>
                      <Plus className="w-4 h-4" />
                      Add Competitor
                    </Button>
                  )}
                </div>

                {/* Competitors Tab */}
                <TabsContent value="competitors" className="mt-0">
                  <div className="border rounded-lg border-zinc-800">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-zinc-800 hover:bg-zinc-800/50">
                          <TableHead className="w-8"></TableHead>
                          <TableHead className="w-12">
                            <Checkbox
                              checked={selectedRows.size === competitors.length && competitors.length > 0}
                              onCheckedChange={toggleAllRows}
                            />
                          </TableHead>
                          <TableHead className="text-zinc-400">Competitor</TableHead>
                          <TableHead className="text-zinc-400">Platforms</TableHead>
                          <TableHead className="text-zinc-400">Status</TableHead>
                          <TableHead className="text-right text-zinc-400">Total Followers</TableHead>
                          <TableHead className="text-right text-zinc-400">Avg. Engagement</TableHead>
                          <TableHead className="text-zinc-400">Last Updated</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {competitors.length > 0 ? (
                          competitors.map((competitor) => {
                            const totalFollowers = competitor.profiles?.reduce((acc, p) => acc + (p.followers || 0), 0) || 0;
                            const avgEngagement = competitor.profiles?.length
                              ? competitor.profiles.reduce((acc, p) => acc + (p.engagement_rate || 0), 0) / competitor.profiles.length
                              : 0;
                            const platformCount = competitor.profiles?.length || 0;
                            const hasData = totalFollowers > 0;
                            const isExpanded = expandedRows.has(competitor.id);

                            return (
                              <React.Fragment key={competitor.id}>
                                <TableRow
                                  className="cursor-pointer border-zinc-800 hover:bg-zinc-800/50"
                                  onClick={() => toggleExpanded(competitor.id)}
                                >
                                  <TableCell className="w-8">
                                    {platformCount > 0 && (
                                      isExpanded ?
                                        <ChevronDown className="w-4 h-4 text-zinc-400" /> :
                                        <ChevronRight className="w-4 h-4 text-zinc-400" />
                                    )}
                                  </TableCell>
                                  <TableCell onClick={(e) => e.stopPropagation()}>
                                    <Checkbox
                                      checked={selectedRows.has(competitor.id)}
                                      onCheckedChange={() => toggleRow(competitor.id)}
                                    />
                                  </TableCell>
                                  <TableCell>
                                    <span className="font-medium text-blue-400 hover:underline">
                                      {competitor.display_name}
                                    </span>
                                  </TableCell>
                                  <TableCell>
                                    <div className="flex flex-wrap gap-1">
                                      {competitor.profiles?.map(p => (
                                        <Badge key={p.id} variant="outline" className="text-xs capitalize">
                                          {p.platform}
                                        </Badge>
                                      ))}
                                      {platformCount === 0 && <span className="text-zinc-500">-</span>}
                                    </div>
                                  </TableCell>
                                  <TableCell>
                                    {hasData ? (
                                      <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">● Active</Badge>
                                    ) : (
                                      <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30">● Processing</Badge>
                                    )}
                                  </TableCell>
                                  <TableCell className="font-medium text-right">
                                    {formatNumber(totalFollowers)}
                                  </TableCell>
                                  <TableCell className="text-right">
                                    <span className="text-emerald-400">{avgEngagement.toFixed(1)}%</span>
                                  </TableCell>
                                  <TableCell className="text-zinc-400">
                                    {competitor.last_checked || 'Never'}
                                  </TableCell>
                                </TableRow>
                                {/* Expanded Platform Details */}
                                {isExpanded && competitor.profiles?.map(profile => (
                                  <TableRow
                                    key={`${competitor.id}-${profile.id}`}
                                    className="bg-zinc-800/30 border-zinc-800"
                                  >
                                    <TableCell></TableCell>
                                    <TableCell></TableCell>
                                    <TableCell>
                                      <div className="flex items-center gap-2 pl-4">
                                        <div className="w-1.5 h-1.5 rounded-full bg-zinc-600"></div>
                                        <Badge variant="outline" className="text-xs capitalize">
                                          {profile.platform}
                                        </Badge>
                                        <span className="text-blue-400">@{profile.handle}</span>
                                      </div>
                                    </TableCell>
                                    <TableCell>
                                      <span className="text-xs text-zinc-500">
                                        {profile.posting_frequency?.toFixed(1) || '0.0'} posts/week
                                      </span>
                                    </TableCell>
                                    <TableCell>
                                      <Badge className="text-xs text-blue-400 bg-blue-500/20 border-blue-500/30">
                                        ● Tracked
                                      </Badge>
                                    </TableCell>
                                    <TableCell className="font-medium text-right">
                                      {formatNumber(profile.followers)}
                                    </TableCell>
                                    <TableCell className="text-right">
                                      <span className="text-emerald-400">{profile.engagement_rate?.toFixed(1) || '0.0'}%</span>
                                    </TableCell>
                                    <TableCell className="text-zinc-500">
                                      {profile.last_checked || '-'}
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </React.Fragment>
                            );
                          })
                        ) : (
                          <TableRow>
                            <TableCell colSpan={8} className="h-24 text-center text-zinc-500">
                              No competitors added yet. Add your first competitor to start tracking.
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </div>
                  <div className="flex items-center justify-between px-2 py-3 text-sm text-zinc-400">
                    <span>{selectedRows.size} of {competitors.length} row(s) selected.</span>
                    <div className="flex items-center gap-4">
                      <span>Rows per page: 10</span>
                      <span>Page 1 of 1</span>
                    </div>
                  </div>
                </TabsContent>

                {/* Campaigns Tab */}
                <TabsContent value="campaigns" className="mt-0">
                  <div className="border rounded-lg border-zinc-800">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-zinc-800 hover:bg-zinc-800/50">
                          <TableHead className="w-12">
                            <Checkbox />
                          </TableHead>
                          <TableHead className="text-zinc-400">Campaign</TableHead>
                          <TableHead className="text-zinc-400">Goal</TableHead>
                          <TableHead className="text-zinc-400">Platforms</TableHead>
                          <TableHead className="text-zinc-400">Posts/Week</TableHead>
                          <TableHead className="text-zinc-400">Status</TableHead>
                          <TableHead className="text-zinc-400">Created</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {campaigns.length > 0 ? (
                          campaigns.map((campaign) => (
                            <TableRow key={campaign.id} className="border-zinc-800 hover:bg-zinc-800/50">
                              <TableCell>
                                <Checkbox />
                              </TableCell>
                              <TableCell>
                                <span className="font-medium text-blue-400">{campaign.name}</span>
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline" className="text-xs capitalize">{campaign.goal}</Badge>
                              </TableCell>
                              <TableCell>
                                <div className="flex flex-wrap gap-1">
                                  {(campaign.cadence?.platforms || []).map((p: string) => (
                                    <Badge key={p} variant="outline" className="text-xs capitalize">{p}</Badge>
                                  ))}
                                </div>
                              </TableCell>
                              <TableCell className="text-zinc-300">
                                {campaign.cadence?.posts_per_week || 0}
                              </TableCell>
                              <TableCell>{getStatusBadge(campaign.status)}</TableCell>
                              <TableCell className="text-zinc-400">
                                {new Date(campaign.created_at).toLocaleDateString()}
                              </TableCell>
                            </TableRow>
                          ))
                        ) : (
                          <TableRow>
                            <TableCell colSpan={7} className="h-24 text-center text-zinc-500">
                              No campaigns yet. Create your first campaign to get started.
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </TabsContent>


              </Tabs>
            </div>
          </CardHeader>
        </Card>
      </div>

      {/* Add Competitor Modal */}
      <AddCompetitorModal
        isOpen={isAddCompetitorOpen}
        onClose={() => setIsAddCompetitorOpen(false)}
        onSuccess={fetchCompetitors}
      />
    </div>
  );
}
