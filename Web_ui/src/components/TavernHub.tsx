import { useState } from 'react';
import { Beer, ShoppingBag, Map as MapIcon, BedDouble, Coins } from 'lucide-react';

export default function TavernHub({ onTravel, onRest, onShop }: { onTravel: () => void, onRest: () => void, onShop: () => void }) {

    return (
        <div className="h-full w-full bg-[#0a0a0a] flex flex-col relative text-stone-300 font-sans">
            {/* HEADER */}
            <div className="p-6 border-b border-stone-800 flex justify-between items-end bg-[#050505]">
                <div>
                    <h2 className="text-2xl font-black text-white tracking-tight uppercase flex items-center gap-2">
                        <Beer size={24} className="text-orange-500" />
                        The Broken Anvil
                    </h2>
                    <p className="text-xs text-stone-500 font-mono italic">Sanctuary for the weary.</p>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 bg-stone-900 rounded border border-stone-800">
                    <Coins size={14} className="text-yellow-500" />
                    <span className="text-sm font-bold text-yellow-100">125g</span>
                </div>
            </div>

            {/* MAIN CONTENT */}
            <div className="flex-1 p-8 flex gap-8 justify-center items-center relative overflow-hidden">
                {/* Background Flavor Image (Overlay) */}
                <div className="absolute inset-0 opacity-10 bg-[url('/bg/tavern_blur.jpg')] bg-cover bg-center pointer-events-none" />

                <div className="bg-stone-900/80 border border-stone-800 p-1 backdrop-blur-sm z-10 w-full max-w-4xl grid grid-cols-3 gap-1 h-96">

                    {/* OPTION 1: REST */}
                    <button
                        onClick={onRest}
                        className="group relative flex flex-col items-center justify-center gap-4 bg-[#080808] border border-stone-800 hover:border-green-500 hover:bg-stone-900 transition-all"
                    >
                        <BedDouble size={48} className="text-stone-600 group-hover:text-green-500 transition-colors" />
                        <div className="text-center">
                            <h3 className="text-lg font-bold uppercase tracking-wider text-stone-300 group-hover:text-white">Rest</h3>
                            <p className="text-[10px] text-stone-500 mt-1">Heal Wounds & Stress<br />(10g)</p>
                        </div>
                    </button>

                    {/* OPTION 2: SUPPLY */}
                    <button
                        onClick={onShop}
                        className="group relative flex flex-col items-center justify-center gap-4 bg-[#080808] border border-stone-800 hover:border-yellow-500 hover:bg-stone-900 transition-all"
                    >
                        <ShoppingBag size={48} className="text-stone-600 group-hover:text-yellow-500 transition-colors" />
                        <div className="text-center">
                            <h3 className="text-lg font-bold uppercase tracking-wider text-stone-300 group-hover:text-white">Supplies</h3>
                            <p className="text-[10px] text-stone-500 mt-1">Gear, Rations & Tools</p>
                        </div>
                    </button>

                    {/* OPTION 3: QUEST */}
                    <button
                        onClick={onTravel}
                        className="group relative flex flex-col items-center justify-center gap-4 bg-[#080808] border border-stone-800 hover:border-[#00f2ff] hover:bg-stone-900 transition-all"
                    >
                        <MapIcon size={48} className="text-stone-600 group-hover:text-[#00f2ff] transition-colors" />
                        <div className="text-center">
                            <h3 className="text-lg font-bold uppercase tracking-wider text-stone-300 group-hover:text-white">Embark</h3>
                            <p className="text-[10px] text-stone-500 mt-1">Travel to Quest Location</p>
                        </div>
                    </button>

                </div>
            </div>
        </div>
    );
}
