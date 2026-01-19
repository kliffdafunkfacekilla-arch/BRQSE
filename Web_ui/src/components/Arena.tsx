import React, { useState, useEffect } from 'react';
import Token from './Token';

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
    const [mapTiles, setMapTiles] = useState<string[][]>([]); // 2D array of tile IDs
    const [step, setStep] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [consoleMsg, setConsoleMsg] = useState<string[]>([]);
    const [animating, setAnimating] = useState<{ [name: string]: string }>({}); // Track active animations
    const [activeEffects, setActiveEffects] = useState<any[]>([]); // Track active sprite effects

    const GRID_SIZE = 10;

    // ASSET MAPPING
    const EFFECT_MAP: { [key: string]: string } = {
        'fireball': '/spells/fire/fireball.png',
        'arrow': '/effect/arrow0.png',
        'bolt': '/effect/bolt0.png',
        'magic_missile': '/effect/cloud_magic_trail0.png'
    };

    useEffect(() => {
        fetch('/data/last_battle_replay.json')
            .then(res => res.json())
            .then(data => {
                // 1. COMBATANTS
                const c1 = { ...data.combatants[0], hp: data.combatants[0].max_hp, x: 2, y: 5 };
                const c2 = { ...data.combatants[1], hp: data.combatants[1].max_hp, x: 7, y: 5 };
                setCombatants([c1, c2]);

                // 2. LOG
                setLog(data.log);

                // 3. MAP
                if (data.map) {
                    setMapTiles(data.map);
                } else {
                    setConsoleMsg(["Connection Established.", "Map Data Missing."]);
                }

                // 4. SYNC
                if (onStatsUpdate && c1.team === 'blue') {
                    onStatsUpdate(c1.hp, c1.max_hp, c1.name);
                }
            })
            .catch(err => setConsoleMsg(["Error: No Battle Data Found."]));
    }, []);

    // PLAYBACK LOOP (Same as before)
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

        if (event.type === "move" && event.to) {
            setCombatants(prev => prev.map(c =>
                c.name === event.actor ? { ...c, x: event.to![0], y: event.to![1] } : c
            ));
        }

        if (event.type === "attack") {
            const actor = combatants.find(c => c.name === event.actor);
            const target = combatants.find(c => c.name === event.target);

            if (actor && target) {
                // 1. TRIGGER ATTACK ANIMATION (LUNGE)
                let lungeAnim = 'animate-sim-lunge-down'; // Default
                const dx = target.x - actor.x;
                const dy = target.y - actor.y;

                if (Math.abs(dx) > Math.abs(dy)) {
                    lungeAnim = dx > 0 ? 'animate-sim-lunge-right' : 'animate-sim-lunge-left';
                } else {
                    lungeAnim = dy > 0 ? 'animate-sim-lunge-down' : 'animate-sim-lunge-up';
                }

                setAnimating(prev => ({ ...prev, [event.actor]: lungeAnim }));
                setTimeout(() => setAnimating(prev => {
                    const newState = { ...prev }; delete newState[event.actor]; return newState;
                }), 300);

                // 2. TRIGGER EFFECT SPRITE (If present)
                // We look for 'effect' field in event, or maybe standard 'hit' effects later
                // For now, relying on the injected 'effect' field in JSON
                const effectKey = (event as any).effect;
                if (effectKey && EFFECT_MAP[effectKey]) {
                    const newEffect = {
                        id: Date.now(),
                        x: target.x,
                        y: target.y,
                        src: EFFECT_MAP[effectKey],
                        rotation: Math.atan2(dy, dx) * (180 / Math.PI) // basic rotation
                    };
                    setActiveEffects(prev => [...prev, newEffect]);

                    // Remove effect after duration
                    setTimeout(() => {
                        setActiveEffects(prev => prev.filter(e => e.id !== newEffect.id));
                    }, 600);
                }
            }

            // 3. TRIGGER DAMAGE ANIMATION (SHAKE)
            if (event.damage && event.damage > 0) {
                setAnimating(prev => ({ ...prev, [event.target!]: 'animate-sim-shake' }));
                setTimeout(() => setAnimating(prev => {
                    const newState = { ...prev }; delete newState[event.target!]; return newState;
                }), 400);

                // Resolve Damage
                setCombatants(prev => prev.map(c => {
                    if (c.name === event.target) {
                        const newHp = Math.max(0, c.hp - event.damage!);
                        if (c.team === 'blue' && onStatsUpdate) {
                            onStatsUpdate(newHp, c.max_hp, c.name);
                        }
                        return { ...c, hp: newHp };
                    }
                    return c;
                }));
            }
        }
    };

    return (
        <div className="flex flex-col items-center bg-[#050505]">
            <div className="w-full flex justify-between items-center p-2 bg-stone-900 border-b border-stone-800 relative z-50">
                <div className="text-[#00f2ff] font-mono text-xs">
                    SIMULATION STATUS: {playing ? "RUNNING" : "PAUSED"}
                </div>
                <button
                    onClick={() => setPlaying(!playing)}
                    className={`px-3 py-1 text-[10px] font-bold rounded border ${playing ? 'border-red-500 text-red-500' : 'border-green-500 text-green-500'} hover:bg-white/5`}
                >
                    {playing ? "HALT" : "EXECUTE"}
                </button>
            </div>

            {/* ARENA CONTAINER */}
            <div
                className="relative shadow-[0_0_50px_rgba(0,0,0,0.5)] bg-[#111]"
                style={{
                    width: '600px', height: '600px',
                    display: 'grid',
                    gridTemplateColumns: `repeat(${GRID_SIZE}, 1fr)`,
                    gridTemplateRows: `repeat(${GRID_SIZE}, 1fr)`
                }}
            >
                {/* 1. RENDER MAP TILES (Layer 0) */}
                {mapTiles.map((row, y) => (
                    row.map((tileId, x) => (
                        <div key={`${x}-${y}`} className="w-full h-full relative border-[0.5px] border-white/5">
                            <img
                                src={`/tiles/${tileId}.png`}
                                alt="tile"
                                className="w-full h-full object-cover opacity-80"
                            />
                            {/* If it's a wall, add a little 3D pop or overlay if needed, currently just the image */}
                        </div>
                    ))
                ))}

                {/* 2. RENDER ACTIVE EFFECTS (Layer 0.5 - Beneath tokens but above map? Or above All?) */}
                {/* Let's put them on top for visibility */}
                {activeEffects.map(effect => (
                    <div
                        key={effect.id}
                        className="absolute flex items-center justify-center z-20 pointer-events-none animate-fade-in"
                        style={{
                            width: `${600 / GRID_SIZE}px`, height: `${600 / GRID_SIZE}px`,
                            left: `${effect.x * (600 / GRID_SIZE)}px`, top: `${effect.y * (600 / GRID_SIZE)}px`,
                            transform: `rotate(${effect.rotation}deg)`
                        }}
                    >
                        <img src={effect.src} alt="effect" className="w-[80%] h-[80%] object-contain drop-shadow-[0_0_10px_rgba(255,255,0,0.8)]" />
                    </div>
                ))}

                {/* 3. RENDER ENTITIES (Layer 1 - Absolute on top) */}
                {combatants.map((c, i) => (
                    <div
                        key={i}
                        className={`absolute transition-all duration-500 ease-out flex flex-col items-center justify-center z-10 pointer-events-none ${animating[c.name] || ''}`}
                        style={{
                            width: `${600 / GRID_SIZE}px`, height: `${600 / GRID_SIZE}px`,
                            left: `${c.x * (600 / GRID_SIZE)}px`, top: `${c.y * (600 / GRID_SIZE)}px`
                        }}
                    >
                        <div className="w-[80%] h-[80%] transition-transform hover:scale-110">
                            <Token
                                name={c.name}
                                facing="down"
                                team={c.team}
                                dead={c.hp <= 0}
                            />
                        </div>
                        <div className="absolute -bottom-1 w-[80%] h-1 bg-black rounded-full overflow-hidden border border-white/20">
                            <div
                                className={`h-full ${c.team === 'blue' ? 'bg-cyan-500' : 'bg-red-500'}`}
                                style={{ width: `${(c.hp / c.max_hp) * 100}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>

            <div className="w-full bg-black p-2 border-t border-stone-800 font-mono text-[10px] text-stone-500 h-8 flex items-center">
                &gt; {consoleMsg[0]}
            </div>
        </div>
    );
}
