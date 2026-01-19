import React, { useState } from 'react';
import Arena from './components/Arena';
import { Sword, Shield, Heart, Zap, Eye, Brain, FileMusic as Muscle, Users, Dice6, Backpack, Map, Settings, Crown, Flame, Scroll, TreePine, Rabbit, Bird, Turtle, Bug, Leaf, Fish, Ear, Skull, DoorClosed as Nose, Hand, Feather, TreeDeciduous, Waves, User, CircleDot, Hexagon, Footprints, Anchor, Cat, Scale, Wheat, Sparkles, Star, Dumbbell, Activity, Plus, Target, Gauge, Move, Zap as Lightning, Mountain, Lightbulb, Compass, Smile, Focus, Swords, ShieldCheck, Battery, HeartPulse, Crosshair, Navigation, Frown, Wind, Timer, Shuffle, UserCheck, Zap as Psychic, Swords as Attack, Shield as Defense, Gauge as Stamina, Heart as HealthPoints, Target as FocusIcon, Move as Movement, Frown as Fatigue, Send, MessageSquare, Terminal, MapPin, Maximize2 } from 'lucide-react';

interface CharacterStats {
  health: number;
  maxHealth: number;
  mana: number;
  maxMana: number;
  strength: number;
  dexterity: number;
  intelligence: number;
  wisdom: number;
  constitution: number;
  charisma: number;
  level: number;
  experience: number;
  gold: number;
}

interface ChatMessage {
  id: string;
  user: string;
  message: string;
  timestamp: Date;
  type: 'player' | 'dm' | 'system';
}

interface LogEntry {
  id: string;
  message: string;
  timestamp: Date;
  type: 'info' | 'warning' | 'error' | 'success';
}

