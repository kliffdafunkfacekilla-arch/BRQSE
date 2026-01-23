import random
import os
import json

class ChaosManager:
    """
    Manages the global Chaos and Tension systems.
    
    Rules:
    - Chaos Level: Set by a d12 (1-12).
    - Tension Die: A d12 rolled on every exploration ACTION.
    - Event Trigger: If Tension Die <= current Tension Threshold.
    - Chaos Trigger: If Tension Die matches the Chaos Level.
    - Escalation: Every 'SAFE' roll increases the Tension Threshold by 1.
    """
    def __init__(self):
        self.chaos_level = random.randint(1, 12) # d12 Target
        self.chaos_clock = 0
        self.tension_threshold = 1
        
    def roll_tension(self):
        """Rolls a d12 tension die and applies project-specific rules."""
        die_roll = random.randint(1, 12) # d12 Tension Die (Updated as per user rule)
        
        # 1. Check for Chaos Match (Clock +1)
        if die_roll == self.chaos_level:
            self.chaos_clock = min(12, self.chaos_clock + 1)
            # Reroll Chaos Level on match
            self.chaos_level = random.randint(1, 12)
            return "CHAOS_EVENT"
            
        # 2. Check for Tension Event
        if die_roll <= self.tension_threshold:
            self.tension_threshold = 1 # Reset on event
            return "EVENT"
        
        # 3. Safe Step - Escalation
        self.tension_threshold = min(11, self.tension_threshold + 1)
        return "SAFE"
    
    @property
    def is_doomed(self) -> bool:
        """Returns True if Chaos Clock is maxed (DOOM STATE)."""
        return self.chaos_clock >= 12
    
    def get_atmosphere(self) -> dict:
        """Returns tone modifiers based on Chaos Clock."""
        if self.chaos_clock >= 12:
            return {
                "tone": "doom",
                "descriptor": "Reality fractures. The shadows hunger. Nothing is safe.",
                "ai_modifier": "Oppressive and actively hostile."
            }
        elif self.chaos_clock >= 9:
            return {
                "tone": "dread", 
                "descriptor": "The air is thick with malice. Something ancient stirs.",
                "ai_modifier": "Dark and ominous."
            }
        elif self.chaos_clock >= 6:
            return {
                "tone": "tense",
                "descriptor": "Unease gnaws at the edges.",
                "ai_modifier": "Subtle tension."
            }
        elif self.chaos_clock >= 3:
            return {
                "tone": "alert",
                "descriptor": "The dungeon watches. Stay sharp.",
                "ai_modifier": "Watchful."
            }
        return {
            "tone": "normal",
            "descriptor": "The air is still and silent.",
            "ai_modifier": ""
        }

class Scene:
    def __init__(self, text, encounter_type="EMPTY", enemy_data=None, biome="DUNGEON"):
        self.text = text
        self.encounter_type = encounter_type
        self.enemy_data = enemy_data 
        self.biome = biome
        self.grid = []
        self.entrances = []
        self.exits = []
        self.interactables = []
        
    def set_grid(self, grid, entrances, exits, interactables):
        self.grid = grid
        self.entrances = entrances
        self.exits = exits
        self.interactables = interactables 

class SceneStack:
    def __init__(self, chaos_manager):
        self.chaos = chaos_manager
        self.stack = []
        self.rules = self._load_rules()
        
    def _load_rules(self):
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../Data/chaos_core.json")
            with open(path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}

    def generate_enemy(self):
        species_list = list(self.rules.get("Species", {}).keys())
        if not species_list: species_list = list(self.rules.get("species", {}).keys())
        s_name = random.choice(species_list) if species_list else "Mammal"
        
        w_list = list(self.rules.get("Weapons", {}).keys())
        if not w_list: w_list = list(self.rules.get("weapons", {}).keys())
        w_name = random.choice(w_list) if w_list else "Club"
        
        return {
            "Species": s_name,
            "Weapon": w_name,
            "Armor": "Leather",
            "Level": self.chaos.chaos_clock + 1
        }

class QuestType:
    INFILTRATION = ["Infiltrate Perimeter", "Disable Sensors", "The Vault", "Extraction"]
    RESCUE = ["Locate Holding Cell", "Eliminate Guard Post", "Rescue VIP", "Defend Extraction"]
    ASSASSINATION = ["Track Target", "Infiltrate Stronghold", "The Mark", "Eliminate & Vanish"]
    COLLECT = ["Survey Area", "Locate Artifact 1", "Locate Artifact 2", "The Core"]

class SceneStack:
    def __init__(self, chaos_manager):
        self.chaos = chaos_manager
        self.stack = []
        self.rules = self._load_rules()
        
    def _load_rules(self):
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../Data/chaos_core.json")
            with open(path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}

    def generate_enemy(self):
        species_list = list(self.rules.get("Species", {}).keys())
        if not species_list: species_list = list(self.rules.get("species", {}).keys())
        s_name = random.choice(species_list) if species_list else "Mammal"
        
        w_list = list(self.rules.get("Weapons", {}).keys())
        if not w_list: w_list = list(self.rules.get("weapons", {}).keys())
        w_name = random.choice(w_list) if w_list else "Club"
        
        return {
            "Species": s_name,
            "Weapon": w_name,
            "Armor": "Leather",
            "Level": self.chaos.chaos_clock + 1
        }

    def generate_quest(self, biome="DUNGEON"):
        self.stack = []
        
        # Select Quest Template
        q_type = random.choice([QuestType.INFILTRATION, QuestType.RESCUE, QuestType.ASSASSINATION, QuestType.COLLECT])
        
        def make_scene(label, force_combat=False):
            # Weighted Encounter Types
            pool = ["COMBAT"] * 4 + ["SOCIAL", "PUZZLE", "STEALTH", "TREASURE", "SAFE_HAVEN", "DECISION"]
            enc = random.choice(pool)
            
            if force_combat: enc = "COMBAT"
            
            enemy = None
            if enc == "COMBAT":
                enemy = self.generate_enemy()
            return Scene(label, enc, enemy, biome=biome)

        # Build Stack (Plot Points with dynamic 1d4 gaps)
        # Reverse order for stack popping
        self.stack.append(make_scene(f"FINALE: {q_type[-1]}", force_combat=True))
        
        for i in range(len(q_type) - 2, -1, -1):
            # Dynamic gap for EACH segment
            gap_size = random.randint(1, 4)
            for j in range(gap_size):
                self.stack.append(make_scene(f"{biome} Exploration {i}_{j}"))
            
            # Plot Point
            is_combat = (i % 2 == 0) # Every other plot point is combat-heavy
            self.stack.append(make_scene(f"GOAL: {q_type[i]}", force_combat=is_combat))

    def advance(self):
        if not self.stack: return Scene("QUEST COMPLETE")
        scene = self.stack.pop()
        if self.chaos.chaos_clock >= 10:
            scene.text += " [DOOMED]"
        return scene
