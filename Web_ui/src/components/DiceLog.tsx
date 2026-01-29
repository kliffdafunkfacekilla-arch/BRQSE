import { Dices, Target } from 'lucide-react';

interface DiceLogEntry {
    source: string;
    action: string;
    roll: number;
    details: string;
    result: string;
}

interface DiceLogProps {
    logs: DiceLogEntry[];
}


const getLogStyle = (text: string) => {
    const t = text.toLowerCase();
    if (t.includes('fire') || t.includes('burn') || t.includes('heat')) return 'border-orange-900/50 bg-orange-950/10 text-orange-200';
    if (t.includes('cold') || t.includes('ice') || t.includes('freeze')) return 'border-cyan-900/50 bg-cyan-950/10 text-cyan-200';
    if (t.includes('necrotic') || t.includes('doom') || t.includes('rot')) return 'border-purple-900/50 bg-purple-950/10 text-purple-200';
    if (t.includes('radiant') || t.includes('holy') || t.includes('light')) return 'border-yellow-900/50 bg-yellow-950/10 text-yellow-200';
    if (t.includes('psychic') || t.includes('mind') || t.includes('fear')) return 'border-pink-900/50 bg-pink-950/10 text-pink-200';
    if (t.includes('acid') || t.includes('poison')) return 'border-green-900/50 bg-green-950/10 text-green-200';
    if (t.includes('force') || t.includes('gravity')) return 'border-indigo-900/50 bg-indigo-950/10 text-indigo-200';
    if (t.includes('lightning') || t.includes('shock')) return 'border-blue-900/50 bg-blue-950/10 text-blue-200';
    if (t.includes('sonic') || t.includes('thunder')) return 'border-sky-900/50 bg-sky-950/10 text-sky-200';
    if (t.includes('heal') || t.includes('regen')) return 'border-emerald-900/50 bg-emerald-950/10 text-emerald-200';
    return 'border-stone-800/50 bg-black/50 text-stone-500';
};

return (
    <div className="h-full bg-[#080808] border-r border-stone-900 flex flex-col w-64 shrink-0 overflow-hidden">
        <div className="p-4 border-b border-stone-800 flex items-center gap-2 bg-[#0a0a0a]">
            <Dices className="text-stone-500" size={16} />
            <span className="text-xs font-bold uppercase tracking-widest text-stone-400">Dice Log</span>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {logs.length === 0 && (
                <div className="text-[10px] text-stone-700 italic text-center mt-10">No rolls recorded yet...</div>
            )}

            {[...logs].reverse().map((log, i) => {
                const styleClass = getLogStyle(log.details + " " + log.action);
                return (
                    <div key={i} className="flex flex-col gap-1 border-b border-stone-900 pb-3 last:border-0 animate-fade-in">
                        <div className="flex justify-between items-center">
                            <span className="text-[10px] font-bold uppercase text-stone-500">{log.source}</span>
                            <span className={`text-[10px] font-bold uppercase px-1 rounded ${log.result === 'HIT' ? 'bg-red-950 text-red-400' :
                                log.result === 'MISS' ? 'bg-stone-900 text-stone-600' : 'bg-blue-950 text-blue-400'
                                }`}>
                                {log.result}
                            </span>
                        </div>

                        <div className="flex items-center gap-2">
                            <Target size={12} className="text-stone-600" />
                            <span className="text-xs font-serif text-stone-300">{log.action}</span>
                        </div>

                        <div className={`p-2 rounded border mt-1 ${styleClass}`}>
                            <div className="flex items-baseline gap-2 mb-1">
                                <span className={`text-xl font-bold ${styleClass.includes('text-stone') ? 'text-stone-200' : 'text-inherit'}`}>{log.roll}</span>
                                <span className="text-[9px] opacity-60 uppercase">Total</span>
                            </div>
                            <p className="text-[9px] font-mono leading-tight break-words opacity-80">
                                {log.details}
                            </p>
                        </div>
                    </div>
                );
            })}
        </div>
    </div>
);
}
