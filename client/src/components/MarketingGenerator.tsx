
import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Loader2, Sparkles, TrendingUp, Calendar, Hash, Zap } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useGroup } from "./groupContext";
import { NoGroupWarning } from "@/components/NoGroupWarning";

interface MarketingStrategyResponse {
    content: string;
    best_posting_day: string;
    posts_per_week: number;
    top_hook?: string;
    top_hashtags?: string[];
    tokens_used_estimate: number;
    data_source: string;
    data_window_days: number;
}

export function MarketingGenerator() {
    const { activeGroup } = useGroup();
    const [platform, setPlatform] = useState("Instagram");
    const [campaignType, setCampaignType] = useState("Teaser");
    const [taskType, setTaskType] = useState("Strategy"); // Strategy or "Script Writing"
    const [customPrompt, setCustomPrompt] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<MarketingStrategyResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleGenerate = async () => {
        if (!activeGroup?.ID) {
            setError("Please select a group first.");
            return;
        }

        setIsLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch('/api/marketing/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    group_id: activeGroup.ID,
                    task_type: taskType,
                    campaign_type: campaignType,
                    platform: platform,
                    custom_prompt: customPrompt,
                }),
            });

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(`Generation failed: ${errText}`);
            }

            const data = await response.json();
            setResult(data);
        } catch (err: any) {
            setError(err.message || "An error occurred");
        } finally {
            setIsLoading(false);
        }
    };

    if (!activeGroup) {
        return <NoGroupWarning featureName="Marketing Generator" />;
    }

    return (
        <div className="flex flex-col gap-6 h-full overflow-y-auto p-1">
            <Card className="bg-card/95 backdrop-blur-sm border-2 shadow-sm">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-primary" />
                        Viral Strategy Generator
                    </CardTitle>
                    <CardDescription>
                        Generate algorithm-optimized content strategies {activeGroup ? `for ${activeGroup.name}` : ''} based on competitor data.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2">
                            <Label>Task Type</Label>
                            <Select value={taskType} onValueChange={setTaskType}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Strategy">Campaign Strategy</SelectItem>
                                    <SelectItem value="Script Writing">Content Script</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>Platform</Label>
                            <Select value={platform} onValueChange={setPlatform}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Instagram">Instagram</SelectItem>
                                    <SelectItem value="TikTok">TikTok</SelectItem>
                                    <SelectItem value="Twitter">Twitter / X</SelectItem>
                                    <SelectItem value="YouTube">YouTube Shorts</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>Campaign Phase</Label>
                            <Select value={campaignType} onValueChange={setCampaignType}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Teaser">Teaser (Pre-launch)</SelectItem>
                                    <SelectItem value="Launch">Launch Day</SelectItem>
                                    <SelectItem value="Update">Major Update</SelectItem>
                                    <SelectItem value="Community">Community Engagement</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label>Additional Context (Optional)</Label>
                        <Textarea
                            placeholder="E.g., Focus on our new multiplayer mode..."
                            value={customPrompt}
                            onChange={(e) => setCustomPrompt(e.target.value)}
                            className="resize-none"
                        />
                    </div>
                </CardContent>
                <CardFooter>
                    <Button onClick={handleGenerate} disabled={isLoading || !activeGroup} className="w-full md:w-auto">
                        {isLoading ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Analyzing Competitors...
                            </>
                        ) : (
                            <>
                                <Zap className="mr-2 h-4 w-4 fill-yellow-400 text-yellow-500" />
                                Generate Optimized Strategy
                            </>
                        )}
                    </Button>
                </CardFooter>
            </Card>

            {error && (
                <div className="p-4 rounded-md bg-red-500/10 border border-red-500/20 text-red-500">
                    {error}
                </div>
            )}

            {result && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {/* Algorithm Insights Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <Card className="bg-gradient-to-br from-green-500/10 to-transparent border-green-500/20">
                            <CardHeader className="p-4 pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                                    <Calendar className="h-4 w-4 text-green-500" /> Best Day to Post
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-4 pt-0">
                                <div className="text-2xl font-bold text-green-500">{result.best_posting_day}</div>
                                <p className="text-xs text-muted-foreground mt-1">
                                    Based on {result.data_window_days} days of data
                                </p>
                            </CardContent>
                        </Card>

                        <Card className="bg-gradient-to-br from-blue-500/10 to-transparent border-blue-500/20">
                            <CardHeader className="p-4 pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                                    <TrendingUp className="h-4 w-4 text-blue-500" /> Competitor Cadence
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-4 pt-0">
                                <div className="text-2xl font-bold text-blue-500">{result.posts_per_week.toFixed(1)} <span className="text-sm font-normal text-muted-foreground">posts/week</span></div>
                                <p className="text-xs text-muted-foreground mt-1">
                                    Recommended frequency
                                </p>
                            </CardContent>
                        </Card>

                        <Card className="bg-gradient-to-br from-purple-500/10 to-transparent border-purple-500/20 col-span-1 md:col-span-2">
                            <CardHeader className="p-4 pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                                    <Hash className="h-4 w-4 text-purple-500" /> Trending Hashtags
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-4 pt-0">
                                <div className="flex flex-wrap gap-2">
                                    {result.top_hashtags && result.top_hashtags.length > 0 ? (
                                        result.top_hashtags.map(tag => (
                                            <Badge key={tag} variant="secondary" className="bg-purple-500/10 text-purple-400 hover:bg-purple-500/20">
                                                #{tag}
                                            </Badge>
                                        ))
                                    ) : (
                                        <span className="text-sm text-muted-foreground">No trending tags found for this niche yet.</span>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Main Content Output */}
                    <Card className="border-2 bg-card/50">
                        <CardHeader>
                            <CardTitle>Generated Strategy</CardTitle>
                            <CardDescription>AI-generated plan based on your game's context and market trends.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="prose prose-invert max-w-none">
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                        h1: ({ node, ...props }) => <h1 className="text-2xl font-bold text-primary mt-6 mb-4 pb-2 border-b border-white/10" {...props} />,
                                        h2: ({ node, ...props }) => <h2 className="text-xl font-semibold text-foreground mt-6 mb-3" {...props} />,
                                        h3: ({ node, ...props }) => <h3 className="text-lg font-medium text-foreground/90 mt-4 mb-2" {...props} />,
                                        ul: ({ node, ...props }) => <ul className="list-disc pl-6 space-y-2 mb-4" {...props} />,
                                        ol: ({ node, ...props }) => <ol className="list-decimal pl-6 space-y-2 mb-4" {...props} />,
                                        li: ({ node, ...props }) => <li className="text-muted-foreground" {...props} />,
                                        p: ({ node, ...props }) => <p className="leading-relaxed mb-4 text-muted-foreground" {...props} />,
                                        strong: ({ node, ...props }) => <strong className="font-semibold text-foreground" {...props} />,
                                        blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-primary/50 pl-4 italic text-muted-foreground my-4" {...props} />,
                                    }}
                                >
                                    {result.content}
                                </ReactMarkdown>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Hook Analysis if available */}
                    {result.top_hook && (
                        <Card className="bg-amber-500/5 border-amber-500/20">
                            <CardHeader>
                                <CardTitle className="text-base flex items-center gap-2">
                                    <Zap className="h-4 w-4 text-amber-500" />
                                    Top Performing Hook Pattern
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="italic text-amber-200/80">"{result.top_hook}"</p>
                                <p className="text-xs text-muted-foreground mt-2">
                                    This hook style is currently driving high engagement for competitors.
                                </p>
                            </CardContent>
                        </Card>
                    )}

                </div>
            )}
        </div>
    );
}
