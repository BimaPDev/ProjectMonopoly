"use client";

import {
  BarChart3,
  Radio, ChevronUp, ChevronDown, Heart, Share, Pencil,
} from "lucide-react";
import CompetitorAddForm from "@/components/competitorAddForm.tsx"
import CompetitorEditModal from "@/components/CompetitorEditModal"

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { Progress } from "@/components/ui/progress";

import { useEffect, useState } from "react";

import { CgComment } from "react-icons/cg";
import { socialPlatforms } from "@/components/socialPlatforms";

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

interface Competitors {
  id: string,
  display_name: string,
  last_checked: string | null,
  total_posts: number | 0,
  profiles: Profile[],
  // Legacy fields for backwards compatibility
  platform?: string,
  username?: string,
  profile_url?: string,
  followers?: number | 0,
  engagement_rate?: number | 0,
  growth_rate?: number | 0,
  posting_frequency?: number | 0,
}
interface CompetitorPost {
  id: number;
  competitor_id: string;
  platform: string;
  post_id: string;
  content: string | null;
  media: any;
  posted_at: string | null;
  engagement: {
    likes: number;
    shares?: number;
    comments: number;
  } | null;
  hashtags: string[];
}


function formatNumber(num: number): string {
  if (num >= 1000000000) {
    return (num / 1000000000).toFixed(1) + "B";
  }
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M";
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + "K";
  }
  return num.toString();
}



