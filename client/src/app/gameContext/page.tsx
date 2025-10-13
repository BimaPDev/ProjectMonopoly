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

interface GameContextData {
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
    const [loading, setLoading] = useState(false);
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

    const handleInputChange = (field: keyof GameContextData, value: string | string[]) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async () => {
        // TODO: Implement save to database
        console.log("Saving to database:", formData);
        toast({
            title: "Coming soon!",
            description: "Save to database functionality will be implemented next.",
        });
    };

    if (!inputMethod) {
        return (
            <div className="flex flex-col min-h-screen p-10 text-white">
                <div className="flex flex-col justify-start ml-10">
                    <h1 className="text-3xl font-bold">Add Game Context</h1>
                    <h2 className="text-slate-400">Choose how you'd like to add game information</h2>
                </div>
                <div className="grid gap-6 mt-5 md:grid-cols-2">
                    <div className="flex flex-col items-center justify-center max-w-xl border hover:border-purple-500">
                        <div className="p-5 rounded-full bg-blue-400/70 "> <Upload /></div>
                        hi
                    </div>
                    <div>

                    </div>
                </div>
            </div>
        );
    }
    return (
        <div>

        </div>
    );
}
