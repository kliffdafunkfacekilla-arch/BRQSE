import React, { useEffect, useRef } from 'react';
import {
    Move, Search, Hammer, RotateCw,
    ArrowUp, LogOut, Package, Eye,
    ArrowDown, Scissors, Play
} from 'lucide-react';

interface Action {
    id: string;
    label: string;
    icon: any;
}

interface ContextMenuProps {
    x: number;
    y: number;
    tileX: number;
    tileY: number;
    objectTags: string[];
    onAction: (actionId: string, tx: number, ty: number) => void;
    onClose: () => void;
}

export default function ContextMenu({ x, y, tileX, tileY, objectTags, onAction, onClose }: ContextMenuProps) {
    const menuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
                onClose();
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [onClose]);

    const actions: Action[] = [
        { id: 'move', label: 'Move', icon: Move },
        { id: 'search', label: 'Search', icon: Search },
        { id: 'inspect', label: 'Inspect', icon: Eye },
    ];

    // Map tags to actions
    if (objectTags.includes('smash')) actions.push({ id: 'smash', label: 'Smash', icon: Hammer });
    if (objectTags.includes('push')) actions.push({ id: 'push', label: 'Push', icon: ArrowUp });
    if (objectTags.includes('pull')) actions.push({ id: 'pull', label: 'Pull', icon: ArrowDown });
    if (objectTags.includes('climb')) actions.push({ id: 'climb', label: 'Climb', icon: ArrowUp });
    if (objectTags.includes('vault')) actions.push({ id: 'vault', label: 'Vault', icon: Play }); // Play icon as vaulting forward
    if (objectTags.includes('flip')) actions.push({ id: 'flip', label: 'Flip', icon: RotateCw });
    if (objectTags.includes('open')) actions.push({ id: 'open', label: 'Open', icon: Package });
    if (objectTags.includes('break')) actions.push({ id: 'break', label: 'Break', icon: Scissors });
    if (objectTags.includes('drop')) actions.push({ id: 'drop', label: 'Drop', icon: ArrowDown });

    return (
        <div
            ref={menuRef}
            className="fixed z-[100] bg-[#0a0a0a] border border-stone-800 shadow-2xl min-w-[120px] py-1 animate-fade-in"
            style={{ left: x, top: y }}
        >
            <div className="px-3 py-1 mb-1 border-b border-stone-900 flex justify-between items-center text-[9px] font-bold text-stone-600 uppercase tracking-widest">
                <span>Tile {tileX},{tileY}</span>
            </div>
            {actions.map((act) => (
                <button
                    key={act.id}
                    onClick={() => {
                        onAction(act.id, tileX, tileY);
                        onClose();
                    }}
                    className="w-full px-3 py-2 flex items-center gap-3 hover:bg-[#92400e]/20 hover:text-white text-stone-400 transition-colors text-left"
                >
                    <act.icon size={12} className="text-[#92400e]" />
                    <span className="text-[10px] font-bold uppercase tracking-widest">{act.label}</span>
                </button>
            ))}
        </div>
    );
}
