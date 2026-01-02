import { useState } from "react";
import { Card } from "@/components/ui/card";
import { ChevronDown, ChevronUp, Edit } from "lucide-react";

export interface GameContextDataE {
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
    updated_at: Date;
}

interface GameDropdownProps {
    gameContexts: GameContextDataE[];
    onEdit: (game: GameContextDataE) => void;
    selectedGame: GameContextDataE | null;
}

export default function GameDropdown({ gameContexts, onEdit, selectedGame }: GameDropdownProps) {
    const [openIndex, setOpenIndex] = useState<number | null>(null);

    const toggleOpen = (index: number, e: React.MouseEvent) => {
        e.stopPropagation();
        setOpenIndex(openIndex === index ? null : index);
    };

    return (
        <div className="w-full max-w-3xl mx-auto space-y-2">
            <h2 className="mb-4 text-lg font-semibold text-white">Existing Game Contexts</h2>

            {gameContexts.length === 0 && (
                <p className="text-center text-gray-400">No game contexts available.</p>
            )}

            {gameContexts.map((game, index) => (
                <Card
                    key={game.id}
                    className={`w-full text-white border transition-colors ${selectedGame?.id === game.id
                            ? "border-purple-500 bg-purple-900/20"
                            : "border-gray-600 hover:border-gray-500"
                        }`}
                >
                    <div
                        className="flex items-center justify-between p-4 cursor-pointer"
                        onClick={(e) => toggleOpen(index, e)}
                    >
                        <div>
                            <p className="font-bold">{game.game_title || "Untitled Game"}</p>
                            <p className="text-sm text-gray-400">
                                {game.studio_name} • Updated: {new Date(game.updated_at).toLocaleDateString()}
                            </p>
                        </div>
                        <div className="text-gray-400">
                            {openIndex === index ? <ChevronUp /> : <ChevronDown />}
                        </div>
                    </div>

                    {openIndex === index && (
                        <div className="p-4 text-gray-200 border-t border-gray-700">
                            <div className="mb-4 space-y-2 text-sm">
                                <p><span className="text-gray-400">Title::</span> {game.game_title || "N/A"}</p>
                                <p><span className="text-gray-400">Platforms:</span> {game.platforms?.join(", ") || "N/A"}</p>
                                <p><span className="text-gray-400">Genre:</span> {[game.primary_genre, game.subgenre].filter(Boolean).join(" / ") || "N/A"}</p>
                                <p><span className="text-gray-400">Marketing Goal:</span> {game.marketing_objective || "N/A"}</p>
                                <p><span className="text-gray-400">Summary:</span> {game.game_summary || "N/A"}</p>
                            </div>

                            <button
                                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white transition-colors bg-purple-600 rounded hover:bg-purple-700"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onEdit(game);
                                }}
                            >
                                <Edit className="w-4 h-4" /> Edit Context
                            </button>
                        </div>
                    )}
                </Card>
            ))}
        </div>
    );
}