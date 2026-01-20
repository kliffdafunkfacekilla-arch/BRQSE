import { Shield, User, Crosshair, Brain, X } from 'lucide-react';
import ItemIcon from './ItemIcon';

interface CharacterSheetProps {
    equipment?: Record<string, string>;
    onUnequip?: (slot: string) => void;
}

export default function CharacterSheet({ equipment, onUnequip }: CharacterSheetProps) {
    // Use props if available, else fallback
    const gear = equipment || {
        "Main Hand": "Empty", "Off Hand": "Empty", "Head": "Empty",
        "Body": "Empty", "Feet": "Empty", "Ring 1": "Empty"
    };

    // Mock Stats - Using your game's stat system
    const stats = {
        Might: 10, Reflexes: 10, Endurance: 12, Vitality: 10, Fortitude: 14, Finesse: 12,
        Knowledge: 12, Logic: 10, Awareness: 10, Intuition: 10, Charm: 12, Willpower: 10
    };

    const getMod = (val: number) => {
        const mod = Math.floor((val - 10) / 2);
        return mod >= 0 ? `+${mod}` : `${mod}`;
    };

    const StatBlock = ({ label, val }: { label: string; val: number }) => (
        <div className="flex justify-between items-center p-2 bg-stone-900 border border-stone-800">
            <span className="text-stone-500 font-bold text-xs">{label}</span>
            <div className="flex gap-2 items-end">
                <span className="text-white font-mono text-lg leading-none">{val}</span>
                <span className="text-[#00f2ff] text-xs font-mono">({getMod(val)})</span>
            </div>
        </div>
    );

    const EquipSlot = ({ slot, item }: { slot: string; item: string }) => (
        <div
            className={`flex items-center gap-3 p-2 border transition-colors group relative
            ${item !== 'Empty' ? 'bg-stone-900/80 border-stone-700' : 'bg-[#0a0a0f] border-stone-800 hover:border-stone-600'}
        `}
        >
            <div className="w-10 h-10 bg-black border border-stone-800 flex items-center justify-center shrink-0">
                {item === "Empty" ? <span className="text-stone-700 text-xs">.</span> : <ItemIcon name={item} />}
            </div>
            <div className="flex-1 overflow-hidden">
                <div className="text-[9px] text-stone-500 uppercase tracking-wider mb-0.5">{slot}</div>
                <div className={`text-xs truncate ${item === 'Empty' ? 'text-stone-700' : 'text-stone-300 group-hover:text-white'}`}>{item}</div>
            </div>

            {/* UNEQUIP BUTTON */}
            {item !== "Empty" && onUnequip && (
                <button
                    onClick={() => onUnequip(slot)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-stone-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Unequip"
                >
                    <X size={14} />
                </button>
            )}
        </div>
    );

    return (
        <div className="flex gap-6 h-full p-6 text-stone-300 justify-center overflow-auto">

            {/* LEFT: PHYSICAL */}
            <div className="w-64 space-y-4">
                <div className="bg-[#080808] p-4 border border-stone-800 rounded">
                    <h3 className="text-stone-500 font-bold uppercase text-xs mb-3 flex items-center gap-2"><User size={14} /> Physical</h3>
                    <div className="space-y-1">
                        <StatBlock label="MIGHT" val={stats.Might} />
                        <StatBlock label="REFLEXES" val={stats.Reflexes} />
                        <StatBlock label="ENDURANCE" val={stats.Endurance} />
                        <StatBlock label="VITALITY" val={stats.Vitality} />
                        <StatBlock label="FORTITUDE" val={stats.Fortitude} />
                        <StatBlock label="FINESSE" val={stats.Finesse} />
                    </div>
                </div>
            </div>

            {/* CENTER: MENTAL + DERIVED */}
            <div className="w-64 space-y-4">
                <div className="bg-[#080808] p-4 border border-stone-800 rounded">
                    <h3 className="text-stone-500 font-bold uppercase text-xs mb-3 flex items-center gap-2"><Brain size={14} /> Mental</h3>
                    <div className="space-y-1">
                        <StatBlock label="KNOWLEDGE" val={stats.Knowledge} />
                        <StatBlock label="LOGIC" val={stats.Logic} />
                        <StatBlock label="AWARENESS" val={stats.Awareness} />
                        <StatBlock label="INTUITION" val={stats.Intuition} />
                        <StatBlock label="CHARM" val={stats.Charm} />
                        <StatBlock label="WILLPOWER" val={stats.Willpower} />
                    </div>
                </div>

                <div className="bg-[#080808] p-4 border border-stone-800 rounded">
                    <h3 className="text-stone-500 font-bold uppercase text-xs mb-3 flex items-center gap-2"><Crosshair size={14} /> Derived</h3>
                    <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-stone-900 p-2">
                            <div className="text-[10px] text-stone-500">HP</div>
                            <div className="text-xl text-white font-mono">40</div>
                        </div>
                        <div className="bg-stone-900 p-2">
                            <div className="text-[10px] text-stone-500">SP</div>
                            <div className="text-xl text-white font-mono">12</div>
                        </div>
                        <div className="bg-stone-900 p-2">
                            <div className="text-[10px] text-stone-500">FP</div>
                            <div className="text-xl text-white font-mono">10</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* RIGHT: EQUIPMENT */}
            <div className="w-80 bg-[#080808] p-4 border border-stone-800 rounded flex flex-col">
                <h3 className="text-stone-500 font-bold uppercase text-xs mb-4 flex items-center gap-2"><Shield size={14} /> Equipment</h3>

                <div className="space-y-2 flex-1">
                    {Object.entries(gear).map(([slot, item]) => (
                        <EquipSlot key={slot} slot={slot} item={item} />
                    ))}
                </div>

                {/* PORTRAIT */}
                <div className="mt-4 pt-4 border-t border-stone-800 flex items-center gap-4">
                    <div className="w-16 h-16 bg-black border border-stone-700 shrink-0 overflow-hidden">
                        <img src="/tokens/badger_front.png" alt="portrait" className="w-full h-full object-contain opacity-80" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-white">HERO</h1>
                        <p className="text-[#00f2ff] font-mono text-xs">Mammal</p>
                    </div>
                </div>
            </div>

        </div>
    );
}
