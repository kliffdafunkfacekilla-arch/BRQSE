import { Sword, Zap, Shield, Heart } from 'lucide-react';

export default function ActionBar() {
    const actions = [
        { icon: Sword, label: 'Attack', hotkey: '1', color: 'hover:border-red-500' },
        { icon: Zap, label: 'Ability', hotkey: '2', color: 'hover:border-yellow-500' },
        { icon: Shield, label: 'Defend', hotkey: '3', color: 'hover:border-blue-500' },
        { icon: Heart, label: 'Heal', hotkey: '4', color: 'hover:border-green-500' },
    ];

    return (
        <div className="h-16 bg-[#0a0a0a] border-t border-stone-800 flex items-center justify-center gap-2 px-4">
            {actions.map((action, i) => (
                <button
                    key={i}
                    className={`w-12 h-12 bg-stone-900 border border-stone-700 ${action.color} transition-colors flex flex-col items-center justify-center gap-1 group`}
                    title={action.label}
                >
                    <action.icon size={18} className="text-stone-400 group-hover:text-white" />
                    <span className="text-[8px] text-stone-600 font-mono">{action.hotkey}</span>
                </button>
            ))}
        </div>
    );
}
