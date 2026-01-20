import { BookOpen, AlertCircle } from 'lucide-react';

export default function Journal() {
    const quests = [
        { id: 1, title: "Protocol Initiation", status: "Active", desc: "Defeat the simulation guardian to prove combat readiness.", reward: "500 XP" },
        { id: 2, title: "Data Recovery", status: "Complete", desc: "Retrieve the lost archives from the corrupt sector.", reward: "Data Cache" }
    ];

    const entries = [
        { date: "Cycle 104.2", content: "System initialized. Combat subroutines loaded. The arena seems stable, but the entities are restless." },
        { date: "Cycle 104.1", content: "Weapon patterns recognized. Magic systems online." }
    ];

    return (
        <div className="flex flex-row gap-4 h-full p-4 text-stone-300">
            {/* QUEST LIST */}
            <div className="w-1/3 bg-[#080808] border border-stone-800 rounded-lg p-4">
                <h2 className="flex items-center gap-2 text-stone-500 font-bold uppercase tracking-widest mb-4 border-b border-stone-800 pb-2">
                    <AlertCircle size={16} /> Active Directives
                </h2>
                <div className="space-y-3">
                    {quests.map(q => (
                        <div key={q.id} className="p-3 bg-stone-900/50 border border-stone-800 hover:border-[#00f2ff] cursor-pointer transition-colors group">
                            <div className="flex justify-between items-start mb-1">
                                <span className="text-[#00f2ff] font-bold text-xs group-hover:text-white">{q.title}</span>
                                <span className={`text-[10px] px-1 rounded ${q.status === 'Active' ? 'bg-green-900 text-green-300' : 'bg-stone-800 text-stone-500'}`}>{q.status}</span>
                            </div>
                            <p className="text-[10px] text-stone-400 mb-2">{q.desc}</p>
                            <div className="text-[9px] font-mono text-stone-500">Reward: {q.reward}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* TEXT LOG */}
            <div className="flex-1 bg-[#080808] border border-stone-800 rounded-lg p-4 overflow-y-auto">
                <h2 className="flex items-center gap-2 text-stone-500 font-bold uppercase tracking-widest mb-4 border-b border-stone-800 pb-2">
                    <BookOpen size={16} /> Personal Logs
                </h2>
                <div className="space-y-6">
                    {entries.map((e, i) => (
                        <div key={i} className="animate-fade-in">
                            <div className="flex items-baseline gap-2 mb-1">
                                <span className="text-[#00f2ff] font-mono text-xs">[{e.date}]</span>
                                <div className="h-[1px] bg-stone-800 flex-1"></div>
                            </div>
                            <p className="text-sm font-serif text-stone-300 leading-relaxed pl-4 border-l border-stone-800">
                                {e.content}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
