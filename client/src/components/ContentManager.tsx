"use client";

import * as React from "react";
import { useState, useEffect, useMemo } from "react";
import {
    Loader2, Upload, X, Check, Clock, AlertCircle,
    Sparkles, Calendar, RefreshCw, Eye, Edit2, Filter,
    ArrowUpDown, MoreHorizontal, Play, Pause, Trash2,
    Instagram, Video, Image, Search, ChevronDown, CalendarClock
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
import { Badge } from "@/components/ui/badge";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
} from "@/components/ui/tabs";
import { toast } from "@/hooks/use-toast";
import { useGroup } from "@/components/groupContext";
import { cn } from "@/lib/utils";

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

// Job status types
type JobStatus =
    | "queued"
    | "generating"
    | "needs_review"
    | "scheduled"
    | "posting"
    | "posted"
    | "failed"
    | "canceled"
    | "needs_reauth";

interface UploadJob {
    id: string;
    platform: string;
    status: JobStatus;
    ai_title: string | null;
    ai_hook: string | null;
    ai_hashtags: string[] | null;
    scheduled_date: string | null;
    error_message: string | null;
    created_at: string;
    updated_at: string;
}

const statusConfig: Record<JobStatus, { label: string; icon: React.ReactNode; color: string; bgColor: string }> = {
    queued: { label: "Queued", icon: <Clock className="h-4 w-4" />, color: "text-gray-400", bgColor: "bg-gray-500/20" },
    generating: { label: "AI Generating", icon: <Sparkles className="h-4 w-4 animate-pulse" />, color: "text-blue-400", bgColor: "bg-blue-500/20" },
    needs_review: { label: "Needs Review", icon: <Eye className="h-4 w-4" />, color: "text-yellow-400", bgColor: "bg-yellow-500/20" },
    scheduled: { label: "Scheduled", icon: <Calendar className="h-4 w-4" />, color: "text-purple-400", bgColor: "bg-purple-500/20" },
    posting: { label: "Posting", icon: <Loader2 className="h-4 w-4 animate-spin" />, color: "text-indigo-400", bgColor: "bg-indigo-500/20" },
    posted: { label: "Posted", icon: <Check className="h-4 w-4" />, color: "text-green-400", bgColor: "bg-green-500/20" },
    failed: { label: "Failed", icon: <AlertCircle className="h-4 w-4" />, color: "text-red-400", bgColor: "bg-red-500/20" },
    canceled: { label: "Canceled", icon: <X className="h-4 w-4" />, color: "text-gray-400", bgColor: "bg-gray-500/20" },
    needs_reauth: { label: "Re-auth Needed", icon: <AlertCircle className="h-4 w-4" />, color: "text-orange-400", bgColor: "bg-orange-500/20" },
};

