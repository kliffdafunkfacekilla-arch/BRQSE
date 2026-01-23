import { useState, useEffect } from 'react';
import { UserPlus, ChevronLeft, Shield, Swords, Sparkles } from 'lucide-react';

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
}

export default function HeroSelector({ onSelect, onCreate, onBack }: HeroSelectorProps) {
    const [heroes, setHeroes] = useState<Hero[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
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
    }, []);

    const handleHeroChoice = async (hero: Hero) => {
        try {
            const res = await fetch('/api/character/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: hero.filename })
            });
            if (res.ok) {
                onSelect(hero.name);
            }
        } catch (e) {
            console.error("Failed to select hero", e);
        }
    };

    return (
        <div className="h-full w-full flex flex-col items-center bg-[#050505] p-8 overflow-y-auto">
            <div className="w-full max-w-6xl flex flex-col gap-8">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-stone-800 pb-4">
                    <button
                        onClick={onBack}
                        className="flex items-center gap-2 text-stone-500 hover:text-[#92400e] transition-colors text-xs font-bold uppercase tracking-widest"
                    >
                        <ChevronLeft size={16} />
                        Back to Menu
                    </button>
                    <h2 className="text-2xl font-black text-white uppercase tracking-[0.2em]">Select Your <span className="text-[#92400e]">Hero</span></h2>
                    <div className="w-24" /> {/* Spacer */}
                </div>

                {loading ? (
                    <div className="flex flex-1 items-center justify-center p-20">
                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[#92400e]"></div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {/* New Hero Card */}
                        <button
                            onClick={onCreate}
                            className="group relative h-80 bg-stone-900/20 border-2 border-dashed border-stone-800 hover:border-[#92400e] transition-all flex flex-col items-center justify-center gap-4 overflow-hidden"
                        >
                            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#92400e]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                            <div className="w-16 h-16 rounded-full border-2 border-stone-800 group-hover:border-[#92400e] flex items-center justify-center transition-colors">
                                <UserPlus size={32} className="text-stone-700 group-hover:text-[#92400e] transition-colors" />
                            </div>
                            <span className="text-xs font-bold text-stone-600 group-hover:text-white uppercase tracking-widest">Begin New Tale</span>
                        </button>

                        {/* Hero List */}
                        {heroes.map((hero) => (
                            <button
                                key={hero.filename}
                                onClick={() => handleHeroChoice(hero)}
                                className="group h-80 bg-[#0a0a0a] border border-stone-800 hover:border-[#92400e] transition-all flex flex-col items-stretch text-left relative overflow-hidden"
                            >
                                {/* Background Sprite Preview */}
                                <div className="h-40 bg-black relative overflow-hidden">
                                    <img
                                        src={`/tokens/${hero.sprite}`}
                                        alt={hero.name}
                                        className="w-full h-full object-contain p-4 transition-transform group-hover:scale-110 duration-500 opacity-50 group-hover:opacity-100"
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0a] via-transparent to-transparent" />

                                    <div className="absolute top-2 right-2 px-2 py-0.5 bg-[#92400e]/80 text-white text-[10px] font-bold rounded-sm uppercase tracking-tighter">
                                        LVL {hero.level}
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="p-4 flex flex-col gap-1 z-10">
                                    <h3 className="text-white font-bold uppercase tracking-widest text-lg group-hover:text-[#92400e] transition-colors">{hero.name}</h3>
                                    <p className="text-[#92400e] text-[10px] font-bold uppercase tracking-[0.2em] mb-4">{hero.species}</p>

                                    <div className="flex gap-3 mt-auto border-t border-stone-900 pt-3">
                                        <div className="flex items-center gap-1.5 opacity-40">
                                            <Shield size={12} className="text-stone-400" />
                                            <span className="text-[10px] font-bold text-stone-500">DEF 12</span>
                                        </div>
                                        <div className="flex items-center gap-1.5 opacity-40">
                                            <Swords size={12} className="text-stone-400" />
                                            <span className="text-[10px] font-bold text-stone-500">ATK 08</span>
                                        </div>
                                        <div className="flex items-center gap-1.5 opacity-40">
                                            <Sparkles size={12} className="text-stone-400" />
                                            <span className="text-[10px] font-bold text-stone-500">MAG 15</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Hover Overlay */}
                                <div className="absolute bottom-0 left-0 right-0 h-1 bg-[#92400e] scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
                            </button>
                        ))}
                    </div>
                )}

                {heroes.length === 0 && !loading && (
                    <div className="text-center py-20 text-stone-600 border border-stone-900 border-dashed rounded-lg">
                        <p className="text-xs uppercase tracking-[0.3em] font-mono italic">The halls of history are currently empty.</p>
                        <p className="text-[10px] mt-2 opacity-50">Choose "Begin New Tale" to forge your first hero.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
