import { useState, useEffect } from 'react';
import {
  Zap, Heart,
  Terminal, Settings, Power,
  Swords, User, Backpack, BookOpen,
  Hammer, UserPlus, Eye, EyeOff
} from 'lucide-react';

import Arena from './components/Arena';
import InventoryPanel from './components/InventoryPanel';
import ActionBar from './components/ActionBar';
import CharacterSheet from './components/CharacterSheet';
import Journal from './components/Journal';
import BattleBuilder from './components/BattleBuilder';
import CharacterBuilder from './components/CharacterBuilder';
import MainMenu from './components/MainMenu';
import TavernHub from './components/TavernHub';
import WorldMap from './components/WorldMap';
import ChaosHUD from './components/ChaosHUD';

interface PlayerState {
  name: string;
  species: string;
  stats: Record<string, number>;
  equipment: Record<string, string>;
  inventory: string[];
  skills: string[];
  powers: any[];
  sprite?: string;
  max_hp?: number;
  current_hp?: number;
}

interface WorldStatus {
  chaos_level: number;
  chaos_clock: number;
  tension_threshold: number;
  atmosphere: {
    descriptor: string;
    tone: string;
  };
}

function App() {
  const [currentView, setCurrentView] = useState<'start' | 'tavern' | 'world' | 'gameplay' | 'arena' | 'character' | 'inventory' | 'journal' | 'builder' | 'create'>('start');
  const [apiOnline, setApiOnline] = useState(false);
  const [showDevTools, setShowDevTools] = useState(false);
  const [playerState, setPlayerState] = useState<PlayerState | null>(null);
  const [worldStatus, setWorldStatus] = useState<WorldStatus>({
    chaos_level: 1,
    chaos_clock: 0,
    tension_threshold: 1,
    atmosphere: { descriptor: "", tone: "normal" }
  });
  const [tacticalStatus, setTacticalStatus] = useState({ elevation: 0, is_behind_cover: false, facing: "N" });
  const [systemLogs, setSystemLogs] = useState<any[]>([]);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        setApiOnline(true);
        loadStateDeep();
      } else {
        setApiOnline(false);
      }
    } catch {
      setApiOnline(false);
    }
  };

  const loadStateDeep = async () => {
    try {
      // 1. Fetch Game State (Events)
      const res = await fetch('/api/game/state');
      const data = await res.json();

      if (data.event === 'QUEST_COMPLETE') {
        addLog('SYSTEM', 'Quest Complete! Safe passage back to town.');
        setCurrentView('tavern');
      }

      setTacticalStatus({
        elevation: data.elevation || 0,
        is_behind_cover: data.is_behind_cover || false,
        facing: data.facing || "N"
      });

      // 2. Fetch World Status (Chaos/Tension)
      const worldRes = await fetch('/api/world/status');
      const worldData = await worldRes.json();
      setWorldStatus(worldData);

      // 3. Fetch Player State if needed
      if (!playerState) {
        const pRes = await fetch('/api/player');
        const pData = await pRes.json();
        setPlayerState(pData);
      }
    } catch (e) { }
  };

  const loadPlayerState = async () => {
    try {
      const res = await fetch('/api/player');
      const data = await res.json();
      if (data && data.name) {
        setPlayerState(data);
        addLog('SYSTEM', `Hydrated character: ${data.name}`);
      }
    } catch (e) {
      addLog('SYSTEM', 'Failed to sync with chronicle', 'error');
    }
  };

  const addLog = (source: string, message: string, type: string = 'info') => {
    setSystemLogs(prev => [{ id: Date.now(), source, message, type, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 30));
  };

  const handleEquip = async (itemName: string) => {
    if (!playerState) return;
    let slot = "Main Hand";
    const n = itemName.toLowerCase();
    if (n.includes('shield')) slot = "Off Hand";
    else if (n.includes('armor') || n.includes('plate') || n.includes('robe')) slot = "Body";

    const newEquipment = { ...playerState.equipment, [slot]: itemName };
    const newState = { ...playerState, equipment: newEquipment };
    setPlayerState(newState);

    await fetch('/api/player', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newState)
    });
    addLog('GEAR', `Equipped ${itemName}`);
  };

  if (currentView === 'start') {
    return (
      <div className="h-screen w-screen bg-[#050505] text-stone-400 font-serif flex flex-col overflow-hidden">
        <MainMenu onStart={() => setCurrentView('tavern')} onLoad={() => { loadPlayerState(); setCurrentView('tavern'); }} onCreate={() => setCurrentView('create')} />
      </div>
    );
  }

  const p = playerState || { name: "Awaiting Soul", species: "Unknown", stats: {}, equipment: {}, inventory: [], powers: [], sprite: "badger_front.png", max_hp: 20, current_hp: 20 };

  return (
    <div className="h-screen w-screen bg-[#050505] text-stone-400 font-serif flex flex-col overflow-hidden">
      <header className="h-12 border-b border-stone-900 bg-[#0a0a0a] flex items-center justify-between px-4 shrink-0 z-50">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${apiOnline ? 'bg-[#92400e]' : 'bg-red-950'}`} />
            <span className="text-xs font-bold uppercase tracking-widest text-stone-200">Shadowfall Chronicles</span>
          </div>
          <nav className="flex gap-1 bg-black border border-stone-800 p-1 rounded-sm">
            <button onClick={() => setCurrentView('tavern')} className={`px-4 py-1 text-[10px] font-bold uppercase transition-all ${currentView === 'tavern' ? 'bg-[#92400e] text-white' : 'text-stone-600 hover:text-white'}`}>Hub</button>
            <button onClick={() => setCurrentView('gameplay')} className={`px-4 py-1 text-[10px] font-bold uppercase transition-all ${currentView === 'gameplay' ? 'bg-[#92400e] text-white' : 'text-stone-600 hover:text-white'}`}>World</button>
            <button onClick={() => setCurrentView('inventory')} className={`px-4 py-1 text-[10px] font-bold uppercase transition-all ${currentView === 'inventory' ? 'bg-[#92400e] text-white' : 'text-stone-600 hover:text-white'}`}>Gear</button>
            <button onClick={() => setCurrentView('character')} className={`px-4 py-1 text-[10px] font-bold uppercase transition-all ${currentView === 'character' ? 'bg-[#92400e] text-white' : 'text-stone-600 hover:text-white'}`}>Hero</button>
          </nav>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setShowDevTools(!showDevTools)} className={`transition-colors ${showDevTools ? 'text-[#92400e]' : 'text-stone-800 hover:text-white'}`}><Eye size={14} /></button>
          <button onClick={() => setCurrentView('start')} className="text-stone-800 hover:text-red-900"><Power size={14} /></button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-64 bg-[#080808] border-r border-stone-900 flex flex-col shrink-0">
          <div className="p-6 border-b border-stone-900 flex flex-col items-center">
            <div className="w-20 h-24 mb-4 bg-black border border-stone-800 p-1 relative group">
              <img src={`/tokens/${p.sprite || 'badger_front.png'}`} className="w-full h-full object-cover grayscale-[0.3]" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
            </div>
            <h2 className="text-white font-bold uppercase tracking-widest text-sm text-center">{p.name}</h2>
            <p className="text-[10px] text-[#92400e] font-bold uppercase tracking-widest mt-1">{p.species}</p>
          </div>

          {/* CHAOS AND TENSION HUD */}
          <ChaosHUD
            chaosLevel={worldStatus.chaos_level}
            chaosClock={worldStatus.chaos_clock}
            tensionThreshold={worldStatus.tension_threshold}
            atmosphere={worldStatus.atmosphere?.descriptor}
            elevation={tacticalStatus.elevation}
            isCovered={tacticalStatus.is_behind_cover}
            facing={tacticalStatus.facing}
          />

          <div className="p-4 border-b border-stone-900">
            <div className="flex justify-between text-[9px] font-bold uppercase mb-1"><span>Integrity</span><span>{p.current_hp}/{p.max_hp}</span></div>
            <div className="h-1 bg-stone-900 w-full mb-1"><div className="h-full bg-red-900" style={{ width: `${(p.current_hp! / p.max_hp!) * 100}%` }} /></div>
          </div>
          {showDevTools && (
            <div className="p-2 space-y-1">
              <button onClick={() => setCurrentView('builder')} className="w-full py-1 text-[9px] bg-stone-900 border border-stone-800 hover:border-[#92400e] uppercase font-bold text-stone-500">Battle Builder</button>
            </div>
          )}
        </aside>

        <main className="flex-1 flex flex-col relative bg-[#030303]">
          <div className="flex-1 overflow-auto">
            {currentView === 'tavern' && <TavernHub onTravel={() => setCurrentView('world')} onRest={() => { }} onShop={() => setCurrentView('inventory')} />}
            {currentView === 'world' && <WorldMap onBack={() => setCurrentView('tavern')} onArrive={() => setCurrentView('gameplay')} />}
            {currentView === 'gameplay' && (
              <div className="h-full flex flex-col">
                <div className="flex-1 min-h-0"><Arena playerSprite={p.sprite} onLog={addLog} /></div>
                <ActionBar powers={p.powers} skills={p.skills} />
              </div>
            )}
            {currentView === 'character' && <CharacterSheet equipment={p.equipment} stats={p.stats} name={p.name} sprite={p.sprite} />}
            {currentView === 'inventory' && <InventoryPanel characterItems={p.inventory} onEquip={handleEquip} />}
            {currentView === 'builder' && <BattleBuilder onBattleStart={() => setCurrentView('gameplay')} />}
            {currentView === 'create' && <CharacterBuilder onSave={() => { loadPlayerState(); setCurrentView('tavern'); }} />}
          </div>

          <div className="h-32 border-t border-stone-900 bg-[#080808] flex flex-col shrink-0">
            <div className="px-3 py-1 bg-[#0a0a0a] border-b border-stone-900 flex items-center gap-2">
              <BookOpen size={10} className="text-[#92400e]" />
              <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-stone-600">Chronicle</span>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {systemLogs.map(log => (
                <div key={log.id} className="text-[10px] flex gap-2">
                  <span className="text-stone-700 font-mono">[{log.time}]</span>
                  <span className={`uppercase font-bold tracking-widest ${log.type === 'error' ? 'text-red-900' : 'text-stone-500'}`}>{log.source}:</span>
                  <span className="italic text-stone-400">"{log.message}"</span>
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