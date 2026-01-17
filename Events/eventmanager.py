
import random

# --- EVENT TYPES ---
class EventType:
    TRAP = "TRAP"
    NPC_SOCIAL = "NPC_SOCIAL"
    MONSTER_AMBUSH = "MONSTER_AMBUSH"
    PUZZLE = "PUZZLE"
    STEALTH = "STEALTH"
    ITEM_FIND = "ITEM_FIND"
    REST_SPOT = "REST_SPOT"
    MERCHANT = "MERCHANT"
    ENVIRONMENTAL = "ENVIRONMENTAL"

# --- CHAOS MODIFIERS ---
class ChaosModifier:
    NONE = "NONE"
    GRAVITY_ANOMALY = "GRAVITY_ANOMALY"           # Everything floats or weighs double
    SPONGE_WORLD = "SPONGE_WORLD"                 # All surfaces are soft/absorbent
    TIME_FREEZE = "TIME_FREEZE"                   # Trapped in a moment
    MIRROR_REALM = "MIRROR_REALM"                 # Everything is reversed
    SHADOW_PLAGUE = "SHADOW_PLAGUE"               # Darkness creeps in
    ELEMENTAL_SURGE = "ELEMENTAL_SURGE"           # Random element is empowered
    WILD_MAGIC = "WILD_MAGIC"                     # Spells have random side effects
    SILENCE_ZONE = "SILENCE_ZONE"                 # No sound, no verbal casting
    BLOOD_MOON = "BLOOD_MOON"                     # Enemies are stronger
    LUCKY_STARS = "LUCKY_STARS"                   # Positive modifier (Bonus Loot)

# --- EVENT TEMPLATES ---
EVENT_TEMPLATES = {
    EventType.TRAP: [
        {"name": "Pit Trap", "danger": 2, "skill_check": "Awareness", "effect": "Fall Damage"},
        {"name": "Poison Dart Wall", "danger": 3, "skill_check": "Reflexes", "effect": "Poison"},
        {"name": "Collapsing Floor", "danger": 4, "skill_check": "Reflexes", "effect": "Fall + Restrained"},
        {"name": "Tripwire Alarm", "danger": 1, "skill_check": "Awareness", "effect": "Alert Enemies"},
        {"name": "Magic Rune", "danger": 5, "skill_check": "Knowledge", "effect": "Elemental Burst"},
    ],
    EventType.NPC_SOCIAL: [
        {"name": "Lost Traveler", "disposition": "Friendly", "skill_check": "Charm", "reward": "Information"},
        {"name": "Shady Merchant", "disposition": "Neutral", "skill_check": "Intuition", "reward": "Discount"},
        {"name": "Wounded Soldier", "disposition": "Desperate", "skill_check": "Awareness", "reward": "Ally"},
        {"name": "Rival Adventurer", "disposition": "Hostile", "skill_check": "Charm", "reward": "Duel or Trade"},
        {"name": "Mysterious Stranger", "disposition": "Unknown", "skill_check": "Intuition", "reward": "Quest Hook"},
    ],
    EventType.MONSTER_AMBUSH: [
        {"name": "Goblin Scouts", "tier": 1, "count": "1d4+1", "behavior": "Aggressive"},
        {"name": "Wolf Pack", "tier": 1, "count": "1d6", "behavior": "Flanking"},
        {"name": "Bandit Gang", "tier": 2, "count": "1d4", "behavior": "Ranged"},
        {"name": "Undead Patrol", "tier": 2, "count": "1d6", "behavior": "Camper"},
        {"name": "Chimera", "tier": 4, "count": "1", "behavior": "Caster"},
    ],
    EventType.PUZZLE: [
        {"name": "Locked Chest", "difficulty": 2, "skill_check": "Finesse", "reward": "Treasure"},
        {"name": "Ancient Riddle Door", "difficulty": 3, "skill_check": "Logic", "reward": "Passage"},
        {"name": "Pressure Plate Sequence", "difficulty": 4, "skill_check": "Awareness", "reward": "Secret Room"},
        {"name": "Magic Seal", "difficulty": 5, "skill_check": "Knowledge", "reward": "Artifact"},
    ],
    EventType.STEALTH: [
        {"name": "Guard Patrol", "difficulty": 2, "skill_check": "Finesse", "fail_result": "Combat"},
        {"name": "Sleeping Dragon", "difficulty": 5, "skill_check": "Reflexes", "fail_result": "Boss Fight"},
        {"name": "Trapped Hallway", "difficulty": 3, "skill_check": "Awareness", "fail_result": "Trap"},
    ],
    EventType.ITEM_FIND: [
        {"name": "Abandoned Campsite", "loot_tier": 1, "description": "Old supplies left behind."},
        {"name": "Skeleton with Pouch", "loot_tier": 2, "description": "A fallen adventurer."},
        {"name": "Hidden Cache", "loot_tier": 3, "description": "Someone buried treasure here."},
        {"name": "Magical Residue", "loot_tier": 4, "description": "A spell left something behind."},
    ],
    EventType.REST_SPOT: [
        {"name": "Quiet Clearing", "safety": 3, "bonus": "Full Rest"},
        {"name": "Abandoned Cabin", "safety": 2, "bonus": "Shelter"},
        {"name": "Sacred Grove", "safety": 5, "bonus": "Heal + Buff"},
        {"name": "Cave Entrance", "safety": 1, "bonus": "Partial Rest"},
    ],
    EventType.MERCHANT: [
        {"name": "Wandering Peddler", "stock_tier": 1, "prices": "Normal"},
        {"name": "Black Market Contact", "stock_tier": 3, "prices": "High"},
        {"name": "Fey Trader", "stock_tier": 4, "prices": "Barter Only"},
    ],
    EventType.ENVIRONMENTAL: [
        {"name": "Sudden Storm", "effect": "Reduced Visibility", "duration": "3 Rounds"},
        {"name": "Earthquake", "effect": "Difficult Terrain", "duration": "1 Round"},
        {"name": "Magical Fog", "effect": "Concealment", "duration": "Until Dispelled"},
        {"name": "Aurora Event", "effect": "Magic Amplified", "duration": "Scene"},
    ],
}

