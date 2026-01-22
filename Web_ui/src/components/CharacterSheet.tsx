import { Shield, User, Crosshair, Brain, X } from 'lucide-react';
import ItemIcon from './ItemIcon';

interface CharacterSheetProps {
    equipment?: Record<string, string>;
    stats?: Record<string, number>;
    onUnequip?: (slot: string) => void;
    sprite?: string;
    name?: string;
}

export default function CharacterSheet({ equipment, stats: propStats, onUnequip, sprite, name }: CharacterSheetProps) {
    const gear = equipment || {
        "Main Hand": "Empty", "Off Hand": "Empty", "Armor": "Empty"
    };

    const stats = propStats && Object.keys(propStats).length > 0 ? propStats : {
        Might: 10, Reflexes: 10, Endurance: 10, Vitality: 10, Fortitude: 10, Finesse: 10,
        Knowledge: 10, Logic: 10, Awareness: 10, Intuition: 10, Charm: 10, Willpower: 10
    };

    const getScore = (name: string) => stats[name] || 10;
    const derivedHP = getScore('Might') + getScore('Reflexes') + getScore('Vitality');
    const derivedSP = getScore('Endurance') + getScore('Finesse') + getScore('Fortitude');
    const derivedFP = getScore('Knowledge') + getScore('Charm') + getScore('Intuition');

    const getMod = (val: number) => {
        const mod = Math.floor((val - 10) / 2);
        return mod >= 0 ? `+${mod}` : `${mod}`;
    };

    const StatBlock = ({ label, val }: { label: string; val: number }) => (
        <div className="flex justify-between items-center p-2 bg-stone-900 border border-stone-800">
            <span className="text-stone-500 font-bold text-xs">{label}</span>
            <div className="flex gap-2 items-end">
                <span className="text-white font-mono text-lg leading-none">{val}</span>
                <span className="text-[#92400e] text-xs font-mono">({getMod(val)})</span>
            </div>
        </div>
    );

    const EquipSlot = ({ slot, item }: { slot: string; item: string }) => (
        <div className={`p-2 border bg-stone-900/80 border-stone-800 transition-colors group relative flex items-center gap-3`}>
            <div className="w-8 h-8 bg-black border border-stone-700 flex items-center justify-center">
                {item && item !== 'Empty' ? <ItemIcon name={item} /> : <span className="text-stone-800">.</span>}
            </div>
            <div className="flex-1">
                <div className="text-[8px] text-stone-600 uppercase tracking-tighter">{slot}</div>
                <div className="text-xs font-bold text-stone-300 truncate">{item || "Empty"}</div>
            </div>
            {item && item !== 'Empty' && onUnequip && (
                <button onClick={() => onUnequip(slot)} className="text-stone-700 hover:text-red-500 opacity-0 group-hover:opacity-100"><X size={12} /></button>
            )}
        </div>
    );

    return (
        <div className="flex gap-6 h-full p-6 text-stone-300 justify-center overflow-auto bg-[#050505] font-serif">
            <div className="w-64 space-y-4">
                <div className="bg-[#0a0a0a] p-4 border border-stone-900">
                    <h3 className="text-stone-500 font-bold uppercase text-[10px] mb-3 flex items-center gap-2 tracking-widest border-b border-stone-900 pb-1"><User size={12} /> Physical Attributes</h3>
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

            <div className="w-64 space-y-4">
                <div className="bg-[#0a0a0a] p-4 border border-stone-900">
                    <h3 className="text-stone-500 font-bold uppercase text-[10px] mb-3 flex items-center gap-2 tracking-widest border-b border-stone-900 pb-1"><Brain size={12} /> Mental Attributes</h3>
                    <div className="space-y-1">
                        <StatBlock label="KNOWLEDGE" val={stats.Knowledge} />
                        <StatBlock label="LOGIC" val={stats.Logic} />
                        <StatBlock label="AWARENESS" val={stats.Awareness} />
                        <StatBlock label="INTUITION" val={stats.Intuition} />
                        <StatBlock label="CHARM" val={stats.Charm} />
                        <StatBlock label="WILLPOWER" val={stats.Willpower} />
                    </div>
                </div>

                <div className="bg-[#0a0a0a] p-4 border border-stone-900">
                    <h3 className="text-stone-500 font-bold uppercase text-[10px] mb-3 flex items-center gap-2 tracking-widest border-b border-stone-900 pb-1"><Crosshair size={12} /> Derived Capacity</h3>
                    <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-stone-900 p-2"><div className="text-[9px] text-stone-600">HP</div><div className="text-lg text-white font-mono">{derivedHP}</div></div>
                        <div className="bg-stone-900 p-2"><div className="text-[9px] text-stone-600">SP</div><div className="text-lg text-white font-mono">{derivedSP}</div></div>
                        <div className="bg-stone-900 p-2"><div className="text-[9px] text-stone-600">FP</div><div className="text-lg text-white font-mono">{derivedFP}</div></div>
                    </div>
                </div>
            </div>

            <div className="w-80 bg-[#0a0a0a] p-4 border border-stone-900 flex flex-col">
                <h3 className="text-stone-500 font-bold uppercase text-[10px] mb-4 flex items-center gap-2 tracking-widest border-b border-stone-900 pb-1"><Shield size={12} /> Active Equipment</h3>
                <div className="space-y-2 flex-1">
                    {Object.entries(gear).map(([slot, item]) => (
                        <EquipSlot key={slot} slot={slot} item={item} />
                    ))}
                </div>
                <div className="mt-4 pt-4 border-t border-stone-900 flex items-center gap-4">
                    <div className="w-16 h-20 bg-black border border-stone-800 shrink-0 overflow-hidden relative p-1">
                        <img src={sprite ? `/tokens/${sprite}` : '/tokens/badger_front.png'} alt="portrait" className="w-full h-full object-cover grayscale-[0.2]" />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                    </div>
                    <div><h1 className="text-md font-bold text-white uppercase tracking-wider">{name || "HERO"}</h1><p className="text-[#92400e] font-mono text-[10px] uppercase tracking-widest">Master of Fate</p></div>
                </div>
            </div>
        </div>
    );
}
