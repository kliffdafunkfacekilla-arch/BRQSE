import React, { useState, useEffect } from 'react';

// --- BURT'S PROTOCOL DEFINITIONS ---
interface ReplayEvent {
    type: string;
    actor: string;
    target?: string;
    from?: number[];
    to?: number[];
    damage?: number;
    result?: string;
}

interface Combatant {
    name: string;
    max_hp: number;
    hp: number;
    x: number;
    y: number;
    team: string;
}

// Add a prop to communicate back to HQ
interface ArenaProps {
    onStatsUpdate?: (currentHp: number, maxHp: number, name: string) => void;
}

export default function Arena({ onStatsUpdate }: ArenaProps) {
    const [combatants, setCombatants] = useState<Combatant[]>([]);
    const [log, setLog] = useState<ReplayEvent[]>([]);
    const [step, setStep] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [consoleMsg, setConsoleMsg] = useState<string[]>([]);

    const GRID_SIZE = 10; // Ensure this matches your CSS grid

    // LOAD DATA
    useEffect(() => {
        fetch('/data/last_battle_replay.json')
            .then(res => res.json())
            .then(data => {
                // Initialize Combatants
                // We assume P1 (Blue) is the "Player" for the UI
                const c1 = { ...data.combatants[0], hp: data.combatants[0].max_hp, x: 2, y: 5 };
                const c2 = { ...data.combatants[1], hp: data.combatants[1].max_hp, x: 7, y: 5 };

                setCombatants([c1, c2]);
                setLog(data.log);
                setConsoleMsg(["Connection Established. Data Loaded."]);

                // SYNC INITIAL STATS
                if (onStatsUpdate && c1.team === 'blue') {
                    onStatsUpdate(c1.hp, c1.max_hp, c1.name);
                }
            })
            .catch(err => setConsoleMsg(["Error: No Battle Data Found. Run generate_replay.py"]));
    }, []);

    // PLAYBACK LOOP
    useEffect(() => {
        let interval: any;
        if (playing && step < log.length) {
            interval = setInterval(() => {
                setStep(s => s + 1);
                processEvent(log[step]);
            }, 800);
        } else {
            setPlaying(false);
        }
        return () => clearInterval(interval);
    }, [playing, step, log]);

    // THE GRAPHICS ENGINE
    const processEvent = (event: ReplayEvent) => {
        if (!event) return;

        setConsoleMsg(prev => [`> ${event.actor}: ${event.type.toUpperCase()} ${event.result || ''}`, ...prev].slice(0, 5));

        // HANDLE MOVEMENT
        if (event.type === "move" && event.to) {
            setCombatants(prev => prev.map(c =>
                c.name === event.actor ? { ...c, x: event.to![0], y: event.to![1] } : c
            ));
        }

        // HANDLE COMBAT & SYNC STATS
        if (event.type === "attack" && event.damage) {
            setCombatants(prev => prev.map(c => {
                if (c.name === event.target) {
                    const newHp = Math.max(0, c.hp - event.damage!);

                    // IF PLAYER GOT HIT, SYNC UI
                    if (c.team === 'blue' && onStatsUpdate) {
                        onStatsUpdate(newHp, c.max_hp, c.name);
                    }
                    return { ...c, hp: newHp };
                }
                return c;
            }));
        }
    };

    return (
        <div className="flex flex-col items-center bg-[#050505]">
            {/* CONTROLS HEADER */}
            <div className="w-full flex justify-between items-center p-2 bg-stone-900 border-b border-stone-800">
                <div className="text-[#00f2ff] font-mono text-xs">
                    SIMULATION STATUS: {playing ? "RUNNING" : "PAUSED"}
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setPlaying(!playing)}
                        className={`px-3 py-1 text-[10px] font-bold rounded border ${playing ? 'border-red-500 text-red-500' : 'border-green-500 text-green-500'} hover:bg-white/5`}
                    >
                        {playing ? "HALT" : "EXECUTE"}
                    </button>
                </div>
            </div>

            {/* THE VIEWPORT */}
            <div
                className="relative shadow-[inset_0_0_50px_rgba(0,0,0,0.8)]"
                style={{
                    width: '600px', height: '600px', // Bigger!
                    display: 'grid', gridTemplateColumns: `repeat(${GRID_SIZE}, 1fr)`,
                    backgroundImage: 'linear-gradient(to right, #1a1a1a 1px, transparent 1px), linear-gradient(to bottom, #1a1a1a 1px, transparent 1px)',
                    backgroundSize: `${600 / GRID_SIZE}px ${600 / GRID_SIZE}px`
                }}
            >
                {/* Render Sprites */}
                {combatants.map((c, i) => (
                    <div
                        key={i}
                        className="absolute transition-all duration-500 ease-out flex flex-col items-center justify-center z-10"
                        style={{
                            width: `${100 / GRID_SIZE}%`, height: `${100 / GRID_SIZE}%`,
                            left: `${c.x * (100 / GRID_SIZE)}%`, top: `${c.y * (100 / GRID_SIZE)}%`
                        }}
                    >
                        {/* Token */}
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shadow-[0_0_15px_rgba(0,0,0,0.5)] border-2
                            ${c.team === 'blue' ? 'bg-cyan-900 border-cyan-400 text-cyan-200' : 'bg-red-900 border-red-400 text-red-200'}
                            transition-transform hover:scale-110 cursor-pointer
                        `}>
                            {c.name.substring(0, 1).toUpperCase()}
                        </div>

                        {/* Mini HP Bar */}
                        <div className="absolute -bottom-2 w-10 h-1 bg-black rounded-full overflow-hidden border border-white/20">
                            <div
                                className={`h-full ${c.team === 'blue' ? 'bg-cyan-500' : 'bg-red-500'}`}
                                style={{ width: `${(c.hp / c.max_hp) * 100}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>

            {/* FOOTER LOG */}
            <div className="w-full bg-black p-2 border-t border-stone-800 font-mono text-[10px] text-stone-500 h-8 flex items-center">
                &gt; {consoleMsg[0]}
            </div>
        </div>
    );
}
