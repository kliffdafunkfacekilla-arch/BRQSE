import { useState, useEffect } from 'react';
import Token from './Token';

const TILE_SIZE = 64;

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
    // Contested roll data
    attack_roll?: number;
    defense_roll?: number;
    target_hp?: number;
    // Clash/effect data
    stat?: string;
    effect?: string;
}

interface Combatant {
    name: string;
    max_hp: number;
    hp: number;
    max_composure?: number;
    composure?: number;
    x: number;
    y: number;
    team: string;
    facing: 'up' | 'down' | 'left' | 'right';
    sprite?: string;  // Optional sprite name for token image
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
    sceneVersion?: number;
}

export default function Arena({ onStatsUpdate, onLog, sceneVersion = 0 }: ArenaProps) {
    const [combatants, setCombatants] = useState<Combatant[]>([]);
    const [visuals, setVisuals] = useState<VisualEffect[]>([]);
    const [persistentVisuals, setPersistentVisuals] = useState<VisualEffect[]>([]);
    const [popups, setPopups] = useState<FloatingText[]>([]);
    const [log, setLog] = useState<ReplayEvent[]>([]);
    const [step, setStep] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [consoleMsg, setConsoleMsg] = useState<string[]>(["SYSTEM IDLE"]);

    // Attack line for visual clarity
    const [attackLine, setAttackLine] = useState<{ from: { x: number, y: number }, to: { x: number, y: number }, color: string } | null>(null);

    const [gridSize, setGridSize] = useState(12); // Dynamic grid size

    // Map tile data from replay
    const [mapTiles, setMapTiles] = useState<string[][]>([]);

    // Terrain colors for visual rendering
    // IMAGE ASSETS MAPPING
    const TERRAIN_ASSETS: Record<string, string> = {
        'normal': '/floor/grass_0_new.png',
        'grass': '/floor/grass_0_new.png',
        'difficult': '/floor/mud_0.png',
        'mud': '/floor/mud_0.png',
        'water': '/water/shallow_water.png',
        'water_shallow': '/water/shallow_water.png',
        'water_deep': '/water/deep_water.png',
        'ice': '/floor/ice_0_new.png',
        'wall': '/wall/stone_brick_1.png',
        'wall_stone': '/wall/stone_brick_1.png',
        'tree': '/trees/tree_1_red.png',
        'door': '/doors/closed_door.png',
        'door_open': '/doors/open_door.png',
    };

    // Color fallbacks for non-image tiles (e.g. Hazards)
    const TERRAIN_COLORS: Record<string, string> = {
        'fire': 'bg-orange-600/60',
        'acid': 'bg-green-600/60',
        'darkness': 'bg-black/80',
    };

    // EXPLORATION STATE
    const [explorationMode, setExplorationMode] = useState(false);
    const [playerPos, setPlayerPos] = useState({ x: 1, y: 6 });
    const [objects, setObjects] = useState<any[]>([]);
    const [explored, setExplored] = useState<Set<string>>(new Set());

    // LOAD DATA WRAPPER
    const fetchData = () => {
        // Try Game Loop State First
        fetch('/api/game/state')
            .then(res => res.json())
            .then(data => {
                if (data.mode === 'EXPLORE') {
                    setExplorationMode(true);
                    setConsoleMsg(["EXPLORATION MODE ACTIVE"]);
                    updateGameState(data);
                } else {
                    // Fallback to Replay Mode
                    loadReplayData();
                }
            })
            .catch(() => loadReplayData());
    };

    const loadReplayData = () => {
        setExplorationMode(false);
        setConsoleMsg(["FETCHING BATTLE DATA..."]);
        setPlaying(false);
        setStep(0);
        setVisuals([]);
        setPersistentVisuals([]);
        setPopups([]);
        fetch('/data/last_battle_replay.json?t=' + Date.now())
            .then(res => res.json())
            .then(data => {
                // Determine Grid Size from Map
                let newGridSize = 12;
                if (data.map && Array.isArray(data.map)) {
                    const rows = data.map.length;
                    const cols = data.map[0]?.length || 0;
                    newGridSize = Math.max(rows, cols, 10);
                    setMapTiles(data.map);
                }
                setGridSize(newGridSize);

                // Load ALL combatants
                const loadedCombatants = data.combatants.map((c: any) => ({
                    ...c,
                    hp: c.max_hp,
                    x: c.x ?? 5,
                    y: c.y ?? 5,
                    facing: c.team === 'blue' ? 'right' : 'left',
                    sprite: c.sprite || null  // Use sprite from replay data
                }));
                setCombatants(loadedCombatants);
                setLog(data.log);

                setConsoleMsg([`DATA LOADED: ${loadedCombatants.length} combatants, ${newGridSize}x${newGridSize} map. READY.`]);
            })
            .catch(() => setConsoleMsg(["ERR: NO DATA STREAM"]));
    };

    const updateGameState = (state: any) => {
        setPlayerPos(state.player_pos ? { x: state.player_pos[0], y: state.player_pos[1] } : { x: 1, y: 6 });
        setObjects(state.objects || []);

        // Parse Explored Tiles
        if (state.explored) {
            const newExplored = new Set<string>();
            state.explored.forEach((t: any) => {
                const [ex, ey] = t;
                newExplored.add(`${ex},${ey}`);
            });
            setExplored(newExplored);
        }

        // Dynamic Grid Size
        const w = state.grid_w || 12;
        const h = state.grid_h || 12;
        setGridSize(Math.max(w, h));

        // Rebuild Map Tiles from Grid (Preferred)
        if (state.grid) {
            const newMap = state.grid.map((row: number[]) => row.map((tileId: number) => {
                // Map ID to Texture Key
                switch (tileId) {
                    case 0: return "wall"; // TILE_WALL
                    case 1: return "grass"; // TILE_FLOOR
                    case 2: return "tree"; // TILE_COVER
                    case 3: return "grass"; // TILE_ENEMY (Floor, entity rendered separately?)
                    case 4: return "door"; // TILE_DOOR
                    case 5: return "mud"; // TILE_HAZARD (Mud for now)
                    case 6: return "grass"; // TILE_LOOT (Floor, object rendered separately)
                    default: return "grass";
                }
            }));
            setMapTiles(newMap);
        } else if (state.walls) {
            // Legacy Fallback
            const newMap = Array(12).fill(null).map(() => Array(12).fill("normal"));
            state.walls.forEach((w: any) => {
                const [wx, wy] = w;
                if (wy < 12 && wx < 12) newMap[wy][wx] = "wall";
            });
            setMapTiles(newMap);
        }
    };

    const handleTileClick = (tx: number, ty: number) => {
        if (!explorationMode) return;

        // Determine Action: Move or Interact
        // Simple heuristic: If object there, interact. Else move.
        const isObject = objects.find(o => o.x === tx && o.y === ty);
        const endpoint = isObject ? '/api/game/interact' : '/api/game/move';

        fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ x: tx, y: ty })
        })
            .then(res => res.json())
            .then(data => {
                if (data.result && data.result.success) {
                    if (data.state) updateGameState(data.state);
                    if (data.result.event === 'COMBAT_STARTED') {
                        setExplorationMode(false);
                        onLog && onLog("COMBAT STARTED!", "combat");
                        setTimeout(loadReplayData, 1000); // Switch to battle view
                    }
                    if (data.result.effect) {
                        onLog && onLog(data.result.effect, "info");
                        // Visual popup
                        setPopups(prev => [...prev, {
                            id: Date.now(), x: tx, y: ty, text: data.result.effect, color: 'text-yellow-400'
                        }]);
                    }
                } else {
                    onLog && onLog(data.result?.reason || "Failed", "error");
                }
            });
    };

    // INITIAL LOAD
    useEffect(() => {
        // Initial load
        fetchData();
    }, [sceneVersion]);
    // Poll for state changes (e.g. scene advance)
    useEffect(() => {
        let interval: any;
        if (explorationMode) {
            interval = setInterval(() => {
                fetch('/api/game/state').then(r => r.json()).then(d => {
                    if (d.mode === 'EXPLORE') updateGameState(d);
                });
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [explorationMode]);

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

        // Improved Logging - show attacker → target clearly
        let msg = '';
        const actor = combatants.find(c => c.name === event.actor);
        const actorTeam = actor?.team === 'blue' ? '🔵' : '🔴';

        if (event.type === 'attack' || event.type === 'ability' || event.type === 'cast') {
            const targetTeam = combatants.find(c => c.name === event.target)?.team === 'blue' ? '🔵' : '🔴';
            msg = `${actorTeam} ${event.actor} → ${targetTeam} ${event.target || '?'}`;
            if (event.ability) msg += ` [${event.ability}]`;

            // Show contested roll values if present
            if (event.attack_roll && event.defense_roll) {
                msg += ` ⚔️${event.attack_roll} vs 🛡️${event.defense_roll}`;
            }

            if (event.damage && event.damage > 0) msg += ` 💥${event.damage}`;
            if (event.result?.toLowerCase() === 'miss') msg += ' ❌MISS';
            if (event.result?.toLowerCase() === 'critical') msg += ' ⚡CRIT!';
            if (event.result?.toLowerCase() === 'hit') msg += ' ✓HIT';
        } else if (event.type === 'clash') {
            // Physical Clash event
            msg = `⚔️ CLASH! ${actorTeam} ${event.actor} wins vs ${event.target}`;
            if (event.description) msg += ` - ${event.description}`;
        } else if (event.type === 'magic_clash') {
            // Magic Clash event  
            msg = `✨ MAGIC CLASH! ${actorTeam} ${event.actor} vs ${event.target}`;
            if (event.description) msg += ` - ${event.description}`;
        } else if (event.type === 'dot_damage') {
            // DoT damage event
            msg = `🔥 ${event.actor} takes ${event.damage} ${event.effect?.toUpperCase()} damage`;
        } else if (event.type === 'death') {
            msg = `💀 ${event.actor} has been SLAIN!`;
        } else {
            // Filter out boring info
            if (event.type === 'info' || event.description?.includes("Turn Starts") || event.type === 'move') return;
            msg = `${actorTeam} ${event.actor}: ${event.type.toUpperCase()}`;
        }

        setConsoleMsg(prev => [msg, ...prev].slice(0, 30));

        if (event.execution_log) {
            event.execution_log.forEach(line => {
                if (line.includes("Dealt") || line.includes("Effect") || line.includes("SLAIN") || line.includes("Save") || line.includes("STAGGERED") || line.includes("CLASH")) {
                    setConsoleMsg(prev => [`  * ${line}`, ...prev].slice(0, 30));
                }
            });
        }

        // MOVEMENT
        if (event.type === "move") {
            const names = combatants.map(c => `'${c.name}'`).join(", ");
            setConsoleMsg(prev => [`DEBUG: MOVE '${event.actor}' vs [${names}]`, ...prev].slice(0, 30));
            if (event.to && event.from) {
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
            } else {
                setConsoleMsg(prev => [`DEBUG: MOVE FAILED (No Coords) for ${event.actor}`, ...prev].slice(0, 30));
            }
        }

        // DEATH EVENT
        if (event.type === "death" && event.x !== undefined && event.y !== undefined) {
            triggerEffect(event.x, event.y, "death", true);
        }

        // COMBAT EVENTS - Show attack line
        if ((event.type === "attack" || event.type === "ability" || event.type === "cast") && event.target) {
            const attacker = combatants.find(c => c.name === event.actor);
            const target = combatants.find(c => c.name === event.target);

            // Draw attack line
            if (attacker && target) {
                const lineColor = attacker.team === 'blue' ? '#00f2ff' : '#ff4444';
                setAttackLine({
                    from: { x: attacker.x, y: attacker.y },
                    to: { x: target.x, y: target.y },
                    color: lineColor
                });
                // Clear attack line after short delay
                setTimeout(() => setAttackLine(null), 600);
            }

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
                        display: 'grid', gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
                        backgroundImage: `url('/tiles/floor_stone.png')`, backgroundSize: '100% 100%', imageRendering: 'pixelated'
                    }}
                >
                    <div className="absolute inset-0 bg-black/20 pointer-events-none" />

                    {/* TERRAIN TILES */}
                    {mapTiles.map((row, y) =>
                        row.map((tile, x) => {
                            const asset = TERRAIN_ASSETS[tile];
                            const colorClass = TERRAIN_COLORS[tile];

                            if (!asset && !colorClass) return null;

                            // FOG OF WAR
                            const isExplored = explored.has(`${x},${y}`);

                            // If not explored, render PURE BLACK (Unrevealed)
                            if (!isExplored && explorationMode) {
                                return (
                                    <div
                                        key={`${x}-${y}`}
                                        className="absolute bg-black flex items-center justify-center z-20"
                                        style={{
                                            width: `${100 / gridSize}%`,
                                            height: `${100 / gridSize}%`,
                                            left: `${x * (100 / gridSize)}%`,
                                            top: `${y * (100 / gridSize)}%`,
                                        }}
                                    />
                                );
                            }

                            return (
                                <div
                                    key={`${x}-${y}`}
                                    onClick={() => handleTileClick(x, y)}
                                    className={`absolute ${!asset ? colorClass : ''} flex items-center justify-center cursor-pointer hover:bg-white/10`}
                                    style={{
                                        width: `${100 / gridSize}%`,
                                        height: `${100 / gridSize}%`,
                                        left: `${x * (100 / gridSize)}%`,
                                        top: `${y * (100 / gridSize)}%`,
                                    }}
                                >
                                    {asset && (
                                        <img src={asset} alt={tile} className="w-full h-full object-cover" style={{ imageRendering: 'pixelated' }} />
                                    )}
                                    {tile === 'fire' && (
                                        <div className="absolute inset-0 w-full h-full animate-pulse bg-orange-500/30" />
                                    )}
                                    {/* Shroud for Explore Mode (Visible but not 'current' could be dimmed if we had LOS) */}
                                </div>
                            );
                        })
                    )}

                    {/* RENDER COMBATANTS OR PLAYER */}
                    {explorationMode ? (
                        <>
                            {/* Player Token */}
                            <div className="absolute transition-all duration-300 z-10"
                                style={{ left: `${playerPos.x * TILE_SIZE}px`, top: `${playerPos.y * TILE_SIZE}px`, width: TILE_SIZE, height: TILE_SIZE }}>
                                <Token
                                    name="Hero"
                                    facing="right"
                                    team="blue"
                                    sprite="/tokens/badger_front.png"
                                />
                            </div>
                            {/* Objects */}
                            {objects.map((obj, i) => (
                                <div key={i} className="absolute z-0 pointer-events-none"
                                    style={{ left: `${obj.x * TILE_SIZE}px`, top: `${obj.y * TILE_SIZE}px`, width: TILE_SIZE, height: TILE_SIZE }}>
                                    {obj.type === 'CHEST' && <div className="w-full h-full bg-yellow-500/50 animate-pulse rounded-full border-2 border-yellow-300" />}
                                    {obj.type === 'SPIKES' && <div className="w-full h-full bg-red-900/50 border border-red-500" />}
                                </div>
                            ))}
                        </>
                    ) : (
                        combatants.map((c, i) => {
                            if (c.hp <= 0) return null; // Dead
                            return (
                                <div key={i} className="absolute transition-all duration-500 z-10"
                                    style={{
                                        left: `${c.x * TILE_SIZE}px`,
                                        top: `${c.y * TILE_SIZE}px`,
                                        width: TILE_SIZE,
                                        height: TILE_SIZE
                                    }}
                                >
                                    <Token
                                        name={c.name}
                                        team={c.team}
                                        facing={c.facing}
                                        sprite={c.sprite}
                                    />
                                </div>
                            );
                        })
                    )}

                    {/* ATTACK LINE */}
                    {attackLine && (
                        <svg className="absolute inset-0 w-full h-full pointer-events-none z-20">
                            <line
                                x1={`${(attackLine.from.x + 0.5) * (100 / gridSize)}%`}
                                y1={`${(attackLine.from.y + 0.5) * (100 / gridSize)}%`}
                                x2={`${(attackLine.to.x + 0.5) * (100 / gridSize)}%`}
                                y2={`${(attackLine.to.y + 0.5) * (100 / gridSize)}%`}
                                stroke={attackLine.color}
                                strokeWidth="3"
                                strokeLinecap="round"
                                opacity="0.8"
                            />
                        </svg>
                    )}

                    {/* TOKENS */}
                    {combatants.map((c, i) => (
                        <div
                            key={i}
                            className="absolute transition-all duration-500 ease-in-out flex flex-col items-center justify-center z-10 p-1"
                            style={{ width: `${100 / gridSize}%`, height: `${100 / gridSize}%`, left: `${c.x * (100 / gridSize)}%`, top: `${c.y * (100 / gridSize)}%` }}
                        >
                            <div className="w-full h-full relative hover:scale-110 transition-transform cursor-pointer group">
                                <Token name={c.name} facing={c.facing} team={c.team} dead={c.hp <= 0} sprite={c.sprite} />
                                {/* Name label */}
                                <div className={`absolute -bottom-4 left-1/2 -translate-x-1/2 text-[8px] font-bold px-1 rounded whitespace-nowrap
                                    ${c.team === 'blue' ? 'text-cyan-300 bg-cyan-900/80' : 'text-red-300 bg-red-900/80'}`}>
                                    {c.name}
                                </div>
                            </div>
                            {/* HP Bar */}
                            <div className="w-full max-w-[40px] h-1 bg-stone-900 mt-1 rounded-full overflow-hidden border border-white/10 relative -top-1">
                                <div className={`h-full ${c.team === 'blue' ? 'bg-[#00f2ff]' : 'bg-red-500'}`} style={{ width: `${(c.hp / c.max_hp) * 100}%` }} />
                            </div>
                            {/* Composure Bar (Purple) */}
                            {c.max_composure && c.max_composure > 0 && (
                                <div className="w-full max-w-[40px] h-1 bg-stone-900 rounded-full overflow-hidden border border-white/10 relative -top-1">
                                    <div className="h-full bg-purple-500" style={{ width: `${((c.composure || 0) / c.max_composure) * 100}%` }} />
                                </div>
                            )}
                        </div>
                    ))}

                    {/* PERSISTENT FX (Blood Puddles) */}
                    {persistentVisuals.map((v) => (
                        <div key={v.id} className="absolute z-5 pointer-events-none flex items-center justify-center opacity-80"
                            style={{ width: `${100 / gridSize}%`, height: `${100 / gridSize}%`, left: `${v.x * (100 / gridSize)}%`, top: `${v.y * (100 / gridSize)}%` }}>
                            <img src={v.img} alt="blood" className="w-full h-full object-contain" />
                        </div>
                    ))}

                    {/* VISUAL FX (Fireballs/Sparks) */}
                    {visuals.map((v) => (
                        <div key={v.id} className="absolute z-20 pointer-events-none flex items-center justify-center animate-ping-slow"
                            style={{ width: `${100 / gridSize}%`, height: `${100 / gridSize}%`, left: `${v.x * (100 / gridSize)}%`, top: `${v.y * (100 / gridSize)}%` }}>
                            <img src={v.img} alt="fx" className="w-full h-full object-contain drop-shadow-[0_0_10px_rgba(255,100,0,0.8)]" />
                        </div>
                    ))}

                    {/* FLOATING TEXT (Damage Numbers) */}
                    {popups.map((p) => (
                        <div
                            key={p.id}
                            className={`absolute z-30 pointer-events-none flex items-center justify-center w-full font-black text-xl text-shadow-outline animate-float ${p.color}`}
                            style={{
                                width: `${100 / gridSize}%`,
                                left: `${p.x * (100 / gridSize)}%`, top: `${p.y * (100 / gridSize)}%`
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
