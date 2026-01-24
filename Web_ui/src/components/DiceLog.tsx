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

export default function DiceLog({ logs = [] }: DiceLogProps) {
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

                {[...logs].reverse().map((log, i) => (
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

                        <div className="bg-black/50 p-2 rounded border border-stone-800/50 mt-1">
                            <div className="flex items-baseline gap-2 mb-1">
                                <span className="text-xl font-bold text-stone-200">{log.roll}</span>
                                <span className="text-[9px] text-stone-600 uppercase">Total</span>
                            </div>
                            <p className="text-[9px] text-stone-500 font-mono leading-tight break-words">
                                {log.details}
                            </p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
