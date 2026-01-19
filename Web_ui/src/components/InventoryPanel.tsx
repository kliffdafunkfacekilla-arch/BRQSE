import React, { useState } from 'react';
import ItemIcon from './ItemIcon';

// Mock Data for "Thorin" until we connect the backend fully
const defaultGear = [
    { name: "Iron Sword", type: "Weapon", description: "Standard issue blade." },
    { name: "Wooden Shield", type: "Armor", description: "Sturdy oak." },
    { name: "Health Potion", type: "Potion", description: "Restores 2d4 HP." },
    { name: "Dried Meat", type: "Food", description: "It tastes like old boots." },
    { name: "Magic Staff", type: "Weapon", description: "Crackles with energy." }
];

export default function InventoryPanel() {
    const [selectedItem, setSelectedItem] = useState<any>(null);
    const inventory = defaultGear; // Later passed as props

    return (
        <div className="flex flex-col h-full bg-stone-900/50 rounded-xl border border-stone-800 p-4">
            <h3 className="text-stone-400 text-xs font-bold uppercase tracking-wider mb-3">
                Equipment
            </h3>

            {/* ITEM GRID */}
            <div className="grid grid-cols-4 gap-2 mb-4 overflow-y-auto max-h-[250px] pr-2">
                {inventory.map((item, idx) => (
                    <button
                        key={idx}
                        onClick={() => setSelectedItem(item)}
                        className={`aspect-square rounded border flex items-center justify-center p-1 transition-all overflow-hidden relative group
                ${selectedItem === item
                                ? 'bg-stone-700 border-[#00f2ff] shadow-[0_0_10px_rgba(0,242,255,0.3)]'
                                : 'bg-stone-800 border-stone-700 hover:border-stone-500'}
              `}
                        title={item.name}
                    >
                        {/* THIS SHOWS THE SWORD */}
                        <ItemIcon name={item.name} type={item.type} />
                    </button>
                ))}
                {/* Fillers */}
                {Array.from({ length: 8 }).map((_, i) => (
                    <div key={`empty-${i}`} className="aspect-square rounded border border-stone-800/30 bg-stone-900/20" />
                ))}
            </div>

            {/* ITEM DETAILS */}
            <div className="mt-auto border-t border-stone-800 pt-4 h-[80px]">
                {selectedItem ? (
                    <div className="animate-pulse">
                        <div className="text-[#00f2ff] font-bold text-sm mb-1">{selectedItem.name}</div>
                        <div className="text-xs text-stone-400 italic">
                            {selectedItem.description}
                        </div>
                    </div>
                ) : (
                    <div className="text-stone-600 text-xs text-center mt-4">Select item to inspect</div>
                )}
            </div>
        </div>
    );
}
