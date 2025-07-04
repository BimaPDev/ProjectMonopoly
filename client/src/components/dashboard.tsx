"use client";

import * as React from "react";
import{ useEffect, useState } from "react";
import {
  ArrowDownIcon,
  ArrowRightIcon,
  ArrowUpIcon,
  CheckCircledIcon,
  CircleIcon,
  CrossCircledIcon,
  LightningBoltIcon,
  QuestionMarkCircledIcon, ReloadIcon,
  StopwatchIcon,
} from "@radix-ui/react-icons";

import {Loader2Icon, ChartArea,Users, TrendingUp, CheckCheckIcon, Circle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,

} from "@/components/ui/card";

import { useGroup } from './groupContext.tsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Arrow } from "@radix-ui/react-tooltip";
import { Calendar, Clock, Check, AlertCircle, Edit, Trash2, Play } from 'lucide-react';





const developmentItems = [
  {item: "Analytics", status: "ip"},
{item: "Log Out", status: "p"},
    
]

const getStatusColor = (status: string) => {
  switch (status) {
    case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'active': return 'bg-green-100 text-green-800 border-green-200';
    case 'completed': return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'failed': return 'bg-red-100 text-red-800 border-red-200';
    default: return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const getPlatformIcon = (platform: string) => {
  switch (platform) {
    case 'facebook': return '📘';
    case 'instagram': return '📷';
    case 'twitter': return '🐦';
    default: return '📱';
  }
};
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString();
};

interface Campaign {
  id: string;
  group_id: number;
  valid: boolean;
  created_at: string;
  platforms: string[];
  status: 'pending' | 'active' | 'completed' | 'failed';
}

export function Dashboard() {
  const [followers, setFollowers] = useState(0);
  const [loading, setLoading] = useState(false);
  const { activeGroup} = useGroup();
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);
  const filteredCampaigns = campaigns.filter(campaign => {
    if (selectedFilter === 'all') return true;
    return campaign.status === selectedFilter;
  });
  async function fetchUserID() {
      const username = localStorage.getItem("username");
      const email = localStorage.getItem("email");
      const token = localStorage.getItem("token");
      if(!localStorage.getItem("userID") ) {
        try {
          console.log("Fetching userid...");
          const response = await fetch(`${import.meta.env.VITE_API_CALL}/api/UserID`, {
            method: "POST",
            headers: {'Content-Type': "application/json", "Authorization": `Bearer ${token}`},

            body: JSON.stringify({
              username,
              email,
            }),
          });

          if (!response.ok) {
            console.log("Failed to get userID");
            return; // Exit early if we can't get the userID
          }

          const data = await response.json();
          const userID = data.userID;
          localStorage.setItem("userID", userID);


        } catch (e) {
          console.log("Error getting userID:", e);
        }
      }
    }
  
  
  async function fetchFollowers() {
    setLoading(true)
    try {
      const response = await fetch(`${import.meta.env.VITE_API_CALL}/followers`);
      const data = await response.json();
      setFollowers(data);
    } catch (error) {
      console.error("Error fetching followers:", error);
    }finally{
      setLoading(false);
    }
  }
  // Transform API data to match component structure
  const transformCampaignData = (rawData: any): Campaign[] => {
    // Handle single object or array
    const dataArray = Array.isArray(rawData) ? rawData : [rawData];

    return dataArray.map((item: any) => ({
      id: item.id,
      group_id: item.group_id?.Int32 || item.group_id || 0,
      valid: item.valid !== undefined ? item.valid : true,
      created_at: item.created_at?.Time || item.created_at || new Date().toISOString(),
      platforms: item.platform ? item.platform.split(',').map((p: string) => p.trim()) : [],
      status: item.status || 'pending'
    }));
  };
  async function fetchPosts() {


    try {
      const res = await fetch(
          `${import.meta.env.VITE_API_CALL}/api/UploadItemsByGroupID?groupID=${activeGroup.ID}`
      );

      if (!res.ok) {
        throw new Error(`Error: ${res.status}`);
      }
      const data = await res.json() as Campaign[];
      // Transform the data
      const transformedData = transformCampaignData(data);
      console.log('Transformed data:', transformedData);

      setCampaigns(transformedData);

      console.log("CAMPAITGN", campaigns)
    } catch (err) {
      console.error("Fetch error:", err);
    }

  }
  useEffect(() => {
      fetchPosts()
      fetchUserID()

      },[])//dependency array, empty means on mount
  return (
    <div className="min-h-screen bg-gradient-to-br from-black-900 via-slate-800 to-slate-900">
    <Tabs defaultValue="overview" className="">
      <TabsList>
        <TabsTrigger value="overview" >Overview</TabsTrigger>
        <TabsTrigger value="analytics" >Analytics</TabsTrigger>
        {/* <TabsTrigger value="reports" >Reports</TabsTrigger>
        <TabsTrigger value="notifications">Notifications</TabsTrigger> */}
      </TabsList>
      <TabsContent value="overview" className="space-y-4">
        <div className="w-full px-4 py-5 mx-auto max-w-7xl">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 ">
        
        <div className="flex flex-col items-center justify-center p-6 m-5 space-y-4 border rounded-lg border-slate-700/50 bg-slate-800/50 backdrop-blur-sm">
          <div className="flex items-center space-x-2">
            <Users className="w-6 h-6 text-blue-400" />
            <div className="text-sm font-medium text-white">Total Followers</div>
          </div>
          <div className="text-2xl font-bold text-white">{followers}</div>
          <p className="text-xs text-green-500">+{20.1}% from last month</p>
          <Button onClick={fetchFollowers} disabled={loading} className="w-full">
            {loading ? (
              <div className="flex items-center justify-center">
                <Loader2Icon className="w-4 h-4 mr-2 animate-spin" />
                <span>Getting Followers..</span>
              </div>
            ) : (
              <>
                <TrendingUp className="w-4 h-4 mr-2" />
                Update Followers
              </>
            )}
          </Button>
        </div>

              
            
        <div className="flex flex-col items-center justify-center p-6 m-5 space-y-4 border rounded-lg border-slate-700/50 bg-slate-800/50 backdrop-blur-sm">
          {/* engagement rate or some other metric*/}
        </div>


              <Card>
                {/* engagement rate or some other metric*/}
              </Card>


              <div className="flex flex-col col-span-3 p-5 border items-left ap-2 bg-slate-800/50 backdrop-blur-sm border-slate-700/50 rounded-t-2xl">
                <div className="flex item-center ">
                  <div className="p-2 rounded bg-yellow-500/50">
                    <LightningBoltIcon className="w-6 h-6 text-yellow-300" />
                  </div>
                 <h1 className="p-2 font-semibold">Development Status</h1>
                </div>
                 <div className="flex flex-wrap gap-4 p-5">
                  {developmentItems.map((feature,index)=>(
                    <div key={index} className="w-40 p-3 rounded-lg opacity-50 bg-slate-500">
                      {feature.status === "c" ? (
                        <CheckCheckIcon className="w-4 h-4 text-green-400"></CheckCheckIcon>

                      ): feature.status === "ip" ? (
                        <Clock className="w-4 h-4 text-amber-400"></Clock>
                      ): (
                        <Circle className="w-4 h-4 text-slate-400"></Circle>
                        
                      )}
                      <span className="text-sm text-white"> {feature.item}</span>
                    </div>
                    
                  ))}
                 </div>
              </div>

          <div className="flex flex-col col-span-3 p-6 border rounded-lg border-slate-700/50 bg-slate-800/50 backdrop-blur-sm">
            <div className="flex items-center justify-start  space-x-2">
              <div className="bg-green-500/50 p-2 rounded ">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    className="w-6 h-6 stroke-2 stroke-current"
                >
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>

              </div>
              <h1 className="p-2 font-semibold">Recent Posts</h1>
              <div className={"flex gap-x-2 items-center rounded-2xl p-2 bg-blue-300/20"}>
                <ReloadIcon></ReloadIcon>
                <button onClick={()=> fetchPosts()}> Reload</button>
              </div>
              </div>
            <div className="min-h-screen  p-6">
              <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                  <h1 className="text-3xl font-bold text-white mb-2">Social Media Campaigns</h1>
                  <p className="text-gray-600">Manage your social media posts across platforms</p>
                </div>

                {/* Filters */}
                <div className=" rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
                  <div className="flex flex-wrap gap-2">
                    {['all', 'pending', 'active', 'completed', 'failed'].map((filter) => (
                        <button
                            key={filter}
                            onClick={() => setSelectedFilter(filter)}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                selectedFilter === filter
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                        >
                          {filter.charAt(0).toUpperCase() + filter.slice(1)}
                        </button>
                    ))}
                  </div>
                </div>

                {/* Loading State */}
                {loading && (
                    <div className="text-center py-12">
                      <div className="text-gray-400 mb-4">
                        <Clock className="w-16 h-16 mx-auto animate-spin" />
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Loading campaigns...</h3>
                    </div>
                )}

                {/* Error State */}
                {error && (
                    <div className="text-center py-12">
                      <div className="text-red-400 mb-4">
                        <AlertCircle className="w-16 h-16 mx-auto" />
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Error loading campaigns</h3>
                      <p className="text-gray-500">{error}</p>
                    </div>
                )}

                {/* Campaign Grid */}
                {!loading && !error && (
                    <div className="flex flex-col gap-6">
                      {filteredCampaigns.map((campaign) => (
                          <div key={campaign.id} className="bg-gray-800 rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow w-full">
                            {/* Header */}
                            <div className="flex items-start justify-between mb-4">
                              <div className="flex items-center gap-2">
                  <span className="text-sm font-mono text-white">
                    Group {campaign.group_id}
                  </span>
                                {campaign.valid ? (
                                    <Check className="w-4 h-4 text-green-600" />
                                ) : (
                                    <AlertCircle className="w-4 h-4 text-red-600" />
                                )}
                              </div>
                              <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(campaign.status)}`}>
                  {campaign.status}
                </span>
                            </div>

                            {/* Campaign ID */}
                            <div className="mb-4">
                              <p className="text-xs text-white mb-1">Campaign ID</p>
                              <p className="text-sm font-mono text-white break-all">{campaign.id}</p>
                            </div>

                            {/* Platforms */}
                            <div className="mb-4">
                              <p className="text-xs text-white mb-2">Platforms</p>
                              <div className="flex gap-2">
                                {campaign.platforms.map((platform) => (
                                    <span
                                        key={platform}
                                        className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-black rounded-lg text-xs font-medium"
                                    >
                                        <span >{getPlatformIcon(platform)}</span>
                                                        {platform}
                                      </span>
                                ))}
                              </div>
                            </div>

                            {/* Created Date */}
                            <div className="mb-4">
                              <div className="flex items-center gap-2 text-xs text-gray-500">
                                <Calendar className="w-3 h-3" />
                                <span>Created: {formatDate(campaign.created_at)}</span>
                              </div>
                            </div>

                            {/* Actions */}

                          </div>
                      ))}
                    </div>
                )}

                {/* Empty State */}
                {!loading && !error && filteredCampaigns.length === 0 && (
                    <div className="text-center py-12">
                      <div className="text-gray-400 mb-4">
                        <Clock className="w-16 h-16 mx-auto" />
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No campaigns found</h3>
                      <p className="text-gray-500">No campaigns match your current filter selection.</p>
                    </div>
                )}
              </div>
            </div>
          </div>

        </div>
        </div>






      </TabsContent>
      <TabsContent value="analytics">
        <div className="py-20 text-center">
            <div className="inline-block p-4 mb-4 rounded-lg bg-blue-500/20">
              <ChartArea className="w-8 h-8 text-slate-400" />
            </div>
            <h3 className="mb-2 text-2xl font-bold text-white">Analytics Coming Soon</h3>
            <p className="text-slate-400">Advanced analytics and insights will be available here.</p>
          </div>
      </TabsContent>
      <TabsContent value="reports">Reports</TabsContent>
      <TabsContent value="notifications">Notifications</TabsContent>
    </Tabs>
    </div>
  );
}
