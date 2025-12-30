import { useState, useEffect } from "react";
import { X, Plus, Trash2 } from "lucide-react";
import { socialPlatforms } from "@/components/socialPlatforms";
import { Button } from "@/components/ui/button";

interface Profile {
    id: string;
    platform: string;
    handle: string;
    profile_url: string;
    followers: number;
    engagement_rate: number;
    growth_rate: number;
    posting_frequency: number;
    last_checked: string | null;
}

interface CompetitorEditModalProps {
    isOpen: boolean;
    onClose: () => void;
    competitorId: string;
    competitorName: string;
    existingProfiles: Profile[];
    onSave: () => void;
}

export function CompetitorEditModal({
    isOpen,
    onClose,
    competitorId,
    competitorName,
    existingProfiles,
    onSave,
}: CompetitorEditModalProps) {
    const [profiles, setProfiles] = useState<Profile[]>([]);
    const [newPlatform, setNewPlatform] = useState(socialPlatforms[0]?.id || "");
    const [newHandle, setNewHandle] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        setProfiles(existingProfiles);
    }, [existingProfiles]);

    if (!isOpen) return null;

    const handleAddProfile = async () => {
        if (!newHandle.trim() || !newPlatform) return;

        setIsSubmitting(true);
        try {
            const res = await fetch(`/api/competitors/${competitorId}/profiles`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
                body: JSON.stringify({
                    platform: newPlatform,
                    handle: newHandle,
                    profile_url: "",
                }),
            });

            if (res.ok) {
                const newProfile = await res.json();
                setProfiles([...profiles, newProfile]);
                setNewHandle("");
                setNewPlatform(socialPlatforms[0]?.id || "");
            } else {
                const err = await res.json();
                alert(err.error || "Failed to add profile");
            }
        } catch (e) {
            console.error("Failed to add profile:", e);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDeleteProfile = async (profileId: string) => {
        if (!confirm("Are you sure you want to remove this platform?")) return;

        try {
            const res = await fetch(`/api/competitors/profiles/${profileId}`, {
                method: "DELETE",
                headers: {
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
            });

            if (res.ok) {
                setProfiles(profiles.filter((p) => p.id !== profileId));
            }
        } catch (e) {
            console.error("Failed to delete profile:", e);
        }
    };

    const handleDeleteCompetitor = async () => {
        if (!confirm(`Are you sure you want to remove "${competitorName}" from your tracked competitors? This will not affect other users tracking this competitor.`)) return;

        try {
            const res = await fetch(`/api/competitors/${competitorId}`, {
                method: "DELETE",
                headers: {
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
            });

            if (res.ok) {
                onSave(); // Refresh the list
                onClose();
            } else {
                const err = await res.json();
                alert(err.error || "Failed to remove competitor");
            }
        } catch (e) {
            console.error("Failed to delete competitor:", e);
            alert("Failed to remove competitor");
        }
    };

    const handleClose = () => {
        onSave();
        onClose();
    };

    const getPlatformIcon = (platformId: string) => {
        const platform = socialPlatforms.find((p) => p.id.toLowerCase() === platformId.toLowerCase());
        return platform?.icon;
    };

    const getPlatformColor = (platformId: string) => {
        const platform = socialPlatforms.find((p) => p.id.toLowerCase() === platformId.toLowerCase());
        return platform?.color || "bg-gray-500";
    };

    const usedPlatforms = profiles.map((p) => p.platform.toLowerCase());
    const availablePlatforms = socialPlatforms.filter(
        (p) => !usedPlatforms.includes(p.id.toLowerCase())
    );

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-lg bg-neutral-900 border border-neutral-700 rounded-xl shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-neutral-700">
                    <h2 className="text-xl font-semibold text-white">
                        Edit {competitorName}
                    </h2>
                    <button
                        onClick={handleClose}
                        className="p-1 rounded-lg hover:bg-neutral-800 transition-colors"
                    >
                        <X className="w-5 h-5 text-neutral-400" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-4 space-y-4 max-h-[60vh] overflow-y-auto">
                    {/* Existing Profiles */}
                    <div className="space-y-2">
                        <h3 className="text-sm font-medium text-neutral-400 uppercase tracking-wider">
                            Connected Platforms
                        </h3>
                        {profiles.length === 0 ? (
                            <p className="text-neutral-500 text-sm py-2">No platforms connected yet.</p>
                        ) : (
                            profiles.map((profile) => {
                                const Icon = getPlatformIcon(profile.platform);
                                return (
                                    <div
                                        key={profile.id}
                                        className="flex items-center justify-between p-3 bg-neutral-800 rounded-lg"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-lg ${getPlatformColor(profile.platform)}`}>
                                                {Icon && <Icon className="w-4 h-4 text-white" />}
                                            </div>
                                            <div>
                                                <p className="text-white font-medium">{profile.handle}</p>
                                                <p className="text-neutral-400 text-xs capitalize">
                                                    {profile.platform}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-neutral-400 text-sm">
                                                {profile.followers?.toLocaleString() || 0} followers
                                            </span>
                                            <button
                                                onClick={() => handleDeleteProfile(profile.id)}
                                                className="p-2 rounded-lg hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-colors"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>

                    {/* Add New Platform */}
                    {availablePlatforms.length > 0 && (
                        <div className="space-y-2 pt-4 border-t border-neutral-700">
                            <h3 className="text-sm font-medium text-neutral-400 uppercase tracking-wider">
                                Add New Platform
                            </h3>
                            <div className="flex gap-2">
                                <select
                                    value={newPlatform}
                                    onChange={(e) => setNewPlatform(e.target.value)}
                                    className="flex-shrink-0 px-3 py-2 bg-neutral-800 border border-neutral-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    {availablePlatforms.map((p) => (
                                        <option key={p.id} value={p.id}>
                                            {p.id}
                                        </option>
                                    ))}
                                </select>
                                <input
                                    type="text"
                                    value={newHandle}
                                    onChange={(e) => setNewHandle(e.target.value)}
                                    placeholder="@username or handle"
                                    className="flex-1 px-3 py-2 bg-neutral-800 border border-neutral-600 rounded-lg text-white placeholder-neutral-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                                <Button
                                    onClick={handleAddProfile}
                                    disabled={isSubmitting || !newHandle.trim()}
                                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
                                >
                                    <Plus className="w-4 h-4" />
                                    Add
                                </Button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex justify-between gap-2 p-4 border-t border-neutral-700">
                    <Button
                        variant="destructive"
                        onClick={handleDeleteCompetitor}
                        className="bg-red-600 hover:bg-red-700 text-white"
                    >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Remove Competitor
                    </Button>
                    <Button variant="outline" onClick={handleClose}>
                        Done
                    </Button>
                </div>
            </div>
        </div>
    );
}

export default CompetitorEditModal;
