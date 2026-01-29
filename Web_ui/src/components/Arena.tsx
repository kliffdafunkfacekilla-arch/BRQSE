import { useState, useEffect } from 'react';
import Token from './Token';
import ContextMenu from './ContextMenu';
import EffectLayer from './EffectLayer';
import { Target } from 'lucide-react';

const TILE_SIZE = 64;

interface ArenaProps {
    onStatsUpdate?: (currentHp: number, maxHp: number, name: string) => void;
    onLog?: (source: string, msg: string, type: 'info' | 'combat' | 'error') => void;
    sceneVersion?: number;
    playerSprite?: string;
    activeAbility?: string | null;
    onAbilityComplete?: () => void;
}

export default function Arena({ onStatsUpdate, onLog, sceneVersion = 0, playerSprite, activeAbility, onAbilityComplete }: ArenaProps) {
    const [combatants, setCombatants] = useState<any[]>([]);
    const [gridSize, setGridSize] = useState(20);
    const [mapTiles, setMapTiles] = useState<string[][]>([]);
    const [explorationMode, setExplorationMode] = useState(true);
    const [playerPos, setPlayerPos] = useState({ x: 5, y: 5 });
    const [objects, setObjects] = useState<any[]>([]);
    const [explored, setExplored] = useState<Set<string>>(new Set());
    const [activeEvents, setActiveEvents] = useState<any[]>([]);
    const [visualEffect, setVisualEffect] = useState<string | null>(null);

    // UI State
    const [tensionEvent, setTensionEvent] = useState<{ type: string, visible: boolean }>({ type: '', visible: false });
    const [activeEvent, setActiveEvent] = useState<{ title: string, description: string, choices: any[] } | null>(null);
    const [menu, setMenu] = useState<{ x: number, y: number, tx: number, ty: number, tags: string[] } | null>(null);

    const TERRAIN_ASSETS: Record<string, string> = {
        'normal': '/tiles/floor_stone.png',
        'grass': '/tiles/floor_stone.png',
        'difficult': '/floor/mud_0.png',
        'water': '/water/shallow_water.png',
        'ice': '/floor/ice_0_new.png',
        'wall': '/wall/stone_brick_1.png',
        'tree': '/trees/tree_1_red.png',
        'door': '/doors/closed_door.png',
        'loot': '/items/chest_closed.png',
        'entrance': '/doors/closed_door.png'
    };

    // Mapping for specific object types
    const OBJECT_ASSETS: Record<string, string> = {
        'Barrel': '/objects/barrel.png',
        'Crate': '/objects/crate.png',
        'Chest': '/objects/chest.png',
        'Loot Cache': '/objects/chest.png',
        'Table': '/objects/table.png',
        'Stone': '/traps/pressure_plate.png',
        'Logs': '/trees/mangrove_1.png',
        'Chandelier': '/icons/weapon/bloodbane.png',
        'Footprints': '/traps/bear_trap.png', // Placeholder
        'Strange Clue': '/items/scroll_map.png', // Placeholder
        'Locked Cage': '/doors/gate_iron.png'
    };

    const fetchData = () => {
        fetch('/api/game/state')
            .then(res => res.json())
            .then(data => {
                if (data.mode === 'EXPLORE' || data.mode === 'COMBAT') {
                    setExplorationMode(true);
                    updateExplorationState(data);
                    if (data.event === 'SCENE_STARTED' && onLog) {
                        onLog('EXPLORE', `Entered: ${data.scene_text}`, 'info');
                    }
                    if (data.active_event) {
                        setActiveEvent(data.active_event);
                    } else {
                        setActiveEvent(null);
                    }
                } else {
                    setExplorationMode(false);
                    loadReplayData();
                }
            })
            .catch(() => loadReplayData());
    };

    const updateExplorationState = (state: any) => {
        setGridSize(state.grid_w || 20);
        setPlayerPos(state.player_pos ? { x: state.player_pos[0], y: state.player_pos[1] } : { x: 5, y: 5 });
        setObjects(state.objects || []);
        if (state.combatants) setCombatants(state.combatants);

        if (state.grid) {
            const newMap = state.grid.map((row: number[]) => row.map((t: number) => {
                if (t === 0) return "wall";
                if (t === 2) return "tree";
                if (t === 4) return "door";
                if (t === 6) return "loot";
                if (t === 7) return "entrance";
                return "grass";
            }));
            setMapTiles(newMap);
        }

        if (state.explored) {
            const set = new Set<string>();
            state.explored.forEach((e: any) => set.add(`${e[0]},${e[1]}`));
            setExplored(set);
        }
    };

    const loadReplayData = () => {
        setExplorationMode(false);
        fetch('/data/last_battle_replay.json?t=' + Date.now())
            .then(res => res.json())
            .then(data => {
                setGridSize(data.map ? data.map.length : 12);
                setMapTiles(data.map || []);
                setCombatants(data.combatants || []);
            });
    };

    const handleAction = (action: string, tx: number, ty: number) => {
        if (!explorationMode) return;

        // If we have an active ability (aiming), override the action
        const finalAction = activeAbility ? activeAbility.toLowerCase() : action;

        fetch('/api/game/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: finalAction, x: tx, y: ty })
        })
            .then(res => res.json())
            .then(data => {
                const res = data.result;
                // If we used an ability, clear the aiming state
                if (activeAbility && onAbilityComplete) {
                    onAbilityComplete();
                }

                if (res.success) {
                    updateExplorationState(data.state);

                    // Capture Combat Events for Animations
                    if (data.events) {
                        setActiveEvents(data.events);
                    }

                    if (res.log && onLog) {
                        onLog(activeAbility ? 'COMBAT' : 'SYSTEM', res.log, 'info');

                        // trigger visual effects based on log content
                        const l = res.log.toLowerCase();
                        if (l.includes('fire') || l.includes('burn')) setVisualEffect('animate-flash-red');
                        else if (l.includes('cold') || l.includes('freeze')) setVisualEffect('animate-flash-cyan');
                        else if (l.includes('necrotic') || l.includes('doom')) setVisualEffect('animate-flash-purple');
                        else if (l.includes('healed') || l.includes('radiant')) setVisualEffect('animate-flash-white');
                        else if (l.includes('force') || l.includes('earthquake')) setVisualEffect('animate-sim-shake');

                        if (l.includes('force') || l.includes('earthquake')) {
                            setTimeout(() => setVisualEffect(null), 500);
                        } else {
                            setTimeout(() => setVisualEffect(null), 600);
                        }
                    }

                    // Tension Trigger
                    if (res.tension && res.tension !== 'SAFE') {
                        triggerTensionFX(res.tension);
                    }

                    if (res.event === 'SCENE_ADVANCED' && onLog) {
                        onLog('EXPLORE', `Advancing: ${res.text}`, 'info');
                    }
                    if (res.event === 'QUEST_COMPLETE' && onLog) {
                        onLog('EXPLORE', "Quest Complete! Returning to Tavern...", 'info');
                    }
                    if (res.event === 'COMBAT_STARTED') fetchData();
                    if (res.event === 'EVENT_TRIGGERED' && data.state.active_event) {
                        setActiveEvent(data.state.active_event);
                    }
                } else if (res.reason) {
                    if (onLog) onLog('ERROR', res.reason, 'error');
                }
            });
    };

    const handleEventChoice = (choiceId: string) => {
        // Resolve event via generic action (needs backend support or simple 'resolve' action)
        // For now, let's assume 'resolve_event' action or similar.
        // Actually, trigger_event in backend usually just requires any valid move or specific resolution? 
        // Logic says "The way is barred until... resolved".
        // Let's implement a 'resolve' action.
        fetch('/api/game/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'resolve_event', selection: choiceId })
        }).then(() => {
            setActiveEvent(null);
            fetchData();
        });
    };

    const triggerTensionFX = (type: string) => {
        setTensionEvent({ type, visible: true });
        if (onLog) {
            const msg = type === 'EVENT' ? 'Something stirs in the dark...' : 'The Chaos clock ticks...';
            const source = type === 'CHAOS_EVENT' ? 'CHAOS' : 'TENSION';
            onLog(source, msg, type === 'CHAOS_EVENT' ? 'error' : 'info');
        }
        setTimeout(() => setTensionEvent(prev => ({ ...prev, visible: false })), 2000);
    };

    const onRightClick = (e: React.MouseEvent, tx: number, ty: number) => {
        e.preventDefault();
        if (!explorationMode) return;

        // Check for object first, then combatant
        const obj = objects.find(o => o.x === tx && o.y === ty);
        const combatant = combatants.find(c => c.x === tx && c.y === ty);

        // If neither, return (unless we want to inspect empty tiles)
        // Actually, we should allow interactions on combatants too

        let tags: string[] = [];
        if (obj) tags = obj.tags || [];
        if (combatant) {
            // Use tags from backend if available, otherwise default
            tags = combatant.tags || ['inspect'];

            // Legacy fallback if backend doesn't define them yet
            if (tags.length === 0 || (tags.length === 1 && tags[0] === 'inspect')) {
                tags = ['inspect'];
                if (combatant.team !== 'Player' && explorationMode) {
                    // This block can be removed once backend is fully trusted, 
                    // but keeping as safety for now.
                }
            }
        }

        if (!obj && !combatant) return;

        setMenu({
            x: e.clientX,
            y: e.clientY,
            tx,
            ty,
            tags: tags
        });
    };

    useEffect(() => { fetchData(); }, [sceneVersion]);

    return (
        <div className="w-full h-full relative flex items-center justify-center p-4 bg-[#050505] overflow-hidden">

            {/* OVERLAYS & UI */}
            {menu && (
                <ContextMenu
                    {...menu}
                    tileX={menu.tx}
                    tileY={menu.ty}
                    objectTags={menu.tags}
                    onAction={handleAction}
                    onClose={() => setMenu(null)}
                />
            )}

            {tensionEvent.visible && (
                <div className="absolute inset-0 z-50 flex items-center justify-center pointer-events-none bg-red-900/10 animate-fade-in">
                    <div className="bg-black/80 border-2 border-red-900 p-6 flex flex-col items-center gap-4 animate-sim-shake scale-150">
                        <Target size={32} className={tensionEvent.type === 'CHAOS_EVENT' ? 'text-orange-500' : 'text-red-600'} />
                        <div className="flex flex-col items-center">
                            <span className="text-[10px] font-bold uppercase tracking-[0.4em] text-stone-500">Tension Roll</span>
                            <span className={`text-xl font-black uppercase tracking-widest ${tensionEvent.type === 'CHAOS_EVENT' ? 'text-orange-500' : 'text-red-600'}`}>
                                {tensionEvent.type.replace('_', ' ')}
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {activeEvent && (
                <div className="absolute inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
                    <div className="w-full max-w-lg bg-[#0a0a0a] border border-[#92400e] p-8 flex flex-col gap-6 shadow-[0_0_50px_rgba(146,64,14,0.3)]">
                        <div className="text-center space-y-2">
                            <span className="text-xs font-bold uppercase tracking-[0.3em] text-[#92400e]">Event Triggered</span>
                            <h3 className="text-2xl font-black text-white uppercase tracking-widest">{activeEvent.title || "Unknown Event"}</h3>
                        </div>
                        <p className="text-stone-300 font-serif text-lg leading-relaxed text-center italic">
                            "{activeEvent.description || "The shadows shift..."}"
                        </p>
                        <div className="flex flex-col gap-3 mt-4">
                            {(activeEvent.choices || []).map((choice: any, i: number) => (
                                <button
                                    key={i}
                                    onClick={() => handleEventChoice(choice.id || i)}
                                    className="py-4 px-6 bg-stone-900 border border-stone-800 hover:border-[#92400e] hover:bg-[#92400e]/10 transition-all group flex items-center justify-between"
                                >
                                    <span className="text-sm font-bold uppercase tracking-wider text-stone-400 group-hover:text-white transition-colors">{choice.label || "Continue"}</span>
                                    <div className="w-2 h-2 bg-stone-800 group-hover:bg-[#92400e] rotate-45 transition-colors" />
                                </button>
                            ))}
                            {(!activeEvent.choices || activeEvent.choices.length === 0) && (
                                <button
                                    onClick={() => handleEventChoice("continue")}
                                    className="py-4 px-6 bg-stone-900 border border-stone-800 hover:border-[#92400e] hover:bg-[#92400e]/10 transition-all group flex items-center justify-between"
                                >
                                    <span className="text-sm font-bold uppercase tracking-wider text-stone-400 group-hover:text-white transition-colors">Continue</span>
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* VISUAL FX OVERLAY */}
            {visualEffect && (
                <div className={`absolute inset-0 z-40 pointer-events-none ${visualEffect}`} />
            )}

            {/* MAP CONTAINER */}
            <div
                className="relative border-4 border-stone-900 shadow-[0_0_50px_rgba(0,0,0,0.8)] overflow-hidden bg-stone-950"
                style={{
                    display: 'grid',
                    gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
                    aspectRatio: '1/1',
                    height: '100%',
                    maxHeight: '100%',
                    maxWidth: '100%'
                }}
                onContextMenu={(e) => e.preventDefault()}
            >
                {mapTiles.map((row, y) => row.map((tile, x) => {
                    const isVisible = explored.has(`${x},${y}`) || !explorationMode;

                    // Check if an object exists on this tile
                    const obj = objects.find(o => o.x === x && o.y === y);
                    const terrainAsset = TERRAIN_ASSETS[tile] || TERRAIN_ASSETS['normal'];
                    let objectAsset = obj ? OBJECT_ASSETS[obj.type] : null;

                    // Fallback for unmapped types (e.g. Social NPCs like "Industrialists")
                    if (obj && !objectAsset) {
                        // Default to NPC sprite for now
                        objectAsset = '/objects/npc.png';
                    }

                    return (
                        <div
                            key={`${x}-${y}`}
                            onContextMenu={(e) => isVisible && onRightClick(e, x, y)}
                            onClick={() => isVisible && handleAction('move', x, y)}
                            className="relative flex items-center justify-center cursor-pointer transition-all duration-300"
                            style={{ opacity: isVisible ? 1 : 0.05 }}
                        >
                            {/* Base Terrain */}
                            <img src={terrainAsset} className="w-full h-full object-cover" style={{ imageRendering: 'pixelated' }} />

                            {/* Object Overlay (Enriched) */}
                            {isVisible && objectAsset && (
                                <div className="absolute inset-0 z-10 p-1 flex items-center justify-center">
                                    <img
                                        src={objectAsset}
                                        className="w-full h-full object-contain drop-shadow-lg"
                                    />
                                </div>
                            )}

                            {/* Player Token */}
                            {isVisible && explorationMode && x === playerPos.x && y === playerPos.y && (
                                <div className="absolute inset-0 z-20 scale-125 pointer-events-none">
                                    <Token name="Kliff" facing="down" team="Blue" sprite={playerSprite} />
                                </div>
                            )}
                        </div>
                    );
                }))}

                {/* Render Combatants (Both in Live and Replay) */}
                {combatants.map((c, i) => (
                    <div
                        key={i}
                        className="absolute transition-all duration-500 pointer-events-none"
                        style={{
                            width: `${100 / gridSize}%`,
                            height: `${100 / gridSize}%`,
                            left: `${c.x * (100 / gridSize)}%`,
                            top: `${c.y * (100 / gridSize)}%`
                        }}
                    >
                        <Token name={c.name} facing={c.facing || 'down'} team={c.team} sprite={c.sprite} dead={c.hp <= 0} />
                    </div>
                ))}

                {/* VISUAL EFFECTS LAYER */}
                <EffectLayer events={activeEvents} gridSize={gridSize} />
            </div>
        </div>
    );
}
