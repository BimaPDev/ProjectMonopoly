"use client";

import * as React from "react";
import {
  ArrowDownIcon,
  ArrowRightIcon,
  ArrowUpIcon,
  CheckCircledIcon,
  CircleIcon,
  CrossCircledIcon,
  QuestionMarkCircledIcon,
  StopwatchIcon,
} from "@radix-ui/react-icons";
import {
  Bar,
  BarChart,
  Line,
  LineChart,
  ResponsiveContainer,
  XAxis,
  Tooltip,
} from "recharts";
import { Calendar, Hash } from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const data = [
  {
    name: "Jan",
    total: Math.floor(Math.random() * 5000) + 1000,
  },
  {
    name: "Feb",
    total: Math.floor(Math.random() * 5000) + 1000,
  },
  {
    name: "Mar",
    total: Math.floor(Math.random() * 5000) + 1000,
  },
  {
    name: "Apr",
    total: Math.floor(Math.random() * 5000) + 1000,
  },
  {
    name: "May",
    total: Math.floor(Math.random() * 5000) + 1000,
  },
  {
    name: "Jun",
    total: Math.floor(Math.random() * 5000) + 1000,
  },
  {
    name: "Jul",
    total: Math.floor(Math.random() * 5000) + 1000,
  },
  {
    name: "Aug",
    total: Math.floor(Math.random() * 5000) + 1000,
  },
  {
    name: "Sep",
    total: Math.floor(Math.random() * 5000) + 1000,
  },
  {
    name: "Oct",
    total: Math.floor(Math.random() * 5000) + 1000,
  },
  {
    name: "Nov",
    total: Math.floor(Math.random() * 5000) + 1000,
  },
  {
    name: "Dec",
    total: Math.floor(Math.random() * 5000) + 1000,
  },
];

