import { useState, useEffect } from 'react';
import { Skull, Sword, Sparkles, FolderOpen, UserPlus } from 'lucide-react';

interface SaveFile {
    name: string;
    species: string;
}

export default function MainMenu({ onStart, onLoad, onCreate }: { onStart: () => void, onLoad: (name: string) => void, onCreate: () => void }) {
    const [saves, setSaves] = useState<SaveFile[]>([]);
    const [choosingLoad, setChoosingLoad] = useState(false);

    useEffect(() => {
        fetch('/api/characters')
            .then(res => res.json())
            .then(data => setSaves(data.characters || []))
            .catch(e => console.error("Failed to load saves", e));
    }, []);

    const handleLoadClick = async (name: string) => {
        try {
            const res = await fetch('/api/character/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            if (res.ok) {
                onLoad(name);
            } else {
                console.error("Failed to load character from API");
            }
        } catch (e) {
            console.error("Load error", e);
        }
    };

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

                {!choosingLoad ? (
                    <div className="flex flex-col gap-4 w-64">
                        <button
                            onClick={onCreate}
                            className="group relative px-6 py-3 bg-stone-900/50 border border-stone-800 text-stone-300 hover:text-white hover:border-[#00f2ff] hover:bg-[#00f2ff]/10 transition-all uppercase tracking-widest text-xs font-bold flex items-center gap-3"
                        >
                            <UserPlus size={16} className="group-hover:text-[#00f2ff] transition-colors" />
                            <span>New Journey</span>
                        </button>

                        <button
                            onClick={() => setChoosingLoad(true)}
                            className="group relative px-6 py-3 bg-stone-900/50 border border-stone-800 text-stone-300 hover:text-white hover:border-yellow-500 hover:bg-yellow-500/10 transition-all uppercase tracking-widest text-xs font-bold flex items-center gap-3"
                        >
                            <FolderOpen size={16} className="group-hover:text-yellow-500 transition-colors" />
                            <span>Continue</span>
                        </button>
                    </div>
                ) : (
                    <div className="flex flex-col gap-2 w-80 max-h-96">
                        <div className="flex items-center justify-between text-xs text-stone-500 uppercase font-bold px-2 mb-2">
                            <span>Select Hero</span>
                            <button onClick={() => setChoosingLoad(false)} className="hover:text-white">Cancel</button>
                        </div>

                        <div className="flex flex-col gap-2 overflow-y-auto pr-1">
                            {saves.map((save) => (
                                <button
                                    key={save.name}
                                    onClick={() => handleLoadClick(save.name)}
                                    className="px-4 py-3 bg-stone-900 border border-stone-800 hover:border-[#00f2ff] text-left transition-colors group"
                                >
                                    <div className="font-bold text-stone-300 group-hover:text-white text-sm">{save.name}</div>
                                    <div className="text-[10px] text-stone-500">{save.species}</div>
                                </button>
                            ))}
                            {saves.length === 0 && (
                                <div className="text-center text-stone-600 text-xs py-4 font-mono">No Saved Games Found</div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
