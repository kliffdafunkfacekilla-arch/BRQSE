import { useState, useEffect } from 'react';
import { Heart, Activity, Brain, Zap, Shield, Sword } from 'lucide-react';
import Token from './Token';

const TILE_SIZE = 40;

interface Entity {
    id: string;
    x: number;
    y: number;
    type: string;
    team: 'player' | 'enemy' | 'neutral';
    hp?: number;
}

interface GameState {
    mode: string;
    player_pos: [number, number];
    scene: string;
    grid: number[][]; // 20x20
    explored: [number, number][]; // List of explored coords
    walls: [number, number][];    // List of wall coords
    objects: any[];
    enemies?: any[]; // New field
}

export default function GameVisualizer() {
    const [state, setState] = useState<GameState | null>(null);
    const [log, setLog] = useState<string[]>([]);

    // Polling fetch for now (socket later?)
    useEffect(() => {
        const fetchState = async () => {
            try {
                const res = await fetch('http://localhost:5001/api/game/state');
                const data = await res.json();
                setState(data);
            } catch (e) {
                // console.error(e);
            }
        };
        fetchState();
        const interval = setInterval(fetchState, 500); // 2Hz refresh
        return () => clearInterval(interval);
    }, []);

    const handleMove = async (x: number, y: number) => {
        if (!state) return;
        // Simple click-to-move for now
        // In real visualizer, we might show a path first
        try {
            const res = await fetch('http://localhost:5001/api/game/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ x, y })
            });
            const result = await res.json();
            if (result.result?.success || result.success) {
                // Wait for poll to update state
                const moveEvent = result.result?.event || result.event;
                if (moveEvent) {
                    setLog(prev => [`${moveEvent}!`, ...prev].slice(0, 5));
                }
            } else {
                const failReason = result.result?.reason || result.reason;
                setLog(prev => [`Move Failed: ${failReason}`, ...prev].slice(0, 5));
            }
        } catch (e) {
            console.error("Move failed");
        }
    };

    if (!state) return <div className="h-full flex items-center justify-center text-stone-500 animate-pulse">Connecting to Neural Link...</div>;

    // --- RENDER HELPERS ---
    const isExplored = (x: number, y: number) => {
        return state.explored.some(([ex, ey]) => ex === x && ey === y);
    };

    // Combine entities
    const entities: Entity[] = [
        { id: 'player', x: state.player_pos[0], y: state.player_pos[1], type: 'Hero', team: 'player', hp: 100 }
    ];

    // Objects
    state.objects.forEach((obj, i) => {
        entities.push({ id: `obj-${i}`, x: obj.x, y: obj.y, type: obj.type || 'Object', team: 'neutral' });
    });

    // Enemies (if any)
    if (state.enemies) {
        state.enemies.forEach((en, i) => {
            entities.push({ id: `enemy-${i}`, x: en.x, y: en.y, type: en.type || 'Enemy', team: 'enemy' });
        });
    }

    return (
        <div className="h-full w-full bg-[#020202] relative overflow-hidden flex flex-col font-sans">

            {/* TOP BAR / HUD */}
            <div className="h-16 bg-gradient-to-b from-black to-transparent z-20 flex items-center justify-between px-6 border-b border-white/5">
                <div className="flex items-center gap-4">
                    <div className="flex flex-col">
                        <div className="text-xs text-stone-500 font-bold uppercase tracking-widest">Active Scene</div>
                        <div className="text-stone-200 font-bold">{state.scene || 'Exploration'}</div>
                    </div>
                    {state.mode === 'COMBAT' && (
                        <div className="px-3 py-1 bg-red-900/50 border border-red-500 text-red-100 text-xs font-bold animate-pulse">
                            COMBAT ENGAGED
                        </div>
                    )}
                </div>

                {/* STATUS BAR (Mock) */}
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2 text-red-500">
                        <Heart size={16} fill="currentColor" />
                        <span className="font-mono font-bold">18/24</span>
                    </div>
                    <div className="flex items-center gap-2 text-blue-500">
                        <Brain size={16} fill="currentColor" />
                        <span className="font-mono font-bold">8/10</span>
                    </div>
                    <div className="flex items-center gap-2 text-green-500">
                        <Activity size={16} />
                        <span className="font-mono font-bold">12/12</span>
                    </div>
                </div>
            </div>

            {/* MAIN VIEWPORT */}
            <div className="flex-1 relative overflow-auto flex items-center justify-center cursor-crosshair bg-[#050505]">

                {/* GAME GRID */}
                <div
                    className="relative shadow-2xl transition-all duration-300"
                    style={{
                        width: state.grid.length * TILE_SIZE,
                        height: state.grid.length * TILE_SIZE,
                    }}
                >
                    {/* TILES LAYER */}
                    {state.grid.map((row, y) => (
                        row.map((tile, x) => {
                            const explored = isExplored(x, y);
                            if (!explored) return <div key={`${x}-${y}`} className="absolute bg-[#000]" style={{ left: x * TILE_SIZE, top: y * TILE_SIZE, width: TILE_SIZE, height: TILE_SIZE }} />;

                            let bgClass = 'bg-stone-800'; // Wall (0)
                            if (tile === 1) bgClass = 'bg-stone-900'; // Floor (1)
                            if (tile === 2) bgClass = 'bg-blue-900/30'; // Cover (2)
                            if (tile === 3) bgClass = 'bg-red-900/20'; // Enemy (3)
                            if (tile === 4) bgClass = 'bg-amber-900/40'; // Door (4)
                            if (tile === 5) bgClass = 'bg-green-900/20'; // Hazard (5)
                            if (tile === 6) bgClass = 'bg-yellow-900/30'; // Loot (6)

                            return (
                                <div
                                    key={`${x}-${y}`}
                                    onClick={() => handleMove(x, y)}
                                    className={`absolute border border-white/5 transition-colors duration-300 hover:bg-white/10 ${bgClass}`}
                                    style={{ left: x * TILE_SIZE, top: y * TILE_SIZE, width: TILE_SIZE, height: TILE_SIZE }}
                                >
                                    {/* Wall decoration */}
                                    {tile === 1 && <div className="absolute inset-1 bg-stone-700/50 rounded-sm" />}
                                </div>
                            );
                        })
                    ))}

                    {/* ENTITY LAYER */}
                    {entities.map(ent => (
                        <div
                            key={ent.id}
                            className="absolute transition-all duration-300 ease-out z-10 pointer-events-none"
                            style={{
                                left: ent.x * TILE_SIZE,
                                top: ent.y * TILE_SIZE,
                                width: TILE_SIZE,
                                height: TILE_SIZE
                            }}
                        >
                            <Token
                                name={ent.type}
                                team={ent.team === 'player' ? 'blue' : 'red'}
                                facing="down"
                            />
                        </div>
                    ))}

                </div>
            </div>

            {/* MESSAGE LOG OVERLAY */}
            <div className="absolute bottom-4 left-4 z-20 w-80 pointer-events-none">
                <div className="flex flex-col-reverse gap-1">
                    {log.map((entry, i) => (
                        <div key={i} className="bg-black/80 text-xs text-green-400 font-mono px-2 py-1 border-l-2 border-green-500 animate-slide-in">
                            {'>'} {entry}
                        </div>
                    ))}
                </div>
            </div>

            {/* ACTION BAR (Bottom) */}
            <div className="h-20 bg-stone-900 border-t border-stone-800 flex items-center justify-center gap-2 px-4 z-20">
                {/* SKILLS */}
                {[1, 2, 3, 4, 5].map(i => (
                    <button key={i} className="w-12 h-12 bg-black border border-stone-700 hover:border-[#00f2ff] flex items-center justify-center relative group">
                        <span className="absolute top-0.5 right-1 text-[8px] text-stone-500">{i}</span>
                        <Zap size={20} className="text-stone-600 group-hover:text-[#00f2ff]" />
                    </button>
                ))}

                <div className="w-px h-10 bg-stone-700 mx-2" />

                <button className="h-12 px-6 bg-red-900/20 border border-red-900 hover:bg-red-900/40 text-red-500 font-bold uppercase text-xs tracking-wider flex items-center gap-2">
                    <Sword size={16} /> Attack
                </button>
                <button className="h-12 px-6 bg-blue-900/20 border border-blue-900 hover:bg-blue-900/40 text-blue-500 font-bold uppercase text-xs tracking-wider flex items-center gap-2">
                    <Shield size={16} /> Defend
                </button>
            </div>
        </div>
    );
}
