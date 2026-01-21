import { useState, useEffect, useMemo } from 'react';
import { User, Save, ArrowRight, ArrowLeft, CheckCircle, AlertTriangle, Book, Shield, Swords, Sparkles } from 'lucide-react';

const API_BASE = 'http://localhost:5001/api';

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
    { id: 'CLASS', label: 'Class' },
    { id: '1_SIZE', label: 'Size' },
    { id: '2_BIO', label: 'Ancestry' },
    { id: '3_HEAD', label: 'Senses' },
    { id: '4_ARMS', label: 'Arms' },
    { id: '5_LEGS', label: 'Legs' },
    { id: '6_BODY', label: 'Body' },
    { id: '7_SPEC', label: 'Special' }
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
                nSteps.push({ id: 'MAGIC', label: 'Magic' });
                nSteps.push({ id: 'GEAR', label: 'Gear' });
                nSteps.push({ id: 'FINALIZE', label: 'Finalize' });

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
                setCompSelections({});
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

        // Background Bonuses? (Currently Backgrounds grant Skills, not Stats, based on CSVs)
        // Check Grants? No stat bonuses in the current generated JSON structure for Backgrounds.

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
        if (currentStep.id === 'FINALIZE' && !backstory) {
            const parts = Object.values(bgSelections).map(o => o.narrative);
            setBackstory(parts.join('\n\n'));
        }
    }, [currentStepIndex, bgSelections, backstory]);

    // --- Handlers ---

    const currentStep = steps[currentStepIndex];

    const canProceed = () => {
        if (currentStep.id === 'CLASS') return !!selectedClass;

        // Component Steps
        if (BASE_STEPS.some(s => s.id === currentStep.id) && currentStep.id !== 'CLASS') {
            return !!compSelections[currentStep.id];
        }

        // Background Steps
        const bgStep = backgroundSteps.find(b => b.id === currentStep.id);
        if (bgStep) {
            return !!bgSelections[currentStep.id];
        }

        // Magic
        if (currentStep.id === 'MAGIC') {
            return selectedSpells.length === 2;
        }

        // Gear
        if (currentStep.id === 'GEAR') {
            // Arbitrary requirement: at least 1 item?
            return selectedGear.rightHand || selectedGear.armor;
        }

        return true;
    };

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
            setStatus('Saved!');
            if (onSave) onSave(char);
        } catch {
            console.log("Offline save");
            setStatus('Saved (Offline)');
            if (onSave) onSave(char);
        }
    };

    // --- Renderers ---

    if (loading) return <div className="p-10 text-stone-500">Loading Builder Data...</div>;

    const renderClassStep = () => (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {['Mammal', 'Reptile', 'Avian', 'Insect', 'Aquatic', 'Plant'].map(cls => (
                <button
                    key={cls}
                    onClick={() => setSelectedClass(cls)}
                    className={`p-6 rounded-lg border-2 text-left transition-all hover:scale-[1.02]
                        ${selectedClass === cls ? 'border-[#66fcf1] bg-[#1f2833]' : 'border-stone-800 bg-stone-900'}`}
                >
                    <div className="text-xl font-bold text-white mb-2">{cls}</div>
                    <div className="text-xs text-stone-400">
                        High: {speciesData.filter(r => parseInt(r[cls]) >= 11).map(r => r.Attribute).join(', ') || 'None'}
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
                        className={`p-4 rounded border text-left flex flex-col gap-2 transition-all
                            ${selected ? 'bg-[#1f2833] border-[#66fcf1] ring-1 ring-[#66fcf1]' : 'bg-stone-900 border-stone-800 hover:bg-stone-800'}`}
                    >
                        <div className="flex justify-between w-full">
                            <span className="font-bold text-white text-lg">{opt["Option Name"]}</span>
                            {selected && <CheckCircle size={18} className="text-[#66fcf1]" />}
                        </div>
                        {currentStep.id === '1_SIZE' ? (
                            <div className="text-xs space-y-1">
                                <div className="text-green-400">{opt['Bio']}</div>
                                <div className="text-red-400">{opt['Head']}</div>
                            </div>
                        ) : (
                            <div className="flex gap-2 text-xs">
                                <span className="text-[#66fcf1]">+{opt["Stat 1"]}</span>
                                <span className="text-[#66fcf1]">+{opt["Stat 2"]}</span>
                            </div>
                        )}
                        <div className="text-sm text-stone-300 mt-1">
                            <span className="text-stone-500 font-bold uppercase text-[10px] mr-2">{opt["Body Part"]}</span>
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
                <div className="text-stone-400 italic mb-4">{bgStep.description}</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {bgStep.options.map((opt, i) => {
                        const selected = bgSelections[currentStep.id]?.name === opt.name;
                        return (
                            <button
                                key={i}
                                onClick={() => setBgSelections(p => ({ ...p, [currentStep.id]: opt }))}
                                className={`p-4 rounded border text-left flex flex-col gap-2 transition-all
                                    ${selected ? 'bg-[#1f2833] border-[#66fcf1] ring-1 ring-[#66fcf1]' : 'bg-stone-900 border-stone-800 hover:bg-stone-800'}`}
                            >
                                <div className="flex justify-between w-full">
                                    <span className="font-bold text-white text-lg">{opt.name}</span>
                                    {selected && <CheckCircle size={18} className="text-[#66fcf1]" />}
                                </div>
                                <div className="text-sm text-stone-300">{opt.narrative}</div>
                                <div className="text-xs bg-stone-800 px-2 py-1 rounded text-stone-500 w-fit mt-2">{opt.category}</div>
                            </button>
                        );
                    })}
                </div>
            </div>
        );
    };

    const renderMagicStep = () => {
        // Filter spells by Schools where Stat >= 12
        // School -> Attribute in Schools of Power.csv?
        // Wait, generated Spells.json has "Attribute" key?
        // My generator script copied ALL rows from CSV.
        // Schools of Power.csv has "Attribute" (e.g. "Might" for Mass).

        const validSpells = spellData.filter(spell => {
            const attr = spell["Attribute"]; // Case sensitive? CSV had "Attribute"
            // stats keys are uppercase (MIGHT, etc) from Species.csv?
            // Species.csv had UPPERCASE headers? Let's check logic.
            // calculateStats uses row.Attribute.
            // Let's assume title case or upper.
            // Just case-insensitive match
            const statVal = stats.total[attr.toUpperCase()] || stats.total[attr] || 0;
            return statVal >= 12;
        });

        // Group by School
        const grouped: Record<string, Spell[]> = {};
        validSpells.forEach(s => {
            if (!grouped[s.School]) grouped[s.School] = [];
            grouped[s.School].push(s);
        });

        return (
            <div className="space-y-6">
                <div className="flex justify-between items-center bg-stone-900 p-4 rounded">
                    <div>Select 2 Spells (Schools with Stat 12+)</div>
                    <div className="text-[#66fcf1] font-bold">{selectedSpells.length} / 2 Selected</div>
                </div>

                {Object.entries(grouped).map(([school, spells]) => (
                    <div key={school} className="space-y-2">
                        <h4 className="text-[#66fcf1] font-bold border-b border-stone-800 pb-1">{school}</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                            {spells.map((spell, i) => {
                                const isSel = selectedSpells.includes(spell);
                                return (
                                    <button
                                        key={i}
                                        onClick={() => {
                                            if (isSel) setSelectedSpells(p => p.filter(s => s !== spell));
                                            else if (selectedSpells.length < 2) setSelectedSpells(p => [...p, spell]);
                                        }}
                                        className={`p-3 rounded border text-left text-sm transition-all h-full flex flex-col justify-between
                                            ${isSel ? 'bg-[#1f2833] border-[#66fcf1]' : 'bg-stone-900 border-stone-800 hover:border-stone-600'}`}
                                    >
                                        <div className="font-bold text-white mb-1">{spell.Name}</div>
                                        <div className="text-stone-400 text-xs">{spell.Description}</div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                ))}
                {validSpells.length === 0 && <div className="text-stone-500">No Stats &ge; 12 to unlock Magic Schools.</div>}
            </div>
        );
    };

    const renderGearStep = () => {
        // Filter items where Related_Skill is in acquiredSkills
        const validGear = gearData.filter(item => acquiredSkills.includes(item.Related_Skill));
        const weapons = validGear.filter(i => i.Type === 'Weapon');
        const armors = validGear.filter(i => i.Type === 'Armor');

        return (
            <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Right Hand */}
                    <div className="bg-stone-900 p-4 rounded border border-stone-800">
                        <h4 className="text-white font-bold mb-4 flex items-center gap-2"><Swords size={16} /> Right Hand</h4>
                        <div className="space-y-2 h-64 overflow-auto custom-scrollbar">
                            {weapons.map((w, i) => (
                                <button
                                    key={i}
                                    onClick={() => setSelectedGear(p => ({ ...p, rightHand: w }))}
                                    className={`w-full p-2 rounded text-left text-xs border ${selectedGear.rightHand === w ? 'border-[#66fcf1] bg-[#1f2833]' : 'border-stone-800'}`}
                                >
                                    <div className="font-bold text-white">{w.Name}</div>
                                    <div className="text-stone-500">{w.Effect}</div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Left Hand */}
                    <div className="bg-stone-900 p-4 rounded border border-stone-800">
                        <h4 className="text-white font-bold mb-4 flex items-center gap-2"><Shield size={16} /> Left Hand / Off</h4>
                        <div className="space-y-2 h-64 overflow-auto custom-scrollbar">
                            <button
                                onClick={() => setSelectedGear(p => ({ ...p, leftHand: undefined }))}
                                className={`w-full p-2 text-stone-500 italic text-xs border ${!selectedGear.leftHand ? 'border-stone-500' : 'border-transparent'}`}
                            >Empty</button>
                            {weapons.map((w, i) => (
                                <button
                                    key={i}
                                    onClick={() => setSelectedGear(p => ({ ...p, leftHand: w }))}
                                    className={`w-full p-2 rounded text-left text-xs border ${selectedGear.leftHand === w ? 'border-[#66fcf1] bg-[#1f2833]' : 'border-stone-800'}`}
                                >
                                    <div className="font-bold text-white">{w.Name}</div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Armor */}
                    <div className="bg-stone-900 p-4 rounded border border-stone-800">
                        <h4 className="text-white font-bold mb-4 flex items-center gap-2"><div className="w-4 h-4 bg-stone-600 rounded-sm" /> Armor</h4>
                        <div className="space-y-2 h-64 overflow-auto custom-scrollbar">
                            {armors.map((a, i) => (
                                <button
                                    key={i}
                                    onClick={() => setSelectedGear(p => ({ ...p, armor: a }))}
                                    className={`w-full p-2 rounded text-left text-xs border ${selectedGear.armor === a ? 'border-[#66fcf1] bg-[#1f2833]' : 'border-stone-800'}`}
                                >
                                    <div className="font-bold text-white">{a.Name}</div>
                                    <div className="text-stone-500">{a.Effect}</div>
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
                {/* Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-stone-900 p-4 rounded border border-stone-800">
                        <label className="block text-stone-500 text-xs font-bold mb-2">HERO NAME</label>
                        <input
                            value={name} onChange={e => setName(e.target.value)}
                            className="w-full bg-black border border-stone-700 p-2 text-white rounded focus:border-[#66fcf1] outline-none"
                            placeholder="Enter Name..."
                        />
                        <label className="block text-stone-500 text-xs font-bold mt-4 mb-2">BACKSTORY</label>
                        <textarea
                            value={backstory} onChange={e => setBackstory(e.target.value)}
                            className="w-full h-40 bg-black border border-stone-700 p-2 text-stone-300 text-sm rounded focus:border-[#66fcf1] outline-none resize-none"
                        />
                    </div>

                    {/* Portrait */}
                    <div className="bg-stone-900 p-4 rounded border border-stone-800 flex flex-col">
                        <label className="block text-stone-500 text-xs font-bold mb-2">PORTRAIT TOKEN</label>
                        <div className="flex-1 overflow-auto bg-black p-2 rounded border border-stone-800 grid grid-cols-4 gap-2 h-64 custom-scrollbar">
                            {tokenData.map(tk => (
                                <button
                                    key={tk}
                                    onClick={() => setSelectedToken(tk)}
                                    className={`relative aspect-square rounded overflow-hidden border-2 transition-all
                                        ${selectedToken === tk ? 'border-[#66fcf1] opacity-100' : 'border-transparent opacity-50 hover:opacity-80'}`}
                                >
                                    <img src={`/tokens/${tk}`} alt={tk} className="w-full h-full object-cover" />
                                </button>
                            ))}
                        </div>
                        {selectedToken && (
                            <div className="mt-4 flex items-center gap-4">
                                <img src={`/tokens/${selectedToken}`} className="w-16 h-16 rounded-full border border-stone-600" />
                                <div className="text-white text-sm">{selectedToken}</div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Summary Stats */}
                <div className="bg-stone-900 p-4 rounded border border-stone-800">
                    <div className="grid grid-cols-6 gap-2">
                        {Object.entries(stats.total).map(([k, v]) => (
                            <div key={k} className="text-center p-2 bg-black rounded">
                                <div className="text-[10px] text-stone-500 uppercase">{k.substring(0, 3)}</div>
                                <div className="text-xl font-bold text-white">{v}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Save */}
                <div className="flex justify-end gap-4 overflow-x-auto">
                    <button
                        onClick={() => {
                            if (!name) {
                                setStatus("Please enter a name.");
                                return;
                            }
                            if (!selectedToken) {
                                setStatus("Please select a portrait token.");
                                return;
                            }
                            saveCharacter();
                        }}
                        className="flex items-center gap-2 px-8 py-4 bg-[#66fcf1] text-black font-bold rounded hover:bg-[#45a29e] transition-all"
                    >
                        <Save /> Create Hero
                    </button>
                </div>
                {status && (
                    <div className={`text-center mt-2 font-bold ${status.includes('Saved') ? 'text-green-400' : 'text-red-400 animate-pulse'}`}>
                        {status}
                    </div>
                )}
            </div>
        );
    };

    // --- Main Render Switch ---

    // Validation Message
    const getValidationMessage = () => {
        if (currentStep.id === 'CLASS' && !selectedClass) return "Select a Species to continue.";

        if (BASE_STEPS.some(s => s.id === currentStep.id) && currentStep.id !== 'CLASS') {
            if (!compSelections[currentStep.id]) return "Make a selection to continue.";
        }

        const bgStep = backgroundSteps.find(b => b.id === currentStep.id);
        if (bgStep && !bgSelections[currentStep.id]) return "Choose an option to continue.";

        if (currentStep.id === 'MAGIC') {
            if (selectedSpells.length !== 2) return `Select exactly 2 spells (${selectedSpells.length}/2).`;
        }

        if (currentStep.id === 'GEAR') {
            if (!selectedGear.rightHand && !selectedGear.armor) return "Select at least a Weapon or Armor.";
        }

        return "";
    };

    const attemptNext = () => {
        const msg = getValidationMessage();
        if (msg) {
            setStatus(msg);
            // Clear status after 3 seconds
            setTimeout(() => setStatus(''), 3000);
            return;
        }
        setStatus('');
        handleNext();
    };

    return (
        <div className="h-full flex flex-col bg-[#0b0c10] text-stone-300">
            {/* Header */}
            <div className="p-4 border-b border-stone-800 flex items-center justify-between bg-[#1f2833]">
                <div className="flex items-center gap-3">
                    <User className="text-[#66fcf1]" />
                    <div>
                        <h2 className="text-lg font-bold text-white">Character Builder</h2>
                        <div className="text-[10px] text-stone-400">Phase {Math.floor(currentStepIndex / 5) + 1}: {currentStep.label}</div>
                    </div>
                </div>
                <div className="flex gap-0.5 max-w-[50%] overflow-hidden">
                    {steps.map((s, i) => (
                        <div
                            key={s.id}
                            className={`h-1.5 w-4 rounded-sm transition-all ${i === currentStepIndex ? 'bg-[#66fcf1] w-6' : i < currentStepIndex ? 'bg-[#45a29e]' : 'bg-stone-800'
                                }`}
                        />
                    ))}
                </div>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-auto p-6">
                <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                    <span className="text-[#66fcf1] opacity-50">{(currentStepIndex + 1).toString().padStart(2, '0')}</span>
                    {currentStep.label}
                </h3>

                {status && currentStep.id !== 'FINALIZE' && (
                    <div className="mb-4 p-3 bg-red-900/50 border border-red-500 text-white rounded text-center font-bold animate-pulse">
                        <AlertTriangle className="inline mr-2 -mt-1" size={16} />
                        {status}
                    </div>
                )}

                {currentStep.id === 'CLASS' && renderClassStep()}
                {BASE_STEPS.some(s => s.id === currentStep.id) && currentStep.id !== 'CLASS' && renderComponentOptions()}
                {backgroundSteps.some(b => b.id === currentStep.id) && renderBackgroundStep()}
                {currentStep.id === 'MAGIC' && renderMagicStep()}
                {currentStep.id === 'GEAR' && renderGearStep()}
                {currentStep.id === 'FINALIZE' && renderFinalizeStep()}
            </div>

            {/* Navigation */}
            <div className="p-4 bg-[#1f2833] border-t border-stone-800 flex justify-between items-center">
                <button
                    onClick={handleBack}
                    disabled={currentStepIndex === 0}
                    className="flex items-center gap-2 px-4 py-2 text-stone-400 hover:text-white disabled:opacity-30 disabled:hover:text-stone-400 transition-colors"
                >
                    <ArrowLeft size={16} /> Back
                </button>

                <div className="flex items-center gap-4">
                    <button
                        onClick={attemptNext}
                        className={`flex items-center gap-2 px-6 py-2 font-bold rounded transition-all
                            ${currentStepIndex === steps.length - 1
                                ? 'bg-stone-700 text-stone-500 cursor-not-allowed hidden'
                                : 'bg-[#66fcf1] text-black hover:bg-[#45a29e]'}`}
                    >
                        Next <ArrowRight size={16} />
                    </button>
                </div>
            </div>
        </div>
    );

}