CHAOS_EFFECTS = {
    ChaosModifier.GRAVITY_ANOMALY: {
        "description": "Gravity shifts unpredictably.",
        "mechanics": ["Movement costs doubled", "Jump distance tripled", "Falling damage halved"]
    },
    ChaosModifier.SPONGE_WORLD: {
        "description": "Everything becomes soft and absorbent.",
        "mechanics": ["Piercing damage halved", "Fire damage doubled", "Stealth +2"]
    },
    ChaosModifier.TIME_FREEZE: {
        "description": "Time stops for everyone except you.",
        "mechanics": ["Free movement phase", "Cannot interact with frozen entities", "Duration: 1 Round"]
    },
    ChaosModifier.MIRROR_REALM: {
        "description": "Left is right, up is down.",
        "mechanics": ["Movement directions reversed", "Spells target opposite", "Perception checks -2"]
    },
    ChaosModifier.SHADOW_PLAGUE: {
        "description": "Darkness creeps in from all sides.",
        "mechanics": ["Light radius halved", "Shadow creatures empowered", "Fear checks required"]
    },
    ChaosModifier.ELEMENTAL_SURGE: {
        "description": "An element surges with power.",
        "mechanics": ["Random element +2d6 damage", "Opposing element -2d6", "Environmental hazards"]
    },
    ChaosModifier.WILD_MAGIC: {
        "description": "Magic is unstable.",
        "mechanics": ["All spells trigger wild surge", "Random beneficial/harmful effects", "FP costs halved"]
    },
    ChaosModifier.SILENCE_ZONE: {
        "description": "No sound can be made.",
        "mechanics": ["Verbal spells fail", "Stealth auto-success (sound)", "Communication limited"]
    },
    ChaosModifier.BLOOD_MOON: {
        "description": "The moon bleeds red.",
        "mechanics": ["Enemies +2 to all stats", "Undead regenerate", "Player crit range expanded"]
    },
    ChaosModifier.LUCKY_STARS: {
        "description": "Fortune smiles upon you.",
        "mechanics": ["Loot quality +1 tier", "Reroll one failed check", "Enemies may flee"]
    },
}

# --- ENCOUNTER GENERATOR ---
class EncounterGenerator:
    def __init__(self, chaos_chance=0.2):
        self.chaos_chance = chaos_chance
        self.event_weights = {
            EventType.TRAP: 15,
            EventType.NPC_SOCIAL: 15,
            EventType.MONSTER_AMBUSH: 25,
            EventType.PUZZLE: 10,
            EventType.STEALTH: 10,
            EventType.ITEM_FIND: 10,
            EventType.REST_SPOT: 5,
            EventType.MERCHANT: 5,
            EventType.ENVIRONMENTAL: 5,
        }

    def generate(self, force_type=None, force_chaos=None):
        """
        Generate a random encounter.
        Returns dict with 'event', 'chaos', and 'description'.
        """
        # Pick Event Type
        if force_type:
            event_type = force_type
        else:
            event_type = self._weighted_choice(self.event_weights)
        
        # Pick Template
        templates = EVENT_TEMPLATES.get(event_type, [])
        if not templates:
            return {"event": None, "chaos": None, "description": "Nothing happens."}
        
        event = random.choice(templates).copy()
        event["type"] = event_type
        
        # Roll for Chaos
        chaos = ChaosModifier.NONE
        if force_chaos:
            chaos = force_chaos
        elif random.random() < self.chaos_chance:
            chaos = random.choice([
                ChaosModifier.GRAVITY_ANOMALY,
                ChaosModifier.SPONGE_WORLD,
                ChaosModifier.TIME_FREEZE,
                ChaosModifier.MIRROR_REALM,
                ChaosModifier.SHADOW_PLAGUE,
                ChaosModifier.ELEMENTAL_SURGE,
                ChaosModifier.WILD_MAGIC,
                ChaosModifier.SILENCE_ZONE,
                ChaosModifier.BLOOD_MOON,
                ChaosModifier.LUCKY_STARS,
            ])
        
        chaos_data = CHAOS_EFFECTS.get(chaos, {})
        
        # Build Description
        desc = f"EVENT: {event.get('name', 'Unknown')}"
        if chaos != ChaosModifier.NONE:
            desc += f"\n  CHAOS: {chaos} - {chaos_data.get('description', '')}"
        
        return {
            "event": event,
            "chaos": chaos,
            "chaos_effects": chaos_data.get("mechanics", []),
            "description": desc
        }

    def _weighted_choice(self, weights):
        total = sum(weights.values())
        r = random.uniform(0, total)
        cumulative = 0
        for key, weight in weights.items():
            cumulative += weight
            if r <= cumulative:
                return key
        return list(weights.keys())[-1]

# --- SINGLETON ---
generator = EncounterGenerator()

# --- PUB/SUB (from original eventmanager) ---
class EventManager:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_type, listener):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)

    def unsubscribe(self, event_type, listener):
        if event_type in self.listeners:
            if listener in self.listeners[event_type]:
                self.listeners[event_type].remove(listener)

    def post(self, event_type, data=None):
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                try:
                    listener(data)
                except Exception as e:
                    print(f"Error handling event {event_type}: {e}")

game_events = EventManager()
