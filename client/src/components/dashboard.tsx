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
  StopwatchIcon,
} from "@radix-ui/react-icons";
import {
  Area,
  AreaChart,
  Line,
  LineChart,
  ResponsiveContainer,
  XAxis,
  Tooltip,
} from "recharts";
import { Bar, BarChart } from "recharts";
import { Calendar, Hash, Loader2Icon, ChartArea,Users, TrendingUp, CheckCheckIcon, Clock, Circle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const developmentItems = [
  {item: "Analytics", status: "ip"},
{item: "Log Out", status: "p"},

]
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Arrow } from "@radix-ui/react-tooltip";
export function Dashboard() {
  const [followers, setFollowers] = useState(0);
  const [loading, setLoading] = useState(false);
  async function fetchUserID() {
      const username = localStorage.getItem("username");
      const email = localStorage.getItem("email");
      const token = localStorage.getItem("token");
      if(!localStorage.getItem("userID") ) {
        try {
          console.log("Fetching userid...");
          const response = await fetch(`${import.meta.env.VITE_API_CALL}/api/getUserID`, {
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
  // async function fetchPosts() {
  //   setLoading(true);
  //   try {
  //     const response = await fetch( `${import.meta.env.VITE_API_CALL}/GetUploadItemsByGroupID?groupID=`)
  //
  //   }
  //
  // }
  fetchUserID();
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

          <div className="flex flex-col p-6 border rounded-lg border-slate-700/50 bg-slate-800/50 backdrop-blur-sm">
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
