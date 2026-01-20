import { Shield, User, Crosshair, Heart, Zap, Brain } from 'lucide-react';
import ItemIcon from './ItemIcon';

export default function CharacterSheet() {
    // Mock Data - Matches your game's stat system
    const stats = {
        // Physical
        Might: 10,
        Reflexes: 10,
        Endurance: 12,
        Vitality: 10,
        Fortitude: 14,
        Finesse: 12,
        // Mental
        Knowledge: 12,
        Logic: 10,
        Awareness: 10,
        Intuition: 10,
        Charm: 12,
        Willpower: 10
    };

    const equipment: Record<string, string> = {
        "Main Hand": "Cane Sword",
        "Off Hand": "Empty",
        "Armor": "Troll Hide",
        "Head": "Empty",
        "Neck": "Empty",
        "Ring 1": "Empty",
        "Ring 2": "Empty"
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
        <div className="flex items-center gap-3 p-2 bg-[#0a0a0f] border border-stone-800 hover:border-stone-600 transition-colors cursor-pointer group">
            <div className="w-10 h-10 bg-black border border-stone-800 flex items-center justify-center">
                {item === "Empty" ? <span className="text-stone-700 text-xs">.</span> : <ItemIcon name={item} />}
            </div>
            <div className="flex-1">
                <div className="text-[9px] text-stone-500 uppercase tracking-wider mb-0.5">{slot}</div>
                <div className={`text-xs ${item === 'Empty' ? 'text-stone-700' : 'text-stone-300 group-hover:text-white'}`}>{item}</div>
            </div>
        </div>
    );

    return (
        <div className="flex gap-6 h-full p-6 text-stone-300 justify-center overflow-auto">

            {/* LEFT: PHYSICAL ATTRIBUTES */}
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

            {/* CENTER: MENTAL ATTRIBUTES + GEAR */}
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
                    <h3 className="text-stone-500 font-bold uppercase text-xs mb-3 flex items-center gap-2"><Crosshair size={14} /> Derived Stats</h3>
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

            {/* RIGHT: GEAR + PORTRAIT */}
            <div className="w-80 space-y-4">
                <div className="bg-[#080808] p-4 border border-stone-800 rounded flex flex-col">
                    <h3 className="text-stone-500 font-bold uppercase text-xs mb-4 flex items-center gap-2"><Shield size={14} /> Equipment</h3>

                    <div className="space-y-2 flex-1">
                        {Object.entries(equipment).map(([slot, item]) => (
                            <EquipSlot key={slot} slot={slot} item={item} />
                        ))}
                    </div>
                </div>

                {/* PORTRAIT */}
                <div className="bg-[#080808] border border-stone-800 rounded flex flex-col items-center p-4">
                    <div className="w-32 h-32 bg-black border-2 border-stone-700 mb-3 shadow-[0_0_20px_rgba(0,0,0,0.5)]">
                        <img src="/tokens/badger_front.png" alt="portrait" className="w-full h-full object-contain p-2 opacity-80" />
                    </div>
                    <h1 className="text-xl font-bold text-white tracking-wider">HERO</h1>
                    <p className="text-[#00f2ff] font-mono text-xs mb-2">Mammal</p>
                    <div className="text-[9px] text-stone-500">Powers: Bolt, Push</div>
                </div>
            </div>

        </div>
    );
}
