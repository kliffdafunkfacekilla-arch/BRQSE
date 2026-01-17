import random
import os
import json

class ChaosManager:
    def __init__(self):
        self.chaos_level = random.randint(1, 10)
        self.chaos_clock = 0
        self.tension_threshold = 1
        
    def roll_tension(self):
        roll = random.randint(1, 10)
        if roll <= self.tension_threshold:
            self.tension_threshold = 1
            return "EVENT"
        elif roll == self.chaos_level:
            self.chaos_clock = min(10, self.chaos_clock + 1)
            self.chaos_level = random.randint(1, 10)
            return "CHAOS_EVENT"
        else:
            self.tension_threshold += 1
            return "SAFE"

class Scene:
    def __init__(self, text, encounter_type="EMPTY", enemy_data=None):
        self.text = text
        self.encounter_type = encounter_type # COMBAT, HAZARD, EMPTY
        self.enemy_data = enemy_data 

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
        # PROCEDURAL GENERATION (The "Creative Lifting")
        # 1. Pick Species
        species_list = list(self.rules.get("Species", {}).keys()) # Uppercase Species key in my JSON
        if not species_list: species_list = list(self.rules.get("species", {}).keys()) # fallback
        s_name = random.choice(species_list) if species_list else "Mammal"
        
        # 2. Pick Gear
        w_list = list(self.rules.get("Weapons", {}).keys())
        if not w_list: w_list = list(self.rules.get("weapons", {}).keys())
        w_name = random.choice(w_list) if w_list else "Club"
        
        # 3. Scale Stats by Chaos Level
        # We return a dict that CharEngine can read
        return {
            "Species": s_name,
            "Weapon": w_name,
            "Armor": "Leather", # Default for now
            "Level": self.chaos.chaos_level # Scales stats in CharEngine
        }

    def generate_quest(self):
        self.stack = []
        
        # Helper to make scenes
        def make_scene(label, force_combat=False):
            enc = "EMPTY"
            enemy = None
            
            # Dynamic Chance based on Tension/Chaos?
            # For now, 40% chance of combat in filler
            if force_combat or random.random() < 0.4:
                enc = "COMBAT"
                enemy = self.generate_enemy()
                
            return Scene(label, enc, enemy)

        # BUILD THE SANDWICH (Reverse order for Stack)
        self.stack.append(make_scene("FINALE BOSS", force_combat=True))
        
        for i in range(random.randint(1, 3)):
            self.stack.append(make_scene(f"Deep Ruins {i}"))
            
        self.stack.append(make_scene("PLOT POINT 2: THE TWIST"))
        
        for i in range(random.randint(1, 3)):
            self.stack.append(make_scene(f"Dungeon Hall {i}"))
            
        self.stack.append(make_scene("PLOT POINT 1: THE GATE"))
        
        for i in range(random.randint(1, 3)):
            self.stack.append(make_scene(f"Entrance Tunnel {i}"))

    def advance(self):
        if not self.stack: return Scene("QUEST COMPLETE")
        scene = self.stack.pop()
        
        # Doom Modifier check
        if self.chaos.chaos_clock >= 10:
            scene.text += " [DOOMED]"
            
        return scene
