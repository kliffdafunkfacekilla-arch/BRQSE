import React, { useState, useEffect } from 'react';
import { Skull } from 'lucide-react';

interface TokenProps {
    name: string;
    facing: 'up' | 'down' | 'left' | 'right';
    team: string;
    dead?: boolean;
    sprite?: string;
}

export default function Token({ name, facing, team, dead, sprite }: TokenProps) {
    const [imgSrc, setImgSrc] = useState<string | null>(null);
    const [isFlipped, setIsFlipped] = useState(false);
    const [error, setError] = useState(false);

    useEffect(() => {
        setError(false);
        setIsFlipped(false);

        // 1. Determine Base Path
        // If sprite starts with / or http, use it directly
        // Otherwise use /tokens/
        let base = sprite || name;

        // Remove .png extension for processing if it exists
        const cleanBase = base.replace(/\.png$/i, '').toLowerCase().replace(/\s+/g, '_');

        // 2. Map Direction
        let suffix = facing;
        if (facing === 'up') suffix = 'back';
        if (facing === 'down') suffix = 'front';

        // 3. Construct Path
        // Check if the base already contains a direction suffix
        const hasSuffix = /(_front|_back|_left|_right|_up|_down)$/.test(cleanBase);

        if (hasSuffix) {
            // Already has a suffix? Just use it.
            setImgSrc(`/tokens/${cleanBase}.png`);
        } else {
            // No suffix? Try adding one.
            setImgSrc(`/tokens/${cleanBase}_${suffix}.png`);
        }

    }, [name, facing, sprite]);

    const handleImageError = () => {
        // Fallback: If specific direction fails, try the generic one
        const cleanBase = (sprite || name).replace(/\.png$/i, '').toLowerCase().replace(/\s+/g, '_');

        // If we haven't tried just 'front' or 'right' yet
        if (imgSrc !== `/tokens/${cleanBase}_front.png` && imgSrc !== `/tokens/${cleanBase}_right.png`) {
            setImgSrc(`/tokens/${cleanBase}_front.png`);
            return;
        }

        // Final Fallback: Just the base
        if (imgSrc !== `/tokens/${cleanBase}.png`) {
            setImgSrc(`/tokens/${cleanBase}.png`);
            return;
        }

        setError(true);
    };

    const borderClass = team.toLowerCase() === 'blue' ? 'border-[#00f2ff] shadow-[0_0_10px_#00f2ff]' : 'border-red-500 shadow-[0_0_10px_red]';

    if (dead) {
        return (
            <div className="w-full h-full rounded-full border-2 border-stone-600 bg-stone-800 flex items-center justify-center opacity-50 grayscale">
                <Skull size={16} className="text-stone-500" />
            </div>
        );
    }

    if (error || !imgSrc) {
        return (
            <div className={`w-full h-full rounded-full border-2 ${borderClass} bg-stone-950 flex items-center justify-center relative`}>
                <span className="font-bold text-white text-[8px] uppercase">{name.substring(0, 2)}</span>
            </div>
        );
    }

    return (
        <div className={`w-full h-full rounded-full border-2 ${borderClass} overflow-hidden bg-black/40 backdrop-blur-sm group-hover:scale-110 transition-transform`}>
            <img
                src={imgSrc}
                alt={name}
                className="w-full h-full object-cover"
                style={{
                    imageRendering: 'pixelated',
                    transform: isFlipped ? 'scaleX(-1)' : 'none'
                }}
                onError={handleImageError}
            />
        </div>
    );
}
