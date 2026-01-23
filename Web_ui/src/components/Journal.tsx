import { useState, useEffect } from 'react';
import { BookOpen, AlertCircle, Loader2 } from 'lucide-react';

interface QuestInfo {
    title: string;
    description: string;
    progress: string;
    objective: string;
    status: string;
}

export default function Journal() {
    const [quest, setQuest] = useState<QuestInfo | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/game/state')
            .then(res => res.json())
            .then(data => {
                if (data.quest_title) {
                    setQuest({
                        title: data.quest_title,
                        description: data.quest_description,
                        progress: data.quest_progress,
                        objective: data.quest_objective,
                        status: data.scene_text === "QUEST COMPLETE" ? "Complete" : "Active"
                    });
                }
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, []);

    const entries = [
        { date: "Current Cycle", content: quest ? `Directive updated: ${quest.objective}` : "Awaiting directives..." },
        { date: "Initialization", content: "System initialized. Combat subroutines loaded. Exploration phase engaged." }
    ];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full text-stone-600 uppercase tracking-widest text-xs gap-2">
                <Loader2 className="animate-spin" size={16} /> syncing with chronicles...
            </div>
        );
    }

    return (
        <div className="flex flex-row gap-4 h-full p-4 text-stone-300">
            {/* QUEST LIST */}
            <div className="w-1/3 bg-[#080808] border border-stone-800 rounded-lg p-4 flex flex-col">
                <h2 className="flex items-center gap-2 text-stone-500 font-bold uppercase tracking-widest mb-4 border-b border-stone-800 pb-2">
                    <AlertCircle size={16} /> Active Directives
                </h2>
                <div className="space-y-3 overflow-y-auto pr-2">
                    {quest ? (
                        <div className="p-3 bg-stone-900/50 border border-stone-800 border-l-2 border-l-[#92400e] transition-colors group">
                            <div className="flex justify-between items-start mb-1">
                                <span className="text-white font-bold text-xs">{quest.title}</span>
                                <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${quest.status === 'Active' ? 'bg-[#92400e]/20 text-[#92400e]' : 'bg-green-900/20 text-green-500'}`}>
                                    {quest.status}
                                </span>
                            </div>
                            <p className="text-[10px] text-stone-400 mb-2 leading-relaxed">{quest.description}</p>
                            <div className="flex justify-between items-center mt-4 pt-2 border-t border-stone-800/50">
                                <div className="text-[9px] font-mono text-stone-500 uppercase">Progress: {quest.progress}</div>
                                <div className="text-[9px] font-mono text-stone-600 italic">Lv. 1 Required</div>
                            </div>
                        </div>
                    ) : (
                        <div className="text-[10px] text-stone-600 italic p-4 text-center">No active directives found. Return to the world map to begin a quest.</div>
                    )}
                </div>
            </div>

            {/* OBJ & LOGS */}
            <div className="flex-1 bg-[#080808] border border-stone-800 rounded-lg p-4 flex flex-col">
                <h2 className="flex items-center gap-2 text-stone-500 font-bold uppercase tracking-widest mb-4 border-b border-stone-800 pb-2">
                    <BookOpen size={16} /> Current Objective & Logs
                </h2>
                <div className="flex-1 overflow-y-auto space-y-6 pr-2">
                    {quest && (
                        <div className="mb-8 p-4 bg-stone-950 border border-stone-900 rounded relative overflow-hidden group">
                            <div className="absolute top-0 left-0 w-1 h-full bg-[#92400e] opacity-50" />
                            <span className="text-[9px] font-bold text-stone-600 uppercase mb-2 block tracking-widest">Active Objective</span>
                            <p className="text-lg font-serif text-stone-200">{quest.objective}</p>
                        </div>
                    )}

                    <div className="space-y-6">
                        {entries.map((e, i) => (
                            <div key={i} className="animate-fade-in">
                                <div className="flex items-baseline gap-2 mb-1">
                                    <span className="text-[#9ea3af] font-mono text-[10px] uppercase">[{e.date}]</span>
                                    <div className="h-[1px] bg-stone-900 flex-1"></div>
                                </div>
                                <p className="text-xs font-serif text-stone-400 leading-relaxed pl-4 border-l border-stone-900">
                                    {e.content}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
