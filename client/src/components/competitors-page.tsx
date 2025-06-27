"use client";

import * as React from "react";
import {
  BarChart3,
  Globe,
  Instagram,
  Linkedin,
  MoreHorizontal,
  Plus,
  Search,
  Twitter,
  Radio, Facebook,
} from "lucide-react";
import { AreaChart, Area, XAxis, ResponsiveContainer, Tooltip } from "recharts";
import { FaTiktok } from "react-icons/fa";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {any, number, string} from "zod";
import {useEffect, useState} from "react";
const socialPlatforms = [
  {
    id: "Instagram",
    name: "instagram",
    icon: Instagram,
    color: "bg-gradient-to-br from-purple-600 to-pink-500",
  },
  {
    id: "Facebook",
    name: "facebook",
    icon: Facebook,
    color: "bg-blue-600",
  },
  {
    id: "Twitter",
    name: "twitter",
    icon: Twitter,
    color: "bg-sky-500",
  },
  {
    id: "Linkedin",
    name: "linkedIn",
    icon: Linkedin,
    color: "bg-blue-700",

  },
  {
    id: "TikTok",
    name: "tiktok",
    icon: FaTiktok,
    color: "bg-black"

  }
];
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
  const [competitorsPost, setCompetitorsPosts] = useState<CompetitorsPosts[]>([]);
  const [competitors, setCompetitors] = useState<Competitors[]>([]);
  const fetchCompetitorsPosts = async () => {
    try{
      const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/competitors/posts`, {
        method: "GET",
        headers: {'Content-Type': "application/json", 'Authorization': `Bearer ${localStorage.getItem('token')}`}
      });

      const data = await res.json();
      const normalized: CompetitorPost[] = data.map((post: any) =>({
        id: post.id,
        competitor_id: post.competitor_id,
        platform: post.platform,
        content: post.content.valid ? post.content.string : null,
        media: post.media.valid? post.media.RawMessage : null,
        posted_at: post.posted_at.valid ? post.posted_at : null,
        engagement: post.engagement.valid ? post.engagement.RawMessage : null,
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
      console.log("NORMAL",normalized)
    }catch(e: any){
      throw new Error (e || "could not fetch competitors");

    }

  }
  useEffect(() => {
      fetchCompetitors();
      fetchCompetitorsPosts();
  }, []);
  return (
    <div className="flex-1 space-y-4 p-4 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Competitors</h2>
        <div className="flex items-center space-x-2">
          <Button variant="outline" className="gap-2" asChild>
            <a href="/competitors/live">
              <Radio className="h-4 w-4 text-red-500 animate-pulse" />
              Live Feed
            </a>
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" /> Add Competitor
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Tracked Competitors
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{competitors.length}</div>
              <p className="text-xs text-muted-foreground">in your industry</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Avg. Engagement Rate
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>

              <p className="text-xs text-muted-foreground">
                Coming soon
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Audience Growth Rate
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Coming soon</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Posting Frequency
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>

              <p className="text-xs text-muted-foreground">Coming soon</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Competitor Analysis</CardTitle>
              <CardDescription>
                Track and compare your competitors' social media performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-10">
                {competitors.map((competitor) => (
                    <div key = {competitor.id} className="flex items-center">
                      <Avatar className="h-9 w-9"
                              src={competitor.profile_url}>
                      <AvatarFallback>
                        {competitor.username.slice(0,2)}
                      </AvatarFallback>

                      </Avatar>
                      <div className="ml-4 ">
                        <p className="font-semibold text-medium">{competitor.username}</p>
                      </div>
                      <div className="flex ml-4">
                        <div className="ml-3 flex items-center gap-4">
                          <div className="flex flex-col items-center">
                            {(() => {
                              const platform = socialPlatforms.find(p => p.id === competitor.platform);
                              const Icon = platform?.icon;
                              return Icon ? (
                                  <div>
                                    <div
                                        className={`flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground`}
                                    >
                                      <Icon className="w-4 h-4" />

                                    </div>

                                  </div>

                              ) : <span className={"text-sm"}> {competitor.platform}</span>;
                            })()}
                            <span className="text-sm font-medium">
                              {competitor.followers}
                            </span>
                          </div>


                        </div>

                      </div>
                      <div className="flex w-[160px] ml-5 items-center gap-4">
                        <div className="w-full">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">
                              Engagement
                            </span>
                            <span className="text-sm text-muted-foreground">
                              {competitor.engagement_rate}%
                            </span>
                          </div>
                          <Progress
                              value={competitor.engagement_rate * 10}
                              className="h-2"
                          />
                        </div>
                      </div>
                    </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
