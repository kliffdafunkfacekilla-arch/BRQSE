import React, { useState, useEffect } from 'react';

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

export default function Arena() {
    const [combatants, setCombatants] = useState<Combatant[]>([]);
    const [log, setLog] = useState<ReplayEvent[]>([]);
    const [step, setStep] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [consoleMsg, setConsoleMsg] = useState<string[]>([]);

    // SIMULATION: This loads the "Server Packet". 
    // In the future, this is replaced by a live socket listener.
    useEffect(() => {
        fetch('/data/last_battle_replay.json')
            .then(res => res.json())
            .then(data => {
                const c1 = { ...data.combatants[0], hp: data.combatants[0].max_hp, x: 2, y: 5 };
                const c2 = { ...data.combatants[1], hp: data.combatants[1].max_hp, x: 7, y: 5 };
                setCombatants([c1, c2]);
                setLog(data.log);
                setConsoleMsg(["Connection Established. Data Loaded."]);
            })
            .catch(err => setConsoleMsg(["Error: No Battle Data Found. Run generate_replay.py"]));
    }, []);

    // RENDER LOOP
    useEffect(() => {
        let interval: any;
        if (playing && step < log.length) {
            interval = setInterval(() => {
                setStep(s => s + 1);
                processEvent(log[step]);
            }, 800); // Speed of animation
        } else {
            setPlaying(false);
        }
        return () => clearInterval(interval);
    }, [playing, step, log]);

    // THE GRAPHICS ENGINE
    const processEvent = (event: ReplayEvent) => {
        if (!event) return;

        setConsoleMsg(prev => [`> ${event.actor}: ${event.type.toUpperCase()} ${event.result || ''}`, ...prev].slice(0, 5));

        if (event.type === "move" && event.to) {
            setCombatants(prev => prev.map(c =>
                c.name === event.actor ? { ...c, x: event.to![0], y: event.to![1] } : c
            ));
        }

        if (event.type === "attack" && event.damage !== undefined) {
            // Visual Shake Logic could go here
            setCombatants(prev => prev.map(c =>
                c.name === event.target ? { ...c, hp: Math.max(0, c.hp - event.damage!) } : c
            ));
        }
    };

    const GRID_SIZE = 10;

    return (
        <div className="flex flex-col items-center justify-center p-4">
            {/* THE VIEWPORT */}
            <div
                className="relative bg-grid-pattern border border-[#00f2ff]/30 shadow-[0_0_50px_rgba(0,242,255,0.15)] rounded-lg overflow-hidden bg-black/40"
                style={{
                    width: '500px', height: '500px',
                    display: 'grid', gridTemplateColumns: `repeat(${GRID_SIZE}, 1fr)`
                }}
            >
                {/* Render Grid */}
                {Array.from({ length: GRID_SIZE * GRID_SIZE }).map((_, i) => (
                    <div key={i} className="border border-white/5 opacity-10" />
                ))}

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
                        {/* HP Bar */}
                        <div className="w-[120%] h-1 bg-red-900/80 mb-1 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-[#00f2ff] transition-all duration-300"
                                style={{ width: `${(c.hp / c.max_hp) * 100}%` }}
                            />
                        </div>

                        {/* Avatar */}
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shadow-lg border-2
              ${c.team === 'blue' ? 'bg-cyan-900/80 border-cyan-400' : 'bg-red-900/80 border-red-400'}
              ${c.hp === 0 ? 'grayscale opacity-50 scale-90' : 'scale-100'}
              transition-transform
            `}>
                            {c.name.substring(0, 2).toUpperCase()}
                        </div>
                    </div>
                ))}
            </div>

            {/* HUD CONTROLS */}
            <div className="mt-4 glass-panel p-2 w-[500px] flex justify-between items-center bg-stone-900/80 border border-stone-700 rounded">
                <div className="font-mono text-[#00f2ff] text-xs">EVENT: {step} / {log.length}</div>
                <div className="space-x-4">
                    <button
                        onClick={() => setPlaying(!playing)}
                        className={`px-4 py-1 rounded font-bold transition-all text-sm border ${playing ? 'bg-red-500/20 text-red-400 border-red-500' : 'bg-green-500/20 text-green-400 border-green-500'}`}
                    >
                        {playing ? "PAUSE" : "PLAY"}
                    </button>

                    <button onClick={() => { setStep(0); setCombatants(prev => prev.map(c => ({ ...c, hp: c.max_hp, x: c.team === 'blue' ? 2 : 7, y: 5 }))); }} className="text-gray-500 hover:text-white text-xs">
                        RESET
                    </button>
                </div>
            </div>

            {/* SYSTEM LOG */}
            <div className="mt-2 w-[500px] font-mono text-[10px] text-gray-500 space-y-1 p-2 bg-black/40 rounded border border-gray-800 h-20 overflow-y-auto">
                {consoleMsg.map((msg, i) => (
                    <div key={i} className="opacity-80">{msg}</div>
                ))}
            </div>
        </div>
    );
}
