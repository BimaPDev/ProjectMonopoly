"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { FileText, Loader2, Upload, CheckCircle2 } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { useGroup } from "../../components/groupContext";
import { TriangleAlert } from "lucide-react";
import {
    EyeClosed,
    Plus,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { useRef } from "react";
import FormField from "@/components/ui/form-field";
import GameDropdown from "@/components/GameContextItem";
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
    additional_info: string;
}
interface GameContextDataEdit {
    id: number;
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
    additional_info: string;
    created_at: Date;
    updated_at: Date
}

export default function GameContextPage() {
    const [inputMethod, setInputMethod] = useState<"upload" | "manual" | null>(null);
    const [file, setFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [loading, setLoading] = useState(false);
    const { activeGroup } = useGroup();
    const [extractedData, setExtractedData] = useState<GameContextData | null>(null);
    const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
    const [groupGameContexts, setGroupGameContexts] = useState<GameContextDataEdit[]>([]);
    const [selectedGame, setSelectedGame] = useState<GameContextDataEdit | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editingGameId, setEditingGameId] = useState<number | null>(null);
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
        additional_info: "",
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

            const res = await fetch(`/api/games/extract`, {
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
        const fieldErrors: Record<string, string> = {};

        // Required fields
        if (!formData.game_title?.trim()) {
            errors.push("Game title is required.")
            fieldErrors.game_title = "Game title is required."
        };
        if (!formData.studio_name?.trim()) {
            errors.push("Studio name is required.")
            fieldErrors.studio_name = "Studio/ Developer name is required."
        };
        if (!formData.game_summary?.trim()) {
            errors.push("Game summary is required.")
            fieldErrors.game_summary = "Game summary is required."
        };

        // Array field validation
        if (!formData.platforms || formData.platforms.length === 0) {
            errors.push("At least one platform must be specified.");
            fieldErrors.platforms = "At least one platform must be specified."
        }

        // Marketing objective validation (radio button)
        if (!formData.marketing_objective?.trim()) {
            errors.push("Please select a marketing objective.");
            fieldErrors.marketing_objective = "Please select a marketing objective."
        }

        return {
            isValid: errors.length === 0,
            errors,
            fieldErrors
        };
    }

    const handleReset = () => {
        setFormData({
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
            additional_info: "",
        });
        setExtractedData(null);
        setFile(null);
        setIsEditing(false);
        setEditingGameId(null);
        setSelectedGame(null);
    }


    const handleInputChange = (field: keyof GameContextData, value: string | string[]) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
        setFieldErrors((prev) => ({ ...prev, [field]: "" }))
    };

    const handleSubmit = async () => {
        const validation = validateGameContext();
        if (!validation.isValid) {
            setFieldErrors(validation.fieldErrors);
            toast({
                title: "Validation Error",
                description: validation.errors.join('\n'),
                variant: "destructive",
            });
            return;
        }

        try {
            const payload = {
                ...formData,
                group_id: activeGroup?.ID
            };

            const url = isEditing
                ? `/api/games/update/${editingGameId}`
                : `/api/games/input`;

            const res = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`
                },
                body: JSON.stringify(payload),
            });

            const body = await res.json();

            if (!res.ok) {
                toast({
                    title: "Error",
                    description: `${body}`,
                    variant: "destructive",
                });
            } else {
                toast({
                    title: isEditing ? "Updated Successfully" : "Saved Successfully",
                    description: isEditing ? "Game context updated" : "Your form was saved",
                });
                fetchGameContexts();
                if (isEditing) {
                    setIsEditing(false);
                    setEditingGameId(null);
                    setInputMethod(null);
                    handleReset();
                }
            }
        } catch (error) {
            toast({
                title: "Error",
                description: `${error}`,
                variant: "destructive",
            });
        }
    };
    const normalizeString = (value: any): string => {
        if (value && typeof value === "object" && "Valid" in value) {
            return value.Valid ? value.String : "";
        }
        if (typeof value === "string") {
            return value;
        }
        return "";
    };
    const normalizeArray = (value: any): string[] => {
        if (Array.isArray(value)) return value;
        if (typeof value === "string" && value.length > 0) return [value];
        return [];
    };

    const fetchGameContexts = async () => {
        try {
            if (activeGroup?.ID) {
                const res = await fetch(`/api/games/view/${activeGroup.ID}`, {
                    method: "GET",
                    headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
                })
                const body = await res.json();
                const gameArray = Array.isArray(body) ? body : body ? [body] : [];

                const normalized: GameContextDataEdit[] = gameArray.map((gc: any) => ({
                    id: gc.id,
                    game_title: normalizeString(gc.game_title),
                    studio_name: normalizeString(gc.studio_name),
                    game_summary: normalizeString(gc.game_summary),
                    engine_tech: normalizeString(gc.engine_tech),
                    primary_genre: normalizeString(gc.primary_genre),
                    subgenre: normalizeString(gc.subgenre),
                    key_mechanics: normalizeString(gc.key_mechanics),
                    playtime_length: normalizeString(gc.playtime_length),
                    art_style: normalizeString(gc.art_style),
                    tone: normalizeString(gc.tone),
                    intended_audience: normalizeString(gc.intended_audience),
                    age_range: normalizeString(gc.age_range),
                    player_motivation: normalizeString(gc.player_motivation),
                    comparable_games: normalizeString(gc.comparable_games),
                    marketing_objective: normalizeString(gc.marketing_objective),
                    key_events_dates: normalizeString(gc.key_events_dates),
                    call_to_action: normalizeString(gc.call_to_action),
                    content_restrictions: normalizeString(gc.content_restrictions),
                    competitors_to_avoid: normalizeString(gc.competitors_to_avoid),
                    additional_info: normalizeString(gc.additional_info),

                    platforms: normalizeArray(gc.platforms),

                    created_at: gc.created_at ?? "",
                    updated_at: gc.updated_at ?? "",
                }));
                setGroupGameContexts(normalized);
            }
        } catch (error) {
            console.log(error);
        }
    }
    const handleGoBack = () => {
        setInputMethod(null);
        setSelectedGame(null);
    }
    const handleContextSelection = (game: GameContextDataEdit) => {
        setSelectedGame(game);
    }
    useEffect(() => {
        fetchGameContexts();
    }, [activeGroup])
    if (!activeGroup) {
        return (
            <div className="flex items-center justify-center h-[400px]">
                <Card className="p-8 text-center bg-card border-border">
                    <EyeClosed className="w-16 h-16 mx-auto mb-4 text-amber-500" />
                    <h3 className="mb-2 text-xl font-semibold">No Group Selected</h3>
                    <p className="text-muted-foreground">Please select a group from the sidebar to view.</p>
                </Card>
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
                <div className="flex flex-col items-center justify-center w-full mt-5">
                    <GameDropdown
                        gameContexts={groupGameContexts}
                        selectedGame={selectedGame}
                        onEdit={(game) => {
                            setSelectedGame(game);
                            setIsEditing(true);
                            setEditingGameId(game.id);
                            setFormData({
                                game_title: game.game_title,
                                studio_name: game.studio_name,
                                game_summary: game.game_summary,
                                platforms: game.platforms,
                                engine_tech: game.engine_tech,
                                primary_genre: game.primary_genre,
                                subgenre: game.subgenre,
                                key_mechanics: game.key_mechanics,
                                playtime_length: game.playtime_length,
                                art_style: game.art_style,
                                tone: game.tone,
                                intended_audience: game.intended_audience,
                                age_range: game.age_range,
                                player_motivation: game.player_motivation,
                                comparable_games: game.comparable_games,
                                marketing_objective: game.marketing_objective,
                                key_events_dates: game.key_events_dates,
                                call_to_action: game.call_to_action,
                                content_restrictions: game.content_restrictions,
                                competitors_to_avoid: game.competitors_to_avoid,
                                additional_info: game.additional_info,
                            });
                            setInputMethod("manual");
                        }}
                    />
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
                        onClick={() => handleGoBack()}
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
                                    Supports PNG or TXT (max. 10MB)
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
                                <h2 className="text-slate-500"> Provide details about your game <span className="text-red-500">*</span> = Required field</h2>
                            </div>
                        }
                    </div>
                    <div className="flex">
                        <Button
                            variant="ghost"
                            onClick={() => {
                                setInputMethod(null);
                            }}
                            className="text-gray-400 hover:text-white"
                        >
                            ← Go Back
                        </Button>
                        <Button
                            variant="ghost"
                            onClick={() => {
                                handleReset();
                            }}
                            className="text-gray-400 hover:text-white"
                        >
                            Start Over
                        </Button>
                    </div>
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
                            <div className="flex items-baseline w-full gap-4 mt-4">
                                <FormField
                                    label="Title"
                                    placeholder="Enter title of game"
                                    id="game_title"
                                    value={formData.game_title}
                                    onChange={(value) => handleInputChange("game_title", value.target.value)}
                                    required
                                    error={fieldErrors.game_title}
                                    className="w-[50%]"
                                />
                                <FormField
                                    label="Studio / Developer Name"
                                    placeholder="Your Company"
                                    id="studio_name"
                                    value={formData.studio_name}
                                    required
                                    error={fieldErrors.studio_name}
                                    onChange={(value) => handleInputChange("studio_name", value.target.value)}
                                    className="w-[50%]"
                                />
                            </div>
                            <div className="mt-4">
                                <Label htmlFor="game_summary">Summary/Description <span className="text-red-500">*</span></Label>
                                <Textarea
                                    id="game_summary"
                                    value={formData.game_summary}
                                    required
                                    onChange={(value) => { handleInputChange("game_summary", value.target.value) }}
                                    placeholder="Summary"
                                    className={fieldErrors.game_summary ? "p-2 !border-red-500 focus-visible:ring-red-500" : "p-2"}
                                />
                                {fieldErrors.game_summary &&
                                    <p className="mt-1 text-sm text-red-500">{fieldErrors.game_summary}</p>
                                }
                            </div>
                            <div className="grid gap-4 mt-4 md:grid-cols-2">
                                <FormField
                                    label="Platforms"
                                    placeholder="PC, Console, Mobile, VR"
                                    id="platforms"
                                    required
                                    error={fieldErrors.platforms}
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
                            <div className="w-full mt-6 border border-slate-500/60"></div>
                            {/* section 2 */}
                            <div className="mt-6">
                                <h1 className="text-xl font-bold">2. Game's Identity</h1>
                                <p className="text-sm text-slate-500">Game's genre and style</p>
                                <div className="flex flex-col">
                                    <div className="flex items-baseline w-full gap-4 mt-4">
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
                                            placeholder="e.g. Roguelike, sandbox"
                                            id="subgenre"
                                            value={formData.subgenre}
                                            onChange={(value) => handleInputChange("subgenre", value.target.value)}
                                            className="w-[50%]"
                                        />
                                    </div>
                                </div>
                                <div className="w-full mt-4">
                                    <Label htmlFor="key_mechanics">Key mechanics / Features</Label>
                                    <Textarea
                                        id="key_mechanics"
                                        value={formData.key_mechanics}
                                        onChange={(value) => { handleInputChange("key_mechanics", value.target.value) }}
                                        placeholder="e.g. Customizable Cars, Procedural Levels"
                                        className="p-2"
                                    />
                                </div>
                                <div className="flex gap-4 mt-4">
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
                            <div className="w-full mt-6 border border-slate-500/60"></div>
                            {/* section 3 */}
                            <div className="mt-6">
                                <h1 className="text-xl font-bold">3. Target Audience</h1>
                                <p className="text-sm text-slate-500">Who will want to play the game?</p>

                                <div className="flex flex-col">
                                    <div className="flex items-baseline w-full gap-4 mt-4">
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
                                    <div className="w-full mt-4">
                                        <Label htmlFor="Player Motivation">Player Motivation</Label>
                                        <Textarea
                                            id="player_motivation"
                                            value={formData.player_motivation}
                                            onChange={(value) => { handleInputChange("player_motivation", value.target.value) }}
                                            placeholder="What do players get out of this? Fun, relaxation, mastery, creativity, competition, etc."
                                            className="p-2"
                                        />
                                    </div>

                                    <div className="flex items-baseline w-full gap-4 mt-4">
                                        <FormField
                                            label="Comparable Games"
                                            placeholder="e.g. Inspired by Stardew Valley and Animal Crossing."
                                            id="comparable_games"
                                            value={formData.comparable_games}
                                            onChange={(value) => handleInputChange("comparable_games", value.target.value)}
                                            className="w-full"
                                        />

                                    </div>
                                </div>
                            </div>
                            <div className="w-full mt-6 border border-slate-500/60"></div>

                            {/* section 4 */}
                            <div className="mt-6">
                                <h1 className="text-xl font-bold">4. Marketing Goals</h1>
                                <p className="text-sm text-slate-500">What success looks like for your campaign</p>
                                <div className="flex flex-col">
                                    <div className="flex flex-wrap justify-between gap-5 mt-4">
                                        {radioButtons.map((option) => {
                                            return (
                                                <div className={`p-2 border ${fieldErrors.marketing_objective ? "border-red-500" : "border-gray-50/20"}`}>
                                                    <label key={option.value} className="flex items-center gap-2">
                                                        <input
                                                            type="radio"
                                                            name="marketing_objective"
                                                            value={option.value}
                                                            required
                                                            onChange={() => handleInputChange("marketing_objective", option.value)}
                                                        />
                                                        <span>{option.label}</span>
                                                    </label>
                                                </div>
                                            );
                                        })}
                                    </div>
                                    {fieldErrors.marketing_objective && (
                                        <p className="mt-1 text-sm text-red-500">{fieldErrors.marketing_objective}</p>
                                    )}
                                </div>
                                <div className="flex items-baseline w-full gap-4 mt-4">
                                    <div className="flex flex-col w-full">
                                        <Label htmlFor="Key Events">Key Events</Label>
                                        <Textarea
                                            placeholder="e.g., demo release, festival submission, convention appearance"
                                            id="key_events_dates"
                                            value={formData.key_events_dates}
                                            onChange={(value) => handleInputChange("key_events_dates", value.target.value)}
                                            className="w-full p-2 mt-2 border-zinc-200"
                                        />
                                    </div>
                                    <FormField
                                        label="Call To Action"
                                        placeholder="e.g Add to Wishlist, Play the Demo"
                                        id="call_to_action"
                                        value={formData.call_to_action}
                                        onChange={(value) => handleInputChange("call_to_action", value.target.value)}
                                        className="w-[50%]"
                                    />
                                </div>
                            </div>
                            <div className="w-full mt-6 border border-slate-500/60"></div>
                            {/* stage 5 */}
                            <div className="mt-6">
                                <h1 className="text-xl font-bold">5. Restrictions / Boundaries</h1>
                                <p className="text-sm text-slate-500">Helps avoid bad or off-brand outputs.</p>
                                <div className="flex flex-col">
                                    <div className="flex items-baseline w-full gap-4 mt-4">
                                        <div className="flex flex-col w-full">
                                            <Label htmlFor="Content Restrictions">Content Restrictions</Label>
                                            <Textarea
                                                placeholder="e.g. “No mention of gambling with real money”, “Avoid dark humor"
                                                id="content_restrictions"
                                                value={formData.content_restrictions}
                                                onChange={(value) => handleInputChange("content_restrictions", value.target.value)}
                                                className="w-full p-2 mt-2"
                                            />
                                        </div>
                                        <div className="flex flex-col w-full">
                                            <Label htmlFor="Competitors">Competitors</Label>
                                            <Textarea
                                                placeholder="e.g. Don't reference real-world casinos or violence."
                                                id="competitors_to_avoid"
                                                value={formData.competitors_to_avoid}
                                                onChange={(value) => handleInputChange("competitors_to_avoid", value.target.value)}
                                                className="w-full mt-2 border-zinc-200"
                                            />
                                        </div>
                                    </div>
                                </div>
                                <div className="flex flex-col mt-4">
                                    <Label htmlFor="Additional Info">Aditional Info</Label>
                                    <Textarea
                                        placeholder="Enter in any additional info about your product"
                                        id="additional_info"
                                        value={formData.additional_info}
                                        onChange={(value) => handleInputChange("additional_info", value.target.value)}
                                        className="p-2 mt-2 border-zinc-200"
                                    />
                                </div>
                            </div>
                            <Separator className="mt-6 bg-gray-800" />

                            {/* Submit Button */}
                            <div className="flex justify-end gap-4 mt-6">
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
                                    size="lg"
                                >
                                    {isEditing ? "Update Game Context" : "Save Game Context"}
                                </Button>
                            </div>
                        </div>
                    </div>

                </div>

            </div>
        </div >
    );
}
