import React, { useState } from "react";
import { socialPlatforms } from "@/components/socialPlatforms";
import { ChevronDown, Plus, X } from "lucide-react";

const CompetitorAddForm: React.FC = () => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [selectedPlatform, setSelectedPlatform] = useState(socialPlatforms[0]);
    const [socialUrl, setSocialUrl] = useState("");
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);

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
                `/api/groups/competitors`,
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
                        <h3 className="text-lg font-semibold text-white mb-4">
                            Add Social Media Account
                        </h3>

                        {/* URL Input */}
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-white mb-2">
                                Account URL or @username
                            </label>
                            <input
                                type="text"
                                value={socialUrl}
                                onChange={(e) => setSocialUrl(e.target.value)}
                                placeholder="https://instagram.com/username or @username"
                                className="w-full px-4 py-2 border bg-black border-gray-300 rounded-lg focus:ring-2  focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                            />
                        </div>

                        {/* Platform Dropdown */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-white mb-2">
                                Social Media Platform
                            </label>
                            <div className="relative">
                                <button
                                    type="button"
                                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                                    className="w-full flex items-center justify-between px-4 py-2 border border-gray-300 rounded-lg bg-black hover:border-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                                >
                                    <div className="flex items-center gap-3">
                                        <div
                                            className={`p-1.5 rounded-md ${selectedPlatform.color} flex items-center justify-center`}
                                        >
                                            <selectedPlatform.icon size={16} className="text-white" />
                                        </div>
                                        <span className="text-white font-semibold">
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
                                            className="w-full flex items-center gap-3 px-4 py-2 hover:bg-neutral-800 transition-colors first:rounded-t-lg last:rounded-b-lg"
                                        >
                                            <div
                                                className={`p-1.5 rounded-md ${platform.color} flex items-center justify-center`}
                                            >
                                                <platform.icon size={16} className="text-white" />
                                            </div>
                                            <span className="text-white font-semibold">
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
                                className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 text-white py-2 px-4 rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 transition-all transform hover:scale-105"
                            >
                                Add Account
                            </button>
                            <button
                                type="button"
                                onClick={handleReset}
                                className="px-4 py-2 border bg-white border-gray-300 text-black rounded-lg hover:bg-gray-50 transition-colors"
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
