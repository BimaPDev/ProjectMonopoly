"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import {
    Loader2, Upload, X, Info, Check, Clock, AlertCircle,
    Sparkles, Calendar, RefreshCw, Eye, Edit2
} from "lucide-react";
import { format } from "date-fns";

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
// Progress component available if needed
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "@/hooks/use-toast";
import { useGroup } from "@/components/groupContext";

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

// Job status types matching backend state machine
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

const statusConfig: Record<JobStatus, { label: string; icon: React.ReactNode; color: string }> = {
    queued: { label: "Queued", icon: <Clock className="h-4 w-4" />, color: "bg-gray-500" },
    generating: { label: "AI Generating...", icon: <Sparkles className="h-4 w-4 animate-pulse" />, color: "bg-blue-500" },
    needs_review: { label: "Needs Review", icon: <Eye className="h-4 w-4" />, color: "bg-yellow-500" },
    scheduled: { label: "Scheduled", icon: <Calendar className="h-4 w-4" />, color: "bg-purple-500" },
    posting: { label: "Posting...", icon: <Loader2 className="h-4 w-4 animate-spin" />, color: "bg-indigo-500" },
    posted: { label: "Posted", icon: <Check className="h-4 w-4" />, color: "bg-green-500" },
    failed: { label: "Failed", icon: <AlertCircle className="h-4 w-4" />, color: "bg-red-500" },
    canceled: { label: "Canceled", icon: <X className="h-4 w-4" />, color: "bg-gray-400" },
    needs_reauth: { label: "Re-auth Needed", icon: <AlertCircle className="h-4 w-4" />, color: "bg-orange-500" },
};

