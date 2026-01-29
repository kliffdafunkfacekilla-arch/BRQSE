import { useState, useEffect } from 'react';
import { UserPlus, ChevronLeft, Shield, Swords, Sparkles, Trash2, AlertTriangle } from 'lucide-react';

interface Hero {
    name: string;
    species: string;
    sprite: string;
    level: number;
    filename: string;
}

interface HeroSelectorProps {
    onSelect: (heroName: string) => void;
    onCreate: () => void;
    onBack: () => void;
    isManageMode?: boolean;
}

export default function HeroSelector({ onSelect, onCreate, onBack, isManageMode = false }: HeroSelectorProps) {
    const [heroes, setHeroes] = useState<Hero[]>([]);
    const [loading, setLoading] = useState(true);
    const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

    const fetchHeroes = () => {
        setLoading(true);
        fetch('/api/characters')
            .then(res => res.json())
            .then(data => {
                setHeroes(data.characters || []);
                setLoading(false);
            })
            .catch(e => {
                console.error("Failed to fetch heroes", e);
                setLoading(false);
            });
    };

    useEffect(() => {
        fetchHeroes();
    }, []);

    const handleHeroChoice = async (hero: Hero) => {
        if (isManageMode) return; // In management mode, selection is disabled (or we could show details)

        try {
            const res = await fetch('/api/character/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: hero.filename }) // Filename includes the .base part
            });
            if (res.ok) {
                onSelect(hero.name);
            }
        } catch (e) {
            console.error("Failed to select hero", e);
        }
    };

    const handleDeleteHero = async (heroName: string) => {
        try {
            await fetch(`/api/character/delete?name=${heroName}`, { method: 'POST' });
            setConfirmDelete(null);
            fetchHeroes(); // Refresh list
        } catch (e) {
            console.error("Failed to delete hero", e);
        }
    };

    return (
        <div className="h-full w-full flex flex-col items-center bg-[#050505] p-8 overflow-y-auto bg-grid-pattern">
            <div className="w-full max-w-6xl flex flex-col gap-8">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-stone-800 pb-4 backdrop-blur-sm sticky top-0 z-50">
                    <button
                        onClick={onBack}
                        className="flex items-center gap-2 text-stone-500 hover:text-[#92400e] transition-colors text-xs font-bold uppercase tracking-widest"
                    >
                        <ChevronLeft size={16} />
                        Exit to Menu
                    </button>
                    <h2 className="text-2xl font-black text-white uppercase tracking-[0.2em]">
                        {isManageMode ? 'Hall of ' : 'Select Your '}
                        <span className="text-[#92400e]">Heroes</span>
                    </h2>
                    <div className="w-24" /> {/* Spacer */}
                </div>

                {loading ? (
                    <div className="flex flex-1 items-center justify-center p-20">
                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[#92400e]"></div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {/* New Hero Card (Hidden in Manage mode for clarity, or kept as creator) */}
                        {!isManageMode && (
                            <button
                                onClick={onCreate}
                                className="group relative h-80 bg-stone-900/10 border-2 border-dashed border-stone-800/50 hover:border-[#92400e] transition-all flex flex-col items-center justify-center gap-4 overflow-hidden"
                            >
                                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#92400e]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                <div className="w-16 h-16 rounded-full border-2 border-stone-800 group-hover:border-[#92400e] flex items-center justify-center transition-colors">
                                    <UserPlus size={32} className="text-stone-700 group-hover:text-[#92400e] transition-colors" />
                                </div>
                                <span className="text-xs font-bold text-stone-600 group-hover:text-white uppercase tracking-widest">Forge Legend</span>
                            </button>
                        )}

                        {/* Hero List */}
                        {heroes.map((hero) => (
                            <div
                                key={hero.filename}
                                onClick={() => handleHeroChoice(hero)}
                                className={`group h-80 bg-black/40 border border-stone-800/80 transition-all flex flex-col items-stretch text-left relative overflow-hidden backdrop-blur-sm ${!isManageMode ? 'hover:border-[#92400e] cursor-pointer active:scale-95' : ''}`}
                            >
                                {/* Background Sprite Preview */}
                                <div className="h-40 bg-[#080808] relative overflow-hidden">
                                    <img
                                        src={`/tokens/${hero.sprite}`}
                                        alt={hero.name}
                                        className="w-full h-full object-contain p-4 transition-transform group-hover:scale-110 duration-500 opacity-40 group-hover:opacity-100"
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent" />

                                    <div className="absolute top-2 right-2 px-2 py-0.5 bg-[#92400e]/80 text-white text-[10px] font-bold rounded-sm uppercase tracking-tighter">
                                        LVL {hero.level}
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="p-4 flex flex-col gap-1 z-10 flex-1">
                                    <h3 className="text-white font-bold uppercase tracking-widest text-lg group-hover:text-[#92400e] transition-colors line-clamp-1">{hero.name}</h3>
                                    <p className="text-[#92400e] text-[10px] font-bold uppercase tracking-[0.2em] mb-4">{hero.species}</p>

                                    <div className="flex gap-3 mt-auto border-t border-stone-900 pt-3">
                                        <div className="flex items-center gap-1.5 opacity-30">
                                            <Shield size={12} className="text-stone-400" />
                                            <span className="text-[10px] font-bold text-stone-500">DEF</span>
                                        </div>
                                        <div className="flex items-center gap-1.5 opacity-30">
                                            <Swords size={12} className="text-stone-400" />
                                            <span className="text-[10px] font-bold text-stone-500">ATK</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Management Actions */}
                                {isManageMode && (
                                    <div className="absolute inset-0 bg-black/90 backdrop-blur-md opacity-0 group-hover:opacity-100 transition-all duration-200 flex flex-col items-center justify-center p-6 text-center gap-4 z-40 pointer-events-none group-hover:pointer-events-auto">
                                        {confirmDelete === hero.filename ? (
                                            <div className="animate-fade-in flex flex-col items-center gap-4 pointer-events-auto">
                                                <AlertTriangle className="text-red-600 animate-bounce" size={32} />
                                                <p className="text-[10px] font-bold text-white uppercase leading-relaxed">This soul will be lost forever.<br />Confirm erasure?</p>
                                                <div className="flex gap-2 w-full">
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); handleDeleteHero(hero.filename); }}
                                                        className="flex-1 py-1.5 bg-red-900/60 border border-red-800 text-red-200 text-[9px] font-bold uppercase tracking-widest hover:bg-red-700 transition-colors"
                                                    >
                                                        Confirm
                                                    </button>
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); setConfirmDelete(null); }}
                                                        className="flex-1 py-1.5 bg-stone-800 border border-stone-700 text-stone-300 text-[9px] font-bold uppercase tracking-widest hover:bg-stone-700 transition-colors"
                                                    >
                                                        Cancel
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <button
                                                onClick={(e) => { e.stopPropagation(); setConfirmDelete(hero.filename); }}
                                                className="w-full py-2 bg-red-900/20 border border-red-900/40 text-red-500 hover:text-white hover:bg-red-900/40 hover:border-red-600 transition-all flex items-center justify-center gap-2 text-[10px] font-bold uppercase tracking-widest pointer-events-auto"
                                            >
                                                <Trash2 size={14} />
                                                Sever Soul
                                            </button>
                                        )}
                                    </div>
                                )}

                                {/* Hover Overlay Decoration */}
                                <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-[#92400e]/50 scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
                            </div>
                        ))}
                    </div>
                )}

                {heroes.length === 0 && !loading && (
                    <div className="text-center py-20 text-stone-700 border border-stone-900 border-dashed rounded-lg bg-black/20">
                        <Skull className="mx-auto mb-4 opacity-10" size={48} />
                        <p className="text-[10px] uppercase tracking-[0.4em] font-mono italic">The chronicles of the fallen are empty.</p>
                        <p className="text-[9px] mt-2 opacity-30">History is written by those who venture forth.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
