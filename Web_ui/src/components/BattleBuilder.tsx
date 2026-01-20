import { useState, useEffect } from 'react';
import { Users, Map, Swords, Plus, X, Flame, Droplets, Mountain } from 'lucide-react';

const API_BASE = 'http://localhost:5001/api';

interface CharacterInfo {
    name: string;
    species: string;
    skills?: number;
    powers?: number;
}

interface TerrainTile {
    x: number;
    y: number;
    type: string;
}

const TERRAIN_TYPES = [
    { id: 'normal', name: 'Clear', icon: null, color: 'bg-stone-700' },
    { id: 'fire', name: 'Fire', icon: Flame, color: 'bg-orange-600' },
    { id: 'water_shallow', name: 'Water', icon: Droplets, color: 'bg-blue-500' },
    { id: 'difficult', name: 'Rubble', icon: Mountain, color: 'bg-stone-500' },
    { id: 'ice', name: 'Ice', icon: null, color: 'bg-cyan-300' },
    { id: 'mud', name: 'Mud', icon: null, color: 'bg-amber-800' },
];

const MAP_SIZE = 12;

interface BattleBuilderProps {
    onBattleStart?: () => void;
}

export default function BattleBuilder({ onBattleStart }: BattleBuilderProps) {
    const [characters, setCharacters] = useState<CharacterInfo[]>([]);
    const [blueTeam, setBlueTeam] = useState<string[]>([]);
    const [redTeam, setRedTeam] = useState<string[]>([]);
    const [terrain, setTerrain] = useState<TerrainTile[]>([]);
    const [selectedTerrain, setSelectedTerrain] = useState('fire');
    const [isLoading, setIsLoading] = useState(false);
    const [status, setStatus] = useState('');

    // Fetch available characters on mount
    useEffect(() => {
        fetch(`${API_BASE}/characters`)
            .then(res => res.json())
            .then(data => setCharacters(data.characters || []))
            .catch(() => setStatus('Failed to load characters'));
    }, []);

    const availableCharacters = characters.filter(
        c => !blueTeam.includes(c.name) && !redTeam.includes(c.name)
    );

    const addToTeam = (name: string, team: 'blue' | 'red') => {
        if (team === 'blue') {
            setBlueTeam([...blueTeam, name]);
        } else {
            setRedTeam([...redTeam, name]);
        }
    };

    const removeFromTeam = (name: string, team: 'blue' | 'red') => {
        if (team === 'blue') {
            setBlueTeam(blueTeam.filter(n => n !== name));
        } else {
            setRedTeam(redTeam.filter(n => n !== name));
        }
    };

    const handleTileClick = (x: number, y: number) => {
        // Remove existing terrain at this position or add new
        const existing = terrain.find(t => t.x === x && t.y === y);

        if (existing && existing.type === selectedTerrain) {
            // Clear if same type clicked
            setTerrain(terrain.filter(t => !(t.x === x && t.y === y)));
        } else {
            // Replace/Add terrain
            setTerrain([
                ...terrain.filter(t => !(t.x === x && t.y === y)),
                { x, y, type: selectedTerrain }
            ]);
        }
    };

    const getTerrainColor = (x: number, y: number) => {
        const tile = terrain.find(t => t.x === x && t.y === y);
        if (tile) {
            return TERRAIN_TYPES.find(t => t.id === tile.type)?.color || 'bg-stone-800';
        }
        return 'bg-stone-800';
    };

    const startBattle = async () => {
        if (blueTeam.length === 0 || redTeam.length === 0) {
            setStatus('Both teams need at least one character!');
            return;
        }

        setIsLoading(true);
        setStatus('Starting battle...');

        try {
            const response = await fetch(`${API_BASE}/battle/staged`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    blue_team: blueTeam,
                    red_team: redTeam,
                    terrain: terrain
                })
            });

            if (response.ok) {
                setStatus('Battle complete! Check Arena tab.');
                if (onBattleStart) onBattleStart();
            } else {
                const err = await response.json();
                setStatus(`Error: ${err.error || 'Unknown error'}`);
            }
        } catch (e) {
            setStatus('Failed to connect to API server');
        } finally {
            setIsLoading(false);
        }
    };

    const TeamPanel = ({ team, name, color }: { team: string[], name: string, color: string }) => (
        <div className={`flex-1 bg-[#0a0a0a] border border-stone-800 rounded p-4`}>
            <h3 className={`font-bold text-sm uppercase tracking-wider mb-3 ${color}`}>
                {name} ({team.length})
            </h3>
            <div className="space-y-1 min-h-[100px]">
                {team.map(char => (
                    <div key={char} className="flex items-center justify-between bg-stone-900 p-2 rounded">
                        <span className="text-sm text-stone-300">{char}</span>
                        <button
                            onClick={() => removeFromTeam(char, name === 'Blue Team' ? 'blue' : 'red')}
                            className="text-stone-600 hover:text-red-500"
                        >
                            <X size={14} />
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );

    return (
        <div className="h-full overflow-auto p-6 text-stone-300">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Swords size={20} className="text-[#00f2ff]" />
                Battle Builder
            </h2>

            {/* Top Section: Teams */}
            <div className="grid grid-cols-3 gap-4 mb-6">
                <TeamPanel team={blueTeam} name="Blue Team" color="text-blue-400" />

                {/* Available Characters */}
                <div className="bg-[#0a0a0a] border border-stone-800 rounded p-4">
                    <h3 className="font-bold text-sm uppercase tracking-wider mb-3 text-stone-500 flex items-center gap-2">
                        <Users size={14} /> Available
                    </h3>
                    <div className="space-y-1 max-h-[150px] overflow-y-auto">
                        {availableCharacters.map(char => (
                            <div key={char.name} className="flex items-center justify-between bg-stone-900 p-2 rounded">
                                <div>
                                    <span className="text-sm text-stone-300">{char.name}</span>
                                    <span className="text-[10px] text-stone-600 ml-2">{char.species}</span>
                                </div>
                                <div className="flex gap-1">
                                    <button
                                        onClick={() => addToTeam(char.name, 'blue')}
                                        className="p-1 text-blue-400 hover:bg-blue-900/50 rounded"
                                        title="Add to Blue"
                                    >
                                        <Plus size={14} />
                                    </button>
                                    <button
                                        onClick={() => addToTeam(char.name, 'red')}
                                        className="p-1 text-red-400 hover:bg-red-900/50 rounded"
                                        title="Add to Red"
                                    >
                                        <Plus size={14} />
                                    </button>
                                </div>
                            </div>
                        ))}
                        {availableCharacters.length === 0 && (
                            <p className="text-stone-600 text-xs text-center py-4">All characters assigned</p>
                        )}
                    </div>
                </div>

                <TeamPanel team={redTeam} name="Red Team" color="text-red-400" />
            </div>

            {/* Middle Section: Map + Terrain Palette */}
            <div className="flex gap-4 mb-6">
                {/* Terrain Palette */}
                <div className="bg-[#0a0a0a] border border-stone-800 rounded p-4 w-32">
                    <h3 className="font-bold text-[10px] uppercase tracking-wider mb-3 text-stone-500 flex items-center gap-2">
                        <Map size={12} /> Terrain
                    </h3>
                    <div className="space-y-2">
                        {TERRAIN_TYPES.map(t => (
                            <button
                                key={t.id}
                                onClick={() => setSelectedTerrain(t.id)}
                                className={`w-full p-2 rounded text-xs flex items-center gap-2 transition-colors
                                    ${selectedTerrain === t.id
                                        ? 'ring-2 ring-[#00f2ff] bg-stone-800'
                                        : 'bg-stone-900 hover:bg-stone-800'}`}
                            >
                                <div className={`w-4 h-4 rounded ${t.color}`} />
                                {t.name}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Map Grid */}
                <div className="flex-1 bg-[#0a0a0a] border border-stone-800 rounded p-4">
                    <h3 className="font-bold text-[10px] uppercase tracking-wider mb-3 text-stone-500">
                        Map ({MAP_SIZE}x{MAP_SIZE}) - Click to place terrain
                    </h3>
                    <div
                        className="grid gap-[1px] bg-stone-900 p-1 w-fit mx-auto"
                        style={{ gridTemplateColumns: `repeat(${MAP_SIZE}, 1fr)` }}
                    >
                        {Array.from({ length: MAP_SIZE * MAP_SIZE }).map((_, i) => {
                            const x = i % MAP_SIZE;
                            const y = Math.floor(i / MAP_SIZE);
                            return (
                                <button
                                    key={i}
                                    onClick={() => handleTileClick(x, y)}
                                    className={`w-6 h-6 ${getTerrainColor(x, y)} hover:brightness-125 transition-all`}
                                    title={`${x}, ${y}`}
                                />
                            );
                        })}
                    </div>
                    <p className="text-[10px] text-stone-600 mt-2 text-center">
                        Terrain placed: {terrain.length} tiles
                    </p>
                </div>
            </div>

            {/* Bottom: Start Button */}
            <div className="flex items-center justify-between bg-[#0a0a0a] border border-stone-800 rounded p-4">
                <div className="text-sm">
                    {status && (
                        <span className={status.includes('Error') || status.includes('Failed') ? 'text-red-400' : 'text-green-400'}>
                            {status}
                        </span>
                    )}
                </div>
                <button
                    onClick={startBattle}
                    disabled={isLoading || blueTeam.length === 0 || redTeam.length === 0}
                    className={`px-6 py-3 font-bold uppercase tracking-wider rounded transition-all
                        ${isLoading || blueTeam.length === 0 || redTeam.length === 0
                            ? 'bg-stone-800 text-stone-600 cursor-not-allowed'
                            : 'bg-[#00f2ff] text-black hover:shadow-[0_0_20px_rgba(0,242,255,0.4)]'
                        }`}
                >
                    {isLoading ? 'Simulating...' : 'Start Battle'}
                </button>
            </div>
        </div>
    );
}
