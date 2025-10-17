"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { FileText, Loader2, Upload, Sparkles, CheckCircle2 } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { UpdateIcon } from "@radix-ui/react-icons";
import { useGroup } from "../../components/groupContext";
import { TriangleAlert } from "lucide-react";
import { useRef } from "react";
import FormField from "@/components/ui/form-field";
interface GameContextData {
    group_id?: number;
    game_title: string;
    studio_name: string;
    game_summary: string;
    platforms: string[];
    engine_tech: string;
    primary_genre: string;
    subgenre: string;
    key_mechanics: string;
    playtime_length: string;
    art_style: string;
    tone: string;
    intended_audience: string;
    age_range: string;
    player_motivation: string;
    comparable_games: string;
    marketing_objective: string;
    key_events_dates: string;
    call_to_action: string;
    content_restrictions: string;
    competitors_to_avoid: string;
}

export default function GameContextPage() {
    const [inputMethod, setInputMethod] = useState<"upload" | "manual" | null>(null);
    const [file, setFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [loading, setLoading] = useState(false);
    const { activeGroup } = useGroup();
    const [extractedData, setExtractedData] = useState<GameContextData | null>(null);
    const [formData, setFormData] = useState<GameContextData>({
        game_title: "",
        studio_name: "",
        game_summary: "",
        platforms: [],
        engine_tech: "",
        primary_genre: "",
        subgenre: "",
        key_mechanics: "",
        playtime_length: "",
        art_style: "",
        tone: "",
        intended_audience: "",
        age_range: "",
        player_motivation: "",
        comparable_games: "",
        marketing_objective: "",
        key_events_dates: "",
        call_to_action: "",
        content_restrictions: "",
        competitors_to_avoid: "",
    });

    const radioButtons = [
        { value: "Awareness", label: "Awareness" },
        { value: "Wishlist Growth", label: "Wishlist Growth" },
        { value: "Demo Downloads", label: "Demo Downloads" },
        { value: "Player Retention", label: "Player Retention" },
        { value: "Event Promotion", label: "Event Promotion" },
    ];
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleFileUpload = async () => {
        if (!file) {
            toast({
                title: "No file selected",
                description: "Please select a file to upload",
                variant: "destructive",
            });
            return;
        }

        setLoading(true);

        try {
            const formDataPayload = new FormData();
            formDataPayload.append("file", file);

            const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/games/extract`, {
                method: "POST",
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
                body: formDataPayload,
            });

            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(`Upload failed: ${errorText}`);
            }

            const data = await res.json();
            setExtractedData(data);
            setFormData(data);

            toast({
                title: "Success!",
                description: "AI extracted the game information. Please review and edit as needed.",
            });
        } catch (err) {
            toast({
                title: "Upload Failed",
                description: err instanceof Error ? err.message : "Something went wrong",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };






    const validateGameContext = () => {
        const errors = [];

        // Required fields
        if (!formData.game_title?.trim()) errors.push("Game title is required");
        if (!formData.studio_name?.trim()) errors.push("Studio name is required");
        if (!formData.game_summary?.trim()) errors.push("Game summary is required");

        // Array field validation
        if (!formData.platforms || formData.platforms.length === 0) {
            errors.push("At least one platform must be specified");
        }

        // Marketing objective validation (radio button)
        if (!formData.marketing_objective?.trim()) {
            errors.push("Please select a marketing objective");
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }




    const handleInputChange = (field: keyof GameContextData, value: string | string[]) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async () => {
        // TODO: Implement save to database
        const validation = validateGameContext();
        if (!validation.isValid) {
            toast({
                title: "Validation Error",
                description: validation.errors.join('\n'),
                variant: "destructive",
            });
            return;
        }

        try {
            // Include group_id from activeGroup
            const payload = {
                ...formData,
                group_id: activeGroup?.ID
            };

            const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/games/input`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("token")}` },
                body: JSON.stringify(payload),
            });
            const body = await res.json();

            if (!res.ok) {
                toast({
                    title: "Error to database",
                    description: `${body}`,
                });
            } else {
                toast({
                    title: "Saved Succesfully",
                    description: "Your form was saved",
                });
            }
        } catch (error) {
            toast({
                title: "Error",
                description: `${error}`,
            });
        }

    };

    if (!activeGroup) {
        return (
            <div className="flex justify-center w-full h-[45px] text-center">
                <div className="flex gap-2 p-2 border border-red-500 border-dashed">
                    <div className=" w-[30px] h-[30px] flex justify-center items-center rounded-lg">

                        <TriangleAlert className="text-yellow-400"></TriangleAlert>
                    </div>
                    <h1 className="font-semibold">Please select a group to continue </h1>
                </div>
            </div>
        );
    }
    if (!inputMethod) {
        return (
            <div className="flex flex-col flex-wrap p-10 text-white h-100vh ">
                <div className="flex flex-col justify-start ">
                    <h1 className="text-3xl font-bold">Add Game Context</h1>
                    <h2 className="text-slate-400">Choose how you'd like to add game information</h2>
                </div>
                <div className="flex items-center justify-center min-w-full">
                    <div className="grid min-w-full gap-5 px-10 mt-5 md:grid-cols-2">
                        <div className="flex flex-col flex-wrap items-center justify-center max-w-xl border hover:border-purple-500 hover:cursor-pointer"
                            onClick={() => setInputMethod("upload")}
                        >
                            <div className="p-3 mt-5 rounded-full bg-blue-500/20"> <Upload className="text-blue-400" /></div>
                            <div className="flex flex-col items-center justify-center p-5 mt-2">
                                <h1 className="text-xl font-semibold">Upload Document</h1>
                                <h2 className="text-sm text-slate-500">Let AI extract information from your PDF or TXT file</h2>
                                <h2 className="text-sm text-slate-500"> Get a chance to review before submit</h2>

                            </div>
                        </div>
                        <div className="flex flex-col flex-wrap items-center justify-center max-w-xl border hover:border-purple-500 hover:cursor-pointer"
                            onClick={() => setInputMethod("manual")}
                        >
                            <div className="p-3 mt-5 rounded-full bg-purple-500/20"> <FileText className="text-purple-400" /></div>
                            <div className="flex flex-col items-center justify-center p-5 mt-2">
                                <h1 className="text-xl font-semibold">Manual Entry</h1>
                                <h2 className="text-sm text-slate-500">Fill out the form yourself</h2>

                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );

    }
    if (inputMethod == "upload" && !extractedData) {
        return (
            <div className="min-h-screen p-8 text-white">
                <div className="max-w-2xl mx-auto">
                    <Button
                        variant="ghost"
                        onClick={() => setInputMethod(null)}
                        className="mb-6 text-gray-400 hover:text-white"
                    >
                        ← Back
                    </Button>
                    <div className="p-12 border border-white border-dashed hover:border-purple-500 hover:cursor-pointer"
                        onClick={() => fileInputRef.current?.click()}>
                        <Input
                            type="file"
                            accept=".pdf,.txt"
                            className="hidden"
                            onChange={handleFileChange}
                            ref={fileInputRef}
                        />


                        <div className="flex flex-col items-center justify-center p-4 space-y-4 text-center">
                            <div className="p-4 rounded-full bg-blue-500/10">
                                <Upload className="w-8 h-8 text-blue-400" />
                            </div>
                            <div className="space-y-2">
                                <p className="text-lg font-medium text-white">
                                    Click to upload files
                                </p>
                                <p className="text-sm text-gray-400">
                                    Supports PNG and TXT (max. 10MB)
                                </p>
                            </div>

                        </div>

                    </div>

                    {file && (
                        <div className="flex items-center justify-between p-4 mt-3 bg-gray-800 ">
                            <div className="flex items-center gap-3">
                                <FileText className="w-8 h-8 text-blue-400" />
                                <div>
                                    <p className="font-medium text-white">{file.name}</p>
                                    <p className="text-sm text-gray-400">
                                        {(file.size / 1024).toFixed(2)} KB
                                    </p>
                                </div>
                            </div>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setFile(null)}
                                className="text-gray-400 hover:text-white"
                            >
                                Remove
                            </Button>
                        </div>
                    )}

                    <Button
                        onClick={handleFileUpload}
                        disabled={!file || loading}
                        className="w-full mt-5 bg-blue-600 hover:bg-blue-700"
                        size="lg"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Extracting Information...
                            </>
                        ) : (
                            <>
                                Extract with AI
                            </>
                        )}
                    </Button>
                </div>
            </div >
        );
    }
    return (
        <div className="p-8 text-white min-h-100">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        {extractedData ?
                            <div>
                                <h1 className="text-2xl font-bold"> Review and edit game context</h1>
                                <h2 className="text-slate-500"> Ai has extracted the information. Review and edit before submitting</h2>
                            </div> :
                            <div>
                                <h1 className="text-2xl font-bold">Enter game context</h1>
                                <h2 className="text-slate-500"> Provide details about your game</h2>
                            </div>
                        }
                    </div>
                    <Button
                        variant="ghost"
                        onClick={() => {
                            setInputMethod(null);
                            setExtractedData(null);
                            setFile(null);
                        }}
                        className="text-gray-400 hover:text-white"
                    >
                        Start Over
                    </Button>
                </div>
                {extractedData && (
                    <div className="flex items-center gap-3 p-4 mb-6 border bg-green-900/20 border-green-500/30">
                        <CheckCircle2 className="flex-shrink-0 w-5 h-5 text-green-400"></CheckCircle2>
                        <p className="text-sm text-green-300"> Extraction complete</p>
                    </div>
                )}
                {/*main form */}
                <div className="space-y-6">
                    <div className="flex flex-col p-5 border border-purple-500/60">
                        <h1 className="text-xl font-bold">1. Basic Game Info</h1>
                        <p className="text-sm text-slate-500">The core details about the game</p>

                        <div className="flex flex-col">
                            <div className="flex items-baseline w-full gap-5 mt-2">
                                <FormField
                                    label="Title"
                                    placeholder="Enter title of game"
                                    id="game_title"
                                    value={formData.game_title}
                                    onChange={(value) => handleInputChange("game_title", value.target.value)}
                                    required
                                    className="w-[50%]"
                                />
                                <FormField
                                    label="Studio / Developer Name"
                                    placeholder="Dogwood"
                                    id="studio_name"
                                    value={formData.studio_name}
                                    onChange={(value) => handleInputChange("studio_name", value.target.value)}
                                    className="w-[50%]"
                                />
                            </div>
                            <div className="mt-2">
                                <Label htmlFor="game_summary">Summary/Description</Label>
                                <Textarea
                                    id="game_summary"
                                    value={formData.game_summary}
                                    onChange={(value) => { handleInputChange("game_summary", value.target.value) }}
                                    placeholder="Summary"
                                />
                            </div>
                            <div className="grid gap-4 mt-2 md:grid-cols-2">
                                <FormField
                                    label="Platforms"
                                    placeholder="PC, Console, Mobile, VR"
                                    id="platforms"
                                    value={Array.isArray(formData.platforms) ? formData.platforms.join(", ") : formData.platforms}
                                    onChange={(value) => handleInputChange("platforms", value.target.value.split(",").map(p => p.trim()))}
                                />
                                <FormField
                                    label="Engine / Tech"
                                    placeholder="Unity, Unreal, Custom, etc."
                                    id="engine_tech"
                                    value={formData.engine_tech}
                                    onChange={(value) => handleInputChange("engine_tech", value.target.value)}
                                />
                            </div>
                            <div className="w-full mt-5 border border-slate-500/60"></div>
                            {/* section 2 */}
                            <div className="mt-2">
                                <h1 className="text-xl font-bold">2. Game's Identity</h1>
                                <p className="text-sm text-slate-500">Game's genre and style</p>
                                <div className="flex flex-col">
                                    <div className="flex items-baseline w-full gap-5 mt-2">
                                        <FormField
                                            label="Primary Genre"
                                            placeholder="e.g. Racing, Simulation, Action"
                                            id="primary_genre"
                                            value={formData.primary_genre}
                                            onChange={(value) => handleInputChange("primary_genre", value.target.value)}
                                            className="w-[50%]"
                                        />
                                        <FormField
                                            label="Subgenre"
                                            placeholder="e.g. rougelike, sandbox"
                                            id="subgenre"
                                            value={formData.subgenre}
                                            onChange={(value) => handleInputChange("subgenre", value.target.value)}
                                            className="w-[50%]"
                                        />
                                    </div>
                                </div>
                                <div className="flex w-full gap-10">
                                    <div className="w-full mt-2">
                                        <Label htmlFor="game_summary">Key mechanics / Features</Label>
                                        <Textarea
                                            id="key_mechanics"
                                            value={formData.game_summary}
                                            onChange={(value) => { handleInputChange("key_mechanics", value.target.value) }}
                                            placeholder="e.g. Customizable Cars, Procedural Levels"
                                        />

                                    </div>

                                </div>
                                <div className="flex gap-5 mt-2">
                                    <FormField
                                        label="Estimated Playtime Length"
                                        placeholder="eg. 10-15 hours"
                                        id="playtime_length"
                                        value={formData.playtime_length}
                                        onChange={(value) => handleInputChange("playtime_length", value.target.value)}
                                        className="w-[50%]"
                                    />
                                    <FormField
                                        label="Art Style"
                                        placeholder="e.g. Realistic, Stylized, Pixel Art"
                                        id="art_style"
                                        value={formData.art_style}
                                        onChange={(value) => handleInputChange("art_style", value.target.value)}
                                        className="w-[50%]"
                                    />
                                </div>
                            </div>
                            <div className="w-full mt-5 border border-slate-500/60"></div>
                            {/* section 3 */}
                            <div className="mt-2">
                                <h1 className="text-xl font-bold">3. Target Audience</h1>
                                <p className="text-sm text-slate-500">who will want to play the game?</p>

                                <div className="flex flex-col">
                                    <div className="flex items-baseline w-full gap-5 mt-2">
                                        <FormField
                                            label="Intended Audience"
                                            placeholder="e.g. Casual Games, History Buffs"
                                            id="intended_audience"
                                            value={formData.intended_audience}
                                            onChange={(value) => handleInputChange("intended_audience", value.target.value)}
                                            className="w-[50%]"
                                        />
                                        <FormField
                                            label="Age Range"
                                            placeholder="e.g. Teen 13-18, Young Adult"
                                            id="age_range"
                                            value={formData.age_range}
                                            onChange={(value) => handleInputChange("age_range", value.target.value)}
                                            className="w-[50%]"
                                        />
                                    </div>
                                    <div className="flex flex-col items-baseline w-full gap-2">
                                        <Label htmlFor="Player Motivation">Player Motivation</Label>
                                        <Textarea
                                            id="player_motivation"
                                            value={formData.player_motivation}
                                            onChange={(value) => { handleInputChange("player_motivation", value.target.value) }}
                                            placeholder="What do players get out of this? Fun, relaxation, mastery, creativity, competition, etc"
                                        />

                                    </div>
                                    <div className="flex gap-2">
                                        <div className="flex flex-col w-[70%]">
                                            <Label htmlFor="Player Motivation">Player Motivation</Label>
                                            <Textarea
                                                id="player_motivation"
                                                value={formData.player_motivation}
                                                onChange={(value) => { handleInputChange("player_motivation", value.target.value) }}
                                                placeholder="What do players get out of this? Fun, relaxation, mastery, creativity, competition, etc"
                                            />
                                        </div>
                                        <FormField
                                            label="Age Range"
                                            placeholder="e.g. Teen 13-18, Young Adult"
                                            id="age_range"
                                            value={formData.age_range}
                                            onChange={(value) => handleInputChange("age_range", value.target.value)}
                                            className="w-[50%]"
                                        />

                                    </div>
                                    <div className="flex items-baseline w-full gap-5 mt-2">
                                        <FormField
                                            label="Comparable Games"
                                            placeholder="e.g. Inspired by Stardew Valley and Animal Crossing."
                                            id="comparable_games"
                                            value={formData.comparable_games}
                                            onChange={(value) => handleInputChange("comparable_games", value.target.value)}
                                            className="w-[75%]"
                                        />

                                    </div>
                                </div>
                            </div>
                            <div className="w-full mt-5 border border-slate-500/60"></div>

                            {/* section 4 */}
                            <div className="mt-2">
                                <h1 className="text-xl font-bold">4. Marketing Goals</h1>
                                <p className="text-sm text-slate-500">What success looks like for your campaign</p>
                                <div className="flex flex-col">
                                    <div className="flex flex-wrap gap-3 p-2">
                                        {radioButtons.map((option) => {
                                            return (
                                                <div className="p-2 border border-gray-50/20">
                                                    <label key={option.value} className="flex items-center gap-2">
                                                        <input
                                                            type="radio"
                                                            name="marketing_objective"
                                                            value={option.value}
                                                            onChange={() => handleInputChange("marketing_objective", option.value)}
                                                        />
                                                        <span>{option.label}</span>
                                                    </label>
                                                </div>
                                            );
                                        })}
                                    </div>

                                </div>
                                <div className="flex items-baseline w-full gap-5 mt-2">
                                    <FormField
                                        label="Key Events or Dates"
                                        placeholder="e.g., demo release, festival submission, convention appearance"
                                        id="key_events_dates"
                                        value={formData.key_events_dates}
                                        onChange={(value) => handleInputChange("key_events_dates", value.target.value)}
                                        className="w-[50%]"
                                    />
                                    <FormField
                                        label="Call To Action"
                                        placeholder="e.g. Add to Wishlist, Play the Demo"
                                        id="call_to_action"
                                        value={formData.call_to_action}
                                        onChange={(value) => handleInputChange("call_to_action", value.target.value)}
                                        className="w-[50%]"
                                    />
                                </div>
                            </div>
                            <div className="w-full mt-5 border border-slate-500/60"></div>
                            {/* stage 5 */}
                            <div className="mt-2">
                                <h1 className="text-xl font-bold">Restrictions / Boundaries</h1>
                                <p className="text-sm text-slate-500">Helps avoid bad or off-brand outputs.</p>
                                <div className="flex flex-col">
                                    <div className="flex items-baseline w-full gap-5 mt-2">
                                        <FormField
                                            label="Content Restrictions"
                                            placeholder="e.g. “No mention of gambling with real money,” “Avoid dark humor."
                                            id="content_restrictions"
                                            value={formData.content_restrictions}
                                            onChange={(value) => handleInputChange("content_restrictions", value.target.value)}
                                            className="w-[50%]"
                                        />
                                        <FormField
                                            label="Competitors / Topics to Avoid"
                                            placeholder="Optional —e.g. “Don't reference real-world casinos or violence."
                                            id="competitors_to_avoid"
                                            value={formData.competitors_to_avoid}
                                            onChange={(value) => handleInputChange("competitors_to_avoid", value.target.value)}
                                            className="w-[50%]"
                                        />
                                    </div>
                                </div>
                            </div>
                            <Separator className="bg-gray-800" />

                            {/* Submit Button */}
                            <div className="flex justify-end gap-4 mt-2">
                                <Button
                                    variant="outline"
                                    onClick={() => {
                                        setInputMethod(null);
                                        setExtractedData(null);
                                        setFile(null);
                                    }}
                                    className="text-gray-300 bg-gray-800 border-gray-700 hover:bg-gray-700"
                                >
                                    Cancel
                                </Button>
                                <Button
                                    onClick={handleSubmit}
                                    className="bg-blue-600 hover:bg-blue-700"
                                    size="lg"
                                >
                                    Save Game Context
                                </Button>
                            </div>
                        </div>
                    </div>

                </div>

            </div>
        </div >
    );
}
