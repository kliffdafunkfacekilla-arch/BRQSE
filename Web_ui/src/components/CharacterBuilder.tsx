import { useState, useEffect, useMemo } from 'react';
import { User, Save, ArrowRight, ArrowLeft, CheckCircle, AlertTriangle, Book, Shield, Swords, Sparkles, Shuffle, Activity, Heart, Zap, Scroll } from 'lucide-react';

const API_BASE = '/api';

// --- Interfaces ---
interface SpeciesBase {
    Attribute: string;
    [key: string]: string;
}

interface ClassOption {
    STEP: string;
    Category: string;
    "Option Name": string;
    "Stat 1": string;
    "Stat 2": string;
    "Body Part": string;
    "Mechanic / Trait": string;
    [key: string]: string;
}

interface BackgroundOption {
    name: string;
    category: string;
    narrative: string;
    grants: string[];
}

interface BackgroundStep {
    id: string;
    title: string;
    description: string;
    options: BackgroundOption[];
}

interface Spell {
    School: string;
    Name: string;
    Tier: string;
    Description: string;
    Type: string;
    Damage_Type: string;
    Attribute: string;
}

interface Item {
    Name: string;
    Type: string;
    Related_Skill: string;
    Description: string;
    Effect: string;
    Logic_Tags: string;
    Cost: string;
}

const getGoldenRuleCap = (baseVal: number) => {
    if (baseVal >= 11) return 6;
    if (baseVal === 10) return 5;
    return 4;
};

// Base Steps (Class + Components)
const BASE_STEPS = [
    { id: 'CLASS', label: 'Ancestry' },
    { id: '1_SIZE', label: 'Stature' },
    { id: '2_BIO', label: 'Bloodline' },
    { id: '3_HEAD', label: 'Perception' },
    { id: '4_ARMS', label: 'Might' },
    { id: '5_LEGS', label: 'Agility' },
    { id: '6_BODY', label: 'Form' },
    { id: '7_SPEC', label: 'Unique Trait' }
];

interface CharacterBuilderProps {
    onSave?: (character: any) => void;
}

