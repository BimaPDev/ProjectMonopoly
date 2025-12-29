"use client";

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  Loader2,
  TrendingUp,
  Clock,
  MessageSquare,
  Heart,
  Share2,
  Eye,
  Lightbulb,
  BarChart3,
} from "lucide-react";

interface MetricsSummary {
  total_posts: number;
  avg_impressions: number;
  avg_engagement: number;
  avg_likes: number;
  avg_comments: number;
  avg_shares: number;
}

interface PostingWindow {
  day_of_week: number;
  hour_of_day: number;
  avg_engagement: number;
  sample_size: number;
}

interface HookPattern {
  hook: string;
  avg_engagement: number;
  usage_count: number;
}

interface InsightsData {
  summary: MetricsSummary;
  best_posting_windows: PostingWindow[];
  top_hook_patterns: HookPattern[];
  recommendations: string[];
  data_window_days: number;
}

const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export default function CampaignInsightsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchInsights(id);
    }
  }, [id]);

  async function fetchInsights(campaignId: string) {
    setIsLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/campaigns/${campaignId}/insights`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error("Failed to fetch insights");
      }
      const data = await res.json();
      setInsights(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black p-8">
        <div className="max-w-4xl mx-auto">
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="text-zinc-400 mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <Card className="bg-red-950/50 border-red-800">
            <CardContent className="py-8 text-center">
              <p className="text-red-400">{error}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!insights) {
    return null;
  }

  const { summary, best_posting_windows, top_hook_patterns, recommendations } = insights;

  return (
    <div className="min-h-screen bg-black p-8">
      <div className="max-w-6xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="text-zinc-400 mb-6"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Campaign
        </Button>

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Campaign Insights</h1>
          <p className="text-zinc-400">
            Performance analysis from the last {insights.data_window_days} days
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-zinc-400 mb-2">
                <BarChart3 className="w-4 h-4" />
                <span className="text-xs">Total Posts</span>
              </div>
              <p className="text-2xl font-bold text-white">{summary.total_posts}</p>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-zinc-400 mb-2">
                <Eye className="w-4 h-4" />
                <span className="text-xs">Avg Impressions</span>
              </div>
              <p className="text-2xl font-bold text-white">
                {summary.avg_impressions?.toLocaleString() || "N/A"}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-zinc-400 mb-2">
                <TrendingUp className="w-4 h-4" />
                <span className="text-xs">Avg Engagement</span>
              </div>
              <p className="text-2xl font-bold text-emerald-400">
                {summary.avg_engagement?.toFixed(2) || "N/A"}%
              </p>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-zinc-400 mb-2">
                <Heart className="w-4 h-4" />
                <span className="text-xs">Avg Likes</span>
              </div>
              <p className="text-2xl font-bold text-white">
                {summary.avg_likes?.toLocaleString() || "N/A"}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-zinc-400 mb-2">
                <MessageSquare className="w-4 h-4" />
                <span className="text-xs">Avg Comments</span>
              </div>
              <p className="text-2xl font-bold text-white">
                {summary.avg_comments?.toLocaleString() || "N/A"}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-zinc-400 mb-2">
                <Share2 className="w-4 h-4" />
                <span className="text-xs">Avg Shares</span>
              </div>
              <p className="text-2xl font-bold text-white">
                {summary.avg_shares?.toLocaleString() || "N/A"}
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Best Posting Windows */}
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-violet-400" />
                <CardTitle className="text-white">Best Posting Windows</CardTitle>
              </div>
              <CardDescription className="text-zinc-400">
                Top performing times based on engagement
              </CardDescription>
            </CardHeader>
            <CardContent>
              {best_posting_windows.length === 0 ? (
                <p className="text-zinc-500 text-sm">
                  Not enough data yet. Keep posting to see patterns!
                </p>
              ) : (
                <div className="space-y-3">
                  {best_posting_windows.slice(0, 5).map((window, idx) => (
                    <div
                      key={`${window.day_of_week}-${window.hour_of_day}`}
                      className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <Badge
                          variant="outline"
                          className={`${
                            idx === 0
                              ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/50"
                              : "border-zinc-700 text-zinc-400"
                          }`}
                        >
                          #{idx + 1}
                        </Badge>
                        <div>
                          <p className="text-white font-medium">
                            {dayNames[window.day_of_week]} at {window.hour_of_day}:00
                          </p>
                          <p className="text-xs text-zinc-500">
                            {window.sample_size} posts analyzed
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-emerald-400 font-semibold">
                          {window.avg_engagement.toFixed(2)}%
                        </p>
                        <p className="text-xs text-zinc-500">engagement</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Top Hook Patterns */}
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-amber-400" />
                <CardTitle className="text-white">Top Hook Patterns</CardTitle>
              </div>
              <CardDescription className="text-zinc-400">
                Hooks that drive the most engagement
              </CardDescription>
            </CardHeader>
            <CardContent>
              {top_hook_patterns.length === 0 ? (
                <p className="text-zinc-500 text-sm">
                  Not enough data yet. Keep posting to see patterns!
                </p>
              ) : (
                <div className="space-y-3">
                  {top_hook_patterns.slice(0, 5).map((pattern, idx) => (
                    <div
                      key={pattern.hook}
                      className="p-3 bg-zinc-800/50 rounded-lg"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <Badge
                          variant="outline"
                          className={`${
                            idx === 0
                              ? "bg-amber-500/20 text-amber-400 border-amber-500/50"
                              : "border-zinc-700 text-zinc-400"
                          }`}
                        >
                          #{idx + 1}
                        </Badge>
                        <div className="text-right">
                          <p className="text-emerald-400 font-semibold">
                            {pattern.avg_engagement.toFixed(2)}%
                          </p>
                          <p className="text-xs text-zinc-500">
                            used {pattern.usage_count}x
                          </p>
                        </div>
                      </div>
                      <p className="text-white text-sm">&ldquo;{pattern.hook}&rdquo;</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Recommendations */}
        <Card className="bg-gradient-to-br from-violet-950/50 to-zinc-900 border-violet-800/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-violet-400" />
              <CardTitle className="text-white">AI Recommendations</CardTitle>
            </div>
            <CardDescription className="text-zinc-400">
              Actionable insights to improve your content strategy
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recommendations.length === 0 ? (
              <p className="text-zinc-500">
                Keep posting and check back for personalized recommendations!
              </p>
            ) : (
              <ul className="space-y-3">
                {recommendations.map((rec, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-3 p-3 bg-zinc-800/50 rounded-lg"
                  >
                    <div className="w-6 h-6 rounded-full bg-violet-500/20 flex items-center justify-center flex-shrink-0">
                      <span className="text-violet-400 text-xs font-bold">
                        {idx + 1}
                      </span>
                    </div>
                    <p className="text-white">{rec}</p>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}




