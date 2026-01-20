import { useState, useEffect } from 'react';
import {
  Zap, Heart,
  Terminal, Settings, Power,
  Swords, User, Backpack, BookOpen
} from 'lucide-react';

import Arena from './components/Arena';
import InventoryPanel from './components/InventoryPanel';
import ActionBar from './components/ActionBar';
import CharacterSheet from './components/CharacterSheet';
import Journal from './components/Journal';

// --- CONFIG ---
const API_BASE = 'http://localhost:5001/api';

// --- TYPES ---
interface CharacterStats {
  name: string;
  class: string;
  level: number;
  health: number; maxHealth: number;
  mana: number; maxMana: number;
}

interface PlayerState {
  name: string;
  species: string;
  stats: Record<string, number>;
  equipment: Record<string, string>;
  inventory: string[];
  skills: string[];
  powers: string[];
}

interface LogEntry {
  id: string;
  timestamp: string;
  source: string;
  message: string;
  type: 'info' | 'combat' | 'error';
}

function App() {
  // 1. NAVIGATION STATE
  const [currentView, setCurrentView] = useState<'arena' | 'character' | 'inventory' | 'journal'>('arena');
  const [apiOnline, setApiOnline] = useState(false);

  // 2. CHARACTER STATE
  const [character, setCharacter] = useState<CharacterStats>({
    name: "NO SIGNAL",
    class: "UNKNOWN ENTITY",
    level: 0,
    health: 0, maxHealth: 100,
    mana: 0, maxMana: 100,
  });

  // 3. PLAYER STATE (Synced with backend)
  const [playerState, setPlayerState] = useState<PlayerState>({
    name: "Hero",
    species: "Mammal",
    stats: {},
    equipment: {
      "Main Hand": "Empty",
      "Off Hand": "Empty",
      "Head": "Empty",
      "Body": "Empty",
      "Feet": "Empty",
      "Ring 1": "Empty"
    },
    inventory: [],
    skills: [],
    powers: []
  });

  // 5. SYSTEM LOGS
  const [systemLogs, setSystemLogs] = useState<LogEntry[]>([
    { id: '0', timestamp: new Date().toLocaleTimeString(), source: 'SYS', message: 'Engine Online.', type: 'info' }
  ]);

  // --- LOAD PLAYER STATE ON MOUNT ---
  useEffect(() => {
    // Check API health
    fetch(`${API_BASE}/health`)
      .then(res => res.json())
      .then(() => {
        setApiOnline(true);
        addLog('API', 'Backend connected', 'info');
        loadPlayerState();
      })
      .catch(() => {
        setApiOnline(false);
        addLog('API', 'Backend offline - using local state', 'error');
        // Fallback: load from public folder directly
        fetch('/data/player_state.json')
          .then(res => res.json())
          .then(data => setPlayerState(data))
          .catch(() => { });
      });
  }, []);

  const loadPlayerState = async () => {
    try {
      const res = await fetch(`${API_BASE}/player`);
      const data = await res.json();
      setPlayerState(data);
      addLog('SYNC', `Loaded: ${data.name}`, 'info');
    } catch (e) {
      addLog('SYNC', 'Failed to load player state', 'error');
    }
  };

  const savePlayerState = async (newState: PlayerState) => {
    setPlayerState(newState);

    if (apiOnline) {
      try {
        await fetch(`${API_BASE}/player`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newState)
        });
        addLog('SYNC', 'State saved to backend', 'info');
      } catch (e) {
        addLog('SYNC', 'Failed to save state', 'error');
      }
    }
  };

  // --- HANDLERS ---
  const handleArenaUpdate = (currentHp: number, maxHp: number, name: string) => {
    setCharacter(prev => ({
      ...prev,
      name: name,
      health: currentHp,
      maxHealth: maxHp,
      class: "Simulated Combatant"
    }));
  };

  const addLog = (source: string, msg: string, type: 'info' | 'combat' | 'error' = 'info') => {
    setSystemLogs(prev => [{
      id: Date.now().toString(), timestamp: new Date().toLocaleTimeString(),
      source, message: msg, type
    }, ...prev].slice(0, 50));
  };

  // Move item from Inventory -> Equipment
  const handleEquip = (itemName: string) => {
    let slot = "Main Hand";
    const n = itemName.toLowerCase();

    if (n.includes('shield')) slot = "Off Hand";
    else if (n.includes('helm') || n.includes('hat') || n.includes('hood')) slot = "Head";
    else if (n.includes('armor') || n.includes('plate') || n.includes('robe') || n.includes('hide')) slot = "Body";
    else if (n.includes('boots') || n.includes('shoes')) slot = "Feet";
    else if (n.includes('ring')) slot = "Ring 1";
    else if (n.includes('staff') || n.includes('wand') || n.includes('sword') || n.includes('axe')) slot = "Main Hand";

    const currentEquipped = playerState.equipment[slot];

    const newEquipment = { ...playerState.equipment, [slot]: itemName };
    let newInventory = playerState.inventory.filter(i => i !== itemName);
    if (currentEquipped !== "Empty") newInventory.push(currentEquipped);

    const newState = { ...playerState, equipment: newEquipment, inventory: newInventory };
    savePlayerState(newState);
    addLog('EQUIP', `Equipped ${itemName} to ${slot}`);
  };

  // Move item from Equipment -> Inventory
  const handleUnequip = (slot: string) => {
    const item = playerState.equipment[slot];
    if (item === "Empty") return;

    const newEquipment = { ...playerState.equipment, [slot]: "Empty" };
    const newInventory = [...playerState.inventory, item];

    const newState = { ...playerState, equipment: newEquipment, inventory: newInventory };
    savePlayerState(newState);
    addLog('EQUIP', `Unequipped ${item}`);
  };

  // Trigger new battle via API
  const handleNewBattle = async () => {
    if (apiOnline) {
      addLog('BATTLE', 'Generating new battle...', 'combat');
      try {
        await fetch(`${API_BASE}/battle`, { method: 'POST' });
        addLog('BATTLE', 'Battle ready! Click RELOAD in Arena.', 'combat');
      } catch (e) {
        addLog('BATTLE', 'Failed to generate battle', 'error');
      }
    } else {
      addLog('BATTLE', 'Backend offline. Run: python scripts/generate_replay.py', 'error');
    }
  };

  // --- NAVIGATION COMPONENT ---
  const NavButton = ({ view, icon: Icon, label }: { view: 'arena' | 'character' | 'inventory' | 'journal'; icon: any; label: string }) => (
    <button
      onClick={() => setCurrentView(view)}
      className={`flex items-center gap-2 px-4 py-2 text-xs font-bold uppercase tracking-wider transition-all
        ${currentView === view
          ? 'text-black bg-[#00f2ff] shadow-[0_0_15px_rgba(0,242,255,0.4)]'
          : 'text-stone-500 hover:text-white hover:bg-white/5'}
      `}
    >
      <Icon size={16} /> {label}
    </button>
  );

  // --- STAT BAR HELPER ---
  const StatBar = ({ current, max, color, icon: Icon, label }: { current: number; max: number; color: string; icon: any; label: string }) => (
    <div className="mb-4">
      <div className="flex justify-between text-[10px] uppercase tracking-widest text-stone-500 mb-1">
        <span className="flex items-center gap-1"><Icon size={10} /> {label}</span>
        <span className="font-mono text-stone-300">{current} / {max}</span>
      </div>
      <div className="h-1 bg-stone-800 w-full overflow-hidden">
        <div className={`h-full transition-all duration-300 ${color}`} style={{ width: `${max > 0 ? (current / max) * 100 : 0}%` }} />
      </div>
    </div>
  );

  return (
    <div className="h-screen w-screen bg-[#050505] text-stone-300 font-sans flex flex-col overflow-hidden">

      {/* HEADER & NAV */}
      <header className="h-12 border-b border-stone-800 bg-[#0a0a0a] flex items-center justify-between px-4 shrink-0 z-50">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full animate-pulse shadow-[0_0_8px] ${apiOnline ? 'bg-[#00f2ff] shadow-[#00f2ff]' : 'bg-red-500 shadow-red-500'}`} />
            <h1 className="text-sm font-bold tracking-[0.2em] text-stone-100 uppercase">
              BRQSE <span className="text-stone-600"> / {currentView}</span>
            </h1>
          </div>

          {/* MAIN MENU TABS */}
          <div className="flex gap-1 bg-black border border-stone-800 rounded p-1">
            <NavButton view="arena" icon={Swords} label="Arena" />
            <NavButton view="character" icon={User} label="Character" />
            <NavButton view="inventory" icon={Backpack} label="Gear" />
            <NavButton view="journal" icon={BookOpen} label="Log" />
          </div>
        </div>

        <div className="flex gap-3 items-center">
          <button
            onClick={handleNewBattle}
            className="text-[10px] font-bold px-3 py-1 bg-stone-900 border border-stone-700 hover:border-[#00f2ff] hover:text-[#00f2ff] transition-colors uppercase"
          >
            New Battle
          </button>
          <Settings size={14} className="text-stone-600 hover:text-white cursor-pointer" />
          <Power size={14} className="text-stone-600 hover:text-red-500 cursor-pointer" />
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      <div className="flex flex-1 overflow-hidden">

        {/* LEFT SIDEBAR */}
        <aside className="w-64 bg-[#080808] border-r border-stone-800 flex flex-col z-10 shrink-0">
          <div className="p-6 border-b border-stone-800 flex flex-col items-center">
            <div className="w-20 h-20 mb-3 bg-stone-900 border border-stone-800 flex items-center justify-center relative rounded-sm overflow-hidden">
              <img src="/tokens/badger_front.png" alt="avatar" className="w-full h-full object-cover opacity-80" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
            </div>
            <h2 className="text-white font-bold tracking-wider text-sm">{playerState.name}</h2>
            <p className="text-[9px] text-stone-500 font-mono">{playerState.species}</p>
          </div>
          <div className="p-4 border-b border-stone-800">
            <StatBar label="Integrity" current={character.health} max={character.maxHealth} color="bg-red-600" icon={Heart} />
            <StatBar label="Energy" current={character.mana} max={character.maxMana} color="bg-blue-500" icon={Zap} />
          </div>
          {/* Mini Inventory */}
          <div className="flex-1 p-2 bg-[#060606] overflow-hidden">
            <div className="text-[9px] text-stone-500 font-bold uppercase mb-2 pl-1">Quick Slots</div>
            <div className="grid grid-cols-4 gap-1">
              {playerState.inventory.slice(0, 8).map((item, i) => (
                <div key={i} className="aspect-square bg-stone-900 border border-stone-800 flex items-center justify-center p-1">
                  <div className="w-2 h-2 bg-stone-700 rounded-full" title={item} />
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* CENTER VIEWPORT */}
        <main className="flex-1 relative flex flex-col bg-[#030303] overflow-hidden">

          <div className="flex-1 overflow-auto relative">
            {currentView === 'arena' && (
              <div className="h-full flex flex-col">
                <div className="flex-1 flex items-center justify-center p-4 bg-grid-pattern relative">
                  <div className="absolute inset-0 bg-radial-gradient pointer-events-none opacity-50" />
                  <Arena onStatsUpdate={handleArenaUpdate} onLog={(msg, type) => addLog('ARENA', msg, type)} />
                </div>
                <ActionBar />
              </div>
            )}

            {currentView === 'character' && (
              <CharacterSheet
                equipment={playerState.equipment}
                stats={playerState.stats}
                onUnequip={handleUnequip}
              />
            )}

            {currentView === 'inventory' && (
              <div className="p-8 h-full">
                <InventoryPanel
                  characterItems={playerState.inventory}
                  onEquip={handleEquip}
                />
              </div>
            )}

            {currentView === 'journal' && <Journal />}
          </div>

          {/* BOTTOM LOG */}
          <div className="h-32 border-t border-stone-800 bg-[#080808] flex flex-col shrink-0">
            <div className="px-3 py-1 border-b border-stone-800 bg-stone-900/50 flex items-center gap-2">
              <Terminal size={10} className="text-[#00f2ff]" />
              <span className="text-[9px] font-bold uppercase tracking-wider text-stone-400">System Feed</span>
              {!apiOnline && <span className="text-[9px] text-red-500 ml-2">(OFFLINE MODE)</span>}
            </div>
            <div className="flex-1 overflow-y-auto p-2 font-mono text-[10px] space-y-1">
              {systemLogs.map((log) => (
                <div key={log.id} className="flex gap-2 opacity-80 hover:opacity-100 border-l-2 border-transparent hover:border-[#00f2ff] pl-1">
                  <span className="text-stone-600">[{log.timestamp}]</span>
                  <span className={`font-bold ${log.type === 'combat' ? 'text-red-400' : log.type === 'error' ? 'text-yellow-500' : 'text-[#00f2ff]'}`}>
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