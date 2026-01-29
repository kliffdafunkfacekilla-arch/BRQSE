import { useState, useEffect } from 'react';

interface Effect {
    id: string;
    type: 'hit' | 'miss' | 'crit' | 'graze' | 'ability' | 'blood';
    sprite: string;
    x: number;
    y: number;
    pos_from?: [number, number];
    pos_to?: [number, number];
    duration?: number;
    opacity?: number;
}

interface EffectLayerProps {
    events: any[];
    gridSize: number;
    onComplete?: () => void;
}

export default function EffectLayer({ events, gridSize, onComplete }: EffectLayerProps) {
    const [activeEffects, setActiveEffects] = useState<Effect[]>([]);

    useEffect(() => {
        if (events && events.length > 0) {
            const newEffects: Effect[] = events.map((event, i) => {
                let sprite = '/effect/bolt0.png';
                let type: Effect['type'] = event.type;
                let duration = 800;

                if (event.type === 'hit' || event.type === 'crit' || event.type === 'graze') {
                    // Randomize Blood Splatter (0-29 available)
                    const idx = Math.floor(Math.random() * 30);
                    sprite = `/blood/blood_red_${idx}.png`;
                    type = 'blood';
                    duration = 5000; // Blood stays longer
                } else if (event.type === 'miss' || event.type === 'whiff') {
                    sprite = '/effect/cloud_grey_smoke.png';
                    type = 'miss';
                } else if (event.type === 'ability' || event.type === 'cast') {
                    type = 'ability';
                    // Comprehensive Spell/Skill Mapping
                    sprite = '/effect/cloud_magic_trail1.png'; // Default magic

                    const name = (event.ability || '').toLowerCase().replace(/ /g, '_');

                    // --- MAPPING LOGIC (Project Schools of Power) ---
                    // NEXUS (Fire)
                    if (name.includes('nexus') || name.includes('fire') || name.includes('flame') || name.includes('heat') || name.includes('burn')) {
                        sprite = '/spells/fire/fireball.png';
                    }
                    // ORDO (Cold)
                    else if (name.includes('ordo') || name.includes('ice') || name.includes('frost') || name.includes('cold') || name.includes('chill')) {
                        sprite = '/spells/ice/ice_bolt.png';
                    }
                    // VITA (Poison/Vita/Life)
                    else if (name.includes('vita') || name.includes('poison') || name.includes('venom') || name.includes('acid') || name.includes('mend')) {
                        sprite = '/spells/poison/venom_bolt.png';
                    }
                    // OMEN (Necrotic/Intuition)
                    else if (name.includes('omen') || name.includes('death') || name.includes('soul') || name.includes('rot') || name.includes('jinx')) {
                        sprite = '/spells/necromancy/corpse_explosion.png';
                    }
                    // MASS (Force/Might)
                    else if (name.includes('mass') || name.includes('earth') || name.includes('stone') || name.includes('push') || name.includes('slam')) {
                        sprite = '/spells/earth/stone_arrow.png';
                    }
                    // RATIO (Shock/Logic)
                    else if (name.includes('ratio') || name.includes('shock') || name.includes('volt') || name.includes('scan')) {
                        sprite = '/spells/air/lightning_bolt.png';
                    }
                    // LUX (Radiant/Awareness)
                    else if (name.includes('lux') || name.includes('light') || name.includes('holy') || name.includes('sun') || name.includes('glare')) {
                        sprite = '/spells/divination/sun_beam.png';
                    }
                    // AURA (Spirit/Charm)
                    else if (name.includes('aura') || name.includes('charm') || name.includes('love') || name.includes('fear') || name.includes('mind')) {
                        sprite = '/spells/enchantment/confuse.png';
                    }
                    // ANUMIS (Arcane/Knowledge)
                    else if (name.includes('anumis') || name.includes('arcane') || name.includes('magic') || name.includes('spell')) {
                        sprite = '/effect/cloud_magic_trail2.png';
                    }
                    // MOTUS (Sonic/Speed)
                    else if (name.includes('motus') || name.includes('sonic') || name.includes('speed') || name.includes('dash') || name.includes('leap')) {
                        sprite = '/effect/cloud_blue_smoke.png';
                    }
                    // LEX (Psychic/Will)
                    else if (name.includes('lex') || name.includes('order') || name.includes('will') || name.includes('command')) {
                        sprite = '/effect/cloud_tloc_energy.png';
                    }
                    // FLUX (Acid/Finesse)
                    else if (name.includes('flux') || name.includes('finesse') || name.includes('bleed') || name.includes('slice')) {
                        sprite = '/effect/cloud_miasma.png';
                    }
                    // SKILLS (PHYSICAL)
                    else if (name.includes('arrow') || name.includes('shot') || name.includes('bow')) {
                        sprite = '/effect/arrow0.png';
                    }
                    else if (name.includes('throw') || name.includes('knife') || name.includes('dagger')) {
                        sprite = '/effect/dart0.png';
                    }
                    else if (name.includes('strike') || name.includes('bash') || name.includes('slam')) {
                        sprite = '/effect/bolt02.png'; // Impact flash
                    }
                }

                return {
                    id: `${Date.now()}-${i}`,
                    type,
                    sprite,
                    x: event.pos_to ? event.pos_to[0] : event.x,
                    y: event.pos_to ? event.pos_to[1] : event.y,
                    pos_from: event.pos_from,
                    pos_to: event.pos_to,
                    duration
                };
            });

            setActiveEffects(prev => [...prev, ...newEffects]);

            newEffects.forEach(eff => {
                setTimeout(() => {
                    setActiveEffects(current => current.filter(e => e.id !== eff.id));
                }, eff.duration || 1000);
            });
        }
    }, [events]);

    return (
        <div className="absolute inset-0 z-40 pointer-events-none overflow-hidden">
            {activeEffects.map(eff => {
                const isProjectile = eff.pos_from && eff.pos_to && (eff.pos_from[0] !== eff.pos_to[0] || eff.pos_from[1] !== eff.pos_to[1]);

                // Animation Logic
                const startX = eff.pos_from ? (eff.pos_from[0] * (100 / gridSize)) : (eff.x * (100 / gridSize));
                const startY = eff.pos_from ? (eff.pos_from[1] * (100 / gridSize)) : (eff.y * (100 / gridSize));
                const endX = eff.pos_to ? (eff.pos_to[0] * (100 / gridSize)) : (eff.x * (100 / gridSize));
                const endY = eff.pos_to ? (eff.pos_to[1] * (100 / gridSize)) : (eff.y * (100 / gridSize));

                const angle = isProjectile ? Math.atan2(endY - startY, endX - startX) * 180 / Math.PI : 0;

                const style: React.CSSProperties = isProjectile ? {
                    position: 'absolute',
                    width: `${50 / gridSize}%`,
                    height: `${50 / gridSize}%`,
                    left: `${startX + (50 / gridSize / 2)}%`,
                    top: `${startY + (50 / gridSize / 2)}%`,
                    transformOrigin: 'center',
                    animation: `projectile-fly-${eff.id.replace(/[^a-zA-Z0-9]/g, '')} 0.4s forwards linear`,
                    imageRendering: 'pixelated'
                } : {
                    position: 'absolute',
                    width: `${200 / gridSize}%`,
                    height: `${200 / gridSize}%`,
                    left: `${endX}%`,
                    top: `${endY}%`,
                    transform: 'translate(-25%, -25%) scale(0.5)',
                    animation: 'impact-pop 0.5s forwards ease-out',
                    opacity: 0,
                    imageRendering: 'pixelated'
                };

                const deltaX = (endX - startX);
                const deltaY = (endY - startY);

                return (
                    <div key={eff.id} style={style} className="flex items-center justify-center">
                        <img src={eff.sprite} className="w-full h-full object-contain" style={{ transform: isProjectile ? 'rotate(90deg)' : 'none' }} />
                        {isProjectile && (
                            <style>{`
                                @keyframes projectile-fly-${eff.id.replace(/[^a-zA-Z0-0]/g, '')} {
                                    0% { transform: translate(0, 0) rotate(${angle}deg); opacity: 0; }
                                    10% { opacity: 1; }
                                    90% { opacity: 1; }
                                    100% { transform: translate(${deltaX * 10}px, ${deltaY * 10}px) rotate(${angle}deg); opacity: 0; }
                                }
                            `}</style>
                        )}
                    </div>
                );
            })}
            <style>{`
                @keyframes impact-pop {
                    0% { transform: translate(-25%, -25%) scale(0.2); opacity: 0; }
                    20% { opacity: 1; }
                    100% { transform: translate(-25%, -25%) scale(1.2); opacity: 0; }
                }
            `}</style>
        </div>
    );
}
