"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { toast } from "@/hooks/use-toast";
import { useGroup } from "../../components/groupContext";
import {
    Sparkles,
    Copy,
    Clock,
    TrendingUp,
    Loader2,
    AlertCircle,
    CheckCircle2,
    Megaphone,
    PenTool
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface MarketingResponse {
    content: string;
    best_posting_hour: number;
    top_hook: string;
    tokens_used_estimate: number;
    data_source: string;
}

export default function MarketingGeneratorPage() {
    const { activeGroup } = useGroup();
    const [isLoading, setIsLoading] = useState(false);
    const [response, setResponse] = useState<MarketingResponse | null>(null);

    // Form state
    const [taskType, setTaskType] = useState<string>("Strategy");
    const [campaignType, setCampaignType] = useState<string>("Teaser");
    const [platform, setPlatform] = useState<string>("Instagram");
    const [customPrompt, setCustomPrompt] = useState<string>("");

    const handleGenerate = async () => {
        if (!activeGroup) {
            toast({
                title: "No Group Selected",
                description: "Please select a group from the dropdown first.",
                variant: "destructive",
            });
            return;
        }

        setIsLoading(true);
        setResponse(null);

        try {
            const token = localStorage.getItem("token");
            const res = await fetch(
                `${import.meta.env.VITE_BACKEND_URL || ""}/api/marketing/generate`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        group_id: activeGroup.ID,
                        task_type: taskType,
                        campaign_type: campaignType,
                        platform: platform,
                        custom_prompt: customPrompt,
                    }),
                }
            );

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.error || "Failed to generate content");
            }

            const data: MarketingResponse = await res.json();
            setResponse(data);

            toast({
                title: "Content Generated!",
                description: `Used approximately ${data.tokens_used_estimate} tokens`,
            });
        } catch (error: unknown) {
            console.error("Generation error:", error);
            toast({
                title: "Generation Failed",
                description: error instanceof Error ? error.message : "An error occurred",
                variant: "destructive",
            });
        } finally {
            setIsLoading(false);
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        toast({
            title: "Copied!",
            description: "Content copied to clipboard",
        });
    };

    const formatHour = (hour: number) => {
        const suffix = hour >= 12 ? "PM" : "AM";
        const displayHour = hour % 12 || 12;
        return `${displayHour}:00 ${suffix}`;
    };

    return (
        <div className="container mx-auto py-6 space-y-6 max-w-4xl">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <Sparkles className="h-5 w-5 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold">Marketing Generator</h1>
                    <p className="text-muted-foreground">
                        AI-powered marketing content with optimized token usage
                    </p>
                </div>
            </div>

            {/* No Group Warning */}
            {!activeGroup && (
                <Card className="border-yellow-500/50 bg-yellow-500/10">
                    <CardContent className="flex items-center gap-3 py-4">
                        <AlertCircle className="h-5 w-5 text-yellow-500" />
                        <p className="text-sm">
                            Please select a group from the sidebar to generate marketing content.
                        </p>
                    </CardContent>
                </Card>
            )}

            <div className="grid gap-6 md:grid-cols-2">
                {/* Configuration Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <PenTool className="h-4 w-4" />
                            Configuration
                        </CardTitle>
                        <CardDescription>
                            Configure your marketing content generation
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Task Type */}
                        <div className="space-y-2">
                            <Label>Task Type</Label>
                            <Select value={taskType} onValueChange={setTaskType}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select task type" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Strategy">
                                        <div className="flex items-center gap-2">
                                            <Megaphone className="h-4 w-4" />
                                            Strategy (High-level, ~300 tokens)
                                        </div>
                                    </SelectItem>
                                    <SelectItem value="Script Writing">
                                        <div className="flex items-center gap-2">
                                            <PenTool className="h-4 w-4" />
                                            Script Writing (Detailed, ~800 tokens)
                                        </div>
                                    </SelectItem>
                                </SelectContent>
                            </Select>
                            <p className="text-xs text-muted-foreground">
                                {taskType === "Strategy"
                                    ? "High-level planning with minimal context for efficiency"
                                    : "Detailed content with full game context and documents"}
                            </p>
                        </div>

                        {/* Campaign Type */}
                        <div className="space-y-2">
                            <Label>Campaign Type</Label>
                            <Select value={campaignType} onValueChange={setCampaignType}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select campaign type" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Teaser">🎭 Teaser (Mystery, no CTAs)</SelectItem>
                                    <SelectItem value="Launch">🚀 Launch (Clear CTAs)</SelectItem>
                                    <SelectItem value="Update">🔄 Update (Feature highlights)</SelectItem>
                                    <SelectItem value="Community">💬 Community (Engagement)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Platform */}
                        <div className="space-y-2">
                            <Label>Platform</Label>
                            <Select value={platform} onValueChange={setPlatform}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select platform" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Instagram">📸 Instagram</SelectItem>
                                    <SelectItem value="TikTok">🎵 TikTok</SelectItem>
                                    <SelectItem value="Twitter">🐦 Twitter/X</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Custom Instructions */}
                        <div className="space-y-2">
                            <Label>Additional Instructions (Optional)</Label>
                            <Textarea
                                placeholder="Any specific requirements or tone preferences..."
                                value={customPrompt}
                                onChange={(e) => setCustomPrompt(e.target.value)}
                                rows={3}
                            />
                        </div>

                        {/* Generate Button */}
                        <Button
                            onClick={handleGenerate}
                            disabled={isLoading || !activeGroup}
                            className="w-full"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Generating...
                                </>
                            ) : (
                                <>
                                    <Sparkles className="mr-2 h-4 w-4" />
                                    Generate Content
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>

                {/* Insights Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <TrendingUp className="h-4 w-4" />
                            Competitor Insights
                        </CardTitle>
                        <CardDescription>
                            Data from the last 14 days of competitor posts
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {response ? (
                            <>
                                {/* Data Source Badge */}
                                <div className="flex items-center gap-2">
                                    <Badge variant={response.data_source === "14_day_window" ? "default" : "secondary"}>
                                        {response.data_source === "14_day_window" ? (
                                            <>
                                                <CheckCircle2 className="mr-1 h-3 w-3" />
                                                Live Data
                                            </>
                                        ) : (
                                            <>
                                                <AlertCircle className="mr-1 h-3 w-3" />
                                                Fallback Mode
                                            </>
                                        )}
                                    </Badge>
                                </div>

                                {/* Best Posting Hour */}
                                <div className="rounded-lg border p-4 space-y-2">
                                    <div className="flex items-center gap-2 text-sm font-medium">
                                        <Clock className="h-4 w-4 text-blue-500" />
                                        Optimal Posting Time
                                    </div>
                                    <p className="text-2xl font-bold">
                                        {formatHour(response.best_posting_hour)}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        Based on competitor engagement data
                                    </p>
                                </div>

                                {/* Top Hook */}
                                {response.top_hook && (
                                    <div className="rounded-lg border p-4 space-y-2">
                                        <div className="flex items-center gap-2 text-sm font-medium">
                                            <TrendingUp className="h-4 w-4 text-green-500" />
                                            Top Competitor Hook
                                        </div>
                                        <p className="text-sm italic">"{response.top_hook}"</p>
                                    </div>
                                )}

                                {/* Token Usage */}
                                <div className="text-xs text-muted-foreground text-center">
                                    Estimated tokens used: {response.tokens_used_estimate}
                                </div>
                            </>
                        ) : (
                            <div className="text-center py-8 text-muted-foreground">
                                <TrendingUp className="h-12 w-12 mx-auto mb-3 opacity-20" />
                                <p>Generate content to see insights</p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Generated Content */}
            {response && (
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <CardTitle>Generated Content</CardTitle>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => copyToClipboard(response.content)}
                            >
                                <Copy className="mr-2 h-4 w-4" />
                                Copy
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="rounded-lg bg-muted p-4 whitespace-pre-wrap font-mono text-sm">
                            {response.content}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
