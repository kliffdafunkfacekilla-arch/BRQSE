# Derived Stats Implementation Status

This document tracks which derived stats from `Data/Derived_Stats.csv` are implemented vs ignored.

## Currently Implemented ✅

| Stat | Full Name | Formula | Where Used |
|------|-----------|---------|------------|
| **HP** | Hit Points | 10 + Might + Reflexes + Vitality | `mechanics.py`, `CharacterSheet.tsx` |
| **SP** | Stamina Points | Endurance + Finesse + Fortitude | `mechanics.py`, `CharacterSheet.tsx` |
| **FP** | Focus Points | Knowledge + Charm + Intuition | `mechanics.py`, `CharacterSheet.tsx` |
| **SPD** | Move Speed | (Vitality + Willpower) rounded to nearest 5 | `mechanics.py` (base_movement) |

## Partially Implemented ⚠️

| Stat | Full Name | Formula | Status |
|------|-----------|---------|--------|
| **CMP** | Composure | 10 + Willpower + Logic + Awareness | Calculated in mechanics but not displayed prominently in UI |
| **ALT** | Alertness | Intuition + Reflexes | Used in `roll_initiative()` but not shown in UI |

## NOT Implemented ❌

| Stat | Full Name | Formula | Notes |
|------|-----------|---------|-------|
| **CAMO** | Stealth | (Finesse + Awareness) | Stealth floor when not moving |
| **CACHE** | Carry Capacity | ((Might + Knowledge) / 10) + 2 | Number of quick-access item slots |
| **THERM** | Temp Regulation | (Endurance + Logic) / 5 | Comfort zone range for temperature |
| **HYDRO** | Drought Sensitivity | (Fortitude + Charm) / 5 | Comfort zone range for hydration |

## Notes

- **THERM** and **HYDRO** are travel/survival mechanics, not combat
- **CAMO** requires stealth system implementation
- **CACHE** affects inventory slot limits (currently unlimited)
- **CMP** should be shown alongside HP as a second health bar (mental)
- **ALT** is hidden but used for initiative order

## Priority for Implementation

1. **CMP (Composure)** - Critical for Graze damage (1d6 Composure)
2. **CACHE** - Inventory slot limit
3. **CAMO** - Stealth system
4. **THERM/HYDRO** - Travel mechanics (later)