export function CompetitorsPage() {
  const [competitorsPost, setCompetitorsPosts] = useState<CompetitorPost[]>([]);
  const [competitors, setCompetitors] = useState<Competitors[]>([]);
  const [expandedCompetitors, setExpandedCompetitors] = useState<Set<string>>(new Set());
  const [editingCompetitor, setEditingCompetitor] = useState<Competitors | null>(null);

  const toggleCompetitorPosts = (competitorId: string) => {
    setExpandedCompetitors(prev => {
      const newSet = new Set(prev);
      if (newSet.has(competitorId)) {
        newSet.delete(competitorId);
      } else {
        newSet.add(competitorId);
      }
      return newSet;
    });
  };

  

  const fetchCompetitorsPosts = async () => {
    try {
      const res = await fetch(`/api/competitors/posts?group_id=${activeGroup?.ID}`, {
        method: "GET",
        headers: { 'Content-Type': "application/json", 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      const data = await res.json();

      const normalized: CompetitorPost[] = data.map((post: any) => ({
        id: post.id,
        competitor_id: post.competitor_id,
        platform: post.platform,
        content: post.content.Valid ? post.content.String : null,
        media: post.media,
        posted_at: post.posted_at.Valid ? post.posted_at.Time : null,
        engagement: post.engagement,
        hashtags: post.hashtags,

      }));

      setCompetitorsPosts(normalized);

    } catch (e: any) {
      throw new Error(e || "error getting posts");
    }
  }

  const fetchCompetitors = async () => {
    try {
      // Try new API first, fallback to legacy
      let res = await fetch(`/api/competitors/with-profiles`, {
        method: "GET",
        headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${localStorage.getItem('token')}` }
      });

      if (res.ok) {
        const data = await res.json();
        const normalized: Competitors[] = (data || []).map((competitor: any) => ({
          id: competitor.id,
          display_name: competitor.display_name || competitor.username || 'Unknown',
          last_checked: competitor.last_checked?.Valid ? new Date(competitor.last_checked.Time).toLocaleDateString() : null,
          total_posts: competitor.total_posts?.Valid ? Number(competitor.total_posts.Int64) : 0,
          profiles: competitor.profiles || [],
        }));
        setCompetitors(normalized);
      } else {
        // Fallback to legacy endpoint
        res = await fetch(`/api/groups/competitors`, {
          method: "GET",
          headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await res.json();
        const normalized: Competitors[] = (data || []).map((competitor: any) => ({
          id: competitor.id,
          display_name: competitor.username,
          last_checked: competitor.last_checked?.Valid ? new Date(competitor.last_checked.Time).toLocaleDateString() : null,
          total_posts: 0,
          profiles: [{
            id: competitor.id,
            platform: competitor.platform,
            handle: competitor.username,
            profile_url: competitor.profile_url,
            followers: competitor.followers?.Valid ? Number(competitor.followers.Int64) : 0,
            engagement_rate: competitor.engagement_rate?.Valid ? parseFloat(competitor.engagement_rate.String) : 0,
            growth_rate: competitor.growth_rate?.Valid ? parseFloat(competitor.growth_rate.String) : 0,
            posting_frequency: competitor.posting_frequency?.Valid ? parseFloat(competitor.posting_frequency.String) : 0,
            last_checked: competitor.last_checked?.Valid ? new Date(competitor.last_checked.Time).toLocaleDateString() : null,
          }],
        }));
        setCompetitors(normalized);
      }
    } catch (e: any) {
      console.error("Could not fetch competitors:", e);
    }
  }
  useEffect(() => {
    if (activeGroup?.ID) {
      fetchCompetitors();
      fetchCompetitorsPosts();
    }
  }, [activeGroup]);

  if (!activeGroup) {
    return (
      <div className="flex justify-center w-full h-[45px] text-center">
        <div className="flex gap-2 p-2 border border-red-500 border-dashed">
          <div className=" w-[30px] h-[30px] flex justify-center items-center rounded-lg">

            <TriangleAlert className="text-yellow-400"></TriangleAlert>
          </div>
          <h1 className="font-semibold">Please select a group to continue </h1>
        </div>
      </div>
    );
  }

  return (

    <div className="flex-1 pt-6 space-y-4">
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">Competitors</h2>
        <div className="flex items-center space-x-2">
          <div className={'mr-2'}>
            <CompetitorAddForm />
          </div>
          <Button variant="outline" className="gap-2" asChild>
            <a href="/competitors/live">
              <Radio className="w-4 h-4 text-red-500 animate-pulse" />
              Live Feed
            </a>
          </Button>

        </div>
      </div>

      <div className="mt-4">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium">
                Tracked Competitors
              </CardTitle>
              <BarChart3 className="w-4 h-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{competitors.length}</div>
              <p className="text-xs text-muted-foreground">in your industry</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium">
                Avg. Engagement Rate
              </CardTitle>
              <BarChart3 className="w-4 h-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(() => {
                  const allProfiles = competitors.flatMap(c => c.profiles || []);
                  if (allProfiles.length === 0) return "0.00";
                  const avg = allProfiles.reduce((acc, p) => acc + (p.engagement_rate || 0), 0) / allProfiles.length;
                  return avg.toFixed(2);
                })()}%
              </div>
              <p className="text-xs text-muted-foreground">
                Average across all competitors
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium">
                Audience Growth Rate
              </CardTitle>
              <BarChart3 className="w-4 h-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(() => {
                  const allProfiles = competitors.flatMap(c => c.profiles || []);
                  if (allProfiles.length === 0) return "0.00";
                  const avg = allProfiles.reduce((acc, p) => acc + (p.growth_rate || 0), 0) / allProfiles.length;
                  return avg.toFixed(2);
                })()}%
              </div>
              <p className="text-xs text-muted-foreground">growth over time</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium">
                Posting Frequency
              </CardTitle>
              <BarChart3 className="w-4 h-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(() => {
                  const allProfiles = competitors.flatMap(c => c.profiles || []);
                  if (allProfiles.length === 0) return "0.0";
                  const avg = allProfiles.reduce((acc, p) => acc + (p.posting_frequency || 0), 0) / allProfiles.length;
                  return avg.toFixed(1);
                })()}
              </div>
              <p className="text-xs text-muted-foreground">posts / week</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid">
          <Card>
            <CardHeader>
              <CardTitle>Competitor Analysis</CardTitle>
              <CardDescription>
                Track and compare your competitors' social media performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mt-4 space-y-6">
                {competitors.map((competitor) => {
                  const posts = competitorsPost.filter(p => p.competitor_id === competitor.id);
                  const isExpanded = expandedCompetitors.has(competitor.id);
                  // Calculate totals from profiles
                  const totalFollowers = competitor.profiles?.reduce((acc, p) => acc + (p.followers || 0), 0) || 0;
                  const avgEngagement = competitor.profiles?.length
                    ? competitor.profiles.reduce((acc, p) => acc + (p.engagement_rate || 0), 0) / competitor.profiles.length
                    : 0;
                  const isScraping = !competitor.last_checked || totalFollowers === 0;

                  return (
                    <div key={competitor.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center flex-1 gap-4">
                          <div className="flex items-center w-[200px]">
                            <Avatar className="h-9 w-9">
                              <AvatarFallback>
                                {(competitor.display_name || 'UN').slice(0, 2).toUpperCase()}
                              </AvatarFallback>
                            </Avatar>
                            <div className="flex flex-col ml-4">
                              <p className="font-semibold text-medium">{competitor.display_name}</p>
                              <span className="text-xs text-slate-600">
                                {isScraping ? "Processing..." : competitor.last_checked}
                              </span>
                              <span className="text-xs text-blue-500">
                                {competitor.profiles?.length || 0} platform(s)
                              </span>
                            </div>
                          </div>

                          {isScraping ? (
                            <div className="flex items-center justify-center flex-1">
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 animate-pulse">
                                Scraping...
                              </span>
                            </div>
                          ) : (
                            <>
                              <div className="flex ml-4 w-[100px] justify-center">
                                <div className="flex flex-col items-center">
                                  <span className="text-sm font-medium">
                                    {formatNumber(totalFollowers)}
                                  </span>
                                  <span className="text-xs text-muted-foreground">Total Followers</span>
                                </div>
                              </div>

                              <div className="flex w-full sm:w-[160px] sm:ml-5 items-center gap-4">
                                <div className="w-full">
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium">Avg Engagement</span>
                                    <span className="text-sm text-muted-foreground">
                                      {avgEngagement.toFixed(1)}%
                                    </span>
                                  </div>
                                  <Progress value={avgEngagement * 10} className="h-2" />
                                </div>
                              </div>
                            </>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setEditingCompetitor(competitor)}
                            className="flex items-center gap-2"
                          >
                            <Pencil className="w-4 h-4" />
                            Edit
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleCompetitorPosts(competitor.id)}
                            className="flex items-center gap-2"
                          >
                            {isExpanded ? (
                              <>
                                <ChevronUp className="w-4 h-4" />
                                Hide
                              </>
                            ) : (
                              <>
                                <ChevronDown className="w-4 h-4" />
                                Show More
                              </>
                            )}
                          </Button>
                        </div>
                      </div>

                      {isExpanded && (
                        <div className="pt-6 mt-6 border-t">
                          <h4 className="mb-4 text-sm font-medium text-neutral-400">Platform Stats</h4>
                          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                            {(competitor.profiles || []).map((profile) => {
                              const platform = socialPlatforms.find(p => p.id.toLowerCase() === profile.platform.toLowerCase());
                              const Icon = platform?.icon;
                              return (
                                <div key={profile.id} className="flex items-center gap-4 p-4 rounded-lg bg-neutral-800/50">
                                  <div className={`p-2 rounded-lg ${platform?.color || 'bg-gray-600'}`}>
                                    {Icon && <Icon className="w-5 h-5 text-white" />}
                                  </div>
                                  <div className="flex-1">
                                    <p className="font-medium text-white">{profile.handle}</p>
                                    <p className="text-xs capitalize text-neutral-400">{profile.platform}</p>
                                  </div>
                                  <div className="text-right">
                                    <p className="font-semibold text-white">{formatNumber(profile.followers || 0)}</p>
                                    <p className="text-xs text-neutral-400">followers</p>
                                  </div>
                                  <div className="text-right">
                                    <p className="font-semibold text-green-400">{(profile.engagement_rate || 0).toFixed(1)}%</p>
                                    <p className="text-xs text-neutral-400">engagement</p>
                                  </div>
                                </div>
                              );
                            })}
                            {(!competitor.profiles || competitor.profiles.length === 0) && (
                              <div className="py-8 text-center col-span-full">
                                <span className="text-neutral-400">No platforms connected. Click Edit to add platforms.</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Edit Modal */}
      {editingCompetitor && (
        <CompetitorEditModal
          isOpen={!!editingCompetitor}
          onClose={() => setEditingCompetitor(null)}
          competitorId={editingCompetitor.id}
          competitorName={editingCompetitor.display_name}
          existingProfiles={editingCompetitor.profiles || []}
          onSave={() => fetchCompetitors()}
        />
      )}
    </div >
  );
}