"use client";

import { useState, useEffect } from "react";
import {
    Plus,
    Trash2,
    ExternalLink,
    AlertTriangle,
    TrendingUp,
    MessageSquare,
    Target,
    Radio,
    RefreshCw,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useGroup } from "./groupContext";
import { TriangleAlert } from "lucide-react";

// Types
interface RedditSource {
    id: number;
    user_id: number;
    group_id: number | null;
    type: string;
    value: string;
    subreddit: string | null;
    enabled: boolean;
    created_at: string;
}

interface RedditItem {
    id: number;
    source_id: number;
    subreddit: string;
    external_id: string;
    external_url: string;
    title: string;
    body: string;
    author: string;
    score: number;
    num_comments: number;
    created_utc: string;
    quality_score: number;
}

interface StrategyCard {
    id: number;
    source: string;
    item_id: number;
    platform_targets: string[];
    niche: string;
    tactic: string;
    steps: any;
    confidence: number;
    created_at: string;
}

interface RedditAlert {
    id: number;
    source_id: number;
    window_start: string;
    window_end: string;
    metric: string;
    current_value: number;
    previous_value: number;
    factor: number;
    created_at: string;
}

export function RedditPage() {
    const { activeGroup } = useGroup();
    const [activeTab, setActiveTab] = useState("sources");
    const [sources, setSources] = useState<RedditSource[]>([]);
    const [items, setItems] = useState<RedditItem[]>([]);
    const [cards, setCards] = useState<StrategyCard[]>([]);
    const [alerts, setAlerts] = useState<RedditAlert[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    // Add source form
    const [sourceType, setSourceType] = useState<"subreddit" | "keyword">("subreddit");
    const [sourceValue, setSourceValue] = useState("");
    const [sourceSubreddit, setSourceSubreddit] = useState("");
    const [isAdding, setIsAdding] = useState(false);

    const getAuthHeaders = () => ({
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
    });

    // Fetch sources
    const fetchSources = async () => {
        if (!activeGroup?.ID) return;
        try {
            const res = await fetch(`/api/reddit/sources?group_id=${activeGroup.ID}`, {
                headers: getAuthHeaders(),
            });
            if (res.ok) {
                const data = await res.json();
                setSources(Array.isArray(data) ? data : []);
            }
        } catch (err) {
            console.error("Failed to fetch sources:", err);
        }
    };

    // Fetch items
    const fetchItems = async () => {
        if (!activeGroup?.ID) return;
        try {
            const res = await fetch(`/api/reddit/items?group_id=${activeGroup.ID}&limit=50`, {
                headers: getAuthHeaders(),
            });
            if (res.ok) {
                const data = await res.json();
                setItems(Array.isArray(data) ? data : []);
            }
        } catch (err) {
            console.error("Failed to fetch items:", err);
        }
    };

    // Fetch strategy cards
    const fetchCards = async () => {
        if (!activeGroup?.ID) return;
        try {
            const res = await fetch(`/api/reddit/cards?group_id=${activeGroup.ID}&limit=50`, {
                headers: getAuthHeaders(),
            });
            if (res.ok) {
                const data = await res.json();
                setCards(Array.isArray(data) ? data : []);
            }
        } catch (err) {
            console.error("Failed to fetch cards:", err);
        }
    };

    // Fetch alerts
    const fetchAlerts = async () => {
        if (!activeGroup?.ID) return;
        try {
            const res = await fetch(`/api/reddit/alerts?group_id=${activeGroup.ID}&limit=50`, {
                headers: getAuthHeaders(),
            });
            if (res.ok) {
                const data = await res.json();
                setAlerts(Array.isArray(data) ? data : []);
            }
        } catch (err) {
            console.error("Failed to fetch alerts:", err);
        }
    };

    // Add source
    const handleAddSource = async () => {
        if (!sourceValue.trim()) return;
        setIsAdding(true);

        try {
            const res = await fetch("/api/reddit/sources", {
                method: "POST",
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    group_id: activeGroup?.ID,
                    type: sourceType,
                    value: sourceValue.toLowerCase().trim(),
                    subreddit: sourceType === "keyword" && sourceSubreddit ? sourceSubreddit.toLowerCase().trim() : null,
                }),
            });

            if (res.ok) {
                setSourceValue("");
                setSourceSubreddit("");
                fetchSources();
            } else {
                const err = await res.json();
                alert(err.error || "Failed to add source");
            }
        } catch (err) {
            console.error("Failed to add source:", err);
        } finally {
            setIsAdding(false);
        }
    };

    // Delete source
    const handleDeleteSource = async (id: number) => {
        if (!confirm("Are you sure you want to delete this source?")) return;

        try {
            const res = await fetch(`/api/reddit/sources/${id}`, {
                method: "DELETE",
                headers: getAuthHeaders(),
            });

            if (res.ok) {
                fetchSources();
            }
        } catch (err) {
            console.error("Failed to delete source:", err);
        }
    };

    // Refresh all data
    const refreshAll = async () => {
        setIsLoading(true);
        await Promise.all([fetchSources(), fetchItems(), fetchCards(), fetchAlerts()]);
        setIsLoading(false);
    };

    useEffect(() => {
        if (activeGroup?.ID) {
            refreshAll();
        }
    }, [activeGroup]);

    if (!activeGroup) {
        return (
            <div className="flex justify-center w-full h-[45px] text-center">
                <div className="flex gap-2 p-2 border border-red-500 border-dashed">
                    <div className="w-[30px] h-[30px] flex justify-center items-center rounded-lg">
                        <TriangleAlert className="text-yellow-400" />
                    </div>
                    <h1 className="font-semibold">Please select a group to continue</h1>
                </div>
            </div>
        );
    }

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    return (
        <div className="flex-1 pt-6 space-y-4">
            <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">Reddit Insights</h2>
                    <p className="text-muted-foreground">Monitor subreddits and keywords for marketing tactics</p>
                </div>
                <Button variant="outline" onClick={refreshAll} disabled={isLoading} className="gap-2">
                    <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
                    Refresh
                </Button>
            </div>

            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-orange-500/20">
                                <Radio className="w-5 h-5 text-orange-400" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">{sources.length}</p>
                                <p className="text-xs text-muted-foreground">Active Sources</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-blue-500/20">
                                <MessageSquare className="w-5 h-5 text-blue-400" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">{items.length}</p>
                                <p className="text-xs text-muted-foreground">Reddit Posts</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-purple-500/20">
                                <Target className="w-5 h-5 text-purple-400" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">{cards.length}</p>
                                <p className="text-xs text-muted-foreground">Strategy Cards</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-amber-500/20">
                                <TrendingUp className="w-5 h-5 text-amber-400" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">{alerts.length}</p>
                                <p className="text-xs text-muted-foreground">Spike Alerts</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="bg-zinc-800">
                    <TabsTrigger value="sources" className="data-[state=active]:bg-zinc-700">
                        Sources
                    </TabsTrigger>
                    <TabsTrigger value="items" className="data-[state=active]:bg-zinc-700">
                        Reddit Posts
                    </TabsTrigger>
                    <TabsTrigger value="cards" className="data-[state=active]:bg-zinc-700">
                        Strategy Cards
                    </TabsTrigger>
                    <TabsTrigger value="alerts" className="data-[state=active]:bg-zinc-700">
                        Alerts
                    </TabsTrigger>
                </TabsList>

                {/* Sources Tab */}
                <TabsContent value="sources" className="mt-4">
                    <Card className="bg-zinc-900/50 border-zinc-800">
                        <CardHeader>
                            <CardTitle>Manage Sources</CardTitle>
                            <CardDescription>Add subreddits or keywords to monitor</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {/* Add Source Form */}
                            <div className="flex flex-wrap gap-3 p-4 rounded-lg bg-zinc-800/50">
                                <Select value={sourceType} onValueChange={(v: "subreddit" | "keyword") => setSourceType(v)}>
                                    <SelectTrigger className="w-[140px] bg-zinc-900 border-zinc-700">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="subreddit">Subreddit</SelectItem>
                                        <SelectItem value="keyword">Keyword</SelectItem>
                                    </SelectContent>
                                </Select>
                                <Input
                                    placeholder={sourceType === "subreddit" ? "e.g., marketing" : "e.g., indie game marketing"}
                                    value={sourceValue}
                                    onChange={(e) => setSourceValue(e.target.value)}
                                    className="flex-1 min-w-[200px] bg-zinc-900 border-zinc-700"
                                />
                                {sourceType === "keyword" && (
                                    <Input
                                        placeholder="Limit to subreddit (optional)"
                                        value={sourceSubreddit}
                                        onChange={(e) => setSourceSubreddit(e.target.value)}
                                        className="w-[200px] bg-zinc-900 border-zinc-700"
                                    />
                                )}
                                <Button onClick={handleAddSource} disabled={isAdding || !sourceValue.trim()}>
                                    <Plus className="w-4 h-4 mr-2" />
                                    Add Source
                                </Button>
                            </div>

                            {/* Sources List */}
                            <div className="space-y-2">
                                {sources.length === 0 ? (
                                    <div className="py-8 text-center text-muted-foreground">
                                        No sources added yet. Add a subreddit or keyword to start monitoring.
                                    </div>
                                ) : (
                                    sources.map((source) => (
                                        <div
                                            key={source.id}
                                            className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50"
                                        >
                                            <div className="flex items-center gap-3">
                                                <Badge variant="outline" className="capitalize">
                                                    {source.type}
                                                </Badge>
                                                <span className="font-medium">
                                                    {source.type === "subreddit" ? `r/${source.value}` : `"${source.value}"`}
                                                </span>
                                                {source.subreddit && (
                                                    <span className="text-sm text-muted-foreground">
                                                        in r/{source.subreddit}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs text-muted-foreground">
                                                    Added {formatDate(source.created_at)}
                                                </span>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => handleDeleteSource(source.id)}
                                                    className="text-red-400 hover:text-red-300 hover:bg-red-500/20"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Items Tab */}
                <TabsContent value="items" className="mt-4">
                    <Card className="bg-zinc-900/50 border-zinc-800">
                        <CardHeader>
                            <CardTitle>Reddit Posts</CardTitle>
                            <CardDescription>Posts fetched from your monitored sources</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {items.length === 0 ? (
                                <div className="py-8 text-center text-muted-foreground">
                                    No posts fetched yet. Add sources and run the scraper to collect data.
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {items.map((item) => (
                                        <div key={item.id} className="p-4 rounded-lg bg-zinc-800/50">
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <Badge variant="outline" className="text-xs">
                                                            r/{item.subreddit}
                                                        </Badge>
                                                        <span className="text-xs text-muted-foreground">
                                                            by u/{item.author}
                                                        </span>
                                                    </div>
                                                    <h4 className="font-medium line-clamp-2">{item.title}</h4>
                                                    {item.body && (
                                                        <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                                                            {item.body}
                                                        </p>
                                                    )}
                                                </div>
                                                <div className="flex flex-col items-end gap-1 text-sm">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-orange-400">↑{item.score}</span>
                                                        <span className="text-blue-400">💬{item.num_comments}</span>
                                                    </div>
                                                    <a
                                                        href={item.external_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="flex items-center gap-1 text-xs text-blue-400 hover:underline"
                                                    >
                                                        <ExternalLink className="w-3 h-3" />
                                                        View
                                                    </a>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Strategy Cards Tab */}
                <TabsContent value="cards" className="mt-4">
                    <Card className="bg-zinc-900/50 border-zinc-800">
                        <CardHeader>
                            <CardTitle>Strategy Cards</CardTitle>
                            <CardDescription>Marketing tactics extracted from Reddit discussions</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {cards.length === 0 ? (
                                <div className="py-8 text-center text-muted-foreground">
                                    No strategy cards yet. Enable LLM extraction to generate tactics.
                                </div>
                            ) : (
                                <div className="grid gap-4 md:grid-cols-2">
                                    {cards.map((card) => (
                                        <div key={card.id} className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700">
                                            <div className="flex items-start justify-between mb-2">
                                                <Badge variant="outline" className="text-xs">
                                                    {card.niche || "General"}
                                                </Badge>
                                                <span className="text-xs text-emerald-400">
                                                    {(card.confidence * 100).toFixed(0)}% confidence
                                                </span>
                                            </div>
                                            <h4 className="font-medium mb-2">{card.tactic}</h4>
                                            {card.platform_targets && card.platform_targets.length > 0 && (
                                                <div className="flex gap-1 flex-wrap">
                                                    {card.platform_targets.map((p, i) => (
                                                        <Badge key={i} className="text-xs bg-purple-500/20 text-purple-400">
                                                            {p}
                                                        </Badge>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Alerts Tab */}
                <TabsContent value="alerts" className="mt-4">
                    <Card className="bg-zinc-900/50 border-zinc-800">
                        <CardHeader>
                            <CardTitle>Spike Alerts</CardTitle>
                            <CardDescription>Volume spikes detected in your monitored sources</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {alerts.length === 0 ? (
                                <div className="py-8 text-center text-muted-foreground">
                                    No alerts yet. Alerts appear when activity doubles in a 24-hour period.
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {alerts.map((alert) => (
                                        <div key={alert.id} className="flex items-center gap-4 p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
                                            <AlertTriangle className="w-5 h-5 text-amber-400" />
                                            <div className="flex-1">
                                                <p className="font-medium">
                                                    {alert.metric} spiked by {alert.factor.toFixed(1)}x
                                                </p>
                                                <p className="text-sm text-muted-foreground">
                                                    {alert.previous_value.toFixed(0)} → {alert.current_value.toFixed(0)}
                                                </p>
                                            </div>
                                            <span className="text-xs text-muted-foreground">
                                                {formatDate(alert.created_at)}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}

export default RedditPage;
