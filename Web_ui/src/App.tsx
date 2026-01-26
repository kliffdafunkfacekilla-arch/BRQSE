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
import SkillsPanel from './components/SkillsPanel';
import BattleBuilder from './components/BattleBuilder';
import CharacterBuilder from './components/CharacterBuilder';
import MainMenu from './components/MainMenu';
import TavernHub from './components/TavernHub';
import WorldMap from './components/WorldMap';
import ChaosHUD from './components/ChaosHUD';
import HeroSelector from './components/HeroSelector';
import DiceLog from './components/DiceLog';
import SceneStack from './components/SceneStack';

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
  sp?: number; max_sp?: number;
  fp?: number; max_fp?: number;
  cmp?: number; max_cmp?: number;
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
  const [currentView, setCurrentView] = useState<'start' | 'tavern' | 'world' | 'gameplay' | 'character' | 'inventory' | 'journal' | 'skills' | 'builder' | 'create' | 'selector'>('start');
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
  const [engineState, setEngineState] = useState<any>(null);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 2000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        setApiOnline(true);
        fetchData();
      } else {
        setApiOnline(false);
      }
    } catch {
      setApiOnline(false);
    }
  };

  const fetchData = async () => {
    try {
      // 1. Fetch Game State (Events, Journal, Grid)
      const res = await fetch('/api/game/state');
      const data = await res.json();
      setEngineState(data);

      if (data.event === 'QUEST_COMPLETE' && currentView === 'gameplay') {
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
    setSystemLogs(prev => [{ id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, source, message, type, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 30));
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

  const [activeAbility, setActiveAbility] = useState<string | null>(null);

  // ... (existing state)

  const handleAbilityAction = async (abilityName: string) => {
    // Check if ability requires a target
    const instantActions = ['wait', 'rest', 'channel', 'defend', 'search', 'track'];
    if (!instantActions.includes(abilityName.toLowerCase())) {
      setActiveAbility(abilityName);
      addLog('COMBAT', `Select target for ${abilityName}...`, 'info');
      return;
    }

    try {
      const res = await fetch('/api/game/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: abilityName.toLowerCase() })
      });
      const data = await res.json();
      if (data.result && data.result.log) {
        addLog('ACTION', data.result.log);
      }
      fetchData();
    } catch (e) {
      addLog('SYSTEM', 'Failed to channel power', 'error');
    }
  };

  useEffect(() => {
    if (currentView === 'world' || currentView === 'gameplay' || currentView === 'character' || currentView === 'inventory' || currentView === 'journal' || currentView === 'skills') {
      const interval = setInterval(fetchData, 1000);
      return () => clearInterval(interval);
    }
  }, [currentView]);

  if (currentView === 'start') {
    return (
      <div className="h-screen w-screen bg-[#050505] text-stone-400 font-serif flex flex-col overflow-hidden">
        <MainMenu onStart={() => setCurrentView('selector')} onCreate={() => setCurrentView('create')} />
      </div>
    );
  }

  if (currentView === 'selector') {
    return (
      <div className="h-screen w-screen bg-[#050505] text-stone-400 font-serif flex flex-col overflow-hidden">
        <HeroSelector
          onSelect={() => { loadPlayerState(); setCurrentView('tavern'); }}
          onCreate={() => setCurrentView('create')}
          onBack={() => setCurrentView('start')}
        />
      </div>
    );
  }

  const p = playerState ? {
    ...playerState,
    skills: playerState.skills || [],
    powers: playerState.powers || [],
    inventory: playerState.inventory || [],
    equipment: playerState.equipment || {},
    stats: playerState.stats || {},
  } : {
    name: "Awaiting Soul",
    species: "Unknown",
    stats: {},
    equipment: {},
    inventory: [],
    powers: [],
    skills: [],
    sprite: "badger_front.png",
    max_hp: 20,
    current_hp: 20,
    sp: 10, max_sp: 10,
    fp: 10, max_fp: 10,
    cmp: 10, max_cmp: 10
  };

  const isQuestActive = engineState && engineState.quest_progress && engineState.quest_progress !== "0/0";

  return (
    <div className="h-screen w-screen bg-[#050505] text-stone-400 font-serif flex flex-col overflow-hidden">
      <header className="h-12 border-b border-stone-900 bg-[#0a0a0a] flex items-center justify-between px-4 shrink-0 z-50">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${apiOnline ? 'bg-[#92400e]' : 'bg-red-950'}`} />
            <span className="text-xs font-bold uppercase tracking-widest text-stone-200">Shadowfall Chronicles</span>
          </div>
          <nav className="flex gap-1 bg-black border border-stone-800 p-1 rounded-sm">
            <button
              onClick={() => setCurrentView('gameplay')}
              className={`px-4 py-1 text-[10px] font-bold uppercase transition-all ${currentView === 'gameplay' ? 'bg-[#92400e] text-white' : 'text-stone-600 hover:text-white'}`}
            >
              World View
            </button>
            <button
              onClick={() => setCurrentView('character')}
              className={`px-4 py-1 text-[10px] font-bold uppercase transition-all ${currentView === 'character' ? 'bg-[#92400e] text-white' : 'text-stone-600 hover:text-white'}`}
            >
              Character Sheet
            </button>
            <button
              onClick={() => setCurrentView('inventory')}
              className={`px-4 py-1 text-[10px] font-bold uppercase transition-all ${currentView === 'inventory' ? 'bg-[#92400e] text-white' : 'text-stone-600 hover:text-white'}`}
            >
              Inventory
            </button>
            <button
              onClick={() => setCurrentView('skills')}
              className={`px-4 py-1 text-[10px] font-bold uppercase transition-all ${currentView === 'skills' ? 'bg-[#92400e] text-white' : 'text-stone-600 hover:text-white'}`}
            >
              Skills
            </button>
            <button
              onClick={() => setCurrentView('journal')}
              className={`px-4 py-1 text-[10px] font-bold uppercase transition-all ${currentView === 'journal' ? 'bg-[#92400e] text-white' : 'text-stone-600 hover:text-white'}`}
            >
              Journal
            </button>
          </nav>
        </div>

        <div className="flex gap-3 items-center">
          {/* SYSTEM ACTIONS */}
          <button
            onClick={async () => {
              if (!p) return;
              await fetch('/api/character/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(p)
              });
              addLog('SYSTEM', 'Game Saved Successfully');
            }}
            className="text-stone-500 hover:text-green-500 transition-colors"
            title="Save Game"
          >
            <Settings size={14} />
          </button>

          <button
            onClick={async () => {
              await fetch('/api/world/quest/generate', { method: 'POST' }); // Force regen/reset
              addLog('SYSTEM', 'Quest Reset Initiated');
              fetchData();
            }}
            className="text-stone-500 hover:text-red-500 transition-colors"
            title="Force New Quest"
          >
            <Swords size={14} />
          </button>

          {(!isQuestActive || engineState?.event === 'QUEST_COMPLETE') && (
            <button
              onClick={() => setCurrentView('tavern')}
              className="px-3 py-1 bg-stone-900 border border-stone-800 text-[10px] font-bold uppercase text-stone-400 hover:text-white hover:border-[#92400e] transition-colors"
            >
              Return to Tavern
            </button>
          )}
          <button onClick={() => setShowDevTools(!showDevTools)} className={`transition-colors ${showDevTools ? 'text-[#92400e]' : 'text-stone-800 hover:text-white'}`}><Eye size={14} /></button>
          <button onClick={() => setCurrentView('start')} className="text-stone-800 hover:text-red-900"><Power size={14} /></button>
        </div>
      </header >

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

          <ChaosHUD
            chaosLevel={worldStatus.chaos_level}
            chaosClock={worldStatus.chaos_clock}
            tensionThreshold={worldStatus.tension_threshold}
            atmosphere={worldStatus.atmosphere?.descriptor}
            elevation={tacticalStatus.elevation}
            isCovered={tacticalStatus.is_behind_cover}
            facing={tacticalStatus.facing}
          />

          <div className="p-4 border-b border-stone-900 space-y-3">
            {/* HP - Integrity */}
            <div>
              <div className="flex justify-between text-[9px] font-bold uppercase mb-1"><span>Integrity</span><span>{p.current_hp}/{p.max_hp}</span></div>
              <div className="h-1 bg-stone-900 w-full"><div className="h-full bg-red-900" style={{ width: `${(p.current_hp! / p.max_hp!) * 100}%` }} /></div>
            </div>

            {/* SP - Stamina */}
            <div>
              <div className="flex justify-between text-[9px] font-bold uppercase mb-1 text-stone-400"><span>Stamina</span><span>{p.sp}/{p.max_sp}</span></div>
              <div className="h-1 bg-stone-900 w-full"><div className="h-full bg-green-700" style={{ width: `${(p.sp! / p.max_sp!) * 100}%` }} /></div>
            </div>

            {/* FP - Focus */}
            <div>
              <div className="flex justify-between text-[9px] font-bold uppercase mb-1 text-stone-400"><span>Focus</span><span>{p.fp}/{p.max_fp}</span></div>
              <div className="h-1 bg-stone-900 w-full"><div className="h-full bg-blue-700" style={{ width: `${(p.fp! / p.max_fp!) * 100}%` }} /></div>
            </div>

            {/* CMP - Composure */}
            <div>
              <div className="flex justify-between text-[9px] font-bold uppercase mb-1 text-stone-400"><span>Composure</span><span>{p.cmp}/{p.max_cmp}</span></div>
              <div className="h-1 bg-stone-900 w-full"><div className="h-full bg-purple-900" style={{ width: `${(p.cmp! / p.max_cmp!) * 100}%` }} /></div>
            </div>
          </div>
          {showDevTools && (
            <div className="p-2 space-y-1">
              <button onClick={() => setCurrentView('builder')} className="w-full py-1 text-[9px] bg-stone-900 border border-stone-800 hover:border-[#92400e] uppercase font-bold text-stone-500">Battle Builder</button>
              <button onClick={() => setCurrentView('world')} className="w-full py-1 text-[9px] bg-stone-900 border border-stone-800 hover:border-[#92400e] uppercase font-bold text-stone-400">Force World Map</button>
            </div>
          )}
          <div className="flex-1 min-h-0 border-t border-stone-900">
            <DiceLog logs={engineState?.dice_log || []} />
          </div>
        </aside>

        <main className="flex-1 flex flex-col relative bg-[#030303]">
          <div className="flex-1 overflow-auto">
            {currentView === 'tavern' && <TavernHub onTravel={() => setCurrentView('world')} onRest={() => { }} onShop={() => setCurrentView('inventory')} />}
            {currentView === 'world' && <WorldMap onBack={() => setCurrentView('tavern')} onArrive={() => setCurrentView('gameplay')} />}
            {currentView === 'gameplay' && (
              <div className="h-full flex flex-col relative group">
                {/* FORCE OVERLAY: z-50 to sit above Arena canvas */}
                <div className="absolute top-0 left-0 w-full h-full z-50 pointer-events-none">
                  <SceneStack onLog={addLog} />
                </div>

                <div className="flex-1 min-h-0 relative z-0">
                  <Arena playerSprite={p.sprite} onLog={addLog} activeAbility={activeAbility} onAbilityComplete={() => setActiveAbility(null)} />
                </div>

                <div className="relative z-50">
                  <ActionBar
                    powers={p.powers}
                    skills={p.skills}
                    onAction={(name) => handleAbilityAction(name)}
                  />
                </div>
              </div>
            )}
            {currentView === 'character' && (
              <CharacterSheet
                equipment={p.equipment}
                stats={p.stats}
                name={p.name}
                sprite={p.sprite}
                powers={p.powers}
                skills={p.skills}
              />
            )}
            {currentView === 'inventory' && <InventoryPanel characterItems={p.inventory} onEquip={handleEquip} />}
            {currentView === 'skills' && <SkillsPanel skills={p.skills} powers={p.powers} />}
            {currentView === 'journal' && (
              <Journal
                entries={engineState?.journal || []}
                questTitle={engineState?.quest_title}
                questDescription={engineState?.quest_description}
                questProgress={engineState?.quest_progress}
                questObjective={engineState?.quest_objective}
              />
            )}
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
    </div >
  );
}

export default App;