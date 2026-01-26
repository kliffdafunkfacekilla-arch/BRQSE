import { useState, useEffect } from 'react';
import { Skull, Clock, Dices, ChevronRight, Map, Flag } from 'lucide-react';

interface Atmosphere {
    tone: string;
    descriptor: string;
}

interface Quest {
    title: string;
    description: string;
    progress: string;
    completed: boolean;
}

interface WorldState {
    chaos_level: number;
    chaos_clock: number;
    tension_threshold: number;
    is_doomed: boolean;
    atmosphere: Atmosphere;
    quest: Quest;
}

interface Scene {
    text: string;
    encounter_type: string;
    enemy_data: any;
    remaining: number;
}

const API_BASE = 'http://localhost:5001/api';

export default function SceneStack({ onLog, onSceneChange }: { onLog: (msg: string, type: 'info' | 'combat') => void, onSceneChange?: () => void }) {
    const [world, setWorld] = useState<WorldState | null>(null);
    const [currentScene, setCurrentScene] = useState<Scene | null>(null);
    const [loading, setLoading] = useState(false);

    // Poll world status
    const fetchStatus = async () => {
        try {
            const res = await fetch(`${API_BASE}/world/status`);
            const data = await res.json();
            setWorld(data);
            if (data.current_scene) {
                setCurrentScene(data.current_scene);
            }
        } catch (e) {
            console.error("Failed to fetch world status");
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleRollTension = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/world/tension/roll`, { method: 'POST' });
            const data = await res.json();

            let msgType: 'info' | 'combat' = 'info';
            if (data.result === 'EVENT' || data.result === 'CHAOS_EVENT') {
                msgType = 'combat';
            }

            onLog(`Tension Roll: ${data.result}`, msgType);
            fetchStatus();
        } catch (e) {
            onLog("Failed to roll tension", 'info');
        }
        setLoading(false);
    };

    const handleAdvanceScene = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/world/scene/advance`, { method: 'POST' });
            const data = await res.json();
            setCurrentScene(data);
            onLog(`Entered: ${data.text}`, 'info');
            fetchStatus();
            onSceneChange?.();
        } catch (e) {
            onLog("Failed to advance scene", 'info');
        }
        setLoading(false);
    };

    const generateQuest = async () => {
        setLoading(true);
        try {
            await fetch(`${API_BASE}/world/quest/generate`, { method: 'POST' });
            onLog("New Quest Generated", 'info');
            // Slight delay to allow backend to process
            setTimeout(() => {
                fetchStatus();
                onSceneChange?.();
            }, 500);
        } catch (e) {
            onLog("Failed to generate quest", 'info');
        }
        setLoading(false);
    };

    if (!world) return <div className="p-4 text-xs">Loading World State...</div>;

    const clockColor = world.is_doomed ? 'text-red-500 animate-pulse' :
        world.chaos_clock >= 9 ? 'text-orange-500' :
            'text-stone-400';

    const hasQuest = world.quest && world.quest.title !== "None";

    return (
        <div className="absolute top-4 left-4 z-[60] w-64 bg-black/90 border border-stone-800 p-3 backdrop-blur-sm pointer-events-auto shadow-[0_0_20px_rgba(0,0,0,0.8)]">

            {/* ATMOSPHERE HEADER */}
            <div className={`text-xs font-bold uppercase tracking-widest mb-2 pb-2 border-b border-stone-800 ${clockColor}`}>
                {world.atmosphere.tone} ATMOSPHERE
            </div>

            {/* METRICS GRID */}
            <div className="grid grid-cols-2 gap-2 mb-3">
                {/* CHAOS CLOCK */}
                <div className="bg-stone-900/50 p-2 rounded flex flex-col items-center border border-stone-800">
                    <div className="flex items-center gap-1 text-[10px] text-stone-500 uppercase mb-1">
                        <Clock size={10} /> Chaos Clock
                    </div>
                    <div className="text-xl font-mono relative">
                        {world.chaos_clock} <span className="text-stone-600 text-xs">/ 12</span>
                        {world.is_doomed && <Skull size={12} className="absolute -top-1 -right-4 text-red-500 animate-bounce" />}
                    </div>
                </div>

                {/* TENSION DIE */}
                <div className="bg-stone-900/50 p-2 rounded flex flex-col items-center border border-stone-800 cursor-pointer hover:bg-stone-800 transition-colors"
                    onClick={handleRollTension}>
                    <div className="flex items-center gap-1 text-[10px] text-stone-500 uppercase mb-1">
                        <Dices size={10} /> Tension (1-{world.tension_threshold})
                    </div>
                    <div className="text-xl font-mono text-[#00f2ff]">
                        d10
                    </div>
                </div>
            </div>

            {/* QUEST & SCENE CARD */}
            <div className="mb-3 space-y-2">

                {/* Active Quest Header */}
                {hasQuest ? (
                    <div className="border border-stone-800 bg-stone-900/80 p-2 rounded">
                        <div className="flex justify-between items-start mb-1">
                            <div className="flex items-center gap-1 text-[10px] text-[#00f2ff] uppercase font-bold">
                                <Flag size={10} /> {world.quest.title}
                            </div>
                            <div className="text-[9px] text-stone-500">{world.quest.progress}</div>
                        </div>
                        <div className="text-[10px] text-stone-400 italic leading-tight">
                            "{world.quest.description}"
                        </div>
                    </div>
                ) : (
                    <button onClick={generateQuest} disabled={loading} className="w-full py-3 border border-dashed border-stone-700 text-stone-500 text-xs hover:text-[#00f2ff] hover:border-[#00f2ff]">
                        + GENERATE NEW QUEST
                    </button>
                )}

                {/* Current Scene Node */}
                {currentScene && hasQuest && (
                    <div className="ml-2 relative border-l-2 border-stone-700 pl-3 py-1">
                        <div className="absolute -left-[5px] top-3 w-2 h-2 rounded-full bg-stone-500" />

                        <div className="text-[9px] text-stone-500 uppercase mb-0.5 flex justify-between">
                            <span>Current Location</span>
                        </div>

                        <div className="bg-stone-900 border border-stone-700 p-2 relative overflow-hidden group">
                            <div className="relative z-10">
                                <div className="text-sm font-bold text-stone-200 mb-1">{currentScene.text}</div>
                                <div className={`text-[10px] inline-block px-1 rounded ${currentScene.encounter_type === 'COMBAT' ? 'bg-red-900/50 text-red-200 border border-red-800' :
                                    'bg-stone-800 text-stone-400 border border-stone-700'
                                    }`}>
                                    {currentScene.encounter_type}
                                </div>
                            </div>
                            {/* Advance Button (Hover) */}
                            <div className="absolute inset-0 bg-black/80 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                                onClick={handleAdvanceScene}>
                                <div className="flex items-center gap-1 text-xs font-bold text-[#00f2ff]">
                                    ADVANCE <ChevronRight size={14} />
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* DESCRIPTOR */}
            {world.atmosphere.descriptor && (
                <div className="text-[10px] text-stone-400 italic font-serif border-l-2 border-stone-700 pl-2">
                    "{world.atmosphere.descriptor}"
                </div>
            )}
        </div>
    );
}
