import { useState, useEffect } from 'react';
import { BookOpen, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';

interface JournalEntry {
    timestamp: string;
    archetype: string;
    subject: string;
    context: string;
    reward: string;
    chaos_twist: string;
    narrative: string;
    outcome: string;
}

interface JournalProps {
    entries?: JournalEntry[];
    questTitle?: string;
    questDescription?: string;
    questProgress?: string;
    questObjective?: string;
}

export default function Journal({ entries = [], questTitle, questDescription, questProgress, questObjective }: JournalProps) {
    return (
        <div className="flex flex-row gap-4 h-full p-4 text-stone-300 bg-[#030303] font-serif">
            {/* QUEST LIST */}
            <div className="w-1/3 bg-[#080808] border border-stone-900 p-4 flex flex-col">
                <h2 className="flex items-center gap-2 text-stone-500 font-bold uppercase tracking-widest mb-4 border-b border-stone-900 pb-2">
                    <AlertCircle size={14} className="text-[#92400e]" /> Active Directives
                </h2>
                <div className="space-y-3 overflow-y-auto pr-2">
                    {questTitle ? (
                        <div className="p-3 bg-stone-900/50 border border-stone-800 border-l-2 border-l-[#92400e] transition-colors group">
                            <div className="flex justify-between items-start mb-1">
                                <span className="text-white font-bold text-xs">{questTitle}</span>
                                <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase bg-[#92400e]/10 text-[#92400e]`}>
                                    ACTIVE
                                </span>
                            </div>
                            <p className="text-[10px] text-stone-400 mb-2 leading-relaxed">{questDescription}</p>
                            <div className="flex justify-between items-center mt-4 pt-2 border-t border-stone-800/50">
                                <div className="text-[9px] font-mono text-stone-500 uppercase">Progress: {questProgress}</div>
                            </div>
                        </div>
                    ) : (
                        <div className="text-[10px] text-stone-600 italic p-4 text-center">No active directives found.</div>
                    )}
                </div>
            </div>

            {/* OBJ & LOGS */}
            <div className="flex-1 bg-[#080808] border border-stone-900 p-4 flex flex-col">
                <h2 className="flex items-center gap-2 text-stone-500 font-bold uppercase tracking-widest mb-4 border-b border-stone-900 pb-2">
                    <BookOpen size={14} className="text-[#92400e]" /> Recorded Chronicles
                </h2>
                <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                    {questObjective && (
                        <div className="mb-6 p-4 bg-black border border-stone-900 relative overflow-hidden group">
                            <div className="absolute top-0 left-0 w-1 h-full bg-[#92400e] opacity-50" />
                            <span className="text-[9px] font-bold text-stone-600 uppercase mb-2 block tracking-widest">Current Objective</span>
                            <p className="text-lg text-stone-200">{questObjective}</p>
                        </div>
                    )}

                    <div className="space-y-4">
                        {(entries || []).length > 0 ? [...(entries || [])].reverse().map((e, i) => (
                            <div key={i} className="p-3 bg-stone-900/30 border border-stone-900 hover:border-stone-700 transition-colors">
                                <div className="flex justify-between items-center mb-2">
                                    <div className="flex gap-2 items-center">
                                        <span className="text-[#9ea3af] font-mono text-[9px] uppercase">[{e.timestamp}]</span>
                                        <span className="text-[#92400e] font-bold text-[10px] uppercase tracking-widest">{e.archetype}</span>
                                    </div>
                                    <span className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded ${e.outcome === 'Unresolved' ? 'text-stone-500 bg-stone-900' : 'text-green-500 bg-green-950/30'}`}>
                                        {e.outcome === 'Unresolved' ? 'Active' : e.outcome}
                                    </span>
                                </div>
                                <p className="text-xs text-stone-300 leading-relaxed italic mb-3">"{e.narrative}"</p>
                                <div className="grid grid-cols-2 gap-4 text-[9px] border-t border-stone-900 pt-2 opacity-60">
                                    <div><span className="text-stone-600 uppercase font-bold">Subject:</span> <span className="text-stone-400">{e.subject}</span></div>
                                    <div><span className="text-stone-600 uppercase font-bold">Rewards:</span> <span className="text-stone-400">{e.reward}</span></div>
                                    <div className="col-span-2"><span className="text-stone-600 uppercase font-bold">Chaos Twist:</span> <span className="text-stone-400">{e.chaos_twist}</span></div>
                                </div>
                            </div>
                        )) : (
                            <div className="text-center py-12 text-stone-600 italic text-xs">The chronicles are empty. Step forth to make your mark.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
