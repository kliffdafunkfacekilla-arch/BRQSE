import { Sword, Zap, Shield, Heart, Sparkles, Activity } from 'lucide-react';

interface ActionBarProps {
    powers?: any[];
    skills?: any[];
    onAction?: (action: string) => void;
}

export default function ActionBar({ powers = [], skills = [], onAction }: ActionBarProps) {
    // Combine base actions with character powers and skills
    const actions = [
        { icon: Sword, label: 'Attack', hotkey: '1', color: 'hover:border-red-500' },
        ...powers.filter(p => p.active).map((p, i) => ({
            icon: Sparkles,
            label: p.name,
            hotkey: (i + 2).toString(),
            color: 'hover:border-yellow-500'
        })),
        ...skills.filter(s => s.active).map((s, i) => ({
            icon: Activity,
            label: s.name,
            hotkey: (powers.length + i + 2).toString(),
            color: 'hover:border-stone-500'
        })),
        { icon: Shield, label: 'Defend', hotkey: '7', color: 'hover:border-blue-500' },
        { icon: Zap, label: 'Channel', hotkey: 'C', color: 'hover:border-purple-500' },
        { icon: Heart, label: 'Wait', hotkey: '8', color: 'hover:border-green-500' },
    ];

    return (
        <div className="h-16 bg-[#0a0a0a] border-t border-stone-800 flex items-center justify-center gap-2 px-4 shrink-0">
            {actions.map((action, i) => (
                <button
                    key={i}
                    onClick={() => onAction && onAction(action.label)}
                    className={`min-w-[48px] h-12 bg-stone-900 border border-stone-700 ${action.color} transition-all flex flex-col items-center justify-center gap-1 group px-2 relative`}
                    title={action.label}
                >
                    <action.icon size={18} className="text-stone-400 group-hover:text-white" />
                    <span className="text-[8px] text-stone-300 font-mono font-bold uppercase truncate max-w-[40px] text-center">{action.label}</span>
                    <span className="text-[8px] text-stone-600 font-mono absolute top-0.5 right-1">{action.hotkey}</span>
                </button>
            ))}
        </div>
    );
}
