"use client";

import * as React from "react";
import {
  BarChart3,

  Radio, ChevronUp, ChevronDown, Heart, Share,
} from "lucide-react";
import CompetitorAddForm from "@/components/competitorAddForm.tsx"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { Progress } from "@/components/ui/progress";

import {useEffect, useState} from "react";

import {CgComment} from "react-icons/cg";

import { socialPlatforms } from "@/components/socialPlatforms";
interface Competitors{
  id: string,
  platform: string,
  username: string,
  profile_url: string,
  last_checked: Date,
  followers: number | 0,
  engagement_rate:number | 0,
  growth_rate: number | 0,
  posting_frequency: number | 0,
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
    shares: number;
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
    try{
      const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/competitors/posts`, {
        method: "GET",
        headers: {'Content-Type': "application/json", 'Authorization': `Bearer ${localStorage.getItem('token')}`}
      });

      const data = await res.json();
      console.log("DATA", data)
      const normalized: CompetitorPost[] = data.map((post: any) =>({
        id: post.id,
        competitor_id: post.competitor_id,
        platform: post.platform,
        content: post.content.Valid ? post.content.String : null,
        media: post.media.Valid? post.media.RawMessage : null,
        posted_at: post.posted_at.Valid ? post.posted_at : null,
        engagement: post.engagement.Valid ? post.engagement.RawMessage : null,
        hashtags: post.hashtags,

      }));

      setCompetitorsPosts(normalized);

    }catch (e: any){
      throw new Error(e || "Could not fetch competitors posts");
    }
  }

  const fetchCompetitors = async () =>{
    try{
      const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/groups/competitors`, {
        method: "GET",
        headers: {'Content-Type': 'application/json', "Authorization": `Bearer ${localStorage.getItem('token')}`}
      });
      const data = await res.json();

