import { Sword, Zap, Shield, Heart, Sparkles, Activity } from 'lucide-react';

interface ActionBarProps {
    powers?: string[];
    skills?: string[];
}

export default function ActionBar({ powers = [], skills = [] }: ActionBarProps) {
    // Combine base actions with character powers
    const actions = [
        { icon: Sword, label: 'Attack', hotkey: '1', color: 'hover:border-red-500' },
        ...powers.map((p, i) => ({
            icon: Sparkles,
            label: p,
            hotkey: (i + 2).toString(),
            color: 'hover:border-yellow-500'
        })),
        { icon: Shield, label: 'Defend', hotkey: '7', color: 'hover:border-blue-500' },
        { icon: Heart, label: 'Heal', hotkey: '8', color: 'hover:border-green-500' },
    ];

    return (
        <div className="h-16 bg-[#0a0a0a] border-t border-stone-800 flex items-center justify-center gap-2 px-4 shrink-0">
            {actions.map((action, i) => (
                <button
                    key={i}
                    className={`min-w-[48px] h-12 bg-stone-900 border border-stone-700 ${action.color} transition-all flex flex-col items-center justify-center gap-1 group px-2`}
                    title={action.label}
                >
                    <action.icon size={18} className="text-stone-400 group-hover:text-white" />
                    <span className="text-[8px] text-stone-200 font-mono font-bold uppercase truncate max-w-[40px] text-center">{action.label}</span>
                    <span className="text-[8px] text-stone-600 font-mono absolute top-0.5 right-1">{action.hotkey}</span>
                </button>
            ))}
        </div>
    );
}
