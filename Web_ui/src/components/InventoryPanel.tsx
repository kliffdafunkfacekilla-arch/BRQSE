import React, { useState } from 'react';
import ItemIcon from './ItemIcon';

export default function InventoryPanel({ characterItems = [] }: { characterItems: string[] }) {
    const [selectedItem, setSelectedItem] = useState<string | null>(null);

    // If no items, show empty slots
    const displayItems = characterItems.length > 0 ? characterItems : ["Empty"];

    return (
        <div className="flex flex-col h-full bg-[#0a0a0f] rounded-xl border border-stone-800 p-3">
            <h3 className="text-stone-500 text-[10px] font-bold uppercase tracking-wider mb-2">
                Cargo Hold
            </h3>

            <div className="grid grid-cols-4 gap-2 mb-4 overflow-y-auto max-h-[200px] pr-1">
                {displayItems.map((item, idx) => (
                    <button
                        key={idx}
                        onClick={() => setSelectedItem(item)}
                        className={`aspect-square rounded border flex items-center justify-center p-1 transition-all overflow-hidden relative
                ${selectedItem === item
                                ? 'bg-stone-800 border-[#00f2ff] shadow-[0_0_10px_rgba(0,242,255,0.2)]'
                                : 'bg-stone-900 border-stone-800 hover:border-stone-600'}
              `}
                        title={item}
                    >
                        {item === "Empty" ? <span className="opacity-20 text-xs">.</span> : <ItemIcon name={item} />}
                    </button>
                ))}
                {/* Fillers */}
                {Array.from({ length: Math.max(0, 12 - displayItems.length) }).map((_, i) => (
                    <div key={`empty-${i}`} className="aspect-square rounded border border-stone-900 bg-black/20" />
                ))}
            </div>

            <div className="mt-auto border-t border-stone-800 pt-2 h-[40px]">
                <div className="text-[#00f2ff] font-mono text-xs truncate">
                    {selectedItem && selectedItem !== "Empty" ? selectedItem : "No Selection"}
                </div>
            </div>
        </div>
    );
}
