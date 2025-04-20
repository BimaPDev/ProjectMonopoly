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
  Radio,
} from "lucide-react";
import { AreaChart, Area, XAxis, ResponsiveContainer, Tooltip } from "recharts";

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

const competitors = [
  {
    id: 1,
    name: "Instagram",
    logo: "/placeholder.svg?height=40&width=40",
    website: "Instagram.com",
    followers: {
      instagram: 685000000,
      twitter: 32300000,
      linkedin: 320000,
    },
    engagement: 4.8,
    postFrequency: 12,
    trending: "up",
    growth: 12.5,
    data: Array.from({ length: 12 }, () => ({
      total: Math.floor(Math.random() * 5000) + 1000,
    })),
  },
  {
    id: 2,
    name: "test",
    logo: "/placeholder.svg?height=40&width=40",
    website: "test.com",
    followers: {
      instagram: 180000,
      twitter: 220000,
      linkedin: 62,
    },
    engagement: 3.9,
    postFrequency: 8,
    trending: "down",
    growth: -2.3,
    data: Array.from({ length: 12 }, () => ({
      total: Math.floor(Math.random() * 5000) + 1000,
    })),
  },
  {
    id: 3,
    name: "test",
    logo: "/placeholder.svg?height=40&width=40",
    website: "test.com",
    followers: {
      instagram: 320000,
      twitter: 150000,
      linkedin: 420000,
    },
    engagement: 5.2,
    postFrequency: 15,
    trending: "up",
    growth: 8.7,
    data: Array.from({ length: 12 }, () => ({
      total: Math.floor(Math.random() * 5000) + 1000,
    })),
  },
];

export function CompetitorsPage() {
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
              <div className="text-2xl font-bold">
                {(
                  competitors.reduce((acc, curr) => acc + curr.engagement, 0) /
                  competitors.length
                ).toFixed(1)}
                %
              </div>
              <p className="text-xs text-muted-foreground">
                across all platforms
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
              <div className="text-2xl font-bold">+5.8%</div>
              <p className="text-xs text-muted-foreground">monthly average</p>
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
              <div className="text-2xl font-bold">12.5</div>
              <p className="text-xs text-muted-foreground">posts per week</p>
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
              <div className="space-y-8">
                {competitors.map((competitor) => (
                  <div key={competitor.id} className="flex items-center">
                    <Avatar className="h-9 w-9">
                      <AvatarImage
                        src={competitor.logo}
                        alt={competitor.name}
                      />
                      <AvatarFallback>
                        {competitor.name.slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="ml-4 space-y-1">
                      <p className="text-sm font-medium leading-none">
                        {competitor.name}
                      </p>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <Globe className="h-3 w-3" />
                        {competitor.website}
                      </div>
                    </div>
                    <div className="ml-auto flex items-center gap-4">
                      <div className="flex items-center gap-4">
                        <div className="flex flex-col items-center">
                          <Instagram className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm font-medium">
                            {formatNumber(competitor.followers.instagram)}
                          </span>
                        </div>
                        <div className="flex flex-col items-center">
                          <Twitter className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm font-medium">
                            {formatNumber(competitor.followers.twitter)}
                          </span>
                        </div>
                        <div className="flex flex-col items-center">
                          <Linkedin className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm font-medium">
                            {formatNumber(competitor.followers.linkedin)}
                          </span>
                        </div>
                      </div>
                      <div className="flex w-[160px] items-center gap-4">
                        <div className="w-full">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">
                              Engagement
                            </span>
                            <span className="text-sm text-muted-foreground">
                              {competitor.engagement}%
                            </span>
                          </div>
                          <Progress
                            value={competitor.engagement * 10}
                            className="h-2"
                          />
                        </div>
                      </div>
                      <div className="w-[100px]">
                        <ResponsiveContainer width="100%" height={40}>
                          <AreaChart
                            data={competitor.data}
                            margin={{
                              top: 0,
                              right: 0,
                              left: 0,
                              bottom: 0,
                            }}
                          >
                            <defs>
                              <linearGradient
                                id={`gradient-${competitor.id}`}
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                              >
                                <stop
                                  offset="0%"
                                  stopColor={
                                    competitor.trending === "up"
                                      ? "rgb(34, 197, 94)"
                                      : "rgb(239, 68, 68)"
                                  }
                                  stopOpacity={0.3}
                                />
                                <stop
                                  offset="100%"
                                  stopColor={
                                    competitor.trending === "up"
                                      ? "rgb(34, 197, 94)"
                                      : "rgb(239, 68, 68)"
                                  }
                                  stopOpacity={0}
                                />
                              </linearGradient>
                            </defs>
                            <Area
                              type="monotone"
                              dataKey="total"
                              stroke={
                                competitor.trending === "up"
                                  ? "rgb(34, 197, 94)"
                                  : "rgb(239, 68, 68)"
                              }
                              fill={`url(#gradient-${competitor.id})`}
                              strokeWidth={2}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Growth</span>
                          <span
                            className={
                              competitor.trending === "up"
                                ? "text-sm font-medium text-green-600"
                                : "text-sm font-medium text-red-600"
                            }
                          >
                            {competitor.trending === "up" ? "+" : ""}
                            {competitor.growth}%
                          </span>
                        </div>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                            <span className="sr-only">More options</span>
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>View Details</DropdownMenuItem>
                          <DropdownMenuItem>Compare</DropdownMenuItem>
                          <DropdownMenuItem>Edit</DropdownMenuItem>
                          <DropdownMenuItem className="text-red-600">
                            Remove
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
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
