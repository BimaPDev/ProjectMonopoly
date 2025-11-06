"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Loader2, AlertCircle, CheckCircle2, Sparkles } from "lucide-react";
import { toast } from "@/hooks/use-toast";

interface LLMTestResponse {
    success: boolean;
    message: string;
    duration?: string;
    error?: string;
}

export default function LLMTestPage() {
    const [prompt, setPrompt] = useState("");
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState<LLMTestResponse | null>(null);

    const handleTest = async () => {
        if (!prompt.trim()) {
            toast({
                title: "Empty Prompt",
                description: "Please enter a prompt to test the LLM",
                variant: "destructive",
            });
            return;
        }

        setLoading(true);
        setResponse(null);

        try {
            const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/test/llm`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`,
                },
                body: JSON.stringify({ prompt }),
            });

            const data = await res.json();
            setResponse(data);

            if (data.success) {
                toast({
                    title: "Success!",
                    description: "LLM responded successfully",
                });
            } else {
                toast({
                    title: "LLM Error",
                    description: data.error || "Something went wrong",
                    variant: "destructive",
                });
            }
        } catch (err) {
            const errorResponse: LLMTestResponse = {
                success: false,
                message: "",
                error: err instanceof Error ? err.message : "Network error occurred",
            };
            setResponse(errorResponse);
            toast({
                title: "Request Failed",
                description: err instanceof Error ? err.message : "Network error occurred",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    const handleClear = () => {
        setPrompt("");
        setResponse(null);
    };

    return (
        <div className="min-h-screen p-8 text-white">
            <div className="max-w-4xl mx-auto">
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 rounded-lg bg-purple-500/20">
                            <Sparkles className="w-6 h-6 text-purple-400" />
                        </div>
                        <h1 className="text-3xl font-bold">LLM Test Console</h1>
                    </div>
                    <p className="text-slate-400">
                        Test the LLM with custom prompts and see the responses
                    </p>
                </div>

                <div className="space-y-6">
                    {/* Input Section */}
                    <Card className="bg-gray-900 border-gray-800">
                        <CardHeader>
                            <CardTitle className="text-white">Test Prompt</CardTitle>
                            <CardDescription className="text-gray-400">
                                Enter a prompt to send to the LLM
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <Label htmlFor="prompt" className="text-white">
                                    Your Prompt
                                </Label>
                                <Textarea
                                    id="prompt"
                                    value={prompt}
                                    onChange={(e) => setPrompt(e.target.value)}
                                    placeholder="e.g., Extract game information from this text: ..."
                                    className="min-h-[150px] mt-2 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                                    disabled={loading}
                                />
                            </div>

                            <div className="flex gap-3">
                                <Button
                                    onClick={handleTest}
                                    disabled={loading || !prompt.trim()}
                                    className="bg-purple-600 hover:bg-purple-700"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                            Processing...
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles className="w-4 h-4 mr-2" />
                                            Test LLM
                                        </>
                                    )}
                                </Button>
                                <Button
                                    onClick={handleClear}
                                    variant="outline"
                                    disabled={loading}
                                    className="text-gray-300 border-gray-700 hover:bg-gray-800"
                                >
                                    Clear
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Response Section */}
                    {response && (
                        <Card className="bg-gray-900 border-gray-800">
                            <CardHeader>
                                <div className="flex items-center gap-2">
                                    {response.success ? (
                                        <CheckCircle2 className="w-5 h-5 text-green-400" />
                                    ) : (
                                        <AlertCircle className="w-5 h-5 text-red-400" />
                                    )}
                                    <CardTitle className={response.success ? "text-green-400" : "text-red-400"}>
                                        {response.success ? "Success" : "Error"}
                                    </CardTitle>
                                </div>
                            </CardHeader>
                            <CardContent>
                                {response.success ? (
                                    <div className="space-y-4">
                                        {response.duration && (
                                            <div className="flex items-center gap-2 text-sm text-gray-400">
                                                <span className="font-semibold">Duration:</span>
                                                <span className="text-green-400">{response.duration}</span>
                                            </div>
                                        )}
                                        <div className="space-y-2">
                                            <Label className="text-white">LLM Response:</Label>
                                            <pre className="p-4 overflow-auto text-sm rounded-lg bg-gray-950 text-gray-300 max-h-[400px]">
                                                {response.message}
                                            </pre>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-2">
                                        <Label className="text-red-400">Error Details:</Label>
                                        <div className="p-4 text-sm border rounded-lg bg-red-950/20 border-red-900/50 text-red-300">
                                            {response.error}
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}

                    {/* Examples Section */}
                    <Card className="bg-gray-900 border-gray-800">
                        <CardHeader>
                            <CardTitle className="text-white">Example Prompts</CardTitle>
                            <CardDescription className="text-gray-400">
                                Click to use these example prompts
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            <Button
                                variant="ghost"
                                className="justify-start w-full text-left text-gray-300 hover:bg-gray-800 hover:text-white"
                                onClick={() => setPrompt('Extract game info as JSON: {"game_title":"","studio_name":"","genre":""}\n\nDocument: Super Adventure is a platformer game by Indie Studios for PC and Console.')}
                            >
                                Extract game information from text
                            </Button>
                            <Button
                                variant="ghost"
                                className="justify-start w-full text-left text-gray-300 hover:bg-gray-800 hover:text-white"
                                onClick={() => setPrompt('List 5 creative marketing taglines for a space exploration game')}
                            >
                                Generate marketing taglines
                            </Button>
                            <Button
                                variant="ghost"
                                className="justify-start w-full text-left text-gray-300 hover:bg-gray-800 hover:text-white"
                                onClick={() => setPrompt('Summarize this game description in one sentence: A fast-paced racing game with customizable cars, dynamic weather, and realistic physics simulation.')}
                            >
                                Summarize game description
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
