import { useState, useEffect } from 'react';
import { Skull, Sword, Sparkles, FolderOpen, UserPlus } from 'lucide-react';

interface SaveFile {
    name: string;
    species: string;
}

export default function MainMenu({ onStart, onCreate }: { onStart: () => void, onCreate: () => void }) {

    // Simplified: All entry points now handled by App.tsx routing

    return (
        <div className="h-full w-full flex flex-col items-center justify-center bg-[#050505] relative overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-stone-900/50 via-[#050505] to-[#050505] z-0" />

            <div className="z-10 flex flex-col items-center gap-8 animate-fade-in-up">
                <div className="flex flex-col items-center mb-8">
                    <Skull size={64} className="text-[#00f2ff] drop-shadow-[0_0_15px_rgba(0,242,255,0.5)] mb-4" />
                    <h1 className="text-4xl font-black tracking-[0.3em] text-white uppercase text-center bg-clip-text text-transparent bg-gradient-to-b from-white to-stone-500">
                        Shadowfall<br />
                        <span className="text-xl tracking-[0.8em] text-[#00f2ff] font-light">Chronicles</span>
                    </h1>
                </div>

                <div className="flex flex-col gap-4 w-64">
                    <button
                        onClick={onStart}
                        className="group relative px-6 py-3 bg-stone-900/50 border border-stone-800 text-stone-300 hover:text-white hover:border-[#92400e] hover:bg-[#92400e]/10 transition-all uppercase tracking-widest text-xs font-bold flex items-center gap-3"
                    >
                        <UserPlus size={16} className="group-hover:text-[#92400e] transition-colors" />
                        <span>Enter the Shadowfall</span>
                    </button>

                    <button
                        onClick={onCreate}
                        className="group relative px-6 py-3 bg-stone-900/50 border border-stone-800 text-stone-300 hover:text-white hover:border-stone-700 hover:bg-stone-800/10 transition-all uppercase tracking-widest text-xs font-bold flex items-center gap-3"
                    >
                        <Sparkles size={16} className="group-hover:text-stone-400 transition-colors" />
                        <span>Forge Legend</span>
                    </button>
                </div>
            </div>
        </div>
    );
}
