import { Zap, Heart, BookOpen, Activity, Swords, User, Backpack } from 'lucide-react';

interface SkillsPanelProps {
    skills: { name: string; active?: boolean; type?: string }[];
    powers: { name: string; active?: boolean; type?: string }[];
}

export default function SkillsPanel({ skills = [], powers = [] }: SkillsPanelProps) {
    return (
        <div className="flex gap-6 h-full p-6 text-stone-300 justify-center overflow-auto bg-[#050505] font-serif">
            <div className="w-96 space-y-4 flex flex-col">
                <div className="bg-[#0a0a0a] p-4 border border-stone-900 flex-1 flex flex-col min-h-0">
                    <h3 className="text-stone-500 font-bold uppercase text-[10px] mb-4 flex items-center gap-2 tracking-widest border-b border-stone-900 pb-1">
                        <Zap size={12} className="text-[#92400e]" /> Known Secrets (Powers)
                    </h3>
                    <div className="space-y-1 overflow-y-auto pr-2">
                        {(powers || []).length > 0 ? (
                            (powers || []).map((p, i) => (
                                (powers || []).map((p, i) => {
                                    const name = typeof p === 'string' ? p : p.name;
                                    const isActive = typeof p === 'object' && p.active;
                                    return (
                                        <div key={i} className={`group flex flex-col p-3 bg-stone-900 border ${isActive ? 'border-[#92400e]' : 'border-stone-800'} hover:border-[#92400e] transition-colors`}>
                                            <div className="flex items-center gap-3">
                                                <Zap size={12} className={isActive ? "text-[#92400e]" : "text-stone-600"} />
                                                <span className="text-stone-300 text-xs font-bold uppercase tracking-wide">{name}</span>
                                                {isActive && <span className="ml-auto text-[8px] bg-[#92400e] text-white px-1 rounded">ACTIVE</span>}
                                            </div>
                                            <p className="text-[9px] text-stone-600 mt-2 italic">A manifestation of your inner will. Requires focus to channel.</p>
                                        </div>
                                    );
                                })
                            ))
                        ) : (
                            <div className="text-[10px] text-stone-700 italic text-center p-4">No secrets learned.</div>
                        )}
                    </div>
                </div>
            </div>

            <div className="w-96 space-y-4 flex flex-col">
                <div className="bg-[#0a0a0a] p-4 border border-stone-900 flex-1 flex flex-col min-h-0">
                    <h3 className="text-stone-500 font-bold uppercase text-[10px] mb-4 flex items-center gap-2 tracking-widest border-b border-stone-900 pb-1">
                        <Activity size={12} className="text-stone-500" /> Proficiencies (Skills)
                    </h3>
                    <div className="space-y-1 overflow-y-auto pr-2">
                        {(skills || []).length > 0 ? (
                            (skills || []).map((s, i) => (
                                (skills || []).map((s, i) => {
                                    const name = typeof s === 'string' ? s : s.name;
                                    const isActive = typeof s === 'object' && s.active;
                                    return (
                                        <div key={i} className={`group flex flex-col p-3 bg-stone-900 border ${isActive ? 'border-blue-900' : 'border-stone-800'} hover:border-stone-600 transition-colors`}>
                                            <div className="flex items-center gap-3">
                                                <Activity size={12} className={isActive ? "text-blue-500" : "text-stone-500"} />
                                                <span className="text-stone-300 text-xs font-bold uppercase tracking-wide">{name}</span>
                                                {isActive && <span className="ml-auto text-[8px] bg-blue-900 text-blue-200 px-1 rounded">ACTION</span>}
                                            </div>
                                            <p className="text-[9px] text-stone-600 mt-2 italic">Refined through practice and hardship.</p>
                                        </div>
                                    );
                                })
                            ))
                        ) : (
                            <div className="text-[10px] text-stone-700 italic text-center p-4">Fundamental skills only.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
