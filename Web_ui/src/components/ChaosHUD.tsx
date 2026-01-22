import React from 'react';
import { Clock, Zap, Target, Shield, ArrowBigUpDash, MapPin } from 'lucide-react';

interface ChaosHUDProps {
    chaosLevel: number;
    chaosClock: number;
    tensionThreshold: number;
    atmosphere?: string;
    elevation?: number;
    isCovered?: boolean;
    facing?: string;
}

export default function ChaosHUD({
    chaosLevel,
    chaosClock,
    tensionThreshold,
    atmosphere,
    elevation = 0,
    isCovered = false,
    facing = "N"
}: ChaosHUDProps) {
    const clockColor = chaosClock >= 9 ? 'text-red-500' : chaosClock >= 6 ? 'text-orange-500' : 'text-[#92400e]';
    const clockGlow = chaosClock >= 9 ? 'drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]' : '';

    return (
        <div className="flex flex-col gap-4 p-4 bg-black/40 border-b border-stone-900 backdrop-blur-md">
            {/* CHAOS CLOCK AREA */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Clock size={16} className={`${clockColor} ${clockGlow}`} />
                    <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-stone-500">Chaos Clock</span>
                </div>
                <div className="flex gap-1">
                    {[...Array(12)].map((_, i) => (
                        <div
                            key={i}
                            className={`w-3 h-1.5 border border-stone-800 transition-all duration-700 ${i < chaosClock ? (i >= 9 ? 'bg-red-600 shadow-[0_0_5px_red]' : 'bg-[#92400e]') : 'bg-stone-950'}`}
                        />
                    ))}
                </div>
            </div>

            {/* STATS ROW */}
            <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-3 bg-stone-950/50 p-2 border border-stone-800 rounded-sm">
                    <Zap size={14} className="text-yellow-600" />
                    <div className="flex flex-col">
                        <span className="text-[8px] font-bold uppercase text-stone-600 leading-none mb-1">Omen Target</span>
                        <span className="text-xs font-mono font-bold text-stone-300">{chaosLevel}</span>
                    </div>
                </div>

                <div className="flex items-center gap-3 bg-stone-950/50 p-2 border border-stone-800 rounded-sm">
                    <Target size={14} className="text-red-800" />
                    <div className="flex flex-col">
                        <span className="text-[8px] font-bold uppercase text-stone-600 leading-none mb-1">Tension</span>
                        <span className="text-xs font-mono font-bold text-stone-300"> d12 &le; {tensionThreshold}</span>
                    </div>
                </div>
            </div>

            {/* TACTICAL STATUS */}
            <div className="flex flex-wrap gap-2">
                {elevation > 0 && (
                    <div className="flex items-center gap-2 px-2 py-1 bg-blue-900/20 border border-blue-800 rounded-full animate-pulse transition-all">
                        <ArrowBigUpDash size={12} className="text-blue-400" />
                        <span className="text-[9px] font-bold text-blue-300 uppercase tracking-widest">High Ground</span>
                        <div className="text-[8px] text-blue-500/50 ml-1">Advantage</div>
                    </div>
                )}
                {isCovered && (
                    <div className="flex items-center gap-2 px-2 py-1 bg-green-900/20 border border-green-800 rounded-full transition-all">
                        <Shield size={12} className="text-green-400" />
                        <span className="text-[9px] font-bold text-green-300 uppercase tracking-widest">In Cover</span>
                        <div className="text-[8px] text-green-500/50 ml-1">Defender Adv</div>
                    </div>
                )}
                <div className="flex items-center gap-2 px-2 py-1 bg-stone-950 border border-stone-800 rounded-full opacity-60">
                    <MapPin size={10} className="text-stone-500" />
                    <span className="text-[8px] font-bold text-stone-500 uppercase">Facing {facing}</span>
                </div>
            </div>

            {/* ATMOSPHERE TEXT */}
            {atmosphere && (
                <div className="text-[9px] italic text-stone-500 font-serif border-t border-stone-900 pt-2 animate-pulse">
                    "{atmosphere}"
                </div>
            )}
        </div>
    );
}