export default function CharacterBuilder({ onSave }: CharacterBuilderProps) {
    // --- State ---

    // Data
    const [speciesData, setSpeciesData] = useState<SpeciesBase[]>([]);
    const [classOptions, setClassOptions] = useState<ClassOption[]>([]);
    const [backgroundSteps, setBackgroundSteps] = useState<BackgroundStep[]>([]);
    const [spellData, setSpellData] = useState<Spell[]>([]);
    const [gearData, setGearData] = useState<Item[]>([]);
    const [tokenData, setTokenData] = useState<string[]>([]);

    // Flow
    const [steps, setSteps] = useState<{ id: string, label: string }[]>(BASE_STEPS);
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [loading, setLoading] = useState(true);
    const [status, setStatus] = useState('');

    // Selections
    const [name, setName] = useState('');
    const [selectedClass, setSelectedClass] = useState<string>('');

    // Phase 1: Body Components
    const [compSelections, setCompSelections] = useState<Record<string, ClassOption | null>>({});

    // Phase 2: Backgrounds
    const [bgSelections, setBgSelections] = useState<Record<string, BackgroundOption>>({});

    // Phase 3: Magic
    const [selectedSpells, setSelectedSpells] = useState<Spell[]>([]);
    useEffect(() => { console.log("Selected Spells Update:", selectedSpells); }, [selectedSpells]);

    // Phase 4: Gear
    const [selectedGear, setSelectedGear] = useState<{
        rightHand?: Item;
        leftHand?: Item;
        armor?: Item;
    }>({});

    // Phase 5: Finalize
    const [selectedToken, setSelectedToken] = useState<string>('');
    const [backstory, setBackstory] = useState('');

    // --- Loading ---

    useEffect(() => {
        const loadAll = async () => {
            try {
                const [spec, bg, sp, gr, tk] = await Promise.all([
                    fetch('/data/Species.json').then(r => r.json()),
                    fetch('/data/Backgrounds.json').then(r => r.json()),
                    fetch('/data/Spells.json').then(r => r.json()),
                    fetch('/data/Gear.json').then(r => r.json()),
                    fetch('/data/Tokens.json').then(r => r.json())
                ]);

                setSpeciesData(spec.filter((r: any) => r.Attribute));
                setBackgroundSteps(bg);
                setSpellData(sp);
                setGearData(gr);
                setTokenData(tk);

                // Build full step list
                const nSteps = [...BASE_STEPS];
                bg.forEach((b: BackgroundStep) => nSteps.push({ id: b.id, label: b.id }));
                nSteps.push({ id: 'MAGIC', label: 'Arcana' });
                nSteps.push({ id: 'GEAR', label: 'Equipment' });
                nSteps.push({ id: 'FINALIZE', label: 'Inscribe Fate' });

                setSteps(nSteps);
                setLoading(false);
            } catch (err) {
                console.error("Data load failed", err);
            }
        };
        loadAll();
    }, []);

    // Load Class Options
    useEffect(() => {
        if (!selectedClass) return;
        fetch(`/data/${selectedClass}.json`)
            .then(res => res.json())
            .then(data => {
                setClassOptions(data);
            });
    }, [selectedClass]);

    // --- Calculations ---

    const stats = useMemo(() => {
        const s: Record<string, number> = {};
        const b: Record<string, number> = {};
        const base: Record<string, number> = {};

        // Base
        speciesData.forEach(row => {
            if (row.Attribute) {
                const val = parseInt(row[selectedClass] || '10');
                s[row.Attribute] = val;
                base[row.Attribute] = val;
                b[row.Attribute] = 0;
            }
        });

        const applyMod = (stat: string, val: number) => {
            if (!stat || stat === 'None' || !s[stat]) return;
            s[stat] += val;
            b[stat] = (b[stat] || 0) + val;
        };

        // Component Bonuses
        Object.values(compSelections).forEach(opt => {
            if (!opt) return;
            if (opt.STEP === '1_SIZE') {
                [opt['Bio'], opt['Head']].forEach(str => {
                    if (!str) return;
                    str.split(',').forEach(p => {
                        const m = p.trim().match(/([+-]\d+)\s+(\w+)/);
                        if (m) applyMod(m[2], parseInt(m[1]));
                    });
                });
            } else {
                applyMod(opt['Stat 1'], 1);
                applyMod(opt['Stat 2'], 1);
            }
        });

        return { total: s, bonus: b, base };
    }, [speciesData, selectedClass, compSelections]);

    // Derived Data
    const acquiredSkills = useMemo(() => {
        const skills: string[] = [];
        Object.values(bgSelections).forEach(opt => {
            if (opt && opt.grants) {
                skills.push(opt.grants[1]); // [Category, Name]
            }
        });
        return skills;
    }, [bgSelections]);

    const physicalTraits = useMemo(() => {
        return Object.values(compSelections)
            .filter((o): o is ClassOption => o !== null)
            .map(o => ({
                name: o["Option Name"],
                part: o["Body Part"],
                effect: o["Mechanic / Trait"]
            }));
    }, [compSelections]);

    const validSpells = useMemo(() => {
        return spellData.filter(spell => {
            const attr = spell["Attribute"];
            const statVal = stats.total[attr] || stats.total[attr.toUpperCase()] || 0;
            return statVal >= 12;
        });
    }, [spellData, stats]);

    const warnings = useMemo(() => {
        const w: string[] = [];
        Object.entries(stats.bonus).forEach(([stat, val]) => {
            const cap = getGoldenRuleCap(stats.base[stat] || 10);
            if (val > cap) w.push(`${stat} +${val} exceeds cap of +${cap}`);
        });
        return w;
    }, [stats]);

    // Auto-Generate Backstory
    useEffect(() => {
        if (steps[currentStepIndex].id === 'FINALIZE' && !backstory) {
            const parts = Object.values(bgSelections).map(o => o.narrative);
            setBackstory(parts.join('\n\n'));
        }
    }, [currentStepIndex, bgSelections, backstory, steps]);

    // --- Handlers ---

    const currentStep = steps[currentStepIndex];

    const handleNext = () => {
        if (currentStepIndex < steps.length - 1) setCurrentStepIndex(p => p + 1);
    };
    const handleBack = () => {
        if (currentStepIndex > 0) setCurrentStepIndex(p => p - 1);
    };

    const saveCharacter = async () => {
        const char = {
            Name: name,
            Species: selectedClass,
            Stats: stats.total,
            Traits: [
                ...Object.values(compSelections).filter(o => o).map(o => ({
                    Name: o?.["Option Name"],
                    Type: o?.Category,
                    Effect: o?.["Mechanic / Trait"],
                    BodyPart: o?.["Body Part"]
                })),
                ...Object.values(bgSelections).map(o => ({
                    Name: o.name, // Skill Name
                    Type: o.category, // Skill Type
                    Effect: "Skill Mastery"
                }))
            ],
            Powers: selectedSpells,
            Inventory: Object.values(selectedGear).filter(i => i),
            Gear: selectedGear,
            Backstory: backstory,
            Portrait: selectedToken
        };

        try {
            await fetch(`${API_BASE}/character/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(char)
            });
            setStatus('Sealed!');
            if (onSave) onSave(char);
        } catch {
            console.log("Offline save");
            setStatus('Sealed (Offline)');
            if (onSave) onSave(char);
        }
    };

    const randomizeCharacter = async () => {
        const speciesChoices = ['Mammal', 'Reptile', 'Avian', 'Insect', 'Aquatic', 'Plant'];
        const randSpecies = speciesChoices[Math.floor(Math.random() * speciesChoices.length)];
        setSelectedClass(randSpecies);

        // Fetch component data manually to randomize immediately
        try {
            const res = await fetch(`/data/${randSpecies}.json`);
            const data: ClassOption[] = await res.json();
            setClassOptions(data);

            const newCompSelections: Record<string, ClassOption> = {};
            ['1_SIZE', '2_BIO', '3_HEAD', '4_ARMS', '5_LEGS', '6_BODY', '7_SPEC'].forEach(stepId => {
                const options = data.filter(o => o.STEP === stepId);
                if (options.length > 0) {
                    newCompSelections[stepId] = options[Math.floor(Math.random() * options.length)];
                }
            });
            setCompSelections(newCompSelections);
        } catch (err) {
            console.error("Manual randomization fetch failed", err);
        }

        // Randomize Backgrounds
        const newBgSelections: Record<string, BackgroundOption> = {};
        backgroundSteps.forEach(step => {
            if (step.options.length > 0) {
                newBgSelections[step.id] = step.options[Math.floor(Math.random() * step.options.length)];
            }
        });
        setBgSelections(newBgSelections);

        const prefixes = ['Shadow', 'Storm', 'Iron', 'Swift', 'Crimson', 'Wild', 'Stone', 'Flame', 'Frost', 'Night'];
        const suffixes = ['claw', 'fang', 'wing', 'heart', 'runner', 'striker', 'walker', 'stalker', 'hunter', 'blade'];
        const randName = prefixes[Math.floor(Math.random() * prefixes.length)] + suffixes[Math.floor(Math.random() * suffixes.length)];
        setName(randName);

        if (tokenData.length > 0) {
            setSelectedToken(tokenData[Math.floor(Math.random() * tokenData.length)]);
        }

        if (spellData.length >= 2) {
            const shuffled = [...spellData].sort(() => Math.random() - 0.5);
            setSelectedSpells(shuffled.slice(0, 2));
        }

        setCurrentStepIndex(steps.length - 1);
        setStatus('Fate has been rolled! Adjust as you see fit.');
    };

    // --- Renderers ---

    if (loading) return <div className="p-10 text-stone-500 font-serif italic tracking-wide">Consulting the ancient scrolls...</div>;

    const renderClassStep = () => (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {['Mammal', 'Reptile', 'Avian', 'Insect', 'Aquatic', 'Plant'].map(cls => (
                <button
                    key={cls}
                    onClick={() => {
                        setSelectedClass(cls);
                        setCompSelections({});
                    }}
                    className={`p-6 rounded-sm border-2 text-left transition-all hover:scale-[1.02]
                        ${selectedClass === cls ? 'border-[#b45309] bg-[#1a140f] shadow-[0_0_15px_rgba(180,83,9,0.2)]' : 'border-stone-800 bg-[#0a0a0a]'}`}
                >
                    <div className="text-xl font-serif font-bold text-stone-100 mb-2 tracking-wide uppercase">{cls}</div>
                    <div className="text-[10px] text-stone-500 font-mono tracking-widest uppercase">
                        Affinity: {speciesData.filter(r => parseInt(r[cls]) >= 11).map(r => r.Attribute).join(', ') || 'None'}
                    </div>
                </button>
            ))}
        </div>
    );

    const renderComponentOptions = () => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {classOptions.filter(o => o.STEP === currentStep.id).map((opt, i) => {
                const selected = compSelections[currentStep.id]?.["Option Name"] === opt["Option Name"];
                return (
                    <button
                        key={i}
                        onClick={() => setCompSelections(p => ({ ...p, [currentStep.id]: opt }))}
                        className={`p-4 rounded-sm border text-left flex flex-col gap-2 transition-all
                            ${selected ? 'bg-[#1a140f] border-[#b45309] shadow-inner' : 'bg-[#0a0a0a] border-stone-800 hover:border-stone-700'}`}
                    >
                        <div className="flex justify-between w-full">
                            <span className="font-serif font-bold text-stone-100 text-lg tracking-wide uppercase">{opt["Option Name"]}</span>
                            {selected && <div className="w-2 h-2 rounded-full bg-[#b45309] shadow-[0_0_8px_#b45309]" />}
                        </div>
                        {currentStep.id === '1_SIZE' ? (
                            <div className="text-[10px] space-y-1 font-mono uppercase tracking-widest">
                                <div className="text-stone-400">{opt['Bio']}</div>
                                <div className="text-red-900/80">{opt['Head']}</div>
                            </div>
                        ) : (
                            <div className="flex gap-2 text-[10px] font-mono tracking-widest uppercase">
                                <span className="text-[#b45309]">+{opt["Stat 1"]}</span>
                                <span className="text-[#b45309]">+{opt["Stat 2"]}</span>
                            </div>
                        )}
                        <div className="text-xs text-stone-400 mt-1 leading-relaxed">
                            <span className="text-[#92400e] font-bold uppercase text-[9px] mr-2 tracking-widest">[{opt["Body Part"]}]</span>
                            {opt["Mechanic / Trait"]}
                        </div>
                    </button>
                );
            })}
        </div>
    );

    const renderBackgroundStep = () => {
        const bgStep = backgroundSteps.find(b => b.id === currentStep.id);
        if (!bgStep) return null;

        return (
            <div className="space-y-4">
                <div className="text-stone-500 italic mb-4 font-serif text-sm tracking-wide">"{bgStep.description}"</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {bgStep.options.map((opt, i) => {
                        const selected = bgSelections[currentStep.id]?.name === opt.name;
                        return (
                            <button
                                key={i}
                                onClick={() => setBgSelections(p => ({ ...p, [currentStep.id]: opt }))}
                                className={`p-4 rounded-sm border text-left flex flex-col gap-2 transition-all
                                    ${selected ? 'bg-[#1a140f] border-[#b45309] shadow-inner' : 'bg-[#0a0a0a] border-stone-800 hover:border-stone-700'}`}
                            >
                                <div className="flex justify-between w-full">
                                    <span className="font-serif font-bold text-stone-100 text-lg tracking-wide uppercase">{opt.name}</span>
                                    {selected && <div className="w-2 h-2 rounded-full bg-[#b45309] shadow-[0_0_8px_#b45309]" />}
                                </div>
                                <div className="text-xs text-stone-400 font-serif italic tracking-wide leading-relaxed">{opt.narrative}</div>
                                <div className="text-[9px] bg-stone-900 border border-stone-800 px-2 py-0.5 rounded-full text-stone-600 w-fit mt-2 uppercase tracking-widest font-mono">{opt.category}</div>
                            </button>
                        );
                    })}
                </div>
            </div>
        );
    };

    const renderMagicStep = () => {
        const grouped: Record<string, Spell[]> = {};
        validSpells.forEach(s => {
            if (!grouped[s.School]) grouped[s.School] = [];
            grouped[s.School].push(s);
        });

        return (
            <div className="space-y-6">
                <div className="flex justify-between items-center bg-[#111] border border-stone-800 p-4 rounded-sm">
                    <div className="font-serif italic text-stone-500">Choose two arts you have mastered (Stat 12+ required)</div>
                    <div className="text-[#b45309] font-black tracking-widest uppercase text-xs">{selectedSpells.length} / 2 Chosen</div>
                </div>

                {Object.entries(grouped).map(([school, spells]) => (
                    <div key={school} className="space-y-2">
                        <h4 className="text-[#92400e] font-serif font-bold border-b border-stone-900 pb-1 uppercase tracking-widest text-xs">{school}</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {spells.map((spell, i) => {
                                const isSel = selectedSpells.some(s => s.Name === spell.Name);
                                return (
                                    <button
                                        key={i}
                                        onClick={() => {
                                            if (isSel) setSelectedSpells(p => p.filter(s => s.Name !== spell.Name));
                                            else if (selectedSpells.length < 2) setSelectedSpells(p => [...p, spell]);
                                        }}
                                        className={`p-3 rounded-sm border text-left transition-all h-full flex flex-col justify-between
                                            ${isSel ? 'bg-[#1a140f] border-[#b45309]' : 'bg-[#0a0a0a] border-stone-800 hover:border-stone-700'}`}
                                    >
                                        <div className="font-serif font-bold text-stone-100 mb-1 uppercase text-sm tracking-wide">{spell.Name}</div>
                                        <div className="text-stone-500 text-[11px] italic font-serif leading-relaxed">{spell.Description}</div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                ))}
                {validSpells.length === 0 && <div className="text-stone-700 font-serif italic text-center py-8 border border-dashed border-stone-800 rounded">No attributes high enough to unlock the Arcane Arts.</div>}
            </div>
        );
    };

    const renderGearStep = () => {
        const validGear = gearData.filter(item => acquiredSkills.includes(item.Related_Skill));
        const weapons = validGear.filter(i => i.Type === 'Weapon');
        const armors = validGear.filter(i => i.Type === 'Armor');

        return (
            <div className="space-y-6">
                <div className="grid grid-cols-1 gap-4">
                    <div className="bg-[#0a0a0a] p-4 rounded-sm border border-stone-800">
                        <h4 className="text-stone-100 font-serif font-bold mb-4 flex items-center gap-2 uppercase tracking-widest text-sm"><Swords size={16} className="text-[#b45309]" /> Martial Armament</h4>
                        <div className="grid grid-cols-2 gap-2">
                            {weapons.map((w, i) => (
                                <button
                                    key={i}
                                    onClick={() => setSelectedGear(p => ({ ...p, rightHand: w }))}
                                    className={`p-3 rounded-sm text-left border transition-all ${selectedGear.rightHand === w ? 'border-[#b45309] bg-[#1a140f]' : 'border-stone-800 hover:border-stone-700'}`}
                                >
                                    <div className="font-serif font-bold text-stone-100 uppercase text-xs tracking-wide">{w.Name}</div>
                                    <div className="text-stone-600 text-[10px] italic font-serif mt-1">{w.Effect}</div>
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="bg-[#0a0a0a] p-4 rounded-sm border border-stone-800">
                        <h4 className="text-stone-100 font-serif font-bold mb-4 flex items-center gap-2 uppercase tracking-widest text-sm"><Shield size={16} className="text-[#b45309]" /> Protective Garb</h4>
                        <div className="grid grid-cols-2 gap-2">
                            {armors.map((a, i) => (
                                <button
                                    key={i}
                                    onClick={() => setSelectedGear(p => ({ ...p, armor: a }))}
                                    className={`p-3 rounded-sm text-left border transition-all ${selectedGear.armor === a ? 'border-[#b45309] bg-[#1a140f]' : 'border-stone-800 hover:border-stone-700'}`}
                                >
                                    <div className="font-serif font-bold text-stone-100 uppercase text-xs tracking-wide">{a.Name}</div>
                                    <div className="text-stone-600 text-[10px] italic font-serif mt-1">{a.Effect}</div>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    const renderFinalizeStep = () => {
        return (
            <div className="space-y-6">
                <div className="bg-[#0a0a0a] p-4 rounded-sm border border-stone-800">
                    <label className="block text-stone-600 text-[10px] font-black uppercase tracking-[0.2em] mb-2">HERO'S NAME</label>
                    <input
                        value={name} onChange={e => setName(e.target.value)}
                        className="w-full bg-[#050505] border border-stone-800 p-3 text-stone-200 rounded-sm focus:border-[#b45309] outline-none font-serif tracking-widest text-lg"
                        placeholder="Inscribe Name..."
                    />
                    <label className="block text-stone-600 text-[10px] font-black uppercase tracking-[0.2em] mt-6 mb-2">CHRONICLE OF FATE</label>
                    <textarea
                        value={backstory} onChange={e => setBackstory(e.target.value)}
                        className="w-full h-40 bg-[#050505] border border-stone-800 p-3 text-stone-400 text-sm rounded-sm focus:border-[#b45309] outline-none resize-none font-serif italic leading-relaxed"
                    />
                </div>

                <div className="bg-[#0a0a0a] p-4 rounded-sm border border-stone-800 flex flex-col">
                    <label className="block text-stone-600 text-[10px] font-black uppercase tracking-[0.2em] mb-2">PORTRAIT TOKEN</label>
                    <div className="grid grid-cols-6 gap-2 h-48 overflow-auto custom-scrollbar bg-[#050505] p-2 rounded-sm border border-stone-800">
                        {tokenData.map(tk => (
                            <button
                                key={tk}
                                onClick={() => setSelectedToken(tk)}
                                className={`relative aspect-square rounded-sm overflow-hidden border-2 transition-all
                                    ${selectedToken === tk ? 'border-[#b45309] opacity-100 shadow-[0_0_10px_rgba(180,83,9,0.3)]' : 'border-transparent opacity-40 hover:opacity-70'}`}
                            >
                                <img src={`/tokens/${tk}`} alt={tk} className="w-full h-full object-cover" />
                            </button>
                        ))}
                    </div>
                </div>

                <div className="flex justify-end gap-4 p-4">
                    <button
                        onClick={saveCharacter}
                        disabled={!name || !selectedToken}
                        className="flex items-center gap-3 px-10 py-4 bg-[#b45309] text-stone-100 font-serif font-black rounded-sm hover:bg-[#92400e] transition-all disabled:opacity-30 disabled:grayscale uppercase tracking-[0.2em] shadow-lg"
                    >
                        <Scroll size={20} /> Seal Fate
                    </button>
                </div>
                {status && (
                    <div className={`text-center mt-2 font-serif font-bold italic ${status.includes('Sealed') ? 'text-green-600' : 'text-red-700 animate-pulse'}`}>
                        {status}
                    </div>
                )}
            </div>
        );
    };

    const getValidationMessage = () => {
        if (currentStep.id === 'CLASS' && !selectedClass) return "An ancestry must be chosen before fate can proceed.";
        if (BASE_STEPS.some(s => s.id === currentStep.id) && currentStep.id !== 'CLASS') {
            if (!compSelections[currentStep.id]) return "Your form is incomplete. Choose a trait.";
        }
        const bgStep = backgroundSteps.find(b => b.id === currentStep.id);
        if (bgStep && !bgSelections[currentStep.id]) return "Your past is shrouded. Select an origin.";

        if (currentStep.id === 'MAGIC') {
            const hasEnoughValid = validSpells.length >= 2;
            if (hasEnoughValid && selectedSpells.length < 2) return `You must master exactly two arts (${selectedSpells.length}/2).`;
            if (!hasEnoughValid && selectedSpells.length < validSpells.length) return `You must select all available arts you qualify for (${selectedSpells.length}/${validSpells.length}).`;
        }

        if (currentStep.id === 'GEAR' && !selectedGear.rightHand && !selectedGear.armor) return "Prepare yourself with at least steel or hide.";
        return "";
    };

    const attemptNext = () => {
        const msg = getValidationMessage();
        if (msg) {
            setStatus(msg);
            setTimeout(() => setStatus(''), 3000);
            return;
        }
        handleNext();
    };

    return (
        <div className="h-full flex flex-col bg-[#050505] text-stone-400 overflow-hidden font-serif">
            {/* Header */}
            <div className="px-6 py-4 border-b border-stone-900 flex items-center justify-between bg-[#111] shrink-0">
                <div className="flex items-center gap-3">
                    <Book className="text-[#b45309]" size={20} />
                    <div>
                        <h2 className="text-lg font-serif font-bold text-stone-100 tracking-widest uppercase">Tome of Destiny</h2>
                        <div className="text-[9px] text-stone-600 font-mono uppercase tracking-[0.3em]">Passage {currentStepIndex + 1} / {steps.length}: {currentStep.label}</div>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <button
                        onClick={randomizeCharacter}
                        className="flex items-center gap-2 px-3 py-1.5 bg-[#4c1d95]/20 border border-[#8b5cf6]/30 hover:bg-[#4c1d95]/40 text-[#a78bfa] text-[9px] font-bold rounded-sm transition-all uppercase tracking-widest"
                    >
                        <Shuffle size={12} /> Fate's Hand
                    </button>
                    <div className="flex gap-1.5">
                        {steps.map((s, i) => (
                            <div key={s.id} className={`h-1.5 w-1.5 rounded-full rotate-45 transition-all ${i === currentStepIndex ? 'bg-[#b45309] scale-125' : i < currentStepIndex ? 'bg-stone-700' : 'bg-stone-900'}`} />
                        ))}
                    </div>
                </div>
            </div>

            {/* Main Area: Two Columns */}
            <div className="flex flex-1 overflow-hidden">

                {/* LEFT: Step Editor */}
                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar border-r border-stone-900/50">
                    <div className="max-w-3xl mx-auto">
                        <div className="flex items-center gap-3 mb-8">
                            <span className="text-3xl font-black text-[#b45309] opacity-30 tracking-tighter italic">{(currentStepIndex + 1).toString().padStart(2, '0')}</span>
                            <h3 className="text-3xl font-serif font-black text-stone-100 uppercase tracking-widest">
                                {currentStep.label}
                            </h3>
                        </div>

                        {status && currentStep.id !== 'FINALIZE' && (
                            <div className="mb-6 p-4 bg-red-950/20 border-l-2 border-red-800 text-red-500 flex items-center gap-3 animate-slide-in">
                                <AlertTriangle size={16} className="shrink-0" />
                                <span className="text-[10px] font-bold uppercase tracking-widest">{status}</span>
                            </div>
                        )}

                        <div className="animate-fade-in">
                            {currentStep.id === 'CLASS' && renderClassStep()}
                            {BASE_STEPS.some(s => s.id === currentStep.id) && currentStep.id !== 'CLASS' && renderComponentOptions()}
                            {backgroundSteps.some(b => b.id === currentStep.id) && renderBackgroundStep()}
                            {currentStep.id === 'MAGIC' && renderMagicStep()}
                            {currentStep.id === 'GEAR' && renderGearStep()}
                            {currentStep.id === 'FINALIZE' && renderFinalizeStep()}
                        </div>
                    </div>
                </div>

                {/* RIGHT: Hero Preview Sidebar */}
                <aside className="w-80 bg-[#080808] p-6 flex flex-col gap-6 shrink-0 overflow-y-auto custom-scrollbar border-l border-stone-900">

                    {/* Portrait & Identity */}
                    <div className="flex flex-col items-center text-center">
                        <div className="w-32 h-40 border border-stone-800 bg-[#0a0a0a] shadow-2xl mb-4 overflow-hidden relative group p-1">
                            <div className="w-full h-full border border-stone-900 relative">
                                {selectedToken ? (
                                    <img src={`/tokens/${selectedToken}`} className="w-full h-full object-cover grayscale-[0.3] contrast-[1.1]" />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-stone-800">
                                        <User size={48} strokeWidth={1} />
                                    </div>
                                )}
                                <div className="absolute inset-0 bg-gradient-to-t from-[#050505] to-transparent" />
                            </div>
                        </div>
                        <h4 className="text-xl font-serif font-bold text-stone-100 uppercase tracking-widest truncate w-full px-2">
                            {name || "Unnamed Soul"}
                        </h4>
                        <div className="text-[10px] text-[#92400e] font-bold uppercase tracking-[0.3em] mt-1 italic">
                            {selectedClass || "Awaiting Descent"}
                        </div>
                    </div>

                    {/* Live Stats */}
                    <div className="space-y-3">
                        <div className="flex justify-between items-center border-b border-stone-900 pb-1">
                            <span className="text-[10px] font-black text-stone-600 uppercase tracking-[0.2em]">Attributes</span>
                            <span className="text-[9px] text-stone-800 font-mono font-bold uppercase tracking-widest">Intrinsic</span>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            {Object.entries(stats.total).map(([stat, val]) => {
                                const bonus = stats.bonus[stat] || 0;
                                return (
                                    <div key={stat} className="bg-[#0a0a0a] p-2 border border-stone-900 transition-colors">
                                        <span className="text-[9px] text-stone-600 uppercase font-black tracking-widest leading-none">{stat.substring(0, 3)}</span>
                                        <div className="flex items-center justify-between mt-1">
                                            <span className="text-xl font-serif font-black text-stone-200 leading-none">{val}</span>
                                            {bonus !== 0 && (
                                                <span className={`text-[9px] font-black px-1 rounded-sm ${bonus > 0 ? 'text-green-800' : 'text-red-900'}`}>
                                                    {bonus > 0 ? `+${bonus}` : bonus}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Evolutions (Physical Traits) */}
                    <div className="space-y-3">
                        <div className="text-[10px] font-black text-stone-600 uppercase border-b border-stone-900 pb-1 tracking-[0.2em]">Physical Form</div>
                        <div className="space-y-1.5 h-40 overflow-y-auto custom-scrollbar pr-1">
                            {physicalTraits.length === 0 && <div className="text-[11px] text-stone-800 italic font-serif">No traits manifested...</div>}
                            {physicalTraits.map((t, i) => (
                                <div key={i} className="flex flex-col bg-[#0a0a0a] p-2 border border-stone-900">
                                    <div className="flex justify-between items-center">
                                        <span className="text-[10px] font-bold text-stone-300 uppercase tracking-widest">{t.name}</span>
                                    </div>
                                    <div className="text-[9px] text-stone-600 leading-tight mt-1 font-serif italic">{t.effect}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Skills & Magic */}
                    <div className="space-y-3 mb-4">
                        <div className="text-[10px] font-black text-stone-600 uppercase border-b border-stone-900 pb-1 tracking-[0.2em]">Learned Arts</div>
                        <div className="flex flex-wrap gap-1.5">
                            {acquiredSkills.length === 0 && selectedSpells.length === 0 && <div className="text-[11px] text-stone-800 italic font-serif">Awaiting the awakening...</div>}
                            {acquiredSkills.map((s, i) => (
                                <div key={i} className="px-2 py-0.5 bg-stone-900 border border-stone-800 text-stone-400 text-[9px] font-bold rounded-sm uppercase tracking-widest">
                                    {s}
                                </div>
                            ))}
                            {selectedSpells.map((s, i) => (
                                <div key={i} className="px-2 py-0.5 bg-[#4c1d95]/10 border border-[#8b5cf6]/20 text-[#a78bfa] text-[9px] font-bold rounded-sm uppercase tracking-widest flex items-center gap-1">
                                    <Activity size={10} /> {s.Name}
                                </div>
                            ))}
                        </div>
                    </div>
                </aside>
            </div>

            {/* Footer: Nav Buttons */}
            <div className="px-8 py-5 bg-[#111] border-t border-stone-900 flex justify-between items-center shrink-0">
                <button
                    onClick={handleBack}
                    disabled={currentStepIndex === 0}
                    className="flex items-center gap-2 px-6 py-2 text-stone-600 hover:text-stone-300 disabled:opacity-30 transition-colors uppercase font-black text-[10px] tracking-[0.4em]"
                >
                    <ArrowLeft size={16} /> Retreat
                </button>

                <div className="flex items-center gap-4">
                    <button
                        onClick={attemptNext}
                        className={`flex items-center gap-2 px-12 py-3 font-serif font-black rounded-sm transition-all uppercase tracking-[0.4em] text-xs
                            ${currentStepIndex === steps.length - 1
                                ? 'hidden'
                                : 'bg-[#1a140f] text-stone-300 border border-stone-800 hover:border-[#b45309] hover:text-[#b45309] shadow-lg'}`}
                    >
                        Advance <ArrowRight size={16} />
                    </button>
                    {currentStepIndex === steps.length - 1 && (
                        <div className="text-[10px] text-[#92400e] animate-pulse font-serif font-bold tracking-[0.2em] italic uppercase">The chronicle awaits your seal</div>
                    )}
                </div>
            </div>
        </div>
    );
}
