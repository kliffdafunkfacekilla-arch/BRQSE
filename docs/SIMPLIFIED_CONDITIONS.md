# Simplified Conditions: Advantage/Disadvantage System

## Core Mechanic

**Advantage:** Roll 2d20, take the HIGHER result.
**Disadvantage:** Roll 2d20, take the LOWER result.

Multiple stacks don't stack — you either have it or you don't. Advantage and Disadvantage cancel each other out.

---

## Simplified Status Effects

### TIER 1: Action Modifiers (Attack/Defense)

| Status | Effect | Duration |
|--------|--------|----------|
| **STAGGERED** | Disadvantage on ALL action rolls | 1 Turn |
| **SHAKEN** | Disadvantage on DEFENSE rolls only | Until Rally |
| **WEAKENED** | Disadvantage on ATTACK rolls only | Until Rest |
| **BLESSED** | Advantage on ALL action rolls | Duration |
| **HASTE** | Advantage + Extra Action | Duration |

### TIER 2: Movement Modifiers

| Status | Effect | Duration |
|--------|--------|----------|
| **SLOWED** | Speed halved | 1 Turn |
| **GRAPPLED** | Speed = 0, Disadvantage on Reflex | Until Escape |
| **RESTRAINED** | Speed = 0, Attacks vs you have Advantage | Until Freed |
| **PRONE** | Melee vs you: Advantage. Ranged vs you: Disadvantage | Until Stand |

### TIER 3: Incapacitating

| Status | Effect | Duration |
|--------|--------|----------|
| **STUNNED** | Cannot act. All attacks vs you have Advantage. | 1 Turn |
| **PARALYZED** | Cannot move or act. Melee = Auto-Crit. | Duration |
| **PETRIFIED** | Turned to stone. Immune to most. | Until Cured |

### TIER 4: Damage Over Time

| Status | Effect | Duration |
|--------|--------|----------|
| **BLEED** | 2 Condition damage per turn | Until Stabilized |
| **BURNING** | 1d6 Fire damage per turn | Until Extinguished |
| **POISONED** | Disadvantage on attacks + 1d4 damage/turn | Until Cured |

### TIER 5: Mental/Social

| Status | Effect | Duration |
|--------|--------|----------|
| **CHARMED** | Cannot attack charmer. Regard as friend. | Until Damaged |
| **FRIGHTENED** | Disadvantage on attacks. Cannot approach source. | Until Save |
| **CONFUSED** | Random action each turn | Until Save |
| **TAUNTED** | Must attack taunter. Others at Disadvantage. | Until Hit |

### TIER 6: Visibility

| Status | Effect | Duration |
|--------|--------|----------|
| **BLINDED** | Disadvantage on attacks. Attacks vs you: Advantage. | Until Cured |
| **INVISIBLE** | Your attacks: Advantage. Attacks vs you: Disadvantage. | Until Attack |

---

## Removed/Merged Conditions

| Old Status | Merged Into | Reason |
|------------|-------------|--------|
| DEAFENED | Special case | Rarely matters in combat |
| EXHAUSTED | WEAKENED + SLOWED | Simplify stacking |
| SICKENED | WEAKENED | Similar effect |
| SILENCED | Special case | Spell-specific |
| FEEBLE | WEAKENED | Rarely used |
| CORRODED | Equipment damage | Not a character status |
| FROZEN | RESTRAINED + Vulnerable | Element combo |
| SHOCKED | SLOWED | Similar effect |
| SOAKED | Vulnerability tag | Not a status |
| VOID-TOUCHED | Special curse | Story-specific |

---

## Implementation Notes

### In Code (mechanics.py)

```python
def roll_with_status(base_roll, has_advantage, has_disadvantage):
    if has_advantage and has_disadvantage:
        return base_roll  # Cancel out
    elif has_advantage:
        return max(random.randint(1,20), random.randint(1,20))
    elif has_disadvantage:
        return min(random.randint(1,20), random.randint(1,20))
    else:
        return random.randint(1,20)
```

### Status Flags on Combatant

```python
# Simple boolean flags
combatant.is_staggered = False  # Disadvantage on all
combatant.is_shaken = False     # Disadvantage on defense
combatant.is_weakened = False   # Disadvantage on attack
combatant.is_blessed = False    # Advantage on all
# etc.
```

---

## Summary

**Before:** 34 unique statuses with different -X penalties
**After:** ~15 core statuses using Advantage/Disadvantage

This reduces cognitive load and makes effects predictable.
