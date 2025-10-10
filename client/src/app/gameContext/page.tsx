"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function GameContextTest() {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setResponse(null);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError("Please select a file first");
            return;
        }

        setLoading(true);
        setError(null);
        setResponse(null);

        try {
            const formData = new FormData();
            formData.append("file", file);

            const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/games/extract`, {
                method: "POST",
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
                body: formData,
            });

            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(`Upload failed: ${errorText}`);
            }

            const data = await res.json();
            setResponse(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Upload failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen p-8 text-white bg-black">
            <div className="max-w-4xl mx-auto space-y-6">
                <h1 className="text-3xl font-bold">Game Context Extraction Test</h1>

                <Card className="bg-gray-900 border-gray-800">
                    <CardHeader>
                        <CardTitle className="text-white">Upload Test File</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <Input
                                type="file"
                                accept=".txt,.pdf"
                                onChange={handleFileChange}
                                className="text-white bg-gray-800 border-gray-700"
                            />
                            {file && (
                                <p className="mt-2 text-sm text-gray-400">
                                    Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
                                </p>
                            )}
                        </div>

                        <Button
                            onClick={handleUpload}
                            disabled={!file || loading}
                            className="bg-blue-600 hover:bg-blue-700"
                        >
                            {loading ? "Processing..." : "Upload & Extract"}
                        </Button>
                    </CardContent>
                </Card>

                {error && (
                    <Card className="bg-red-900/20 border-red-500/30">
                        <CardContent className="pt-6">
                            <h3 className="font-semibold text-red-400">Error:</h3>
                            <pre className="mt-2 text-sm text-red-300 whitespace-pre-wrap">{error}</pre>
                        </CardContent>
                    </Card>
                )}

                {response && (
                    <Card className="bg-gray-900 border-gray-800">
                        <CardHeader>
                            <CardTitle className="text-white">Backend Response:</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <pre className="p-4 overflow-auto text-sm text-gray-300 rounded bg-gray-950">
                                {JSON.stringify(response, null, 2)}
                            </pre>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
}
