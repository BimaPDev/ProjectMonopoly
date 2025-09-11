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
  QuestionMarkCircledIcon, 
  ReloadIcon,
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
    case 'pending': return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
    case 'active': return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
    case 'completed': return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
    case 'failed': return 'bg-red-500/20 text-red-300 border-red-500/30';
    default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
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
            return;
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

  const transformCampaignData = (rawData: any): Campaign[] => {
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
  },[])

  return (
    <div className="min-h-screen bg-black text-white">
      <Tabs defaultValue="overview" className="w-full">
        <div className="border-b border-gray-800">
          <TabsList className="bg-transparent border-none h-auto p-0">
            <TabsTrigger 
              value="overview" 
              className="bg-transparent text-gray-400 data-[state=active]:text-white data-[state=active]:bg-gray-900 border-b-2 border-transparent data-[state=active]:border-blue-500 rounded-none px-6 py-4"
            >
              Overview
            </TabsTrigger>
            <TabsTrigger 
              value="analytics"
              className="bg-transparent text-gray-400 data-[state=active]:text-white data-[state=active]:bg-gray-900 border-b-2 border-transparent data-[state=active]:border-blue-500 rounded-none px-6 py-4"
            >
              Analytics
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="overview" className="mt-0">
          <div className="w-full px-6 py-8 mx-auto max-w-7xl">
            {/* Stats Cards */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-8">
              {/* Followers Card */}
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="bg-blue-500/10 p-3 rounded-lg">
                      <Users className="w-6 h-6 text-blue-400" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-400">Total Followers</p>
                      <p className="text-2xl font-semibold text-white">{followers}</p>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-xs text-emerald-400 flex items-center">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    
                  </p>
                </div>
                <Button 
                  onClick={fetchFollowers} 
                  disabled={loading} 
                  className="w-full mt-4 bg-blue-600 hover:bg-blue-700 border-none text-white"
                >
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <Loader2Icon className="w-4 h-4 mr-2 animate-spin" />
                      <span>Updating...</span>
                    </div>
                  ) : (
                    <>
                      <ReloadIcon className="w-4 h-4 mr-2" />
                      Update Followers
                    </>
                  )}
                </Button>
              </div>

              {/* Placeholder Cards */}
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="bg-emerald-500/10 p-3 rounded-lg">
                    <ChartArea className="w-6 h-6 text-emerald-400" />
                  </div>
                  <div>
                    {/* engagement rate */}
                  </div>
                </div>
                 {/* engagement rate increase decrease */}
              </div>

              <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="bg-purple-500/10 p-3 rounded-lg">
                    <LightningBoltIcon className="w-6 h-6 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Active Campaigns</p>
                    <p className="text-2xl font-semibold text-white">{campaigns.filter(c => c.status === 'active').length}</p>
                  </div>
                </div>
                <p className="text-xs text-gray-400">Total campaigns running</p>
              </div>
            </div>

            {/* Development Status */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-8">
              <div className="flex items-center space-x-3 mb-6">
                <div className="bg-amber-500/10 p-3 rounded-lg">
                  <LightningBoltIcon className="w-6 h-6 text-amber-400" />
                </div>
                <h2 className="text-xl font-semibold text-white">Development Status</h2>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {developmentItems.map((feature, index) => (
                  <div key={index} className="bg-gray-800 border border-gray-700 rounded-lg p-4 flex items-center space-x-3">
                    {feature.status === "c" ? (
                      <CheckCheckIcon className="w-5 h-5 text-emerald-400" />
                    ) : feature.status === "ip" ? (
                      <Clock className="w-5 h-5 text-amber-400" />
                    ) : (
                      <Circle className="w-5 h-5 text-gray-500" />
                    )}
                    <span className="text-sm text-white font-medium">{feature.item}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Posts */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="bg-emerald-500/10 p-3 rounded-lg">
                    <Clock className="w-6 h-6 text-emerald-400" />
                  </div>
                  <h2 className="text-xl font-semibold text-white">Recent Campaigns</h2>
                </div>
                <Button
                  onClick={() => fetchPosts()}
                  variant="outline"
                  size="sm"
                  className="border-gray-700 bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-white"
                >
                  <ReloadIcon className="w-4 h-4 mr-2" />
                  Reload
                </Button>
              </div>

              {/* Filters */}
              <div className="mb-6">
                <div className="flex flex-wrap gap-2">
                  {['all', 'pending', 'active', 'completed', 'failed'].map((filter) => (
                    <button
                      key={filter}
                      onClick={() => setSelectedFilter(filter)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        selectedFilter === filter
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
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
                    <Loader2Icon className="w-16 h-16 mx-auto animate-spin" />
                  </div>
                  <h3 className="text-lg font-medium text-white mb-2">Loading campaigns...</h3>
                </div>
              )}

              {/* Error State */}
              {error && (
                <div className="text-center py-12">
                  <div className="text-red-400 mb-4">
                    <AlertCircle className="w-16 h-16 mx-auto" />
                  </div>
                  <h3 className="text-lg font-medium text-white mb-2">Error loading campaigns</h3>
                  <p className="text-gray-400">{error}</p>
                </div>
              )}

              {/* Campaign Grid */}
              {!loading && !error && (
                <div className="space-y-4">
                  {filteredCampaigns.map((campaign) => (
                    <div key={campaign.id} className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-gray-600 transition-colors">
                      {/* Header */}
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-mono text-gray-300 bg-gray-700 px-3 py-1 rounded">
                            Group {campaign.group_id}
                          </span>
                          {campaign.valid ? (
                            <Check className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <AlertCircle className="w-4 h-4 text-red-400" />
                          )}
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(campaign.status)}`}>
                          {campaign.status}
                        </span>
                      </div>

                      {/* Campaign ID */}
                      <div className="mb-4">
                        <p className="text-xs text-gray-400 mb-1">Campaign ID</p>
                        <p className="text-sm font-mono text-gray-300 break-all">{campaign.id}</p>
                      </div>

                      {/* Platforms */}
                      <div className="mb-4">
                        <p className="text-xs text-gray-400 mb-2">Platforms</p>
                        <div className="flex gap-2 flex-wrap">
                          {campaign.platforms.map((platform) => (
                            <span
                              key={platform}
                              className="flex items-center gap-2 px-3 py-1 bg-gray-700 border border-gray-600 text-gray-200 rounded-lg text-xs font-medium"
                            >
                              <span>{getPlatformIcon(platform)}</span>
                              {platform}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Created Date */}
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <Calendar className="w-3 h-3" />
                        <span>Created: {formatDate(campaign.created_at)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Empty State */}
              {!loading && !error && filteredCampaigns.length === 0 && (
                <div className="text-center py-12">
                  <div className="text-gray-500 mb-4">
                    <Clock className="w-16 h-16 mx-auto" />
                  </div>
                  <h3 className="text-lg font-medium text-white mb-2">No campaigns found</h3>
                  <p className="text-gray-400">No campaigns match your current filter selection.</p>
                </div>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="mt-0">
          <div className="w-full px-6 py-16 mx-auto max-w-7xl">
            <div className="text-center">
              <div className="bg-blue-500/10 p-6 rounded-2xl inline-block mb-6">
                <ChartArea className="w-12 h-12 text-blue-400" />
              </div>
              <h3 className="text-2xl font-semibold text-white mb-3">Analytics Coming Soon</h3>
              <p className="text-gray-400 max-w-md mx-auto">
                Advanced analytics and insights will be available here to help you track your social media performance.
              </p>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}