import React, { useState, useEffect } from 'react';
import { Package, Shield, Sword, FlaskConical, Utensils, Wand2 } from 'lucide-react';

interface ItemIconProps {
    name: string;
    type?: string;
    className?: string;
}

export default function ItemIcon({ name, type = "Misc", className = "w-full h-full" }: ItemIconProps) {
    const [imgSrc, setImgSrc] = useState<string | null>(null);
    const [error, setError] = useState(false);

    useEffect(() => {
        setError(false);
        // "Iron Sword" -> "iron_sword"
        const filename = name.toLowerCase().trim().replace(/\s+/g, '_').replace(/['"()]/g, '');
        const folder = getFolder(type, name);

        if (folder) {
            setImgSrc(`/icons/${folder}/${filename}.png`);
        } else {
            setImgSrc(null);
            setError(true);
        }
    }, [name, type]);

    if (error || !imgSrc) {
        return (
            <div className={`flex items-center justify-center bg-stone-800/50 rounded ${className}`}>
                {getFallbackIcon(type, name)}
            </div>
        );
    }

    return (
        <img
            src={imgSrc}
            alt={name}
            className={`object-contain drop-shadow-md ${className}`}
            onError={() => setError(true)}
        />
    );
}

function getFolder(type: string, name: string): string | null {
    const n = name.toLowerCase();
    if (n.includes('staff')) return 'staff';
    if (n.includes('rod')) return 'rod';
    if (n.includes('potion') || n.includes('elixir')) return 'potion';
    if (n.includes('meat') || n.includes('bread') || n.includes('food')) return 'food';
    if (n.includes('shield') || n.includes('helm') || n.includes('plate') || n.includes('armor')) return 'armor';
    if (n.includes('sword') || n.includes('axe') || n.includes('mace') || n.includes('bow')) return 'weapon';
    return null;
}

function getFallbackIcon(type: string, name: string) {
    const n = name.toLowerCase();
    if (n.includes('staff') || n.includes('rod')) return <Wand2 className="text-indigo-400 w-2/3 h-2/3" />;
    if (n.includes('sword') || n.includes('axe')) return <Sword className="text-stone-500 w-2/3 h-2/3" />;
    if (n.includes('shield') || n.includes('armor')) return <Shield className="text-stone-500 w-2/3 h-2/3" />;
    if (n.includes('potion')) return <FlaskConical className="text-purple-500 w-2/3 h-2/3" />;
    if (n.includes('food')) return <Utensils className="text-orange-400 w-2/3 h-2/3" />;
    return <Package className="text-stone-600 w-2/3 h-2/3" />;
}