export function Dashboard() {
  return (
    <Tabs defaultValue="overview" className="space-y-4">
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="analytics">Analytics</TabsTrigger>
        <TabsTrigger value="reports">Reports</TabsTrigger>
        <TabsTrigger value="notifications">Notifications</TabsTrigger>
      </TabsList>
      <TabsContent value="overview" className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Followers
              </CardTitle>
              <ArrowUpIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">45,231</div>
              <p className="text-xs text-muted-foreground">
                +20.1% from last month
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Engagement Rate
              </CardTitle>
              <ArrowUpIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">5.2%</div>
              <p className="text-xs text-muted-foreground">
                +1.2% from last month
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Scheduled Posts
              </CardTitle>
              <StopwatchIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">12</div>
              <p className="text-xs text-muted-foreground">
                For the next 7 days
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Active Campaigns
              </CardTitle>
              <CircleIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">3</div>
              <p className="text-xs text-muted-foreground">
                2 ending this week
              </p>
            </CardContent>
          </Card>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Card className="col-span-4">
            <CardHeader>
              <CardTitle>Engagement Overview</CardTitle>
            </CardHeader>
            <CardContent className="pl-2">
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={data}>
                  <XAxis
                    dataKey="name"
                    stroke="#888888"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    cursor={{
                      fill: "var(--hover-color)",
                      opacity: 0.1,
                    }}
                    contentStyle={{
                      backgroundColor: "hsl(var(--background))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "var(--radius)",
                    }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="rounded-lg border bg-background p-2 shadow-sm">
                            <div className="grid grid-cols-2 gap-2">
                              <div className="flex flex-col">
                                <span className="text-[0.70rem] uppercase text-muted-foreground">
                                  Month
                                </span>
                                <span className="font-bold text-foreground">
                                  {payload[0].payload.name}
                                </span>
                              </div>
                              <div className="flex flex-col">
                                <span className="text-[0.70rem] uppercase text-muted-foreground">
                                  Engagement
                                </span>
                                <span className="font-bold text-foreground">
                                  {payload[0].value}
                                </span>
                              </div>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar
                    dataKey="total"
                    style={{
                      fill: "hsl(var(--primary))",
                      opacity: 0.9,
                    }}
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
          <Card className="col-span-3">
            <CardHeader>
              <CardTitle>Recent Posts</CardTitle>
              <CardDescription>
                Your most recent social media posts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-8">
                <div className="flex items-center">
                  <Avatar className="h-9 w-9">
                    <AvatarImage src="/placeholder.svg" alt="Avatar" />
                    <AvatarFallback>OM</AvatarFallback>
                  </Avatar>
                  <div className="ml-4 space-y-1">
                    <p className="text-sm font-medium leading-none">
                      New Product Launch
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Instagram • 2 hours ago
                    </p>
                  </div>
                  <div className="ml-auto font-medium">
                    <Badge>Live</Badge>
                  </div>
                </div>
                <div className="flex items-center">
                  <Avatar className="flex h-9 w-9 items-center justify-center space-y-0 border">
                    <AvatarImage src="/placeholder.svg" alt="Avatar" />
                    <AvatarFallback>JL</AvatarFallback>
                  </Avatar>
                  <div className="ml-4 space-y-1">
                    <p className="text-sm font-medium leading-none">
                      Summer Collection
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Twitter • 5 hours ago
                    </p>
                  </div>
                  <div className="ml-auto font-medium">
                    <Badge variant="outline">Scheduled</Badge>
                  </div>
                </div>
                <div className="flex items-center">
                  <Avatar className="h-9 w-9">
                    <AvatarImage src="/placeholder.svg" alt="Avatar" />
                    <AvatarFallback>WK</AvatarFallback>
                  </Avatar>
                  <div className="ml-4 space-y-1">
                    <p className="text-sm font-medium leading-none">
                      Customer Story
                    </p>
                    <p className="text-sm text-muted-foreground">
                      LinkedIn • 1 day ago
                    </p>
                  </div>
                  <div className="ml-auto font-medium">
                    <Badge variant="secondary">Draft</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Card className="col-span-4">
            <CardHeader>
              <CardTitle>Upcoming Content</CardTitle>
              <CardDescription>
                Your content calendar for the next 7 days
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-8">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center">
                    <div className="flex items-center justify-center w-10">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="ml-4 space-y-1">
                      <p className="text-sm font-medium leading-none">
                        {
                          [
                            "Product Update",
                            "Customer Spotlight",
                            "Tips & Tricks",
                            "Behind the Scenes",
                            "Weekend Special",
                          ][i]
                        }
                      </p>
                      <div className="flex items-center pt-2">
                        <Badge variant="secondary" className="mr-2">
                          Instagram
                        </Badge>
                        <Badge variant="secondary">Facebook</Badge>
                      </div>
                    </div>
                    <div className="ml-auto font-medium">
                      {new Date(
                        Date.now() + (i + 1) * 24 * 60 * 60 * 1000
                      ).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card className="col-span-3">
            <CardHeader>
              <CardTitle>Hashtag Performance</CardTitle>
              <CardDescription>
                Top performing hashtags this month
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-8">
                {[
                  { tag: "#marketing", count: "12.3K", trend: "up" },
                  { tag: "#socialmedia", count: "8.7K", trend: "up" },
                  { tag: "#digital", count: "6.2K", trend: "down" },
                  { tag: "#strategy", count: "4.5K", trend: "up" },
                  { tag: "#content", count: "3.8K", trend: "down" },
                ].map((item) => (
                  <div key={item.tag} className="flex items-center">
                    <Hash className="h-4 w-4 text-muted-foreground" />
                    <div className="ml-4 space-y-1">
                      <p className="text-sm font-medium leading-none">
                        {item.tag}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {item.count} mentions
                      </p>
                    </div>
                    <div className="ml-auto">
                      {item.trend === "up" ? (
                        <ArrowUpIcon className="h-4 w-4 text-green-500" />
                      ) : (
                        <ArrowDownIcon className="h-4 w-4 text-red-500" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>
    </Tabs>
  );
}
