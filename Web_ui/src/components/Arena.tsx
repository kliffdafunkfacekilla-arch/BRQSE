import { useState, useEffect } from 'react';
import Token from './Token';
import ContextMenu from './ContextMenu';
import { Target } from 'lucide-react';

const TILE_SIZE = 64;

interface ArenaProps {
    onStatsUpdate?: (currentHp: number, maxHp: number, name: string) => void;
    onLog?: (source: string, msg: string, type: 'info' | 'combat' | 'error') => void;
    sceneVersion?: number;
    playerSprite?: string;
}

export default function Arena({ onStatsUpdate, onLog, sceneVersion = 0, playerSprite }: ArenaProps) {
    const [combatants, setCombatants] = useState<any[]>([]);
    const [gridSize, setGridSize] = useState(20);
    const [mapTiles, setMapTiles] = useState<string[][]>([]);
    const [explorationMode, setExplorationMode] = useState(true);
    const [playerPos, setPlayerPos] = useState({ x: 5, y: 5 });
    const [objects, setObjects] = useState<any[]>([]);
    const [explored, setExplored] = useState<Set<string>>(new Set());

    // UI State
    const [tensionEvent, setTensionEvent] = useState<{ type: string, visible: boolean }>({ type: '', visible: false });
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
        'Barrel': '/items/chest_closed.png', // Placeholder
        'Crate': '/items/chest_closed.png',  // Placeholder
        'Chest': '/items/chest_closed.png',
        'Table': '/tiles/wall_stone.png',   // Placeholder
        'Stone': '/traps/pressure_plate.png',
        'Logs': '/trees/mangrove_1.png',
        'Chandelier': '/icons/weapon/bloodbane.png' // Visual placeholder
    };

    const fetchData = () => {
        fetch('/api/game/state')
            .then(res => res.json())
            .then(data => {
                if (data.mode === 'EXPLORE') {
                    setExplorationMode(true);
                    updateExplorationState(data);
                    if (data.event === 'SCENE_STARTED' && onLog) {
                        onLog('EXPLORE', `Entered: ${data.scene_text}`, 'info');
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
        fetch('/api/game/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, x: tx, y: ty })
        })
            .then(res => res.json())
            .then(data => {
                const res = data.result;
                if (res.success) {
                    updateExplorationState(data.state);

                    if (res.log && onLog) onLog('SYSTEM', res.log, 'info');

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
                }
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

        // Find object at this position
        const obj = objects.find(o => o.x === tx && o.y === ty);
        setMenu({
            x: e.clientX,
            y: e.clientY,
            tx,
            ty,
            tags: obj?.tags || []
        });
    };

    useEffect(() => { fetchData(); }, [sceneVersion]);

    return (
        <div className="flex h-full w-full gap-4 p-4 overflow-hidden relative">
            <div className="flex-1 flex flex-col items-center relative">

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

                <div
                    className="relative border-4 border-stone-900 shadow-[0_0_50px_rgba(0,0,0,0.8)] aspect-square max-w-full overflow-hidden bg-stone-950"
                    style={{
                        display: 'grid',
                        gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
                        width: 'min(calc(100vh - 300px), 100%)'
                    }}
                    onContextMenu={(e) => e.preventDefault()}
                >
                    {mapTiles.map((row, y) => row.map((tile, x) => {
                        const isVisible = explored.has(`${x},${y}`) || !explorationMode;

                        // Check if an object exists on this tile
                        const obj = objects.find(o => o.x === x && o.y === y);
                        const terrainAsset = TERRAIN_ASSETS[tile] || TERRAIN_ASSETS['normal'];
                        const objectAsset = obj ? OBJECT_ASSETS[obj.type] : null;

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
                                    <div className="absolute inset-0 z-10 p-1">
                                        <img src={objectAsset} className="w-full h-full object-contain drop-shadow-lg" />
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

                    {!explorationMode && combatants.map((c, i) => (
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
                </div>
            </div>
        </div>
    );
}
