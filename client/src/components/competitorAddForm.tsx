import React, { useState } from "react";
import { socialPlatforms } from "@/components/socialPlatforms";
import { ChevronDown, Plus, X } from "lucide-react";
import { useGroup } from "./groupContext";

interface CompetitorAddFormProps {
    onSuccess?: () => void;
}

const CompetitorAddForm: React.FC<CompetitorAddFormProps> = ({ onSuccess }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [selectedPlatform, setSelectedPlatform] = useState(socialPlatforms[0]);
    const [socialUrl, setSocialUrl] = useState("");
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const { activeGroup } = useGroup();
    const handleReset = () => {
        setIsExpanded(false);
        setSocialUrl("");
        setSelectedPlatform(socialPlatforms[0]);
        setIsDropdownOpen(false);
    };

    const handleSubmit = async () => {
        if (!socialUrl.trim() || !selectedPlatform?.id?.trim()) {
            alert("Enter both username and platform");
            return;
        }
        try {
            const res = await fetch(
                `/api/groups/${activeGroup?.ID || ""}/competitors`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${localStorage.getItem("token")}`,
                    },
                    body: JSON.stringify({
                        Platform: selectedPlatform.id,
                        Username: socialUrl,
                    }),
                }
            );
            const data = await res.json();
            console.log(data);
            handleReset();
            // Notify parent to refresh the competitors list
            if (onSuccess) {
                onSuccess();
            }
        } catch (e: any) {
            throw new Error(e || "Could not add competitor");
        }
    };

    return (
        <div>
            <div className="relative">
                {/* Main Button */}
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className={`
            flex items-center gap-3 px-6 py-3 rounded-full font-semibold 
            transition-all duration-500 ease-in-out transform
            ${isExpanded
                            ? "bg-gray-800 text-white scale-105 shadow-2xl"
                            : "text-black bg-white shadow-lg hover:shadow-xl hover:scale-105"
                        }
          `}
                >
                    {isExpanded ? (
                        <>
                            <X size={20} />
                            Cancel
                        </>
                    ) : (
                        <>
                            <Plus size={20} />
                            Add Social Media
                        </>
                    )}
                </button>

                {/* Sliding Form (slides horizontally from the LEFT) */}
                <div
                    className={`
            absolute top-full mt-4 right-2 bg-black rounded-2xl shadow-2xl border border-gray-700
            transition-all duration-500 ease-in-out transform origin-bottom-left
            ${isExpanded
                            ? "opacity-100 scale-100 translate-x-0"
                            : "opacity-0 scale-95 -translate-x-10 pointer-events-none"
                        }
          `}
                >
                    <div className="p-6 w-80">
                        <h3 className="mb-4 text-lg font-semibold text-white">
                            Add Social Media Account
                        </h3>

                        {/* URL Input */}
                        <div className="mb-4">
                            <label className="block mb-2 text-sm font-medium text-white">
                                Account URL or @username
                            </label>
                            <input
                                type="text"
                                value={socialUrl}
                                onChange={(e) => setSocialUrl(e.target.value)}
                                placeholder="https://instagram.com/username or @username"
                                className="w-full px-4 py-2 transition-all bg-black border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        {/* Platform Dropdown */}
                        <div className="mb-6">
                            <label className="block mb-2 text-sm font-medium text-white">
                                Social Media Platform
                            </label>
                            <div className="relative">
                                <button
                                    type="button"
                                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                                    className="flex items-center justify-between w-full px-4 py-2 transition-all bg-black border border-gray-300 rounded-lg outline-none hover:border-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <div className="flex items-center gap-3">
                                        <div
                                            className={`p-1.5 rounded-md ${selectedPlatform.color} flex items-center justify-center`}
                                        >
                                            <selectedPlatform.icon size={16} className="text-white" />
                                        </div>
                                        <span className="font-semibold text-white">
                                            {selectedPlatform.id}
                                        </span>
                                    </div>
                                    <ChevronDown
                                        size={16}
                                        className={`text-gray-500 transition-transform duration-200 ${isDropdownOpen ? "rotate-180" : ""
                                            }`}
                                    />
                                </button>

                                {/* Dropdown Options */}
                                <div
                                    className={`
                    absolute top-full left-0 right-0 mt-1 bg-black border border-gray-300 rounded-lg shadow-lg z-10
                    transition-all duration-200 origin-top
                    ${isDropdownOpen ? "opacity-100 scale-100" : "opacity-0 scale-95 pointer-events-none"}
                  `}
                                >
                                    {socialPlatforms.map((platform) => (
                                        <button
                                            key={platform.id}
                                            type="button"
                                            onClick={() => {
                                                setSelectedPlatform(platform);
                                                setIsDropdownOpen(false);
                                            }}
                                            className="flex items-center w-full gap-3 px-4 py-2 transition-colors hover:bg-neutral-800 first:rounded-t-lg last:rounded-b-lg"
                                        >
                                            <div
                                                className={`p-1.5 rounded-md ${platform.color} flex items-center justify-center`}
                                            >
                                                <platform.icon size={16} className="text-white" />
                                            </div>
                                            <span className="font-semibold text-white">
                                                {platform.id}
                                            </span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-3">
                            <button
                                type="button"
                                onClick={handleSubmit}
                                className="flex-1 px-4 py-2 font-medium text-black transition-all transform bg-white rounded-lg hover:cursorcursor-pointer"
                            >
                                Add Account
                            </button>
                            <button
                                type="button"
                                onClick={handleReset}
                                className="px-4 py-2 font-medium text-black transition-colors bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CompetitorAddForm
