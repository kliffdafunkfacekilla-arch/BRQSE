import { useState } from 'react';
import ItemIcon from './ItemIcon';

interface InventoryPanelProps {
    characterItems: string[];
    onEquip?: (item: string) => void;
}

export default function InventoryPanel({ characterItems = [], onEquip }: InventoryPanelProps) {
    const [selectedItem, setSelectedItem] = useState<string | null>(null);

    return (
        <div className="flex flex-col h-full bg-[#0a0a0f] rounded-xl border border-stone-800 p-4">
            <h3 className="text-stone-500 text-[10px] font-bold uppercase tracking-wider mb-4 flex justify-between items-center">
                <span>Cargo Hold</span>
                <span className="text-stone-600">{characterItems.length} Items</span>
            </h3>

            <div className="grid grid-cols-6 gap-3 mb-4 overflow-y-auto flex-1 content-start">
                {characterItems.map((item, idx) => (
                    <button
                        key={idx}
                        onClick={() => setSelectedItem(item)}
                        onDoubleClick={() => onEquip && onEquip(item)}
                        className={`aspect-square rounded border flex flex-col items-center justify-center p-2 transition-all relative group
                ${selectedItem === item
                                ? 'bg-stone-800 border-[#00f2ff] shadow-[0_0_15px_rgba(0,242,255,0.15)]'
                                : 'bg-[#111] border-stone-800 hover:border-stone-500'}
              `}
                        title={item}
                    >
                        <ItemIcon name={item} />
                        <span className="text-[9px] text-stone-400 truncate w-full text-center group-hover:text-white mt-1">{item}</span>
                    </button>
                ))}
                {/* Empty Slots */}
                {Array.from({ length: Math.max(0, 24 - characterItems.length) }).map((_, i) => (
                    <div key={`empty-${i}`} className="aspect-square rounded border border-stone-900 bg-black/20" />
                ))}
            </div>

            {/* FOOTER ACTIONS */}
            <div className="mt-auto border-t border-stone-800 pt-4 h-16 flex justify-between items-center">
                <div className="text-white font-bold text-sm">
                    {selectedItem || "Select an item..."}
                </div>

                {selectedItem && (
                    <button
                        onClick={() => { onEquip && onEquip(selectedItem); setSelectedItem(null); }}
                        className="bg-[#00f2ff] hover:bg-cyan-400 text-black font-bold px-6 py-2 rounded uppercase text-xs tracking-widest shadow-[0_0_10px_#00f2ff]"
                    >
                        Equip Item
                    </button>
                )}
            </div>
        </div>
    );
}
