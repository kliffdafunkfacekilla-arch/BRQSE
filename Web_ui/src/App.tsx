import React, { useState, useEffect } from 'react';
import { Shield, Zap, Heart, Star, Swords, Scroll, Backpack } from 'lucide-react';
import Arena from './components/Arena';
import InventoryPanel from './components/InventoryPanel'; // Ensure this exists!

// --- TYPES ---
interface CharacterStats {
  health: number; maxHealth: number;
  mana: number; maxMana: number;
  strength: number; dexterity: number; intelligence: number;
  wisdom: number; constitution: number; charisma: number;
  level: number; experience: number; gold: number;
}

interface ChatMessage {
  id: string; user: string; message: string; timestamp: Date; type: 'player' | 'dm' | 'system';
}

function App() {
  // --- STATE ---
  const [character, setCharacter] = useState<CharacterStats>({
    health: 100, maxHealth: 100,
    mana: 42, maxMana: 60,
    strength: 16, dexterity: 14, intelligence: 12,
    wisdom: 15, constitution: 18, charisma: 10,
    level: 7, experience: 2850, gold: 347
  });

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { id: '1', user: 'SYSTEM', message: 'Uplink Established. Waiting for combat data...', timestamp: new Date(), type: 'system' }
  ]);

  // Inventory Mock Data (Replace with real data later)
  const [inventoryIds] = useState<string[]>([
    "Iron Sword", "Steel Shield", "Health Potion", "Dried Meat", "Magic Staff", "Ruby Gem", "Leather Helm"
  ]);

  // --- HANDLERS ---
  const handleArenaUpdate = (currentHp: number, maxHp: number, name: string) => {
    setCharacter(prev => ({ ...prev, health: currentHp, maxHealth: maxHp }));
    if (currentHp < character.health) {
      addLog(`combat`, `${name} took damage! HP: ${currentHp}/${maxHp}`);
    }
  };

  const addLog = (type: string, msg: string) => {
    setChatMessages(prev => [...prev, {
      id: Date.now().toString(), user: type.toUpperCase(), message: msg, timestamp: new Date(), type: 'system'
    }].slice(-20)); // Keep last 20
  };

  // --- COMPONENTS ---
  const StatBar = ({ current, max, color, icon: Icon, label }: any) => (
    <div className="mb-2">
      <div className="flex justify-between text-xs mb-1 text-stone-400 uppercase font-bold tracking-wider">
        <span className="flex items-center gap-1"><Icon size={12} /> {label}</span>
        <span>{current}/{max}</span>
      </div>
      <div className="h-2 bg-black/50 rounded-full border border-stone-800 overflow-hidden">
        <div className={`h-full transition-all duration-500 ${color}`} style={{ width: `${(current / max) * 100}%` }} />
      </div>
    </div>
  );

  const Attribute = ({ label, value }: any) => (
    <div className="flex flex-col items-center bg-stone-800/40 p-2 rounded border border-stone-700/50">
      <span className="text-[10px] text-stone-500 uppercase font-bold">{label}</span>
      <span className="text-lg font-mono text-stone-200">{value}</span>
    </div>
  );

  return (
    <div className="h-screen w-screen bg-[#0c0c10] text-stone-200 font-sans flex flex-col overflow-hidden selection:bg-[#00f2ff] selection:text-black">

      {/* HEADER */}
      <header className="h-14 border-b border-stone-800 bg-[#15151a] flex items-center justify-between px-6 z-20 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-[#00f2ff] shadow-[0_0_10px_#00f2ff]" />
          <h1 className="text-lg font-bold tracking-widest text-stone-100">B.R.Q.S.E. <span className="text-stone-500 text-xs font-normal">v0.9.1</span></h1>
        </div>
        <div className="text-xs font-mono text-stone-500 flex gap-4">
          <span>NET: ONLINE</span>
          <span>LATENCY: 12ms</span>
        </div>
      </header>

      {/* MAIN LAYOUT */}
      <div className="flex flex-1 overflow-hidden">

        {/* LEFT SIDEBAR (Stats & Inventory) */}
        <aside className="w-80 bg-[#111116] border-r border-stone-800 flex flex-col z-10 shadow-xl">

          {/* Top Stats */}
          <div className="p-4 border-b border-stone-800 bg-stone-900/50">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-16 h-16 rounded border-2 border-stone-700 overflow-hidden bg-stone-800">
                {/* Avatar Placeholder */}
                <div className="w-full h-full flex items-center justify-center text-2xl font-bold text-stone-600">?</div>
              </div>
              <div>
                <h2 className="font-bold text-white text-lg">Thorin</h2>
                <p className="text-xs text-[#00f2ff]">Lvl {character.level} Human Fighter</p>
              </div>
            </div>

            <StatBar current={character.health} max={character.maxHealth} color="bg-red-600 shadow-[0_0_10px_rgba(220,38,38,0.4)]" icon={Heart} label="Health" />
            <StatBar current={character.mana} max={character.maxMana} color="bg-blue-600 shadow-[0_0_10px_rgba(37,99,235,0.4)]" icon={Zap} label="Mana" />
          </div>

          {/* Attributes Grid */}
          <div className="p-4 grid grid-cols-3 gap-2 border-b border-stone-800">
            <Attribute label="STR" value={character.strength} />
            <Attribute label="DEX" value={character.dexterity} />
            <Attribute label="CON" value={character.constitution} />
            <Attribute label="INT" value={character.intelligence} />
            <Attribute label="WIS" value={character.wisdom} />
            <Attribute label="CHA" value={character.charisma} />
          </div>

          {/* Inventory (Fills remaining space) */}
          <div className="flex-1 overflow-hidden p-2 bg-[#0a0a0f]">
            <InventoryPanel characterItems={inventoryIds} />
          </div>
        </aside>

        {/* CENTER STAGE (Arena + Chat) */}
        <main className="flex-1 flex flex-col relative bg-[#050508]">
          <div className="flex-1 relative bg-grid-pattern flex items-center justify-center p-8">
            <div className="absolute inset-0 pointer-events-none bg-radial-gradient" />

            {/* The Arena Component */}
            <div className="z-10 shadow-2xl border border-stone-800 rounded-lg overflow-hidden bg-black/80">
              <Arena onStatsUpdate={handleArenaUpdate} />
            </div>
          </div>

          {/* BOTTOM CHAT / COMM LOG */}
          <div className="h-48 bg-[#111116] border-t border-stone-800 flex flex-col z-20">
            <div className="flex items-center justify-between px-4 py-2 bg-stone-900/50 border-b border-stone-800">
              <span className="font-bold text-xs uppercase tracking-wider text-stone-400">Comm Log</span>
              <div className="flex gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-[10px] font-mono text-stone-500">LIVE FEED</span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-1 font-mono text-xs">
              {chatMessages.map((msg) => (
                <div key={msg.id} className="animate-fade-in flex gap-2">
                  <span className="text-stone-600 block min-w-[60px]">{msg.timestamp.toLocaleTimeString()}</span>
                  <span className={`font-bold ${msg.user === 'SYSTEM' ? 'text-[#00f2ff]' : 'text-yellow-500'}`}>
                    [{msg.user}]
                  </span>
                  <span className="text-stone-300">{msg.message}</span>
                </div>
              ))}
            </div>

            <div className="p-2 border-t border-stone-800 bg-[#0a0a0f]">
              <div className="flex gap-2 items-center">
                <span className="text-[#00f2ff] font-bold">&gt;</span>
                <input
                  type="text"
                  placeholder="Enter command..."
                  className="flex-1 bg-transparent text-sm text-white focus:outline-none font-mono"
                />
              </div>
            </div>
          </div>
        </main>

      </div>
    </div>
  );
}

export default App;