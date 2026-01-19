
"use client";

import { useState, useEffect } from "react";
import { DataLoader, Species, Skill } from "../../lib/DataLoader";
import Link from 'next/link';

interface Trait {
    Category: string;
    Option: string;
    "Choice Name": string;
    "Body Part": string;
    "Stat 1": string;
    "Stat 2": string;
    [key: string]: any;
}

interface BackgroundItem {
    Attribute?: string;
    "Skill Name"?: string;
    "The Armor"?: string;
    "The Weapon"?: string;
    Description?: string;
    "Description (The Reaction)"?: string;
    // For Armor Groups (Adulthood)
    "Family Name"?: string;
    Effect?: string;
    [key: string]: any;
}

interface MagicAbility {
    School: string;
    Attribute: string;
    Tier: string;
    Type: string;
    Name: string;
    Damage_Type: string;
    Description: string;
}

export default function WizardProp() {
    const [step, setStep] = useState(1);
    const TOTAL_STEPS = 6;

    // --- DATA ---
    const [speciesList, setSpeciesList] = useState<Species[]>([]);
    const [traitOptions, setTraitOptions] = useState<Trait[]>([]);
    const [availableSkills, setAvailableSkills] = useState<Skill[]>([]);

    const [socialOrigin, setSocialOrigin] = useState<BackgroundItem[]>([]);
    const [socialEdu, setSocialEdu] = useState<BackgroundItem[]>([]);
    const [socialAdult, setSocialAdult] = useState<BackgroundItem[]>([]);

    const [weaponGroups, setWeaponGroups] = useState<any[]>([]);
    const [toolTypes, setToolTypes] = useState<any[]>([]);
    const [utilitySkills, setUtilitySkills] = useState<any[]>([]);

    const [magicAbilities, setMagicAbilities] = useState<MagicAbility[]>([]);
    const [gearList, setGearList] = useState<any[]>([]);

    // --- USER SELECTION ---
    const [charName, setCharName] = useState("Subject_01");
    const [selectedSpecies, setSelectedSpecies] = useState<Species | null>(null);
    const [selectedTraits, setSelectedTraits] = useState<Trait[]>([]);

    const [bgOrigin, setBgOrigin] = useState<BackgroundItem | null>(null);
    const [bgEdu, setBgEdu] = useState<BackgroundItem | null>(null);
    const [bgAdult, setBgAdult] = useState<BackgroundItem | null>(null);

    // Phase 3 Extensions
    const [selectedSpeciesSkill, setSelectedSpeciesSkill] = useState<Skill | null>(null);
    const [selectedMelee, setSelectedMelee] = useState<string | null>(null);
    const [selectedRanged, setSelectedRanged] = useState<string | null>(null);
    const [selectedUtility, setSelectedUtility] = useState<string | null>(null);
    const [selectedTool, setSelectedTool] = useState<string | null>(null);

    // Phase 4 Magic
    const [selectedSpells, setSelectedSpells] = useState<MagicAbility[]>([]);

    // Phase 5 Gear
    const [gold, setGold] = useState(100);
    const [inventory, setInventory] = useState<string[]>([]);

    // Load Initial Data
    useEffect(() => {
        DataLoader.loadSpecies().then(setSpeciesList);
        DataLoader.loadSocialOrigin().then(setSocialOrigin);
        DataLoader.loadSocialEducation().then(setSocialEdu);
        DataLoader.loadSocialAdulthood().then(setSocialAdult); // Now Armor Groups
        DataLoader.loadMagicSchools().then(setMagicAbilities);
        DataLoader.loadWeaponGroups().then(setWeaponGroups);
        DataLoader.loadToolTypes().then(setToolTypes);
        DataLoader.loadGear().then(setGearList);
        DataLoader.loadAllSkills().then(data => {
            setUtilitySkills(data.filter((s: any) => s.Type === "Utility"));
        });
    }, []);

    // Load Traits/Skills when Species matches state
    useEffect(() => {
        if (selectedSpecies) {
            const spName = selectedSpecies.Species;
            DataLoader.loadJSON<Trait>(`${spName}.json`).then(data => {
                setTraitOptions(data.filter(t => t["Choice Name"]));
            });
            DataLoader.loadSpeciesSkills(spName).then(setAvailableSkills);
        }
    }, [selectedSpecies]);

    // --- STAT CALCULATION ---
    const calculateStats = () => {
        const base: any = {
            Might: 0, Reflexes: 0, Vitality: 0, Endurance: 0, Finesse: 0, Fortitude: 0,
            Will: 0, Logic: 0, Awareness: 0, Knowledge: 0, Charm: 0, Intuition: 0
        };

        if (selectedSpecies) {
            Object.keys(base).forEach(key => {
                if ((selectedSpecies as any)[key]) base[key] = Number((selectedSpecies as any)[key]);
            });
        }

        selectedTraits.forEach(t => {
            if (t["Stat 1"] && base[t["Stat 1"]] !== undefined) base[t["Stat 1"]] += 1;
            if (t["Stat 2"] && base[t["Stat 2"]] !== undefined) base[t["Stat 2"]] += 1;
            // Aliases
            if (t["Stat 1"] === "Reflex") base["Reflexes"] += 1;
            if (t["Stat 2"] === "Reflex") base["Reflexes"] += 1;
            if (t["Stat 1"] === "Will") base["Will"] = (base["Will"] || 0) + 1;
            if (t["Stat 2"] === "Will") base["Will"] = (base["Will"] || 0) + 1;
            if (t["Stat 1"] === "Endure") base["Endurance"] += 1;
            if (t["Stat 2"] === "Endure") base["Endurance"] += 1;
        });

        const stats = { ...base, Willpower: base.Will || 0, Endurance: base.Endurance || 0 };

        const hp = 10 + stats.Might + stats.Reflexes + stats.Vitality;
        const cmp = 10 + stats.Willpower + stats.Logic + stats.Awareness;
        const sp = stats.Endurance + stats.Finesse + stats.Fortitude;
        const fp = stats.Knowledge + stats.Charm + stats.Intuition;
        const rawSpeed = (stats.Vitality + stats.Willpower);
        const speed = Math.ceil(rawSpeed / 5) * 5 + 20;

        return { stats, derived: { hp, cmp, sp, fp, speed } };
    };

    const currentStats = calculateStats();

    // --- RENDERERS ---

    // Step 1: Species & Name
    const renderSpeciesStep = () => (
        <div className="animate-[fadeIn_0.5s_ease-out]">
            <div className="glass-panel p-6 mb-8 max-w-xl mx-auto border border-[#00f2ff]/30">
                <label className="text-sm text-[#00f2ff] uppercase font-bold tracking-widest mb-2 block">Designation (Name)</label>
                <input
                    type="text"
                    value={charName}
                    onChange={e => setCharName(e.target.value)}
                    className="w-full bg-black/50 border border-gray-700 p-4 text-xl text-white focus:border-[#00f2ff] outline-none"
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {speciesList.map((sp) => (
                    <div
                        key={sp.Species}
                        onClick={() => { setSelectedSpecies(sp); setSelectedTraits([]); }}
                        className={`glass-panel p-6 cursor-pointer transition transform hover:scale-105 ${selectedSpecies?.Species === sp.Species ? 'border-[#00f2ff] shadow-[0_0_15px_rgba(0,242,255,0.4)]' : 'hover:border-white/30'}`}
                    >
                        <div className="h-40 bg-black/40 mb-4 rounded-lg flex items-center justify-center text-4xl">
                            {sp.Species ? sp.Species[0] : "?"}
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">{sp.Species || "Unknown Entity"}</h3>
                        <div className="text-sm text-gray-400 space-y-1">
                            <p><span className="text-[#00f2ff]">Might:</span> {sp.Might} | <span className="text-[#00f2ff]">Reflex:</span> {sp.Reflexes}</p>
                            <p><span className="text-[#00f2ff]">Endure:</span> {sp.Endurance}</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    // Step 2: Evolution & Species Skill
    const renderEvolutionStep = () => {
        const categories = Array.from(new Set(traitOptions.map(t => t.Category))).filter(Boolean);
        const validSpSkills = availableSkills.filter(s => {
            // Only show skills if we have the required body part
            // Note: JSON might have "Required Body Part" or "Body Part"
            const req = s["Body Part"] || s["Required Body Part"];
            if (!req) return false;
            // Check if any selected trait grants this body part
            return selectedTraits.some(t => t["Body Part"] === req);
        });

        return (
            <div className="space-y-8 animate-[fadeIn_0.5s_ease-out] pb-20">
                <div className="glass-panel p-4 mb-6 sticky top-0 z-40 bg-[#050510]/90 backdrop-blur-xl border-[#00f2ff]/30 shadow-lg">
                    <div className="flex justify-between items-center">
                        <h2 className="text-xl font-bold text-[#00f2ff]">Biology</h2>
                        <div className={`text-xl font-mono font-bold ${selectedTraits.length === 6 ? 'text-[#00f2ff]' : 'text-gray-500'}`}>{selectedTraits.length} / 6</div>
                    </div>
                    <div className="w-full bg-gray-800 h-2 mt-2 rounded-full overflow-hidden">
                        <div className="bg-[#00f2ff] h-full transition-all duration-300" style={{ width: `${(selectedTraits.length / 6) * 100}%` }}></div>
                    </div>
                </div>

                {categories.map(cat => (
                    <div key={cat}>
                        <h3 className="text-lg font-bold text-gray-400 mb-3 border-b border-gray-700 pb-1">{cat}</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {traitOptions.filter(t => t.Category === cat).map((trait, idx) => {
                                const isSelected = selectedTraits.some(t => t["Choice Name"] === trait["Choice Name"]);
                                return (
                                    <div key={idx}
                                        onClick={() => {
                                            if (isSelected) setSelectedTraits(prev => prev.filter(t => t["Choice Name"] !== trait["Choice Name"]));
                                            else if (selectedTraits.length < 6) setSelectedTraits(prev => [...prev, trait]);
                                        }}
                                        className={`glass-panel p-4 cursor-pointer transition-all border relative overflow-hidden ${isSelected ? 'border-[#bd00ff] bg-[#bd00ff]/10' : 'border-transparent hover:border-gray-500'}`}
                                    >
                                        {isSelected && <div className="absolute top-0 right-0 p-1 bg-[#bd00ff] text-xs font-bold text-black">EQUIPPED</div>}
                                        <h4 className="font-bold text-gray-200">{trait["Choice Name"]}</h4>
                                        <span className="text-xs font-mono bg-black/40 px-2 py-1 rounded text-gray-400 mb-2 inline-block">{trait["Body Part"]}</span>
                                        <div className="text-xs text-gray-400 mb-2">
                                            <span className="bg-gray-800 px-2 rounded font-bold text-white">+1 {trait["Stat 1"]} {trait["Stat 2"] ? `& ${trait["Stat 2"]}` : ""}</span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                ))}

                {/* SPECIES SKILL SELECTOR (Unlocks when traits selected) */}
                {selectedTraits.length >= 1 && (
                    <div className="mt-12 pt-8 border-t border-gray-800">
                        <h3 className="text-2xl font-bold text-white mb-4 title-gradient">Species Ability</h3>
                        <p className="text-gray-400 mb-4">Select one special ability enabled by your physiology.</p>
                        {validSpSkills.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {validSpSkills.map((s, idx) => (
                                    <div key={idx}
                                        onClick={() => setSelectedSpeciesSkill(s)}
                                        className={`glass-panel p-4 cursor-pointer border ${selectedSpeciesSkill === s ? 'border-[#00f2ff] bg-[#00f2ff]/20' : 'border-gray-700'}`}
                                    >
                                        <h4 className="font-bold text-white">{s["Skill Name"]}</h4>
                                        <div className="text-xs text-[#00f2ff] mb-1">Requires: {s["Body Part"] || s["Required Body Part"]}</div>
                                        <p className="text-xs text-gray-400">{s["Effect Description"]}</p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-red-400 italic">No special abilities available for your current body parts.</div>
                        )}
                    </div>
                )}
            </div>
        );
    };

    // Step 3: Social & Training
    const renderProfessionStep = () => {
        return (
            <div className="space-y-12 animate-[fadeIn_0.5s_ease-out] pb-24">
                <div className="glass-panel p-6 mb-8 bg-gradient-to-r from-[#050510] to-[#1a1a3a]">
                    <h2 className="text-3xl font-bold title-gradient mb-2">Social & Training</h2>
                </div>

                {/* 1. ORIGIN */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-1 border-r border-gray-800 pr-4">
                        <h3 className="text-xl font-bold text-[#00f2ff] mb-4">Origin</h3>
                        <div className="space-y-2">
                            {socialOrigin.map((item, idx) => (
                                <div key={idx} onClick={() => setBgOrigin(item)}
                                    className={`p-3 cursor-pointer border rounded ${bgOrigin === item ? 'border-[#00f2ff] bg-[#00f2ff]/10' : 'border-gray-700 hover:bg-gray-800'}`}
                                >
                                    <div className="font-bold text-white text-sm">{item["Skill Name"]}</div>
                                    <div className="text-xs text-gray-500">{item["The Armor"]}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* 2. EDUCATION */}
                    <div className="lg:col-span-1 border-r border-gray-800 pr-4">
                        <h3 className="text-xl font-bold text-[#bd00ff] mb-4">Education</h3>
                        <div className="space-y-2">
                            {socialEdu.map((item, idx) => (
                                <div key={idx} onClick={() => setBgEdu(item)}
                                    className={`p-3 cursor-pointer border rounded ${bgEdu === item ? 'border-[#bd00ff] bg-[#bd00ff]/10' : 'border-gray-700 hover:bg-gray-800'}`}
                                >
                                    <div className="font-bold text-white text-sm">{item["Skill Name"]}</div>
                                    <div className="text-xs text-gray-500">{item["The Weapon"]}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* 3. ADULTHOOD (Armor) */}
                    <div className="lg:col-span-1">
                        <h3 className="text-xl font-bold text-[#ffae00] mb-4">Adulthood (Armor)</h3>
                        <div className="space-y-2">
                            {socialAdult.map((item, idx) => (
                                <div key={idx} onClick={() => setBgAdult(item)}
                                    className={`p-3 cursor-pointer border rounded ${bgAdult === item ? 'border-[#ffae00] bg-[#ffae00]/10' : 'border-gray-700 hover:bg-gray-800'}`}
                                >
                                    <div className="font-bold text-white text-sm">{item["Family Name"]}</div>
                                    <div className="text-xs text-gray-500">{item.Effect?.slice(0, 50)}...</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 4. TRAINING (Weapons) */}
                <div className="pt-8 border-t border-gray-800">
                    <h3 className="text-2xl font-bold text-white mb-6">Combat Training</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                            <h4 className="text-[#00f2ff] mb-2 uppercase text-sm">Melee Proficiency</h4>
                            <div className="grid grid-cols-2 gap-2">
                                {weaponGroups.filter(w => w.Type === "Melee").map((w, i) => (
                                    <button key={i} onClick={() => setSelectedMelee(w["Family Name"])}
                                        className={`text-left p-2 text-xs border ${selectedMelee === w["Family Name"] ? 'border-[#00f2ff] bg-[#00f2ff]/20 text-white' : 'border-gray-700 text-gray-400'}`}
                                    >
                                        {w["Family Name"]}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div>
                            <h4 className="text-[#00f2ff] mb-2 uppercase text-sm">Ranged Proficiency</h4>
                            <div className="grid grid-cols-2 gap-2">
                                {weaponGroups.filter(w => w.Type === "Ranged").map((w, i) => (
                                    <button key={i} onClick={() => setSelectedRanged(w["Family Name"])}
                                        className={`text-left p-2 text-xs border ${selectedRanged === w["Family Name"] ? 'border-[#00f2ff] bg-[#00f2ff]/20 text-white' : 'border-gray-700 text-gray-400'}`}
                                    >
                                        {w["Family Name"]}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* 5. EXPERTISE (Utility/Tools) */}
                <div className="pt-8 border-t border-gray-800">
                    <h3 className="text-2xl font-bold text-white mb-6">Expertise</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                            <h4 className="text-[#bd00ff] mb-2 uppercase text-sm">Utility Skill</h4>
                            <select
                                className="w-full bg-black border border-gray-700 text-gray-300 p-2 text-sm"
                                onChange={(e) => setSelectedUtility(e.target.value)}
                                value={selectedUtility || ""}
                            >
                                <option value="">Select Ability...</option>
                                {utilitySkills.map((s, i) => (
                                    <option key={i} value={s["Skill Name"]}>{s["Skill Name"]} ({s["Attribute"]})</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <h4 className="text-[#bd00ff] mb-2 uppercase text-sm">Tool Proficiency</h4>
                            <select
                                className="w-full bg-black border border-gray-700 text-gray-300 p-2 text-sm"
                                onChange={(e) => setSelectedTool(e.target.value)}
                                value={selectedTool || ""}
                            >
                                <option value="">Select Tool...</option>
                                {toolTypes.map((t, i) => (
                                    <option key={i} value={t["Tool_Name"]}>{t["Tool_Name"]} ({t["Attribute"]})</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    // Step 4: Magic (Spell Selection)
    const renderMagicStep = () => {
        // Filter spells: Tier 1 AND Player Stat >= 12
        const validSpells = magicAbilities.filter(m => {
            if (m.Tier !== "1") return false;
            const attr = m.Attribute;
            const playerStat = (currentStats.stats as any)[attr] || 0;
            return playerStat >= 12;
        });

        return (
            <div className="space-y-8 animate-[fadeIn_0.5s_ease-out] pb-20">
                <div className="glass-panel p-6 mb-8 bg-gradient-to-r from-[#050510] to-[#1a1a3a] border border-[#ffae00]/50">
                    <h2 className="text-3xl font-bold title-gradient mb-2">Arcane Alignment</h2>
                    <p className="text-gray-400">Select exactly 2 Tier 1 Abilities. Validated against your attributes (Must be 12+).</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {validSpells.map((spell, idx) => {
                        const isSelected = selectedSpells.some(s => s.Name === spell.Name);
                        return (
                            <div key={idx}
                                onClick={() => {
                                    if (isSelected) {
                                        setSelectedSpells(prev => prev.filter(s => s.Name !== spell.Name));
                                    } else if (selectedSpells.length < 2) {
                                        setSelectedSpells(prev => [...prev, spell]);
                                    }
                                }}
                                className={`glass-panel p-4 cursor-pointer border relative ${isSelected ? 'border-[#ffae00] bg-[#ffae00]/10' : 'border-gray-700 hover:border-gray-500'}`}
                            >
                                {isSelected && <div className="absolute top-0 right-0 p-1 bg-[#ffae00] text-black font-bold text-xs">SELECTED</div>}
                                <h4 className="font-bold text-white">{spell.Name}</h4>
                                <div className="text-xs text-[#ffae00] mb-2">{spell.School} • {spell.Type} • {spell.Attribute}</div>
                                <p className="text-xs text-gray-400">{spell.Description}</p>
                            </div>
                        );
                    })}
                </div>
                {validSpells.length === 0 && (
                    <div className="text-center text-red-500 text-xl mt-12">
                        Neural Check Failed: No attributes meet the minimum requirement (12) for Tier 1 programs.
                    </div>
                )}
            </div>
        );
    };

    // Step 5: Gear Shop (NEW)
    const renderGearStep = () => {
        const toggleBuy = (item: any) => {
            const name = item["Name"] || item["Item"];
            const cost = Number((item["Cost"] || item["Value"] || "0").replace(/[^0-9]/g, "")) || 0;

            if (inventory.includes(name)) {
                // Sell
                setInventory(inv => inv.filter(i => i !== name));
                setGold(g => g + cost);
            } else {
                // Buy
                if (gold >= cost) {
                    setInventory(inv => [...inv, name]);
                    setGold(g => g - cost);
                }
            }
        };

        return (
            <div className="space-y-8 animate-[fadeIn_0.5s_ease-out] pb-20">
                <div className="glass-panel p-6 mb-4 sticky top-0 z-40 bg-[#050510]/95 border-b border-[#00f2ff]">
                    <div className="flex justify-between items-center">
                        <h2 className="text-2xl font-bold text-white">Requisition</h2>
                        <div className="text-2xl font-mono text-[#ffae00]">CREDITS: {gold}</div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {gearList.map((item, idx) => {
                        const name = item["Name"] || item["Item"];
                        if (!name) return null;
                        const cost = Number((item["Cost"] || item["Value"] || "0").replace(/[^0-9]/g, "")) || 0;
                        const owned = inventory.includes(name);
                        const canAfford = gold >= cost;

                        if (cost > 100 && !owned) return null; // Hide expensive stuff not purchasable

                        return (
                            <div key={idx} onClick={() => toggleBuy(item)}
                                className={`glass-panel p-3 flex justify-between items-center cursor-pointer border ${owned ? 'border-green-500 bg-green-900/20' : canAfford ? 'border-gray-700 hover:border-white' : 'border-gray-800 opacity-50'}`}
                            >
                                <div>
                                    <div className="text-white font-bold text-sm">{name}</div>
                                    <div className="text-xs text-gray-500">{item["Type"]}</div>
                                </div>
                                <div className={`font-mono ${owned ? 'text-green-400' : 'text-[#ffae00]'}`}>
                                    {owned ? "OWNED" : cost + "cr"}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    };


    // Step 6: Summary
    const renderSummaryStep = () => (
        <div className="text-center p-8 glass-panel animate-[fadeIn_0.5s_ease-out] max-w-6xl mx-auto border border-[#00f2ff]/30">
            <h2 className="text-4xl mb-6 title-gradient font-bold">{charName}</h2>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-left">
                {/* COL 1: BIO */}
                <div className="bg-black/40 p-4 rounded-lg border border-gray-800">
                    <h3 className="text-[#00f2ff] font-bold mb-4 uppercase text-xs tracking-wider">Biological</h3>
                    <div className="text-sm text-gray-300"><span className="text-gray-500">Form:</span> {selectedSpecies?.Species}</div>
                    <div className="text-sm text-gray-300 mt-2"><span className="text-gray-500">Ability:</span> {selectedSpeciesSkill?.["Skill Name"]}</div>
                    <div className="my-2 border-t border-gray-700"></div>
                    <ul className="text-xs space-y-1 text-gray-400">
                        {selectedTraits.map(t => (
                            <li key={t["Choice Name"]}>• {t["Choice Name"]}</li>
                        ))}
                    </ul>
                </div>

                {/* COL 2: TRAINING */}
                <div className="bg-black/40 p-4 rounded-lg border border-gray-800">
                    <h3 className="text-[#bd00ff] font-bold mb-4 uppercase text-xs tracking-wider">Training</h3>
                    <div className="space-y-2 text-xs text-gray-300">
                        <div><span className="text-gray-500">Origin:</span> {bgOrigin?.["Skill Name"]}</div>
                        <div><span className="text-gray-500">Edu:</span> {bgEdu?.["Skill Name"]}</div>
                        <div><span className="text-gray-500">Armor:</span> {bgAdult?.["Family Name"]}</div>
                        <div className="border-t border-gray-700 pt-1 mt-1"></div>
                        <div><span className="text-gray-500">Melee:</span> {selectedMelee}</div>
                        <div><span className="text-gray-500">Range:</span> {selectedRanged}</div>
                        <div><span className="text-gray-500">Util:</span> {selectedUtility}</div>
                        <div><span className="text-gray-500">Tool:</span> {selectedTool}</div>
                    </div>
                </div>

                {/* COL 3: MAGIC & GEAR */}
                <div className="bg-black/40 p-4 rounded-lg border border-gray-800">
                    <h3 className="text-[#ffae00] font-bold mb-4 uppercase text-xs tracking-wider">Loadout</h3>
                    <div className="text-xs text-gray-500 mb-1">PROGRAMS:</div>
                    <ul className="text-xs text-white mb-4 space-y-1">
                        {selectedSpells.map(s => <li key={s.Name}>♦ {s.Name}</li>)}
                    </ul>
                    <div className="text-xs text-gray-500 mb-1">INVENTORY ({gold}cr):</div>
                    <ul className="text-xs text-gray-400 h-32 overflow-y-auto">
                        {inventory.map(i => <li key={i}>{i}</li>)}
                    </ul>
                </div>

                {/* COL 4: STATS */}
                <div className="bg-black/40 p-4 rounded-lg border border-gray-800">
                    <h3 className="text-green-400 font-bold mb-4 uppercase text-xs tracking-wider">Biometrics</h3>
                    <div className="grid grid-cols-2 gap-2 mb-4">
                        <div className="bg-gray-900 p-1 rounded text-center"><div className="text-[10px] text-gray-500">HP</div><div className="font-bold text-white">{currentStats.derived.hp}</div></div>
                        <div className="bg-gray-900 p-1 rounded text-center"><div className="text-[10px] text-gray-500">CMP</div><div className="font-bold text-white">{currentStats.derived.cmp}</div></div>
                        <div className="bg-gray-900 p-1 rounded text-center"><div className="text-[10px] text-gray-500">SP</div><div className="font-bold text-white">{currentStats.derived.sp}</div></div>
                        <div className="bg-gray-900 p-1 rounded text-center"><div className="text-[10px] text-gray-500">FP</div><div className="font-bold text-white">{currentStats.derived.fp}</div></div>
                    </div>
                    <div className="space-y-1 text-xs text-gray-400">
                        {Object.entries(currentStats.stats).map(([k, v]) => (
                            <div key={k} className="flex justify-between border-b border-gray-800"><span>{k.toUpperCase()}</span> <span className="text-white">{v as any}</span></div>
                        ))}
                    </div>
                </div>
            </div>

            <button
                onClick={downloadCharacter}
                className="btn-primary mt-8 w-full text-lg py-4 shadow-[0_0_30px_rgba(0,242,255,0.2)] hover:shadow-[0_0_50px_rgba(0,242,255,0.4)] transition-all"
            >
                EXPORT NEURAL PROFILE (.JSON)
            </button>
        </div>
    );

    // --- DOWNLOAD ---
    const downloadCharacter = () => {
        if (!selectedSpecies) return;
        const characterData = {
            name: charName,
            species: selectedSpecies.Species,
            stats: { attributes: currentStats.stats, derived: currentStats.derived },
            traits: selectedTraits.map(t => ({ name: t["Choice Name"], bodyPart: t["Body Part"] })),
            skills: [
                selectedSpeciesSkill?.["Skill Name"],
                bgOrigin?.["Skill Name"],
                bgEdu?.["Skill Name"],
                bgAdult?.["Family Name"], // Armor Group
                selectedMelee,
                selectedRanged,
                selectedUtility,
                selectedTool
            ].filter(Boolean),
            magic: selectedSpells.map(s => s.Name),
            inventory: inventory,
            gold: gold,
            timestamp: new Date().toISOString()
        };

        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(characterData, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", `${charName.replace(/ /g, "_")}_${new Date().getTime()}.json`);
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    };

    const StatWidget = () => (
        <div className="fixed top-24 right-4 z-50 w-48 glass-panel p-4 hidden xl:block bg-black/60 border-l border-[#00f2ff]/50">
            <h3 className="text-[#00f2ff] font-bold text-xs uppercase mb-2 tracking-widest border-b border-gray-700 pb-1">Biometrics</h3>
            <div className="grid grid-cols-2 gap-y-1 text-[10px] text-gray-300">
                <div className="flex justify-between px-1"><span>HP</span> <span className="text-white font-bold">{currentStats.derived.hp}</span></div>
                <div className="flex justify-between px-1"><span>CMP</span> <span className="text-white font-bold">{currentStats.derived.cmp}</span></div>
                <div className="col-span-2 border-t border-gray-800 my-1"></div>
                <div className="flex justify-between px-1"><span>MIGHT</span> <span>{currentStats.stats.Might}</span></div>
                <div className="flex justify-between px-1"><span>AGI</span> <span>{currentStats.stats.Reflexes}</span></div>
                <div className="flex justify-between px-1"><span>INT</span> <span>{currentStats.stats.Knowledge}</span></div>
                <div className="flex justify-between px-1"><span>CHA</span> <span>{currentStats.stats.Charm}</span></div>
            </div>
        </div>
    );

    return (
        <div className="min-h-screen p-4 pb-24 relative">
            {step > 1 && <StatWidget />}

            <header className="flex justify-between items-center mb-6 container mx-auto">
                <Link href="/" className="text-gray-500 hover:text-white font-mono text-sm">← ABORT</Link>
                <div className="text-lg md:text-xl font-bold tracking-widest text-[#00f2ff] text-right">
                    PHASE 0{step} // {["BIO-FORM", "EVOLUTION", "PROFESSION", "MAGIC", "REQUISITION", "FINALIZE"][step - 1]}
                </div>
            </header>

            <div className="container mx-auto">
                {step === 1 && renderSpeciesStep()}
                {step === 2 && renderEvolutionStep()}
                {step === 3 && renderProfessionStep()}
                {step === 4 && renderMagicStep()}
                {step === 5 && renderGearStep()}
                {step === 6 && renderSummaryStep()}
            </div>

            <footer className="fixed bottom-0 left-0 w-full glass-panel border-t border-t-[#ffffff10] border-x-0 border-b-0 rounded-none p-4 z-50 bg-[#050510]/80 backdrop-blur-md">
                <div className="container mx-auto flex justify-between items-center">
                    <button
                        disabled={step === 1}
                        onClick={() => setStep(s => s - 1)}
                        className="px-6 py-2 rounded-full border border-gray-600 text-gray-400 disabled:opacity-20 hover:border-white transition"
                    >
                        PREV
                    </button>
                    <div className="flex gap-2">
                        {[1, 2, 3, 4, 5, 6].map(n => (
                            <div key={n} className={`h-2 w-2 rounded-full transition-colors duration-300 ${step >= n ? 'bg-[#00f2ff] shadow-[0_0_8px_#00f2ff]' : 'bg-gray-700'}`} />
                        ))}
                    </div>
                    <button
                        disabled={
                            (step === 1 && (!selectedSpecies || !charName)) ||
                            (step === 2 && (selectedTraits.length !== 6 || !selectedSpeciesSkill)) ||
                            (step === 3 && (!bgOrigin || !bgEdu || !bgAdult || !selectedMelee || !selectedRanged || !selectedUtility || !selectedTool)) ||
                            (step === 4 && selectedSpells.length < 2)
                        }
                        onClick={() => setStep(s => s + 1)}
                        className="btn-primary px-8 py-2 disabled:opacity-50 disabled:grayscale disabled:cursor-not-allowed"
                    >
                        NEXT
                    </button>
                </div>
            </footer>
        </div>
    );
}
