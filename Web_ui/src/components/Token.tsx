import React, { useState, useEffect } from 'react';
import { Skull } from 'lucide-react';

interface TokenProps {
    name: string;
    facing: 'up' | 'down' | 'left' | 'right';
    team: string;
    dead?: boolean;
    sprite?: string;  // Optional sprite name (e.g., "badger", "wolf")
}

export default function Token({ name, facing, team, dead, sprite }: TokenProps) {
    const [imgSrc, setImgSrc] = useState<string | null>(null);
    const [isFlipped, setIsFlipped] = useState(false);
    const [retryCount, setRetryCount] = useState(0);
    const [error, setError] = useState(false);

    useEffect(() => {
        // RESET everything when the character updates
        setError(false);
        setIsFlipped(false);
        setRetryCount(0);

        // Use sprite prop if provided, otherwise fall back to name
        const tokenName = sprite || name;
        const cleanName = tokenName.toLowerCase().replace(/\s+/g, '_');

        // 1. Map Logic Direction -> File Suffix
        // facing: 'up' -> file: '_back'
        // facing: 'down' -> file: '_front'
        let suffix = facing;
        if (facing === 'up') suffix = 'back';
        if (facing === 'down') suffix = 'front';

        // 2. Try the Perfect Match first
        setImgSrc(`/tokens/${cleanName}_${suffix}.png`);

    }, [name, facing, sprite]);

    // --- THE SMART FALLBACK SYSTEM ---
    const handleImageError = () => {
        const cleanName = name.toLowerCase().replace(/\s+/g, '_');

        // Attempt 1: If LEFT fails, try RIGHT (flipped)
        if (facing === 'left' && retryCount === 0) {
            setRetryCount(1);
            setIsFlipped(true); // <--- MAGIC FLIP
            setImgSrc(`/tokens/${cleanName}_right.png`);
            return;
        }

        // Attempt 2: If RIGHT fails, try LEFT (flipped)
        if (facing === 'right' && retryCount === 0) {
            setRetryCount(1);
            setIsFlipped(true); // <--- MAGIC FLIP
            setImgSrc(`/tokens/${cleanName}_left.png`);
            return;
        }

        // Attempt 3: If Back/Front fail, maybe default to Front?
        if (facing === 'up' && retryCount === 0) {
            setRetryCount(1);
            setImgSrc(`/tokens/${cleanName}_front.png`);
            return;
        }

        // If we tried swapping and it STILL failed -> Show the colored circle
        setError(true);
    };

    // VISUALS
    const borderClass = team === 'blue' ? 'border-[#00f2ff] shadow-[0_0_10px_#00f2ff]' : 'border-red-500 shadow-[0_0_10px_red]';

    if (dead) {
        return (
            <div className="w-full h-full rounded-full border-2 border-stone-600 bg-stone-800 flex items-center justify-center opacity-50 grayscale">
                <Skull size={16} className="text-stone-500" />
            </div>
        );
    }

    // FALLBACK DISPLAY (If all images missing)
    if (error || !imgSrc) {
        return (
            <div className={`w-full h-full rounded-full border-2 ${borderClass} bg-stone-900 flex items-center justify-center relative`}>
                <span className="font-bold text-white text-xs">{name.substring(0, 1).toUpperCase()}</span>
                {/* Tiny facing arrow to show we still know which way to look */}
                <div className={`absolute w-2 h-2 border-t-2 border-r-2 border-white/50 
            ${facing === 'up' ? '-top-1 rotate-[-45deg]' : ''}
            ${facing === 'down' ? '-bottom-1 rotate-[135deg]' : ''}
            ${facing === 'left' ? '-left-1 rotate-[-135deg]' : ''}
            ${facing === 'right' ? '-right-1 rotate-[45deg]' : ''}
        `} />
            </div>
        );
    }

    return (
        <div className={`w-full h-full rounded-full border-2 ${borderClass} overflow-hidden bg-transparent`}>
            <img
                src={imgSrc}
                alt={`${name} ${facing}`}
                className="w-full h-full object-cover scale-110"
                style={{
                    imageRendering: 'pixelated',
                    // THIS IS THE KEY: If we borrowed the opposite sprite, FLIP IT.
                    transform: isFlipped ? 'scaleX(-1)' : 'none'
                }}
                onError={handleImageError}
            />
        </div>
    );
}
