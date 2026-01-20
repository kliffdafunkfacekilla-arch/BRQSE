# Tactical Combat Rules (Revised)

## 1. COVER SYSTEM

| Cover | Defender Effect | Notes |
|-------|-----------------|-------|
| **None** | Normal | No obstruction |
| **Half** | Defender has **Advantage** on defense | Low wall, furniture, ally |
| **Full** | Cannot be targeted | Complete wall, requires LOS check |

**Line of Sight (LOS):**
- Draw a line from attacker center to target center
- If line passes through a wall or Full Cover tile → Blocked
- Partial obstruction (passes edge) → Half Cover

---

## 2. MULTI-ATTACKER SYSTEM (Engagement)

Combat tracks who has been attacked each round.

| Situation | Effect |
|-----------|--------|
| **1st attack against you this round** | Normal roll |
| **2nd+ attack against you this round** | Defender has **Disadvantage** |
| **Attack from behind (rear arc)** | Attacker has **Advantage** |
| **3rd+ enemy engaging you** | Attacker has **Advantage** |

### Implementation:
```python
# On Combatant:
combatant.attacks_received_this_round = 0  # Reset at start of turn

# In attack_target():
target.attacks_received_this_round += 1

if target.attacks_received_this_round >= 2:
    defender_disadvantage = True

# Rear arc = attacker is behind target's facing direction
# 3rd+ enemy = count enemies currently adjacent

enemies_adjacent = count_adjacent_enemies(target)
if enemies_adjacent >= 3:
    attacker_advantage = True
```

---

## 3. FLANKING (Simplified)

Flanking is NOT a separate mechanic. It's covered by:
- **Behind attacks** → Advantage
- **3rd+ enemies** → Advantage

Remove the `is_flanked()` and `has_ally_adjacent_to()` checks.

---

## 4. FACING DIRECTION

Each combatant has a facing direction (N/S/E/W or NE/NW/SE/SW).

**Rear Arc:** 
- If attacker is in the 180° arc behind target's facing → Attack from behind → Advantage

```python
combatant.facing = "N"  # Default facing North

def is_behind(attacker, target):
    # Calculate angle from target to attacker
    dx = attacker.x - target.x
    dy = attacker.y - target.y
    
    # Check if attacker is in rear arc based on target's facing
    if target.facing == "N" and dy > 0: return True  # Attacker is South
    if target.facing == "S" and dy < 0: return True  # Attacker is North
    if target.facing == "E" and dx < 0: return True  # Attacker is West
    if target.facing == "W" and dx > 0: return True  # Attacker is East
    return False
```

---

## 5. LINE OF SIGHT (LOS)

Simple Bresenham line check between attacker and target.

```python
def has_line_of_sight(self, attacker, target):
    """Returns True if clear LOS, False if blocked."""
    x0, y0 = attacker.x, attacker.y
    x1, y1 = target.x, target.y
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    while True:
        if (x0, y0) == (x1, y1):
            return True  # Reached target
        
        # Check current tile for blocking
        if (x0, y0) != (attacker.x, attacker.y):  # Skip attacker's tile
            if (x0, y0) in self.walls:
                return False
            tile = self.get_tile(x0, y0)
            if tile and tile.provides_full_cover:
                return False
        
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return True
```

---

## SUMMARY OF CHANGES

| Old Rule | New Rule |
|----------|----------|
| 3/4 Cover | Removed |
| Half Cover = Attacker Disadvantage | Half Cover = Defender Advantage |
| Flanking (enemies on opposite sides) | Removed - use 3rd+ enemies |
| Pack Tactics (ally adjacent) | Removed - redundant |
| No engagement tracking | Track attacks_received_this_round |
| No facing | Add facing direction + rear arc check |
