import React, { useState } from 'react';
import { Heart, Zap, Terminal, Settings, Power, Activity } from 'lucide-react';
import Arena from './components/Arena';
import InventoryPanel from './components/InventoryPanel';

// --- TYPES ---
interface CharacterStats {
  name: string;
  class: string;
  health: number; maxHealth: number;
  mana: number; maxMana: number;
}

interface LogEntry {
  id: string;
  timestamp: string;
  source: string;
  message: string;
  type: 'info' | 'combat' | 'error';
}

function App() {
  // 1. CLEAN STATE (No fake Thorin)
  const [character, setCharacter] = useState<CharacterStats>({
    name: "NO SIGNAL",
    class: "UNKNOWN ENTITY",
    health: 0, maxHealth: 100,
    mana: 0, maxMana: 100,
  });

  // Mock items to test your icons (Replace with [] later)
  const [inventoryIds] = useState<string[]>([
    "Iron Sword", "Health Potion", "Leather Armor", "Ration"
  ]);

  // 2. REAL LOGS ONLY
  const [systemLogs, setSystemLogs] = useState<LogEntry[]>([
    { id: '0', timestamp: new Date().toLocaleTimeString(), source: 'SYS', message: 'Engine Online.', type: 'info' }
  ]);

  // --- HANDLERS ---
  const handleArenaUpdate = (currentHp: number, maxHp: number, name: string) => {
    setCharacter(prev => ({
      ...prev,
      name: name,
      health: currentHp,
      maxHealth: maxHp,
      class: "Simulated Combatant"
    }));

    if (currentHp < character.health) {
      addLog('COMBAT', `Integrity Loss detected: -${character.health - currentHp} HP`, 'combat');
    }
  };

  const addLog = (source: string, msg: string, type: 'info' | 'combat' | 'error' = 'info') => {
    setSystemLogs(prev => [{
      id: Date.now().toString(),
      timestamp: new Date().toLocaleTimeString(),
      source, message: msg, type
    }, ...prev].slice(0, 50));
  };

  // --- COMPONENT: STAT BAR ---
  const StatBar = ({ current, max, color, icon: Icon, label }: any) => (
    <div className="mb-4">
      <div className="flex justify-between text-[10px] uppercase tracking-widest text-stone-500 mb-1">
        <span className="flex items-center gap-1"><Icon size={10} /> {label}</span>
        <span className="font-mono text-stone-300">{current} / {max}</span>
      </div>
      <div className="h-1 bg-stone-800 w-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${color}`}
          style={{ width: `${max > 0 ? (current / max) * 100 : 0}%` }}
        />
      </div>
    </div>
  );

  return (
    <div className="h-screen w-screen bg-[#050505] text-stone-300 font-sans flex flex-col overflow-hidden">

      {/* HEADER */}
      <header className="h-10 border-b border-stone-800 bg-[#0a0a0a] flex items-center justify-between px-4 z-20">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 bg-[#00f2ff] rounded-full animate-pulse shadow-[0_0_8px_#00f2ff]" />
          <h1 className="text-xs font-bold tracking-[0.2em] text-stone-100 uppercase">
            BRQSE <span className="text-stone-600"> / BATTLE VIEWER</span>
          </h1>
        </div>
        <div className="flex gap-2 text-stone-600">
          <Settings size={14} className="hover:text-white cursor-pointer" />
          <Power size={14} className="hover:text-red-500 cursor-pointer" />
        </div>
      </header>

      {/* MAIN CONTENT */}
      <div className="flex flex-1 overflow-hidden">

        {/* LEFT SIDEBAR */}
        <aside className="w-64 bg-[#080808] border-r border-stone-800 flex flex-col z-10">

          {/* Portrait */}
          <div className="p-6 border-b border-stone-800 flex flex-col items-center">
            <div className="w-20 h-20 mb-3 bg-stone-900 border border-stone-800 flex items-center justify-center relative rounded-sm">
              <Activity size={24} className="text-stone-700" />
            </div>
            <h2 className="text-white font-bold tracking-wider text-sm">{character.name}</h2>
            <p className="text-[9px] text-stone-500 font-mono">{character.class}</p>
          </div>

          {/* Stats */}
          <div className="p-4 border-b border-stone-800">
            <StatBar label="Integrity" current={character.health} max={character.maxHealth} color="bg-red-600" icon={Heart} />
            <StatBar label="Energy" current={character.mana} max={character.maxMana} color="bg-blue-500" icon={Zap} />
          </div>

          {/* Inventory */}
          <div className="flex-1 p-2 bg-[#060606]">
            <InventoryPanel characterItems={inventoryIds} />
          </div>
        </aside>

        {/* CENTER STAGE */}
        <main className="flex-1 relative flex flex-col bg-[#030303]">

          {/* Arena Container */}
          <div className="flex-1 flex items-center justify-center p-4 bg-grid-pattern relative">

            <Arena onStatsUpdate={handleArenaUpdate} />
          </div>

          {/* Bottom Log */}
          <div className="h-40 border-t border-stone-800 bg-[#080808] flex flex-col">
            <div className="px-3 py-1 border-b border-stone-800 bg-stone-900/50 flex items-center gap-2">
              <Terminal size={10} className="text-[#00f2ff]" />
              <span className="text-[9px] font-bold uppercase tracking-wider text-stone-400">System Feed</span>
            </div>

            <div className="flex-1 overflow-y-auto p-2 font-mono text-[10px] space-y-1">
              {systemLogs.map((log) => (
                <div key={log.id} className="flex gap-2 opacity-80 hover:opacity-100 border-l-2 border-transparent hover:border-[#00f2ff] pl-1">
                  <span className="text-stone-600">[{log.timestamp}]</span>
                  <span className={`font-bold ${log.type === 'combat' ? 'text-red-400' : 'text-[#00f2ff]'}`}>
                    {log.source}:
                  </span>
                  <span className="text-stone-300">{log.message}</span>
                </div>
              ))}
            </div>
          </div>
        </main>

      </div>
    </div>
  );
}

export default App;