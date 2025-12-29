"use client";

import { useState } from "react";
import { Plus, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { socialPlatforms } from "@/components/socialPlatforms";
import { useGroup } from "@/components/groupContext";

interface AddCompetitorModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export function AddCompetitorModal({
    isOpen,
    onClose,
    onSuccess,
}: AddCompetitorModalProps) {
    const { activeGroup } = useGroup();
    const [competitorName, setCompetitorName] = useState("");
    const [handle, setHandle] = useState("");
    const [platform, setPlatform] = useState(socialPlatforms[0]?.id || "Instagram");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async () => {
        if (!competitorName.trim() || !handle.trim() || !platform) {
            setError("Please fill in all fields");
            return;
        }

        if (!activeGroup?.ID) {
            setError("No active group selected");
            return;
        }

        setIsSubmitting(true);
        setError(null);

        try {
            const res = await fetch(`/api/groups/${activeGroup.ID}/competitors`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
                body: JSON.stringify({
                    Username: handle.replace(/^@/, ""), // Remove leading @ if present
                    Platform: platform,
                }),
            });

            if (res.ok) {
                // Reset form
                setCompetitorName("");
                setHandle("");
                setPlatform(socialPlatforms[0]?.id || "Instagram");
                onSuccess();
                onClose();
            } else {
                const data = await res.json();
                setError(data.error || "Failed to add competitor");
            }
        } catch (e) {
            console.error("Failed to add competitor:", e);
            setError("Failed to add competitor. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleClose = () => {
        setCompetitorName("");
        setHandle("");
        setPlatform(socialPlatforms[0]?.id || "Instagram");
        setError(null);
        onClose();
    };

    const getPlatformIcon = (platformId: string) => {
        const p = socialPlatforms.find(
            (sp) => sp.id.toLowerCase() === platformId.toLowerCase()
        );
        return p?.icon;
    };

    const getPlatformColor = (platformId: string) => {
        const p = socialPlatforms.find(
            (sp) => sp.id.toLowerCase() === platformId.toLowerCase()
        );
        return p?.color || "bg-gray-500";
    };

    const SelectedIcon = getPlatformIcon(platform);

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
            <DialogContent className="sm:max-w-[425px] bg-zinc-900 border-zinc-700">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <div className="p-2 rounded-lg bg-blue-500/20">
                            <Plus className="w-5 h-5 text-blue-400" />
                        </div>
                        Add New Competitor
                    </DialogTitle>
                    <DialogDescription>
                        Add a competitor to track their social media performance. Fill in
                        their name, handle, and select the platform.
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    {/* Competitor Name */}
                    <div className="grid gap-2">
                        <Label htmlFor="name" className="text-zinc-300">
                            Competitor Name
                        </Label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                            <Input
                                id="name"
                                value={competitorName}
                                onChange={(e) => setCompetitorName(e.target.value)}
                                placeholder="e.g., Nike, Adidas, Apple"
                                className="pl-10 bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-500 focus:border-blue-500"
                            />
                        </div>
                        <p className="text-xs text-zinc-500">
                            The display name for this competitor
                        </p>
                    </div>

                    {/* Social Media Handle */}
                    <div className="grid gap-2">
                        <Label htmlFor="handle" className="text-zinc-300">
                            Social Media Handle
                        </Label>
                        <Input
                            id="handle"
                            value={handle}
                            onChange={(e) => setHandle(e.target.value)}
                            placeholder="@username or profile URL"
                            className="bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-500 focus:border-blue-500"
                        />
                        <p className="text-xs text-zinc-500">
                            Enter the username (with or without @) or profile URL
                        </p>
                    </div>

                    {/* Platform Selection */}
                    <div className="grid gap-2">
                        <Label htmlFor="platform" className="text-zinc-300">
                            Platform
                        </Label>
                        <Select value={platform} onValueChange={setPlatform}>
                            <SelectTrigger className="bg-zinc-800 border-zinc-700 text-white focus:ring-blue-500">
                                <SelectValue placeholder="Select a platform">
                                    <div className="flex items-center gap-2">
                                        {SelectedIcon && (
                                            <div
                                                className={`p-1 rounded ${getPlatformColor(platform)}`}
                                            >
                                                <SelectedIcon className="w-3 h-3 text-white" />
                                            </div>
                                        )}
                                        <span>{platform}</span>
                                    </div>
                                </SelectValue>
                            </SelectTrigger>
                            <SelectContent className="bg-zinc-800 border-zinc-700">
                                {socialPlatforms.map((p) => {
                                    const Icon = p.icon;
                                    return (
                                        <SelectItem
                                            key={p.id}
                                            value={p.id}
                                            className="text-white hover:bg-zinc-700 focus:bg-zinc-700"
                                        >
                                            <div className="flex items-center gap-2">
                                                <div className={`p-1 rounded ${p.color}`}>
                                                    <Icon className="w-3 h-3 text-white" />
                                                </div>
                                                <span>{p.id}</span>
                                            </div>
                                        </SelectItem>
                                    );
                                })}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="p-3 text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg">
                            {error}
                        </div>
                    )}
                </div>

                <DialogFooter className="gap-2 sm:gap-0">
                    <Button
                        variant="outline"
                        onClick={handleClose}
                        className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                    >
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSubmit}
                        disabled={isSubmitting || !competitorName.trim() || !handle.trim()}
                        className="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                        {isSubmitting ? (
                            <span className="flex items-center gap-2">
                                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                Adding...
                            </span>
                        ) : (
                            <span className="flex items-center gap-2">
                                <Plus className="w-4 h-4" />
                                Add Competitor
                            </span>
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

export default AddCompetitorModal;
