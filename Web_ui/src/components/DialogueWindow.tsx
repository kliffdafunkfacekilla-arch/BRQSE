
import { useState, useEffect, useRef } from 'react';
import { MessageSquare, X, Send, User } from 'lucide-react';

interface DialogueWindowProps {
    speaker: string;
    text: string;
    archetype?: string;
    onReply: (text: string) => void;
    onClose: () => void;
}

export default function DialogueWindow({ speaker, text, archetype, onReply, onClose }: DialogueWindowProps) {
    const [reply, setReply] = useState("");
    const [history, setHistory] = useState<{ speaker: string, text: string }[]>([]);
    const inputRef = useRef<HTMLInputElement>(null);

    // Reset history when speaker changes (new conversation)
    useEffect(() => {
        setHistory([{ speaker, text }]);
    }, [speaker, text]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!reply.trim()) return;

        // Optimistic UI update? 
        // Or just let parent handle it. The backend will return the NEXT chunk.
        // But for visual continuity, let's append our reply locally first.
        const myReply = reply;
        setHistory(prev => [...prev, { speaker: "Me", text: myReply }]);
        setReply("");

        onReply(myReply);
    };

    useEffect(() => {
        if (inputRef.current) inputRef.current.focus();
    }, [history]);

    return (
        <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
            <div className="w-full max-w-2xl bg-[#0a0a0a] border border-stone-700 shadow-[0_0_50px_rgba(0,0,0,0.5)] flex flex-col overflow-hidden">

                {/* Header */}
                <div className="bg-stone-900 p-4 border-b border-stone-800 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-stone-800 rounded-full flex items-center justify-center border border-stone-600">
                            <User size={20} className="text-stone-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-white uppercase tracking-wider">{speaker}</h3>
                            {archetype && <span className="text-xs text-[#92400e] font-bold uppercase tracking-widest">{archetype}</span>}
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-stone-800 rounded-full transition-colors">
                        <X size={20} className="text-stone-500 hover:text-white" />
                    </button>
                </div>

                {/* Body (History) */}
                <div className="flex-1 p-6 space-y-4 max-h-[60vh] overflow-y-auto bg-[#0c0c0c]">
                    {history.map((msg, i) => (
                        <div key={i} className={`flex ${msg.speaker === 'Me' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[80%] p-4 rounded-lg border ${msg.speaker === 'Me'
                                    ? 'bg-stone-900 border-stone-700 text-stone-300'
                                    : 'bg-[#1a1a1a] border-[#92400e]/30 text-white shadow-lg'
                                }`}>
                                {msg.speaker !== 'Me' && i === history.length - 1 && (
                                    <MessageSquare size={16} className="text-[#92400e] mb-2" />
                                )}
                                <p className="font-serif text-lg leading-relaxed italic">"{msg.text}"</p>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Footer (Input) */}
                <form onSubmit={handleSubmit} className="p-4 bg-stone-900 border-t border-stone-800 flex gap-2">
                    <input
                        ref={inputRef}
                        type="text"
                        value={reply}
                        onChange={(e) => setReply(e.target.value)}
                        placeholder="Type your response..."
                        className="flex-1 bg-black border border-stone-700 p-3 text-white focus:border-[#92400e] focus:outline-none font-serif"
                    />
                    <button
                        type="submit"
                        className="px-6 bg-[#92400e] hover:bg-[#b45309] text-white font-bold uppercase tracking-wide transition-colors flex items-center gap-2"
                    >
                        <span>Reply</span>
                        <Send size={16} />
                    </button>
                </form>

            </div>
        </div>
    );
}
