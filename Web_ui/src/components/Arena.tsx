import { useState, useEffect } from 'react';
import Token from './Token';

interface ReplayEvent {
    type: string;
    style?: string;
    actor: string;
    target?: string;
    from?: number[];
    to?: number[];
    damage?: number;
    result?: string;
    execution_log?: string[];
    x?: number; // For death events
    y?: number; // For death events
    ability?: string;
    description?: string;
}

interface Combatant {
    name: string;
    max_hp: number;
    hp: number;
    x: number;
    y: number;
    team: string;
    facing: 'up' | 'down' | 'left' | 'right';
}

interface VisualEffect {
    id: number;
    x: number;
    y: number;
    img: string;
}

// --- NEW: FLOATING TEXT INTERFACE ---
interface FloatingText {
    id: number;
    x: number;
    y: number;
    text: string;
    color: string;
}

interface ArenaProps {
    onStatsUpdate?: (currentHp: number, maxHp: number, name: string) => void;
    onLog?: (msg: string, type: 'info' | 'combat' | 'error') => void;
}

export default function Arena({ onStatsUpdate }: ArenaProps) {
    const [combatants, setCombatants] = useState<Combatant[]>([]);
    const [visuals, setVisuals] = useState<VisualEffect[]>([]);
    const [persistentVisuals, setPersistentVisuals] = useState<VisualEffect[]>([]);
    const [popups, setPopups] = useState<FloatingText[]>([]); // <--- NEW STATE FOR DAMAGE NUMBERS
    const [log, setLog] = useState<ReplayEvent[]>([]);
    const [step, setStep] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [consoleMsg, setConsoleMsg] = useState<string[]>(["SYSTEM IDLE"]);

    const GRID_SIZE = 10;

    // LOAD DATA WRAPPER
    const fetchData = () => {
        setConsoleMsg(["FETCHING BATTLE DATA..."]);
        setPlaying(false);
        setStep(0);
        setVisuals([]);
        setPersistentVisuals([]);
        setPopups([]); // Reset popups
        fetch('/data/last_battle_replay.json?t=' + Date.now())
            .then(res => res.json())
            .then(data => {
                const c1 = {
                    ...data.combatants[0],
                    hp: data.combatants[0].max_hp,
                    x: data.combatants[0].x ?? 2,
                    y: data.combatants[0].y ?? 5,
                    facing: 'right'
                };
                const c2 = {
                    ...data.combatants[1],
                    hp: data.combatants[1].max_hp,
                    x: data.combatants[1].x ?? 7,
                    y: data.combatants[1].y ?? 5,
                    facing: 'left'
                };
                setCombatants([c1, c2]);
                setLog(data.log);
                setConsoleMsg(["DATA LOADED. READY."]);
            })
            .catch(() => setConsoleMsg(["ERR: NO DATA STREAM"]));
    };

    // Initial Load
    useEffect(() => {
        fetchData();
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

    const processEvent = (event: ReplayEvent) => {
        if (!event) return;

        // Logging Logic
        let msg = `> ${event.actor}: ${event.type.toUpperCase()}`;
        if (event.ability) msg += ` [${event.ability}]`;
        if (event.damage && event.damage > 0) msg += ` -${event.damage} HP`;
        if (event.description) msg += ` (${event.description})`;

        setConsoleMsg(prev => [msg, ...prev].slice(0, 30));

        if (event.execution_log) {
            event.execution_log.forEach(line => {
                if (line.includes("Dealt") || line.includes("Effect") || line.includes("SLAIN") || line.includes("Save")) {
                    setConsoleMsg(prev => [`  * ${line}`, ...prev].slice(0, 30));
                }
            });
        }

        // MOVEMENT
        if (event.type === "move" && event.to && event.from) {
            const [oldX, oldY] = event.from;
            const [newX, newY] = event.to;
            let newFacing: 'up' | 'down' | 'left' | 'right' = 'down';
            if (newX > oldX) newFacing = 'right';
            else if (newX < oldX) newFacing = 'left';
            else if (newY > oldY) newFacing = 'down';
            else if (newY < oldY) newFacing = 'up';

            setCombatants(prev => prev.map(c =>
                c.name === event.actor ? { ...c, x: newX, y: newY, facing: newFacing } : c
            ));
        }

        // DEATH EVENT
        if (event.type === "death" && event.x !== undefined && event.y !== undefined) {
            triggerEffect(event.x, event.y, "death", true);
        }

        // COMBAT EVENTS
        if ((event.type === "attack" || event.type === "ability" || event.type === "cast") && event.target) {
            const target = combatants.find(c => c.name === event.target);
            if (target) {
                // 1. Visual Effect
                let style = event.style || 'hit';
                triggerEffect(target.x, target.y, style);

                // 2. Floating Damage Number
                if (event.damage !== undefined && event.damage > 0) {
                    let color = "text-red-500";
                    let text = `-${event.damage}`;
                    if (event.result === "CRITICAL") {
                        color = "text-yellow-400";
                        text = `CRIT -${event.damage}!`;
                    }
                    triggerPopup(target.x, target.y, text, color);
                } else if (event.result === "MISS") {
                    triggerPopup(target.x, target.y, "MISS", "text-stone-500");
                }
            }

            // 3. Update Health
            if (event.damage !== undefined && event.damage > 0) {
                setCombatants(prev => prev.map(c => {
                    if (c.name === event.target) {
                        const newHp = Math.max(0, c.hp - event.damage!);
                        if (c.team === 'blue' && onStatsUpdate) onStatsUpdate(newHp, c.max_hp, c.name);
                        return { ...c, hp: newHp };
                    }
                    return c;
                }));
            }
        }
    };

    // --- FX ENGINE ---
    const triggerEffect = (x: number, y: number, style: string, persistent = false) => {
        const id = Date.now() + Math.random();
        let img = '/effect/cloud_grey_smoke.png';

        if (style.includes('fire')) img = '/effect/cloud_fire1.png';
        if (style.includes('ice') || style.includes('frost')) img = '/effect/cloud_cold1.png';
        if (style.includes('arrow')) img = '/effect/arrow0.png';
        if (style.includes('bolt') || style.includes('lightning')) img = '/effect/bolt01.png';
        if (style.includes('poison')) img = '/effect/cloud_poison1.png';
        if (style.includes('crit')) {
            const bloods = ['blood_red_10.png', 'blood_red_11.png', 'blood_red_12.png', 'blood_red_13.png'];
            const rnd = bloods[Math.floor(Math.random() * bloods.length)];
            img = `/blood/${rnd}`; // Ensure this path exists or matches your folder structure
        }
        if (style.includes('death')) {
            const puddles = ['blood_puddle_red.png', 'blood_puddle_red_1.png', 'blood_puddle_red_2.png', 'blood_puddle_red_3.png'];
            const rnd = puddles[Math.floor(Math.random() * puddles.length)];
            img = `/blood/${rnd}`;
        }

        const newVis = { id, x, y, img };

        if (persistent) {
            setPersistentVisuals(prev => [...prev, newVis]);
        } else {
            setVisuals(prev => [...prev, newVis]);
            setTimeout(() => {
                setVisuals(prev => prev.filter(v => v.id !== id));
            }, 600);
        }
    };

    // --- FLOATING TEXT ENGINE ---
    const triggerPopup = (x: number, y: number, text: string, color: string) => {
        const id = Date.now() + Math.random();
        setPopups(prev => [...prev, { id, x, y, text, color }]);
        // Float up and disappear after 1s
        setTimeout(() => setPopups(prev => prev.filter(v => v.id !== id)), 1000);
    };

    const handleReset = () => {
        setPlaying(false);
        setStep(0);
        setConsoleMsg(["SIMULATION RESET."]);
        setVisuals([]);
        setPersistentVisuals([]);
        setPopups([]);
        fetchData();
    };

    return (
        <div className="flex flex-row items-start justify-center w-full max-w-6xl mx-auto gap-4 p-4">

            {/* LEFT COLUMN: Arena */}
            <div className="flex flex-col w-full max-w-2xl">
                <div className="w-full flex justify-between items-center p-2 bg-black border border-stone-800 border-b-0 rounded-t-lg">
                    <div className="flex gap-2 items-center">
                        <div className={`w-2 h-2 rounded-full ${playing ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                        <span className="font-mono text-[10px] text-stone-400">TICK: {step}</span>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={handleReset} className="text-[10px] font-bold px-3 py-1 bg-stone-900 border border-stone-700 hover:text-red-500">RESET</button>
                        <button onClick={fetchData} className="text-[10px] font-bold px-3 py-1 bg-stone-900 border border-stone-700 hover:text-yellow-500">RELOAD</button>
                        <button onClick={() => setPlaying(!playing)} className="text-[10px] font-bold px-4 py-1 bg-stone-900 border border-stone-700 hover:text-[#00f2ff]">{playing ? "PAUSE" : "PLAY"}</button>
                    </div>
                </div>

                <div
                    className="relative border border-stone-800 shadow-2xl overflow-hidden w-full aspect-square rounded-sm"
                    style={{
                        display: 'grid', gridTemplateColumns: `repeat(${GRID_SIZE}, 1fr)`,
                        backgroundImage: `url('/tiles/floor_stone.png')`, backgroundSize: '100% 100%', imageRendering: 'pixelated'
                    }}
                >
                    <div className="absolute inset-0 bg-black/20 pointer-events-none" />

                    {/* TOKENS */}
                    {combatants.map((c, i) => (
                        <div
                            key={i}
                            className="absolute transition-all duration-500 ease-in-out flex flex-col items-center justify-center z-10 p-1"
                            style={{ width: `${100 / GRID_SIZE}%`, height: `${100 / GRID_SIZE}%`, left: `${c.x * (100 / GRID_SIZE)}%`, top: `${c.y * (100 / GRID_SIZE)}%` }}
                        >
                            <div className="w-full h-full relative hover:scale-110 transition-transform cursor-pointer group">
                                <Token name={c.name} facing={c.facing} team={c.team} dead={c.hp <= 0} />
                            </div>
                            <div className="w-full max-w-[40px] h-1 bg-stone-900 mt-1 rounded-full overflow-hidden border border-white/10 relative -top-1">
                                <div className={`h-full ${c.team === 'blue' ? 'bg-[#00f2ff]' : 'bg-red-500'}`} style={{ width: `${(c.hp / c.max_hp) * 100}%` }} />
                            </div>
                        </div>
                    ))}

                    {/* PERSISTENT FX (Blood Puddles) */}
                    {persistentVisuals.map((v) => (
                        <div key={v.id} className="absolute z-5 pointer-events-none flex items-center justify-center opacity-80"
                            style={{ width: `${100 / GRID_SIZE}%`, height: `${100 / GRID_SIZE}%`, left: `${v.x * (100 / GRID_SIZE)}%`, top: `${v.y * (100 / GRID_SIZE)}%` }}>
                            <img src={v.img} alt="blood" className="w-full h-full object-contain" />
                        </div>
                    ))}

                    {/* VISUAL FX (Fireballs/Sparks) */}
                    {visuals.map((v) => (
                        <div key={v.id} className="absolute z-20 pointer-events-none flex items-center justify-center animate-ping-slow"
                            style={{ width: `${100 / GRID_SIZE}%`, height: `${100 / GRID_SIZE}%`, left: `${v.x * (100 / GRID_SIZE)}%`, top: `${v.y * (100 / GRID_SIZE)}%` }}>
                            <img src={v.img} alt="fx" className="w-full h-full object-contain drop-shadow-[0_0_10px_rgba(255,100,0,0.8)]" />
                        </div>
                    ))}

                    {/* FLOATING TEXT (Damage Numbers) */}
                    {popups.map((p) => (
                        <div
                            key={p.id}
                            className={`absolute z-30 pointer-events-none flex items-center justify-center w-full font-black text-xl text-shadow-outline animate-float ${p.color}`}
                            style={{
                                width: `${100 / GRID_SIZE}%`,
                                left: `${p.x * (100 / GRID_SIZE)}%`, top: `${p.y * (100 / GRID_SIZE)}%`
                            }}
                        >
                            {p.text}
                        </div>
                    ))}
                </div>
            </div>

            {/* RIGHT COLUMN: Sidebar Log */}
            <div className="w-64 h-[calc(100vh-4rem)] max-h-[600px] bg-black border border-stone-800 rounded-lg p-2 flex flex-col mt-[35px]">
                <div className="text-[10px] font-bold text-stone-500 mb-2 border-b border-stone-800 pb-1">COMBAT LOG</div>
                <div className="flex-1 overflow-y-auto font-mono text-[10px] space-y-1 scrollbar-thin scrollbar-thumb-stone-800">
                    {consoleMsg.map((msg, i) => (
                        <div key={i} className={`pb-1 border-b border-stone-900/50 ${msg.includes('SLAIN') ? 'text-red-500 font-bold' : msg.startsWith('>') ? 'text-[#00f2ff] opacity-90' : 'text-stone-400 opacity-70 ml-2'}`}>
                            {msg}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
