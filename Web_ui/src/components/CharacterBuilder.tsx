import { useState, useEffect } from 'react';
import { User, Save, Plus, Minus, Swords, Shield, Sparkles } from 'lucide-react';

const API_BASE = 'http://localhost:5001/api';

// Species base stats
const SPECIES_STATS: Record<string, Record<string, number>> = {
    Mammal: { Might: 10, Endurance: 11, Finesse: 12, Reflexes: 9, Vitality: 10, Fortitude: 8, Knowledge: 12, Logic: 8, Awareness: 9, Intuition: 10, Charm: 11, Willpower: 10 },
    Avian: { Might: 8, Endurance: 10, Finesse: 10, Reflexes: 12, Vitality: 11, Fortitude: 9, Knowledge: 11, Logic: 9, Awareness: 12, Intuition: 8, Charm: 10, Willpower: 10 },
    Reptile: { Might: 10, Endurance: 9, Finesse: 8, Reflexes: 11, Vitality: 10, Fortitude: 12, Knowledge: 10, Logic: 12, Awareness: 8, Intuition: 11, Charm: 10, Willpower: 9 },
    Insect: { Might: 12, Endurance: 8, Finesse: 10, Reflexes: 10, Vitality: 9, Fortitude: 11, Knowledge: 9, Logic: 10, Awareness: 11, Intuition: 10, Charm: 8, Willpower: 12 },
    Aquatic: { Might: 9, Endurance: 12, Finesse: 11, Reflexes: 10, Vitality: 8, Fortitude: 10, Knowledge: 10, Logic: 11, Awareness: 10, Intuition: 12, Charm: 9, Willpower: 8 },
    Plant: { Might: 11, Endurance: 10, Finesse: 9, Reflexes: 8, Vitality: 12, Fortitude: 10, Knowledge: 8, Logic: 10, Awareness: 10, Intuition: 9, Charm: 12, Willpower: 11 }
};

const STAT_LIST = ['Might', 'Endurance', 'Finesse', 'Reflexes', 'Vitality', 'Fortitude', 'Knowledge', 'Logic', 'Awareness', 'Intuition', 'Charm', 'Willpower'];
const SPECIES_LIST = Object.keys(SPECIES_STATS);

interface CharacterBuilderProps {
    onSave?: (character: any) => void;
}