export function UploadScheduler() {
    const { activeGroup } = useGroup();
    const groupId = activeGroup?.ID;
    const [jobs, setJobs] = useState<UploadJob[]>([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [platform, setPlatform] = useState<string>("instagram");
    const [reviewJob, setReviewJob] = useState<UploadJob | null>(null);
    const [editCaption, setEditCaption] = useState("");
    const [editHashtags, setEditHashtags] = useState("");

    // Fetch pending jobs
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
        // Poll every 10 seconds for status updates
        const interval = setInterval(fetchJobs, 10000);
        return () => clearInterval(interval);
    }, [groupId]);

    // Handle file upload
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
                toast({
                    title: "Upload Started",
                    description: "AI is generating your caption. Check back soon!",
                });
                setSelectedFile(null);
                fetchJobs();
            } else {
                throw new Error("Upload failed");
            }
        } catch (error) {
            toast({
                title: "Upload Failed",
                description: "Please try again.",
                variant: "destructive",
            });
        } finally {
            setUploading(false);
        }
    };

    // Approve job for scheduling
    const handleApprove = async (jobId: string) => {
        try {
            const token = localStorage.getItem("token");
            const response = await fetch(`${API_URL}/api/uploads/${jobId}/approve`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    caption: editCaption,
                    hashtags: editHashtags.split(",").map(h => h.trim()),
                }),
            });

            if (response.ok) {
                toast({
                    title: "Scheduled!",
                    description: "Your post will be published at the optimal time.",
                });
                setReviewJob(null);
                fetchJobs();
            }
        } catch (error) {
            toast({
                title: "Failed to schedule",
                description: "Please try again.",
                variant: "destructive",
            });
        }
    };

    // Cancel job
    const handleCancel = async (jobId: string) => {
        try {
            const token = localStorage.getItem("token");
            await fetch(`${API_URL}/api/uploads/${jobId}/cancel`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
            });
            fetchJobs();
        } catch (error) {
            console.error("Failed to cancel:", error);
        }
    };

    // Open review dialog
    const openReview = (job: UploadJob) => {
        setReviewJob(job);
        setEditCaption(job.ai_title || "");
        setEditHashtags((job.ai_hashtags || []).join(", "));
    };

    return (
        <div className="space-y-6">
            {/* Upload Section */}
            <Card className="bg-gradient-to-br from-gray-900 to-gray-800 border-gray-700">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-white">
                        <Sparkles className="h-5 w-5 text-purple-400" />
                        AI-Powered Upload
                    </CardTitle>
                    <CardDescription className="text-gray-400">
                        Upload your video and let AI generate the perfect caption
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* File Drop Zone */}
                    <div
                        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${selectedFile
                            ? "border-purple-500 bg-purple-500/10"
                            : "border-gray-600 hover:border-gray-500"
                            }`}
                    >
                        {selectedFile ? (
                            <div className="flex items-center justify-center gap-4">
                                <div className="text-sm text-gray-300">{selectedFile.name}</div>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setSelectedFile(null)}
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>
                        ) : (
                            <label className="cursor-pointer block">
                                <Upload className="h-10 w-10 mx-auto text-gray-500 mb-2" />
                                <span className="text-gray-400">Drop video here or click to upload</span>
                                <input
                                    type="file"
                                    accept="video/*,image/*"
                                    className="hidden"
                                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                                />
                            </label>
                        )}
                    </div>

                    {/* Platform Selection */}
                    <div className="flex gap-4">
                        <div className="flex-1">
                            <Label className="text-gray-300">Platform</Label>
                            <Select value={platform} onValueChange={setPlatform}>
                                <SelectTrigger className="bg-gray-800 border-gray-600 text-white">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="instagram">Instagram</SelectItem>
                                    <SelectItem value="tiktok">TikTok</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="flex items-end">
                            <Button
                                onClick={handleUpload}
                                disabled={!selectedFile || uploading}
                                className="bg-purple-600 hover:bg-purple-700"
                            >
                                {uploading ? (
                                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                ) : (
                                    <Sparkles className="h-4 w-4 mr-2" />
                                )}
                                Generate & Schedule
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Pending Jobs */}
            <Card className="bg-gray-900/50 border-gray-700">
                <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                        <CardTitle className="text-white">Scheduled Posts</CardTitle>
                        <CardDescription className="text-gray-400">
                            Track your content pipeline
                        </CardDescription>
                    </div>
                    <Button variant="ghost" size="sm" onClick={fetchJobs}>
                        <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                    </Button>
                </CardHeader>
                <CardContent>
                    {jobs.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            No pending posts. Upload a video to get started!
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {jobs.map((job) => (
                                <div
                                    key={job.id}
                                    className="flex items-center justify-between p-4 rounded-lg bg-gray-800/50 border border-gray-700"
                                >
                                    <div className="flex items-center gap-4">
                                        <Badge className={`${statusConfig[job.status].color} text-white`}>
                                            {statusConfig[job.status].icon}
                                            <span className="ml-1">{statusConfig[job.status].label}</span>
                                        </Badge>
                                        <div>
                                            <div className="font-medium text-white">
                                                {job.ai_hook || job.platform}
                                            </div>
                                            {job.scheduled_date && (
                                                <div className="text-sm text-gray-400">
                                                    {format(new Date(job.scheduled_date), "MMM d, yyyy 'at' h:mm a")}
                                                </div>
                                            )}
                                            {job.error_message && (
                                                <div className="text-sm text-red-400">{job.error_message}</div>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        {job.status === "needs_review" && (
                                            <Button
                                                size="sm"
                                                onClick={() => openReview(job)}
                                                className="bg-yellow-600 hover:bg-yellow-700"
                                            >
                                                <Edit2 className="h-4 w-4 mr-1" /> Review
                                            </Button>
                                        )}
                                        {["queued", "scheduled", "needs_review"].includes(job.status) && (
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                onClick={() => handleCancel(job.id)}
                                            >
                                                <X className="h-4 w-4" />
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Review Dialog */}
            <Dialog open={!!reviewJob} onOpenChange={() => setReviewJob(null)}>
                <DialogContent className="bg-gray-900 border-gray-700">
                    <DialogHeader>
                        <DialogTitle className="text-white">Review AI Content</DialogTitle>
                        <DialogDescription className="text-gray-400">
                            Edit the generated caption before scheduling
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4">
                        <div>
                            <Label className="text-gray-300">Caption</Label>
                            <Textarea
                                value={editCaption}
                                onChange={(e) => setEditCaption(e.target.value)}
                                className="bg-gray-800 border-gray-600 text-white min-h-[100px]"
                            />
                        </div>
                        <div>
                            <Label className="text-gray-300">Hashtags (comma-separated)</Label>
                            <Input
                                value={editHashtags}
                                onChange={(e) => setEditHashtags(e.target.value)}
                                className="bg-gray-800 border-gray-600 text-white"
                                placeholder="gaming, indiedev, gamedev"
                            />
                        </div>
                        {reviewJob && (
                            <div className="text-sm text-gray-400">
                                <Info className="h-4 w-4 inline mr-1" />
                                Scheduled for: {reviewJob.scheduled_date
                                    ? format(new Date(reviewJob.scheduled_date), "MMM d, yyyy 'at' h:mm a")
                                    : "To be determined"}
                            </div>
                        )}
                    </div>

                    <DialogFooter className="gap-2">
                        <Button variant="ghost" onClick={() => setReviewJob(null)}>
                            Cancel
                        </Button>
                        <Button
                            onClick={() => reviewJob && handleApprove(reviewJob.id)}
                            className="bg-green-600 hover:bg-green-700"
                        >
                            <Check className="h-4 w-4 mr-1" /> Approve & Schedule
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}

export default UploadScheduler;
