import { useState } from 'react';
import { MapPin, Compass, Skull, Tent, Mountain, Trees } from 'lucide-react';

interface LocationNode {
    id: string;
    name: string;
    type: string;
    biome: string;
    distance: number; // Days/Provisions needed
    risk: 'Low' | 'Medium' | 'High' | 'Deadly';
    x: number; // For visual positioning %
    y: number;
}

const LOCATIONS: LocationNode[] = [
    { id: 'ruins', name: 'Ruins of Old Valoria', type: 'Dungeon', biome: 'Ruins', distance: 2, risk: 'Medium', x: 60, y: 30 },
    { id: 'forest', name: 'Whispering Woods', type: 'Extermination', biome: 'Forest', distance: 1, risk: 'Low', x: 25, y: 50 },
    { id: 'cave', name: 'Gloomrot Caverns', type: 'Exploration', biome: 'Cave', distance: 3, risk: 'High', x: 70, y: 70 },
    { id: 'mountain', name: 'Iron Peak', type: 'Boss', biome: 'Mountain', distance: 4, risk: 'Deadly', x: 40, y: 15 },
];

export default function WorldMap({ onArrive, onBack }: { onArrive: (loc: LocationNode) => void, onBack: () => void }) {
    const [selected, setSelected] = useState<LocationNode | null>(null);
    const [traveling, setTraveling] = useState(false);
    const [log, setLog] = useState<string[]>([]);

    const handleTravel = () => {
        if (!selected) return;
        setTraveling(true);
        setLog(prev => [...prev, `Departing for ${selected.name}...`]);

        // Simulate travel time / random events
        let day = 1;
        const interval = setInterval(() => {
            if (day > selected.distance) {
                clearInterval(interval);
                setLog(prev => [...prev, `Arrived at ${selected.name}!`]);
                setTimeout(() => {
                    onArrive(selected);
                }, 1000);
            } else {
                setLog(prev => [...prev, `Day ${day}: Traveling... -1 Rations`]);
                day++;
            }
        }, 800);
    };

    return (
        <div className="h-full w-full bg-[#050505] flex relative text-stone-300 font-sans overflow-hidden">

            {/* MAP AREA */}
            <div className="flex-1 relative bg-stone-900 overflow-hidden">
                <div className="absolute inset-0 opacity-20 bg-[url('/bg/world_map_texture.jpg')] bg-cover grayscale pointer-events-none" />
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_transparent_0%,_#050505_100%)] pointer-events-none" />

                {/* NODES */}
                {LOCATIONS.map(loc => (
                    <button
                        key={loc.id}
                        onClick={() => setSelected(loc)}
                        className={`absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-1 group transition-all duration-300
                            ${selected?.id === loc.id ? 'z-20 scale-110' : 'z-10 hover:scale-105'}
                        `}
                        style={{ left: `${loc.x}%`, top: `${loc.y}%` }}
                    >
                        <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center shadow-[0_0_15px_rgba(0,0,0,0.8)] transition-colors
                            ${selected?.id === loc.id
                                ? 'bg-[#00f2ff] border-white text-black'
                                : 'bg-stone-800 border-stone-600 text-stone-400 group-hover:bg-stone-700 group-hover:text-white group-hover:border-white'}
                        `}>
                            {loc.biome === 'Forest' && <Trees size={16} />}
                            {loc.biome === 'Ruins' && <Skull size={16} />}
                            {loc.biome === 'Cave' && <Tent size={16} />}
                            {loc.biome === 'Mountain' && <Mountain size={16} />}
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider bg-black/80 px-2 py-0.5 rounded backdrop-blur-sm
                            ${selected?.id === loc.id ? 'text-[#00f2ff]' : 'text-stone-500 group-hover:text-stone-300'}
                        `}>
                            {loc.name}
                        </span>
                    </button>
                ))}

                {/* Overlay UI */}
                <div className="absolute top-4 left-4 flex gap-2">
                    <button onClick={onBack} className="px-3 py-1 bg-black/50 border border-stone-700 hover:text-white text-xs uppercase font-bold backdrop-blur-sm">
                        &larr; Return to Hub
                    </button>
                </div>
            </div>

            {/* SIDEBAR INFO */}
            <div className="w-80 bg-[#080808] border-l border-stone-800 p-6 flex flex-col z-20 shadow-2xl">
                <div className="mb-6 flex items-center gap-3 text-[#00f2ff] opacity-80">
                    <Compass size={24} />
                    <h2 className="text-lg font-black uppercase tracking-widest">World Map</h2>
                </div>

                {selected ? (
                    <div className="flex-1 flex flex-col animate-fade-in">
                        <h3 className="text-xl font-bold text-white mb-1">{selected.name}</h3>
                        <div className="text-xs text-stone-500 font-mono mb-4 uppercase">{selected.type} // {selected.biome}</div>

                        <div className="space-y-4 mb-8">
                            <div className="p-3 bg-stone-900 border border-stone-800 rounded">
                                <div className="text-[10px] uppercase text-stone-500 font-bold mb-1">Travel Cost</div>
                                <div className="text-sm text-stone-300 flex justify-between">
                                    <span>Time</span>
                                    <span>{selected.distance} Days</span>
                                </div>
                                <div className="text-sm text-stone-300 flex justify-between">
                                    <span>Rations</span>
                                    <span>{selected.distance} needed</span>
                                </div>
                            </div>

                            <div className="p-3 bg-stone-900 border border-stone-800 rounded">
                                <div className="text-[10px] uppercase text-stone-500 font-bold mb-1">Risk Level</div>
                                <div className={`text-sm font-bold flex justify-between
                                    ${selected.risk === 'Low' ? 'text-green-500' :
                                        selected.risk === 'Medium' ? 'text-yellow-500' :
                                            selected.risk === 'High' ? 'text-orange-500' : 'text-red-600'}
                                `}>
                                    <span>Danger</span>
                                    <span>{selected.risk}</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex-1">
                            <div className="text-[10px] uppercase text-stone-500 font-bold mb-2">Travel Log</div>
                            <div className="h-32 bg-black border border-stone-800 p-2 font-mono text-[10px] text-stone-400 overflow-y-auto w-full">
                                {log.map((l, i) => (
                                    <div key={i}>{l}</div>
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={handleTravel}
                            disabled={traveling}
                            className={`w-full py-4 mt-4 font-black uppercase tracking-widest transition-all
                                ${traveling
                                    ? 'bg-stone-800 text-stone-500 cursor-not-allowed'
                                    : 'bg-[#00f2ff] text-black hover:bg-white hover:shadow-[0_0_20px_rgba(0,242,255,0.4)]'}
                            `}
                        >
                            {traveling ? 'Traveling...' : 'Travel'}
                        </button>
                    </div>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-stone-600">
                        <MapPin size={48} className="mb-4 opacity-50" />
                        <p className="text-xs uppercase font-bold tracking-widest text-center">Select a Destination</p>
                    </div>
                )}
            </div>
        </div>
    );
}
