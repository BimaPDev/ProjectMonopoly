import { TriangleAlert } from "lucide-react";
import { Card } from "@/components/ui/card";

interface NoGroupWarningProps {
    featureName: string;
}

export function NoGroupWarning({ featureName }: NoGroupWarningProps) {
    return (
        <div className="flex items-center justify-center min-h-[400px]">
            <Card className="max-w-md p-8 text-center bg-zinc-900/50 border-zinc-800">
                <div className="flex justify-center mb-4">
                    <div className="p-3 rounded-full bg-yellow-500/20">
                        <TriangleAlert className="w-8 h-8 text-yellow-400" />
                    </div>
                </div>
                <h2 className="text-xl font-bold mb-2">Group Required</h2>
                <p className="text-muted-foreground mb-6">
                    Please select or create a group to access {featureName}.
                </p>
                <p className="text-sm text-muted-foreground">
                    Use the group selector in the sidebar to choose an existing group
                    or create a new one.
                </p>
            </Card>
        </div>
    );
}

export default NoGroupWarning;