      const normalized: Competitors[] = data.map((competitor: any) => ({
        id:competitor.id,
        platform: competitor.platform,
        username: competitor.username,
        profile_url: competitor.profile_url,
        followers: competitor.followers.Valid ? competitor.followers.Int64 : 0,
        last_checked: competitor.last_checked.Valid? new Date(competitor.last_checked.Time).toLocaleDateString(): null,
        engagement_rate: competitor.engagement_rate?.Valid
            ? parseFloat(competitor.engagement_rate.String)
            : 0,

        growth_rate: competitor.growth_rate?.Valid
            ? parseFloat(competitor.growth_rate.String)
            : 0,

        posting_frequency: competitor.posting_frequency?.Valid
            ? parseFloat(competitor.posting_frequency.String)
            : 0,
      }));
      setCompetitors(normalized)

    }catch(e: any){
      throw new Error (e || "could not fetch competitors");

    }

  }
  useEffect(() => {
    fetchCompetitors();
    fetchCompetitorsPosts();
  }, []);
  return (
      <div className="flex-1 pt-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-3xl font-bold tracking-tight">Competitors</h2>
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

                <p className="text-xs text-muted-foreground">
                  Coming soon
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
                <p className="text-xs text-muted-foreground">Coming soon</p>
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

                <p className="text-xs text-muted-foreground">Coming soon</p>
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

                    return (
                        <div key={competitor.id + competitor.username} className="p-4 border rounded-lg">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center flex-1 gap-4">
                              <div className="flex items-center w-[150px]">
                                <Avatar className="h-9 w-9">
                                  <AvatarImage src={competitor.profile_url} />
                                  <AvatarFallback>
                                    {competitor.username.slice(0, 2)}
                                  </AvatarFallback>
                                </Avatar>
                                <div className="flex flex-col ml-4">
                                  <p className="font-semibold text-medium">{competitor.username}</p>
                                  <span className="text-xs text-slate-600">
                                  {new Date(competitor.last_checked).toLocaleDateString()}
                                </span>
                                </div>
                              </div>

                              <div className="flex ml-4 w-[100px] justify-center">
                                <div className="flex items-center gap-4 ml-3">
                                  <div className="flex flex-col items-center">
                                    {(() => {
                                      const platform = socialPlatforms.find(p => p.id === competitor.platform);
                                      const Icon = platform?.icon;
                                      return Icon ? (
                                          <div>
                                            <div className="flex items-center justify-center w-8 h-8 rounded-full text-muted-foreground">
                                              <Icon className="w-4 h-4"/>
                                            </div>
                                          </div>
                                      ) : <span className="text-sm"> {competitor.platform}</span>;
                                    })()}
                                    <span className="text-sm font-medium">
                                    {formatNumber(competitor.followers)}
                                  </span>
                                  </div>
                                </div>
                              </div>

                              <div className="flex w-[160px] ml-5 items-center gap-4">
                                <div className="w-full">
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium">Engagement</span>
                                    <span className="text-sm text-muted-foreground">
                                    {competitor.engagement_rate}%
                                  </span>
                                  </div>
                                  <Progress value={competitor.engagement_rate * 10} className="h-2" />
                                </div>
                              </div>

                              <div className="flex items-center justify-between ml-2">
                              <span className={
                                competitor.growth_rate > 0.0
                                    ? "text-sm font-medium text-green-600"
                                    : "text-sm font-medium text-red-600"
                              }>
                                <div className="flex items-center w-[100px]">
                                  {competitor.growth_rate > 0.0 ?
                                      <ChevronUp className="text-green-500" /> :
                                      <ChevronDown className="text-red-500"/>
                                  }
                                  {competitor.growth_rate}%
                                </div>
                              </span>
                              </div>
                            </div>

                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleCompetitorPosts(competitor.id)}
                                className="flex items-center gap-2"
                            >
                              {isExpanded ? (
                                  <>
                                    <ChevronUp className="w-4 h-4" />
                                    Hide Posts
                                  </>
                              ) : (
                                  <>
                                    <ChevronDown className="w-4 h-4" />
                                    Show Posts ({posts.length})
                                  </>
                              )}
                            </Button>
                          </div>

                          {isExpanded && (
                              <div className="pt-6 mt-6 border-t">
                                <div className="overflow-y-auto max-h-80 scrollbar-hide">
                                  <div className="space-y-4">
                                    {posts.length > 0 ? (
                                        posts.map((post) => (
                                            <div key={post.id} className="flex flex-col items-start gap-4 p-4 border rounded-lg ">
                                              <div className="flex w-full gap-4">
                                                {post.media?.video ? (
                                                    <video
                                                        src={post.media.video}
                                                        className="object-cover w-2/3 h-64 rounded-lg"
                                                        muted
                                                        controls
                                                    />
                                                ) : post.media?.image ? (
                                                    <img
                                                        src={post.media.image}
                                                        alt="Post"
                                                        className="object-cover w-2/3 h-64 rounded-lg"
                                                    />
                                                ) : (
                                                    <div className="flex items-center justify-center w-2/3 h-64 bg-gray-200 rounded-lg">
                                                      <span className="text-lg text-gray-500">No media</span>
                                                    </div>
                                                )}
                                                <div className="flex flex-col flex-1 gap-4 p-4">
                                                  <div className="flex items-center gap-2">
                                                    <Heart className="w-6 h-6 text-red-500" />
                                                    <span className="text-base font-medium text-slate-700">
                                                  {post.engagement?.likes.toLocaleString()}
                                                </span>
                                                  </div>
                                                  <div className="flex items-center gap-2">
                                                    <Share className="w-6 h-6 text-blue-500"/>
                                                    <span className="text-base font-medium text-slate-700">
                                                  {post.engagement?.shares.toLocaleString()}
                                                </span>
                                                  </div>
                                                  <div className="flex items-center gap-2">
                                                    <CgComment className="w-6 h-6 text-green-500"/>
                                                    <span className="text-base font-medium text-slate-700">
                                                  {post.engagement?.comments.toLocaleString()}
                                                </span>
                                                  </div>
                                                </div>
                                              </div>
                                              <div className="w-full">
                                                <p className="text-sm leading-relaxed text-slate-600">
                                                  {post.content}
                                                </p>
                                              </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="py-8 text-center">
                                          <span className="text-lg text-gray-400">No posts available</span>
                                        </div>
                                    )}
                                  </div>
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
      </div>
  );
}