export function ContentManager() {
    const { activeGroup } = useGroup();
    const groupId = activeGroup?.ID;

    // State
    const [jobs, setJobs] = useState<UploadJob[]>([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [platform, setPlatform] = useState<string>("instagram");
    const [reviewJob, setReviewJob] = useState<UploadJob | null>(null);
    const [editCaption, setEditCaption] = useState("");
    const [editHashtags, setEditHashtags] = useState("");
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState<string>("all");
    const [activeTab, setActiveTab] = useState("all");
    const [showUploadDialog, setShowUploadDialog] = useState(false);

    // Fetch jobs
    const fetchJobs = async () => {
        if (!groupId) return;
        setLoading(true);
        try {
            const token = localStorage.getItem("token");
            const response = await fetch(`${API_URL}/api/uploads/pending?group_id=${groupId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (response.ok) {
                const data = await response.json();
                setJobs(data.jobs || []);
            }
        } catch (error) {
            console.error("Failed to fetch jobs:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchJobs();
        const interval = setInterval(fetchJobs, 10000);
        return () => clearInterval(interval);
    }, [groupId]);

    // Stats
    const stats = useMemo(() => {
        const total = jobs.length;
        const pending = jobs.filter(j => ['queued', 'generating', 'needs_review'].includes(j.status)).length;
        const scheduled = jobs.filter(j => j.status === 'scheduled').length;
        const posted = jobs.filter(j => j.status === 'posted').length;
        const failed = jobs.filter(j => j.status === 'failed').length;
        return { total, pending, scheduled, posted, failed };
    }, [jobs]);

    // Filtered jobs
    const filteredJobs = useMemo(() => {
        let result = jobs;

        // Tab filter
        if (activeTab !== "all") {
            if (activeTab === "pending") {
                result = result.filter(j => ['queued', 'generating', 'needs_review'].includes(j.status));
            } else if (activeTab === "scheduled") {
                result = result.filter(j => j.status === 'scheduled');
            } else if (activeTab === "completed") {
                result = result.filter(j => ['posted', 'failed', 'canceled'].includes(j.status));
            }
        }

        // Status filter
        if (statusFilter !== "all") {
            result = result.filter(j => j.status === statusFilter);
        }

        // Search
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            result = result.filter(j =>
                j.platform.toLowerCase().includes(query) ||
                j.ai_title?.toLowerCase().includes(query) ||
                j.ai_hook?.toLowerCase().includes(query) ||
                j.ai_hashtags?.some(h => h.toLowerCase().includes(query))
            );
        }

        return result;
    }, [jobs, activeTab, statusFilter, searchQuery]);

    // Upload handler
    const handleUpload = async () => {
        if (!selectedFile || !groupId) return;
        setUploading(true);
        try {
            const token = localStorage.getItem("token");
            const formData = new FormData();
            formData.append("file", selectedFile);
            formData.append("platform", platform);
            formData.append("group_id", groupId.toString());
            // Note: user_id is derived from JWT token on server, not sent by client

            const response = await fetch(`${API_URL}/api/upload`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                body: formData,
            });

            if (response.ok) {
                toast({ title: "Upload Started", description: "AI is generating your caption..." });
                setSelectedFile(null);
                setShowUploadDialog(false);
                fetchJobs();
            } else {
                throw new Error("Upload failed");
            }
        } catch (error) {
            toast({ title: "Upload Failed", description: "Please try again.", variant: "destructive" });
        } finally {
            setUploading(false);
        }
    };

    // Approve handler
    const handleApprove = async (jobId: string) => {
        try {
            const token = localStorage.getItem("token");
            const response = await fetch(`${API_URL}/api/uploads/${jobId}/approve`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
                body: JSON.stringify({ caption: editCaption, hashtags: editHashtags.split(",").map(h => h.trim()) }),
            });
            if (response.ok) {
                toast({ title: "Scheduled!", description: "Your post will be published at the optimal time." });
                setReviewJob(null);
                fetchJobs();
            }
        } catch (error) {
            toast({ title: "Failed to schedule", variant: "destructive" });
        }
    };

    // Cancel handler
    const handleCancel = async (jobId: string) => {
        try {
            const token = localStorage.getItem("token");
            await fetch(`${API_URL}/api/uploads/${jobId}/cancel`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
            });
            fetchJobs();
            toast({ title: "Canceled", description: "Upload job has been canceled." });
        } catch (error) {
            console.error("Failed to cancel:", error);
        }
    };

    // Open review
    const openReview = (job: UploadJob) => {
        setReviewJob(job);
        setEditCaption(job.ai_title || "");
        setEditHashtags((job.ai_hashtags || []).join(", "));
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white">Content Manager</h1>
                    <p className="text-gray-400 mt-1">Manage your scheduled posts and uploads</p>
                </div>
                <Button onClick={() => setShowUploadDialog(true)} className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700">
                    <Upload className="h-4 w-4 mr-2" />
                    New Upload
                </Button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <Card className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-blue-500/20"><Video className="h-5 w-5 text-blue-400" /></div>
                            <div>
                                <p className="text-2xl font-bold text-white">{stats.total}</p>
                                <p className="text-xs text-gray-400">Total</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-yellow-500/20"><Clock className="h-5 w-5 text-yellow-400" /></div>
                            <div>
                                <p className="text-2xl font-bold text-white">{stats.pending}</p>
                                <p className="text-xs text-gray-400">Pending</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-purple-500/20"><CalendarClock className="h-5 w-5 text-purple-400" /></div>
                            <div>
                                <p className="text-2xl font-bold text-white">{stats.scheduled}</p>
                                <p className="text-xs text-gray-400">Scheduled</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-green-500/20"><Check className="h-5 w-5 text-green-400" /></div>
                            <div>
                                <p className="text-2xl font-bold text-white">{stats.posted}</p>
                                <p className="text-xs text-gray-400">Posted</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-red-500/20"><AlertCircle className="h-5 w-5 text-red-400" /></div>
                            <div>
                                <p className="text-2xl font-bold text-white">{stats.failed}</p>
                                <p className="text-xs text-gray-400">Failed</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Filters & Tabs */}
            <Card className="bg-gray-900/50 border-gray-700">
                <CardHeader className="pb-4">
                    <div className="flex flex-col md:flex-row md:items-center gap-4">
                        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
                            <TabsList className="bg-gray-800">
                                <TabsTrigger value="all" className="data-[state=active]:bg-gray-700">All</TabsTrigger>
                                <TabsTrigger value="pending" className="data-[state=active]:bg-gray-700">Pending</TabsTrigger>
                                <TabsTrigger value="scheduled" className="data-[state=active]:bg-gray-700">Scheduled</TabsTrigger>
                                <TabsTrigger value="completed" className="data-[state=active]:bg-gray-700">Completed</TabsTrigger>
                            </TabsList>
                        </Tabs>
                        <div className="flex items-center gap-2">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
                                <Input
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-9 bg-gray-800 border-gray-600 text-white w-48"
                                />
                            </div>
                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                <SelectTrigger className="w-36 bg-gray-800 border-gray-600 text-white">
                                    <Filter className="h-4 w-4 mr-2" />
                                    <SelectValue placeholder="Status" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Status</SelectItem>
                                    {Object.entries(statusConfig).map(([key, { label }]) => (
                                        <SelectItem key={key} value={key}>{label}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <Button variant="ghost" size="icon" onClick={fetchJobs}>
                                <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                            </Button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    {filteredJobs.length === 0 ? (
                        <div className="text-center py-12">
                            <Video className="h-12 w-12 mx-auto text-gray-600 mb-4" />
                            <p className="text-gray-500">No uploads found</p>
                            <Button onClick={() => setShowUploadDialog(true)} className="mt-4" variant="outline">
                                <Upload className="h-4 w-4 mr-2" /> Upload Content
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {filteredJobs.map((job) => (
                                <div key={job.id} className="flex items-center justify-between p-4 rounded-xl bg-gray-800/50 border border-gray-700/50 hover:border-gray-600 transition-all">
                                    <div className="flex items-center gap-4">
                                        {/* Platform Icon */}
                                        <div className={cn("p-3 rounded-xl", statusConfig[job.status].bgColor)}>
                                            {job.platform.toLowerCase() === 'instagram' ? (
                                                <Instagram className={cn("h-6 w-6", statusConfig[job.status].color)} />
                                            ) : (
                                                <Video className={cn("h-6 w-6", statusConfig[job.status].color)} />
                                            )}
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <Badge className={cn("text-xs", statusConfig[job.status].bgColor, statusConfig[job.status].color)}>
                                                    {statusConfig[job.status].icon}
                                                    <span className="ml-1">{statusConfig[job.status].label}</span>
                                                </Badge>
                                                <span className="text-xs text-gray-500 capitalize">{job.platform}</span>
                                            </div>
                                            <p className="font-medium text-white truncate max-w-md">
                                                {job.ai_hook || job.ai_title || "Processing..."}
                                            </p>
                                            <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                                                {job.scheduled_date && (
                                                    <span className="flex items-center gap-1">
                                                        <Calendar className="h-3 w-3" />
                                                        {format(new Date(job.scheduled_date), "MMM d 'at' h:mm a")}
                                                    </span>
                                                )}
                                                <span>Created {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}</span>
                                            </div>
                                            {job.ai_hashtags && job.ai_hashtags.length > 0 && (
                                                <div className="flex gap-1 mt-2 flex-wrap">
                                                    {job.ai_hashtags.slice(0, 4).map((tag, i) => (
                                                        <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-gray-700/50 text-gray-400">
                                                            #{tag}
                                                        </span>
                                                    ))}
                                                    {job.ai_hashtags.length > 4 && (
                                                        <span className="text-xs text-gray-500">+{job.ai_hashtags.length - 4}</span>
                                                    )}
                                                </div>
                                            )}
                                            {job.error_message && (
                                                <p className="text-xs text-red-400 mt-1">{job.error_message}</p>
                                            )}
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex items-center gap-2">
                                        {job.status === "needs_review" && (
                                            <Button size="sm" onClick={() => openReview(job)} className="bg-yellow-600 hover:bg-yellow-700">
                                                <Edit2 className="h-4 w-4 mr-1" /> Review
                                            </Button>
                                        )}
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="icon">
                                                    <MoreHorizontal className="h-4 w-4" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end" className="bg-gray-800 border-gray-700">
                                                {job.status === "needs_review" && (
                                                    <DropdownMenuItem onClick={() => openReview(job)} className="text-white">
                                                        <Edit2 className="h-4 w-4 mr-2" /> Review & Approve
                                                    </DropdownMenuItem>
                                                )}
                                                {["queued", "scheduled", "needs_review"].includes(job.status) && (
                                                    <>
                                                        <DropdownMenuSeparator className="bg-gray-700" />
                                                        <DropdownMenuItem onClick={() => handleCancel(job.id)} className="text-red-400">
                                                            <Trash2 className="h-4 w-4 mr-2" /> Cancel
                                                        </DropdownMenuItem>
                                                    </>
                                                )}
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Upload Dialog */}
            <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
                <DialogContent className="bg-gray-900 border-gray-700 max-w-lg">
                    <DialogHeader>
                        <DialogTitle className="text-white flex items-center gap-2">
                            <Sparkles className="h-5 w-5 text-purple-400" />
                            AI-Powered Upload
                        </DialogTitle>
                        <DialogDescription className="text-gray-400">
                            Upload your video and AI will generate the perfect caption
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4">
                        <div
                            className={cn(
                                "border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer",
                                selectedFile ? "border-purple-500 bg-purple-500/10" : "border-gray-600 hover:border-purple-500/50"
                            )}
                            onClick={() => document.getElementById('file-upload')?.click()}
                        >
                            {selectedFile ? (
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <Video className="h-8 w-8 text-purple-400" />
                                        <div className="text-left">
                                            <p className="text-sm font-medium text-white">{selectedFile.name}</p>
                                            <p className="text-xs text-gray-400">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                                        </div>
                                    </div>
                                    <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}>
                                        <X className="h-4 w-4" />
                                    </Button>
                                </div>
                            ) : (
                                <>
                                    <Upload className="h-10 w-10 mx-auto text-gray-500 mb-3" />
                                    <p className="text-gray-400 mb-1">Drop your video here or click to browse</p>
                                    <p className="text-xs text-gray-500">MP4, MOV, AVI up to 100MB</p>
                                </>
                            )}
                            <input
                                id="file-upload"
                                type="file"
                                accept="video/*,image/*"
                                className="hidden"
                                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                            />
                        </div>

                        <div>
                            <Label className="text-gray-300">Platform</Label>
                            <Select value={platform} onValueChange={setPlatform}>
                                <SelectTrigger className="bg-gray-800 border-gray-600 text-white mt-1">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="instagram">
                                        <div className="flex items-center gap-2">
                                            <Instagram className="h-4 w-4" /> Instagram
                                        </div>
                                    </SelectItem>
                                    <SelectItem value="tiktok">
                                        <div className="flex items-center gap-2">
                                            <Video className="h-4 w-4" /> TikTok
                                        </div>
                                    </SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="ghost" onClick={() => setShowUploadDialog(false)}>Cancel</Button>
                        <Button onClick={handleUpload} disabled={!selectedFile || uploading} className="bg-purple-600 hover:bg-purple-700">
                            {uploading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}
                            Generate & Schedule
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Review Dialog */}
            <Dialog open={!!reviewJob} onOpenChange={() => setReviewJob(null)}>
                <DialogContent className="bg-gray-900 border-gray-700 max-w-lg">
                    <DialogHeader>
                        <DialogTitle className="text-white">Review AI Content</DialogTitle>
                        <DialogDescription className="text-gray-400">
                            Review and edit the AI-generated caption before scheduling
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4">
                        <div>
                            <Label className="text-gray-300">Caption</Label>
                            <Textarea
                                value={editCaption}
                                onChange={(e) => setEditCaption(e.target.value)}
                                className="bg-gray-800 border-gray-600 text-white min-h-[120px] mt-1"
                            />
                        </div>
                        <div>
                            <Label className="text-gray-300">Hashtags (comma-separated)</Label>
                            <Input
                                value={editHashtags}
                                onChange={(e) => setEditHashtags(e.target.value)}
                                className="bg-gray-800 border-gray-600 text-white mt-1"
                                placeholder="gaming, indiedev, gamedev"
                            />
                        </div>
                        {reviewJob?.scheduled_date && (
                            <div className="flex items-center gap-2 p-3 rounded-lg bg-purple-500/10 border border-purple-500/30">
                                <CalendarClock className="h-5 w-5 text-purple-400" />
                                <div>
                                    <p className="text-sm font-medium text-white">Scheduled Time</p>
                                    <p className="text-xs text-gray-400">
                                        {format(new Date(reviewJob.scheduled_date), "EEEE, MMMM d 'at' h:mm a")}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>

                    <DialogFooter className="gap-2">
                        <Button variant="ghost" onClick={() => setReviewJob(null)}>Cancel</Button>
                        <Button onClick={() => reviewJob && handleApprove(reviewJob.id)} className="bg-green-600 hover:bg-green-700">
                            <Check className="h-4 w-4 mr-1" /> Approve & Schedule
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}

export default ContentManager;
