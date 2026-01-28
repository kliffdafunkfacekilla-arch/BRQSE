import { Skull, Sparkles, FolderOpen, Cog, Users, Play } from 'lucide-react';

interface MainMenuProps {
    onStart: () => void;
    onLoad: () => void;
    onManage: () => void;
    onOptions: () => void;
}

export default function MainMenu({ onStart, onLoad, onManage, onOptions }: MainMenuProps) {
    return (
        <div className="h-full w-full flex flex-col items-center justify-center bg-[#050505] relative overflow-hidden bg-grid-pattern">
            {/* Ambient Background Elements */}
            <div className="absolute inset-0 bg-radial-gradient z-0 opacity-60" />
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#92400e]/5 rounded-full blur-[120px] animate-pulse" />
            <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-[#4c1d95]/5 rounded-full blur-[100px] animate-pulse delay-1000" />

            <div className="z-10 flex flex-col items-center gap-12 animate-fade-in max-w-md w-full px-8">
                {/* Logo Section */}
                <div className="flex flex-col items-center group cursor-default">
                    <div className="relative mb-6">
                        <div className="absolute inset-0 bg-[#92400e]/20 blur-xl rounded-full scale-0 group-hover:scale-150 transition-transform duration-1000" />
                        <Skull size={80} className="text-white/10 group-hover:text-[#92400e]/40 transition-colors duration-700 relative z-10" />
                    </div>
                    <h1 className="text-5xl font-black tracking-[0.4em] text-white uppercase text-center leading-tight">
                        Shadowfall<br />
                        <span className="text-xl tracking-[0.9em] text-[#92400e] font-light block mt-2 opacity-80">Chronicles</span>
                    </h1>
                </div>

                {/* Navigation Grid */}
                <div className="grid grid-cols-1 gap-3 w-full">
                    {/* Primary Action */}
                    <button
                        onClick={onStart}
                        className="group relative px-6 py-4 bg-stone-900/40 border border-[#92400e]/30 hover:border-[#92400e] transition-all duration-300 flex items-center gap-4 backdrop-blur-sm overflow-hidden"
                    >
                        <div className="absolute inset-0 bg-gradient-to-r from-[#92400e]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <Sparkles size={18} className="text-[#92400e] group-hover:scale-110 transition-transform" />
                        <div className="flex flex-col items-start translate-x-0 group-hover:translate-x-1 transition-transform">
                            <span className="text-xs font-black text-white uppercase tracking-[0.2em]">Forge New Tale</span>
                            <span className="text-[9px] text-stone-500 uppercase tracking-widest font-serif italic mt-0.5">Begin a fresh journey</span>
                        </div>
                        <div className="ml-auto opacity-0 group-hover:opacity-100 group-hover:translate-x-0 translate-x-4 transition-all">
                            <Play size={12} className="text-[#92400e]" />
                        </div>
                    </button>

                    {/* Secondary Actions */}
                    <div className="grid grid-cols-2 gap-3">
                        <button
                            onClick={onLoad}
                            className="group relative p-4 bg-stone-900/20 border border-stone-800/50 hover:border-stone-700 hover:bg-stone-900/40 transition-all flex flex-col gap-3 items-start"
                        >
                            <FolderOpen size={16} className="text-stone-600 group-hover:text-stone-400 transition-colors" />
                            <span className="text-[10px] font-bold text-stone-500 group-hover:text-stone-300 uppercase tracking-widest">Load Chronicled</span>
                        </button>

                        <button
                            onClick={onManage}
                            className="group relative p-4 bg-stone-900/20 border border-stone-800/50 hover:border-stone-700 hover:bg-stone-900/40 transition-all flex flex-col gap-3 items-start"
                        >
                            <Users size={16} className="text-stone-600 group-hover:text-stone-400 transition-colors" />
                            <span className="text-[10px] font-bold text-stone-500 group-hover:text-stone-300 uppercase tracking-widest">Hall of Heroes</span>
                        </button>
                    </div>

                    {/* Meta Action */}
                    <button
                        onClick={onOptions}
                        className="group relative px-6 py-3 border border-stone-900 hover:border-stone-800 hover:bg-stone-900/10 transition-all flex items-center justify-center gap-3 opacity-60 hover:opacity-100"
                    >
                        <Cog size={14} className="text-stone-700 group-hover:text-[#92400e] transition-colors group-hover:rotate-45 duration-500" />
                        <span className="text-[9px] font-bold text-stone-600 uppercase tracking-[0.3em]">Codex Options</span>
                    </button>
                </div>

                {/* Version Info */}
                <div className="mt-8 flex flex-col items-center opacity-30 group cursor-default">
                    <div className="h-px w-8 bg-stone-800 mb-4 group-hover:w-16 transition-all duration-700" />
                    <span className="text-[8px] uppercase tracking-[0.4em] font-mono">Build 2.4.0-Final</span>
                </div>
            </div>
        </div>
    );
}
