import { useState, useEffect } from 'react';
import { Skull, Clock, Dices, ChevronRight, Flag, ChevronUp, ChevronDown } from 'lucide-react';

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

const API_BASE = '/api';

export default function SceneStack({ onLog, onSceneChange }: { onLog: (msg: string, type: 'info' | 'combat') => void, onSceneChange?: () => void }) {
    const [world, setWorld] = useState<WorldState | null>(null);
    const [currentScene, setCurrentScene] = useState<Scene | null>(null);
    const [loading, setLoading] = useState(false);
    const [isCollapsed, setIsCollapsed] = useState(false);

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
        <div className={`absolute top-4 left-4 z-[60] ${isCollapsed ? 'w-48' : 'w-56'} bg-black/90 border border-stone-800 backdrop-blur-sm pointer-events-auto shadow-[0_0_20px_rgba(0,0,0,0.8)] transition-all duration-300`}>

            {/* HUD TOGGLE */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="absolute -bottom-6 left-0 bg-black/90 border border-stone-800 border-t-0 px-2 py-1 text-[8px] font-bold text-stone-500 hover:text-white flex items-center gap-1 transition-all"
            >
                {isCollapsed ? <ChevronDown size={8} /> : <ChevronUp size={8} />}
                {isCollapsed ? 'EXPAND HUD' : 'COLLAPSE HUD'}
            </button>

            {/* ATMOSPHERE HEADER */}
            <div className={`text-[10px] font-bold uppercase tracking-widest p-2 border-b border-stone-800 flex justify-between items-center ${clockColor}`}>
                <span>{world.atmosphere.tone} ATMOSPHERE</span>
                {isCollapsed && <Clock size={10} className="text-stone-500" />}
            </div>

            {!isCollapsed && (
                <div className="p-2">
                    {/* METRICS GRID */}
                    <div className="grid grid-cols-2 gap-1.5 mb-2">
                        {/* CHAOS CLOCK */}
                        <div className="bg-stone-900/50 p-1.5 rounded flex flex-col items-center border border-stone-800">
                            <div className="flex items-center gap-1 text-[8px] text-stone-500 uppercase mb-0.5">
                                <Clock size={8} /> Chaos
                            </div>
                            <div className="text-sm font-mono relative">
                                {world.chaos_clock} <span className="text-stone-600 text-[10px]">/ 12</span>
                                {world.is_doomed && <Skull size={10} className="absolute -top-1 -right-3 text-red-500 animate-bounce" />}
                            </div>
                        </div>

                        {/* TENSION DIE */}
                        <div className="bg-stone-900/50 p-1.5 rounded flex flex-col items-center border border-stone-800 cursor-pointer hover:bg-stone-800 transition-colors"
                            onClick={handleRollTension}>
                            <div className="flex items-center gap-1 text-[8px] text-stone-500 uppercase mb-0.5">
                                <Dices size={8} /> Tension
                            </div>
                            <div className="text-sm font-mono text-[#00f2ff]">
                                1-{world.tension_threshold}
                            </div>
                        </div>
                    </div>

                    {/* QUEST & SCENE CARD */}
                    <div className="space-y-1.5">
                        {hasQuest ? (
                            <div className="border border-stone-800 bg-stone-900/80 p-1.5 rounded">
                                <div className="flex justify-between items-start mb-0.5">
                                    <div className="flex items-center gap-1 text-[9px] text-[#00f2ff] uppercase font-bold truncate">
                                        <Flag size={9} /> {world.quest.title}
                                    </div>
                                    <div className="text-[8px] text-stone-500 shrink-0">{world.quest.progress}</div>
                                </div>
                                <div className="text-[9px] text-stone-500 italic leading-tight line-clamp-2">
                                    "{world.quest.description}"
                                </div>
                            </div>
                        ) : (
                            <button onClick={generateQuest} disabled={loading} className="w-full py-2 border border-dashed border-stone-700 text-stone-500 text-[10px] hover:text-[#00f2ff] hover:border-[#00f2ff]">
                                + NEW QUEST
                            </button>
                        )}

                        {currentScene && hasQuest && (
                            <div className="bg-stone-900 border border-stone-700 p-2 relative overflow-hidden group shadow-lg">
                                <div className="text-[9px] font-bold text-stone-200 mb-1 leading-tight truncate">{currentScene.text}</div>
                                <div className={`text-[8px] inline-block px-1 py-0.25 rounded font-bold uppercase tracking-wider ${currentScene.encounter_type === 'COMBAT' ? 'bg-red-900/50 text-red-200 border border-red-800' :
                                    'bg-stone-800 text-stone-400 border border-stone-700'
                                    }`}>
                                    {currentScene.encounter_type}
                                </div>

                                <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-all cursor-pointer hover:scale-110"
                                    onClick={handleAdvanceScene} title="Force Advance">
                                    <ChevronRight size={12} className="text-[#00f2ff]" />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* DESCRIPTOR */}
                    {world.atmosphere.descriptor && (
                        <div className="text-[9px] text-stone-500 italic font-serif border-l-2 border-stone-800 pl-2 mt-2 line-clamp-2">
                            "{world.atmosphere.descriptor}"
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