function App() {
  const [chatMessage, setChatMessage] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { id: '1', user: 'DM', message: 'Welcome to the Whispering Caverns...', timestamp: new Date(), type: 'dm' },
    { id: '2', user: 'Thorin', message: 'I ready my sword and shield', timestamp: new Date(), type: 'player' },
    { id: '3', user: 'System', message: 'Roll for initiative', timestamp: new Date(), type: 'system' },
  ]);

  const [systemLogs, setSystemLogs] = useState<LogEntry[]>([
    { id: '1', message: 'Connected to server', timestamp: new Date(), type: 'success' },
    { id: '2', message: 'Character sheet loaded', timestamp: new Date(), type: 'info' },
    { id: '3', message: 'Map data synced', timestamp: new Date(), type: 'info' },
  ]);

  const character: CharacterStats = {
    health: 85,
    maxHealth: 100,
    mana: 42,
    maxMana: 60,
    strength: 16,
    dexterity: 14,
    intelligence: 12,
    wisdom: 15,
    constitution: 18,
    charisma: 10,
    level: 7,
    experience: 2850,
    gold: 347
  };

  const sendMessage = () => {
    if (chatMessage.trim()) {
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        user: 'Thorin',
        message: chatMessage,
        timestamp: new Date(),
        type: 'player'
      };
      setChatMessages([...chatMessages, newMessage]);
      setChatMessage('');
    }
  };

  const StatBar = ({ current, max, color, icon: Icon }: { current: number; max: number; color: string; icon: React.ElementType }) => (
    <div className="flex items-center gap-2 mb-2">
      <Icon className="w-4 h-4 text-purple-400" />
      <div className="flex-1">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-stone-300">{current}/{max}</span>
          <span className="text-stone-400">{Math.round((current / max) * 100)}%</span>
        </div>
        <div className="h-2 bg-stone-800 rounded-full overflow-hidden border border-stone-700">
          <div
            className={`h-full transition-all duration-500 ${color} shadow-glow`}
            style={{ width: `${(current / max) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-dungeon text-stone-100 font-sans flex flex-col">
      {/* Background texture overlay */}
      <div className="fixed inset-0 opacity-10 pointer-events-none bg-noise" />

      {/* Header */}
      <header className="border-b border-stone-800 bg-stone-900/50 backdrop-blur-sm z-10">
        <div className="px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Crown className="w-6 h-6 text-purple-400 glow-icon" />
              <h1 className="text-lg font-bold text-purple-400 glow-text font-medieval tracking-wider">
                SHADOWFALL CHRONICLES
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <Settings className="w-5 h-5 text-stone-400 hover:text-purple-400 transition-colors cursor-pointer" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Character Info */}
        <aside className="w-80 border-r border-stone-800 bg-stone-900/30 overflow-y-auto">
          <div className="p-4">
            {/* Character Portrait & Basic Info */}
            <div className="stone-panel p-4 mb-4">
              <div className="text-center mb-4">
                <div className="w-16 h-16 mx-auto mb-3 bg-gradient-to-b from-purple-600 to-purple-800 rounded-full flex items-center justify-center border-4 border-purple-400 glow-border">
                  <Crown className="w-8 h-8 text-purple-100" />
                </div>
                <h2 className="text-lg font-bold text-purple-300 glow-text font-medieval">Thorin Ironforge</h2>
                <p className="text-stone-400 text-sm">Dwarven Paladin</p>
                <div className="flex justify-center gap-3 mt-2 text-xs">
                  <span className="text-purple-400">Level {character.level}</span>
                  <span className="text-stone-400">•</span>
                  <span className="text-green-400">{character.gold} Gold</span>
                </div>
              </div>

              <div className="space-y-1">
                <StatBar current={character.health} max={character.maxHealth} color="bg-red-500" icon={Heart} />
                <StatBar current={character.mana} max={character.maxMana} color="bg-blue-500" icon={Zap} />
              </div>

              <div className="mt-4 pt-3 border-t border-stone-700">
                <div className="text-xs text-stone-400 mb-1">Experience</div>
                <div className="h-2 bg-stone-800 rounded-full overflow-hidden border border-stone-700">
                  <div
                    className="h-full bg-gradient-to-r from-purple-600 to-purple-400 glow-purple"
                    style={{ width: '75%' }}
                  />
                </div>
                <div className="text-xs text-stone-400 mt-1">{character.experience}/3000 XP</div>
              </div>
            </div>

            {/* Attributes */}
            <div className="stone-panel p-4 mb-4">
              <h3 className="text-sm font-bold text-purple-300 glow-text mb-3 font-medieval">ATTRIBUTES</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="stat-item p-2">
                  <Muscle className="w-4 h-4 text-red-400 mb-1 mx-auto" />
                  <div className="text-xs text-stone-400">STR</div>
                  <div className="text-lg font-bold text-red-300 glow-stat">{character.strength}</div>
                </div>
                <div className="stat-item p-2">
                  <Eye className="w-4 h-4 text-green-400 mb-1 mx-auto" />
                  <div className="text-xs text-stone-400">DEX</div>
                  <div className="text-lg font-bold text-green-300 glow-stat">{character.dexterity}</div>
                </div>
                <div className="stat-item p-2">
                  <Brain className="w-4 h-4 text-blue-400 mb-1 mx-auto" />
                  <div className="text-xs text-stone-400">INT</div>
                  <div className="text-lg font-bold text-blue-300 glow-stat">{character.intelligence}</div>
                </div>
                <div className="stat-item p-2">
                  <Scroll className="w-4 h-4 text-purple-400 mb-1 mx-auto" />
                  <div className="text-xs text-stone-400">WIS</div>
                  <div className="text-lg font-bold text-purple-300 glow-stat">{character.wisdom}</div>
                </div>
                <div className="stat-item p-2">
                  <Shield className="w-4 h-4 text-yellow-400 mb-1 mx-auto" />
                  <div className="text-xs text-stone-400">CON</div>
                  <div className="text-lg font-bold text-yellow-300 glow-stat">{character.constitution}</div>
                </div>
                <div className="stat-item p-2">
                  <Flame className="w-4 h-4 text-orange-400 mb-1 mx-auto" />
                  <div className="text-xs text-stone-400">CHA</div>
                  <div className="text-lg font-bold text-orange-300 glow-stat">{character.charisma}</div>
                </div>
              </div>
            </div>

            {/* Combat Stats */}
            <div className="stone-panel p-4 mb-4">
              <h3 className="text-sm font-bold text-purple-300 glow-text mb-3 font-medieval">COMBAT</h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center p-2 bg-stone-800/50 rounded border border-stone-700">
                  <div className="flex items-center gap-2">
                    <Sword className="w-3 h-3 text-red-400" />
                    <span className="text-xs text-stone-300">Attack</span>
                  </div>
                  <span className="text-sm font-bold text-red-300 glow-stat">+8</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-stone-800/50 rounded border border-stone-700">
                  <div className="flex items-center gap-2">
                    <Shield className="w-3 h-3 text-blue-400" />
                    <span className="text-xs text-stone-300">AC</span>
                  </div>
                  <span className="text-sm font-bold text-blue-300 glow-stat">18</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-stone-800/50 rounded border border-stone-700">
                  <div className="flex items-center gap-2">
                    <Eye className="w-3 h-3 text-green-400" />
                    <span className="text-xs text-stone-300">Init</span>
                  </div>
                  <span className="text-sm font-bold text-green-300 glow-stat">+2</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="stone-panel p-4">
              <h3 className="text-sm font-bold text-purple-300 glow-text mb-3 font-medieval">QUICK ACTIONS</h3>
              <div className="grid grid-cols-2 gap-2">
                <button className="stone-button p-2 text-xs">
                  <Dice6 className="w-3 h-3 mx-auto mb-1" />
                  ROLL
                </button>
                <button className="stone-button p-2 text-xs">
                  <Backpack className="w-3 h-3 mx-auto mb-1" />
                  ITEMS
                </button>
                <button className="stone-button p-2 text-xs">
                  <Sword className="w-3 h-3 mx-auto mb-1" />
                  ATTACK
                </button>
                <button className="stone-button p-2 text-xs">
                  <Shield className="w-3 h-3 mx-auto mb-1" />
                  DEFEND
                </button>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          {/* Map View */}
          {/* Map View */}
          <main className="flex-1 relative bg-stone-900/20">
            <div className="absolute inset-0 flex items-center justify-center">
              <Arena />
            </div>
          </main>

          {/* Bottom Section */}
          <div className="flex border-t border-stone-800">
            {/* Chat Interface */}
            <div className="flex-1 bg-stone-900/30">
              <div className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <MessageSquare className="w-4 h-4 text-purple-400" />
                  <h3 className="text-sm font-bold text-purple-300 glow-text font-medieval">PARTY CHAT</h3>
                </div>

                {/* Chat Messages */}
                <div className="h-32 overflow-y-auto mb-3 space-y-2">
                  {chatMessages.map(msg => (
                    <div key={msg.id} className="text-sm">
                      <span className={`font-semibold ${msg.type === 'dm' ? 'text-purple-400' :
                        msg.type === 'system' ? 'text-blue-400' : 'text-green-400'
                        }`}>
                        {msg.user}:
                      </span>
                      <span className="text-stone-300 ml-2">{msg.message}</span>
                    </div>
                  ))}
                </div>

                {/* Chat Input */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Type your message..."
                    className="flex-1 px-3 py-2 bg-stone-800 border border-stone-700 rounded text-stone-300 text-sm focus:border-purple-500 focus:outline-none"
                  />
                  <button
                    onClick={sendMessage}
                    className="stone-button px-3 py-2"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* System Log */}
            <div className="w-80 border-l border-stone-800 bg-stone-900/50">
              <div className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Terminal className="w-4 h-4 text-purple-400" />
                  <h3 className="text-sm font-bold text-purple-300 glow-text font-medieval">SYSTEM LOG</h3>
                </div>

                <div className="h-32 overflow-y-auto space-y-1">
                  {systemLogs.map(log => (
                    <div key={log.id} className="text-xs">
                      <span className="text-stone-500">
                        {log.timestamp.toLocaleTimeString()}
                      </span>
                      <span className={`ml-2 ${log.type === 'success' ? 'text-green-400' :
                        log.type === 'warning' ? 'text-yellow-400' :
                          log.type === 'error' ? 'text-red-400' : 'text-blue-400'
                        }`}>
                        {log.message}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;