export default function CharacterBuilder({ onSave }: CharacterBuilderProps) {
    const [name, setName] = useState('');
    const [species, setSpecies] = useState('Mammal');
    const [stats, setStats] = useState<Record<string, number>>({ ...SPECIES_STATS.Mammal });
    const [bonusPoints, setBonusPoints] = useState(10);
    const [status, setStatus] = useState('');
    const [powers, setPowers] = useState<string[]>([]);
    const [availablePowers] = useState(['Bolt', 'Heal', 'Shield', 'Push', 'Burn']);

    // Update stats when species changes
    useEffect(() => {
        setStats({ ...SPECIES_STATS[species] });
        setBonusPoints(10);
    }, [species]);

    const totalStats = Object.values(stats).reduce((a, b) => a + b, 0);
    const baseTotal = Object.values(SPECIES_STATS[species]).reduce((a, b) => a + b, 0);

    const adjustStat = (stat: string, delta: number) => {
        if (delta > 0 && bonusPoints <= 0) return;
        if (delta < 0 && stats[stat] <= SPECIES_STATS[species][stat]) return;

        setStats(prev => ({ ...prev, [stat]: prev[stat] + delta }));
        setBonusPoints(prev => prev - delta);
    };

    const togglePower = (power: string) => {
        if (powers.includes(power)) {
            setPowers(powers.filter(p => p !== power));
        } else if (powers.length < 3) {
            setPowers([...powers, power]);
        }
    };

    const saveCharacter = async () => {
        if (!name.trim()) {
            setStatus('Name is required!');
            return;
        }

        const character = {
            Name: name,
            Species: species,
            Stats: stats,
            Skills: [],
            Powers: powers,
            Inventory: [],
            Gear: []
        };

        try {
            const response = await fetch(`${API_BASE}/character/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(character)
            });

            if (response.ok) {
                setStatus(`Saved ${name}!`);
                if (onSave) onSave(character);
            } else {
                setStatus('Save failed!');
            }
        } catch {
            // Fallback: save locally
            setStatus('API offline - save pending');
        }
    };

    // Derived stats calculation
    const hp = 10 + stats.Might + stats.Reflexes + stats.Vitality;
    const sp = stats.Endurance + stats.Finesse + stats.Fortitude;
    const fp = stats.Knowledge + stats.Charm + stats.Intuition;
    const cmp = 10 + stats.Willpower + stats.Logic + stats.Awareness;

    return (
        <div className="h-full overflow-auto p-6 text-stone-300">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                <User size={20} className="text-[#00f2ff]" />
                Character Builder
            </h2>

            <div className="grid grid-cols-2 gap-6">
                {/* Left Column: Name, Species, Stats */}
                <div className="space-y-4">
                    {/* Name */}
                    <div className="bg-[#0a0a0a] border border-stone-800 rounded p-4">
                        <label className="text-[10px] uppercase text-stone-500 font-bold mb-2 block">Name</label>
                        <input
                            type="text"
                            value={name}
                            onChange={e => setName(e.target.value)}
                            placeholder="Enter name..."
                            className="w-full bg-stone-900 border border-stone-700 rounded px-3 py-2 text-white focus:border-[#00f2ff] focus:outline-none"
                        />
                    </div>

                    {/* Species */}
                    <div className="bg-[#0a0a0a] border border-stone-800 rounded p-4">
                        <label className="text-[10px] uppercase text-stone-500 font-bold mb-2 block">Species</label>
                        <div className="grid grid-cols-3 gap-2">
                            {SPECIES_LIST.map(s => (
                                <button
                                    key={s}
                                    onClick={() => setSpecies(s)}
                                    className={`p-2 rounded text-xs font-bold transition-all
                                        ${species === s
                                            ? 'bg-[#00f2ff] text-black'
                                            : 'bg-stone-900 text-stone-400 hover:bg-stone-800'}`}
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Stats */}
                    <div className="bg-[#0a0a0a] border border-stone-800 rounded p-4">
                        <div className="flex justify-between items-center mb-3">
                            <label className="text-[10px] uppercase text-stone-500 font-bold">Attributes</label>
                            <span className={`text-xs font-mono ${bonusPoints > 0 ? 'text-green-400' : 'text-stone-500'}`}>
                                {bonusPoints} bonus pts
                            </span>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            {STAT_LIST.map(stat => (
                                <div key={stat} className="flex items-center justify-between bg-stone-900 p-2 rounded">
                                    <span className="text-xs text-stone-400 w-20">{stat}</span>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => adjustStat(stat, -1)}
                                            disabled={stats[stat] <= SPECIES_STATS[species][stat]}
                                            className="w-5 h-5 flex items-center justify-center bg-stone-800 rounded text-stone-400 hover:bg-red-900 disabled:opacity-30"
                                        >
                                            <Minus size={10} />
                                        </button>
                                        <span className={`text-sm font-mono w-6 text-center
                                            ${stats[stat] > SPECIES_STATS[species][stat] ? 'text-green-400' : 'text-white'}`}>
                                            {stats[stat]}
                                        </span>
                                        <button
                                            onClick={() => adjustStat(stat, 1)}
                                            disabled={bonusPoints <= 0}
                                            className="w-5 h-5 flex items-center justify-center bg-stone-800 rounded text-stone-400 hover:bg-green-900 disabled:opacity-30"
                                        >
                                            <Plus size={10} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right Column: Powers, Preview, Save */}
                <div className="space-y-4">
                    {/* Powers */}
                    <div className="bg-[#0a0a0a] border border-stone-800 rounded p-4">
                        <label className="text-[10px] uppercase text-stone-500 font-bold mb-2 block flex items-center gap-1">
                            <Sparkles size={10} /> Powers (Max 3)
                        </label>
                        <div className="grid grid-cols-3 gap-2">
                            {availablePowers.map(p => (
                                <button
                                    key={p}
                                    onClick={() => togglePower(p)}
                                    className={`p-2 rounded text-xs font-bold transition-all
                                        ${powers.includes(p)
                                            ? 'bg-purple-600 text-white'
                                            : 'bg-stone-900 text-stone-400 hover:bg-stone-800'}`}
                                >
                                    {p}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Derived Stats Preview */}
                    <div className="bg-[#0a0a0a] border border-stone-800 rounded p-4">
                        <label className="text-[10px] uppercase text-stone-500 font-bold mb-3 block">Derived Stats</label>
                        <div className="grid grid-cols-2 gap-3">
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 flex items-center justify-center bg-red-900/50 rounded">
                                    <Swords size={14} className="text-red-400" />
                                </div>
                                <div>
                                    <div className="text-[10px] text-stone-500">HP</div>
                                    <div className="text-lg font-bold text-red-400">{hp}</div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 flex items-center justify-center bg-blue-900/50 rounded">
                                    <Shield size={14} className="text-blue-400" />
                                </div>
                                <div>
                                    <div className="text-[10px] text-stone-500">CMP</div>
                                    <div className="text-lg font-bold text-blue-400">{cmp}</div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 flex items-center justify-center bg-green-900/50 rounded">
                                    <div className="text-green-400 text-xs font-bold">SP</div>
                                </div>
                                <div>
                                    <div className="text-[10px] text-stone-500">Stamina</div>
                                    <div className="text-lg font-bold text-green-400">{sp}</div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 flex items-center justify-center bg-purple-900/50 rounded">
                                    <div className="text-purple-400 text-xs font-bold">FP</div>
                                </div>
                                <div>
                                    <div className="text-[10px] text-stone-500">Focus</div>
                                    <div className="text-lg font-bold text-purple-400">{fp}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Summary */}
                    <div className="bg-[#0a0a0a] border border-stone-800 rounded p-4">
                        <label className="text-[10px] uppercase text-stone-500 font-bold mb-2 block">Summary</label>
                        <div className="text-xs text-stone-400 space-y-1">
                            <p>Total Stats: <span className="text-white font-mono">{totalStats}</span> (Base: {baseTotal})</p>
                            <p>Powers: <span className="text-purple-400">{powers.join(', ') || 'None'}</span></p>
                        </div>
                    </div>

                    {/* Save Button */}
                    <div className="flex items-center justify-between">
                        {status && <span className={`text-xs ${status.includes('Saved') ? 'text-green-400' : 'text-yellow-400'}`}>{status}</span>}
                        <button
                            onClick={saveCharacter}
                            className="flex items-center gap-2 px-6 py-3 bg-[#00f2ff] text-black font-bold uppercase tracking-wider rounded hover:shadow-[0_0_20px_rgba(0,242,255,0.4)] transition-all"
                        >
                            <Save size={16} /> Save Character
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
