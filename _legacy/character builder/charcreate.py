
import pygame
import sys
import os
import csv
import json

# --- CONSTANTS ---
SCREEN_W, SCREEN_H = 1200, 800
COLOR_BG = (20, 20, 30)
COLOR_PANEL = (40, 40, 50)
COLOR_TEXT = (220, 220, 220)
COLOR_ACCENT = (100, 200, 255)
COLOR_HIGHLIGHT = (255, 200, 50)
COLOR_SELECTED = (50, 200, 50)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../Data")
SAVE_DIR = os.path.join(BASE_DIR, "../Saves")

# --- DATA MANAGER ---
class DataManager:
    def __init__(self):
        self.species_stats = {}
        self.evolutions = {} 
        self.skills = {} 
        self.backgrounds = {} 
        self.abilities = {} 
        self.gear = []
        
        self.load_all()

    def load_csv(self, filename):
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                return list(csv.DictReader(f))
        except: return []

    def load_all(self):
        # 1. Species Base
        rows = self.load_csv("Species.csv")
        if rows:
            headers = [k for k in rows[0].keys() if k not in ["Attribute", "Reference", ""]]
            for sp in headers:
                self.species_stats[sp] = {}
                for row in rows:
                    attr = row.get("Attribute")
                    val = row.get(sp)
                    if attr and val:
                        try: self.species_stats[sp][attr] = int(val)
                        except: self.species_stats[sp][attr] = val

        # 2. Evolutions & Skills
        for sp in self.species_stats.keys():
            self.evolutions[sp] = self.load_csv(f"{sp}.csv")
            self.skills[sp] = self.load_csv(f"{sp}_Skills.csv")

        # 3. Backgrounds & Skills
        self.backgrounds["Origin"] = self.load_csv("Social_Def.csv")
        self.backgrounds["Education"] = self.load_csv("Social_Off.csv")
        self.backgrounds["Adulthood"] = self.load_csv("Social_Arm.csv")
        
        self.weapon_groups = self.load_csv("Weapon_Groups.csv")
        self.all_skills = self.load_csv("Skills.csv") # Generic skills list
        self.tool_types = self.load_csv("Tool_types.csv")

        # 4. Abilities
        self.abilities["Schools"] = self.load_csv("Schools of Power.csv")
        self.abilities["Shapes"] = self.load_csv("Power_Shapes.csv")
        self.abilities["Power"] = self.load_csv("Power_Power.csv")

        # 5. Gear & Armor Groups
        self.gear = self.load_csv("weapons_and_armor.csv")
        self.armor_groups = self.load_csv("Armor_Groups.csv")
        
        print("[DATA] Loading Complete.")

# --- CHARACTER STATE ---
class CharacterBuilder:
    def __init__(self):
        self.name = ""
        self.species = ""
        self.attributes = {} 
        self.current_stats = {} 
        
        self.traits = [] 
        self.body_parts = [] 
        self.armor_prof = [] # Added for safety
        
        self.skills = [] 
        self.powers = [] 
        self.inventory = [] 
        self.money = 100
        self.derived = {}
        
    def init_stats(self, base_stats):
        self.attributes = base_stats.copy()
        self.recalc()
        
    def recalc(self):
        self.current_stats = self.attributes.copy()
        # Mods applied by App logic

# --- UI ---
class Button:
    def __init__(self, rect, text, action_id, tooltip=""):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action_id = action_id
        self.tooltip = tooltip
        self.hover = False

    def draw(self, screen, font, is_selected=False):
        col = COLOR_SELECTED if is_selected else (COLOR_ACCENT if self.hover else COLOR_PANEL)
        pygame.draw.rect(screen, col, self.rect)
        pygame.draw.rect(screen, (255,255,255), self.rect, 1)
        
        txt_surf = font.render(self.text, True, COLOR_TEXT)
        text_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, text_rect)

# --- APP ---
class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Chaos RPG: Character Creator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier New", 18)
        self.title_font = pygame.font.SysFont("Courier New", 32, bold=True)
        
        self.data = DataManager()
        self.builder = CharacterBuilder()
        
        self.state = "MENU"
        self.wizard_step = 0
        self.buttons = []
        
        self.input_active = False
        self.input_text = ""
        self.hover_text = ""
        self.validation_error = None

    def run(self):
        while True:
            self.handle_input()
            self.draw()
            self.clock.tick(30)

    def handle_input(self):
        mouse_pos = pygame.mouse.get_pos()
        self.hover_text = ""
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
                
            if event.type == pygame.MOUSEMOTION:
                for btn in self.buttons:
                    btn.hover = btn.rect.collidepoint(mouse_pos)
                    if btn.hover and btn.tooltip:
                        self.hover_text = btn.tooltip
                        
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for btn in self.buttons:
                        if btn.hover:
                            self.handle_action(btn.action_id)
                            
            if event.type == pygame.KEYDOWN:
                if self.input_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        self.input_active = False
                        self.builder.name = self.input_text
                        self.setup_wizard_ui()
                    else:
                        self.input_text += event.unicode
                elif self.wizard_step > 0:
                     if event.key == pygame.K_RIGHT: self.handle_action("NEXT")
                     if event.key == pygame.K_LEFT: self.handle_action("BACK")

    def handle_action(self, action_id):
        self.validation_error = None
        if action_id == "NEW_CHAR":
            self.state = "WIZARD"
            self.wizard_step = 1
            self.buttons = []
            self.setup_wizard_ui()
        elif action_id == "MANAGE":
            self.state = "MANAGE"
            self.buttons = []
        elif action_id == "RANDOM":
            self.generate_random()
        elif action_id == "EXIT":
            pygame.quit(); sys.exit()
        
        # MANAGE State Logic
        elif action_id == "BACK":
            if self.state == "MANAGE":
                self.state = "MENU"
                self.buttons = []
            else:
                self.wizard_step -= 1
                self.setup_wizard_ui()
        elif action_id.startswith("DEL_"):
            fname = action_id[4:]
            path = os.path.join(SAVE_DIR, fname)
            if os.path.exists(path):
                os.remove(path)
            self.buttons = [] # Refresh list handling

        elif action_id == "NEXT":
            if not self.validate_step(): return
            self.wizard_step += 1
            self.setup_wizard_ui()

        elif action_id == "INPUT_NAME":
            self.input_active = True
        elif action_id == "SAVE":
            self.save_character()
            self.state = "MENU"
            self.buttons = []
            
        elif action_id.startswith("SELECT_SPECIES_"):
            sp = action_id.replace("SELECT_SPECIES_", "")
            self.builder.species = sp
            self.builder.init_stats(self.data.species_stats.get(sp, {}))
            self.setup_wizard_ui()
            
        elif action_id.startswith("SELECT_TRAIT_"):
            trait = action_id.replace("SELECT_TRAIT_", "")
            self.select_trait(trait)
            self.setup_wizard_ui()

        elif action_id.startswith("SELECT_BG_"):
            skill = action_id.replace("SELECT_BG_", "")
            self.select_background_skill(skill)
            self.setup_wizard_ui()
            
        elif action_id.startswith("SELECT_SKILL_"):
            skill = action_id.replace("SELECT_SKILL_", "")
            self.select_skill_exclusive(skill)
            self.setup_wizard_ui()
            
        elif action_id.startswith("SELECT_SPSKILL_"):
            skill = action_id.replace("SELECT_SPSKILL_", "")
            phase_skills = [r["Skill Name"] for r in self.data.skills.get(self.builder.species, [])]
            for s in phase_skills: 
                if s in self.builder.skills: self.builder.skills.remove(s)
            self.builder.skills.append(skill)
            self.setup_wizard_ui()
            
        elif action_id.startswith("SELECT_POWER_"):
             power = action_id.replace("SELECT_POWER_", "")
             if power in self.builder.powers:
                 self.builder.powers.remove(power)
             else:
                 if len(self.builder.powers) < 2:
                     self.builder.powers.append(power)
             self.setup_wizard_ui()
             
        elif action_id.startswith("BUY_"):
            item_name = action_id.replace("BUY_", "")
            item = next((i for i in self.data.gear if i["Item"] == item_name), None)
            if item:
                cost = int(item["Cost"])
                if self.builder.money >= cost:
                    self.builder.money -= cost
                    self.builder.inventory.append(item_name)
                    self.setup_wizard_ui()

    def validate_step(self):
        # Step 1: Name & Species
        if self.wizard_step == 1:
            if not self.builder.name or not self.builder.name.strip() or self.builder.name == "Unknown": 
                self.validation_error = "ENTER A NAME FIRST"
                return False
            if not self.builder.species: 
                self.validation_error = "SELECT A SPECIES FIRST"
                return False
            
        # Steps 2-7: Evolution
        elif 2 <= self.wizard_step <= 7:
            expected = self.wizard_step - 1
            if len(self.builder.traits) < expected: 
                self.validation_error = "SELECT A TRAIT FIRST"
                return False
            
        # Step 8-10: Backgrounds
        elif 8 <= self.wizard_step <= 10:
             phases = [self.data.backgrounds["Origin"], self.data.backgrounds["Education"], self.data.armor_groups]
             rows = phases[self.wizard_step - 8]
             found = False
             for r in rows:
                 if self.wizard_step == 10:
                     grp = r.get("Family Name")
                     if grp and grp in self.builder.armor_prof: found = True
                 else:
                     s = r.get("Skill Name") or r.get("Skill")
                     if s and s in self.builder.skills: found = True
                 if found: break
             if not found: 
                 self.validation_error = "MAKE A SELECTION FIRST"
                 return False

        # Step 11: Training
        elif self.wizard_step == 11:
            weps = [r['Family Name'] for r in self.data.weapon_groups]
            if not any(s in self.builder.skills for s in weps): 
                self.validation_error = "SELECT WEAPON TRAINING"
                return False

        # Step 12: Catalyst
        elif self.wizard_step == 12:
             utils = [r['Skill Name'] for r in self.data.all_skills if r.get("Type") == "Utility"]
             tools = [r['Tool_Name'] for r in self.data.tool_types]
             if not any(s in self.builder.skills for s in utils + tools): 
                 self.validation_error = "SELECT UTILITY OR TOOL"
                 return False

        # Step 13: Species Skill
        elif self.wizard_step == 13:
             sp_skills = [r.get("Skill Name") or r.get("Skill") for r in self.data.skills.get(self.builder.species, [])]
             if not any(s in self.builder.skills for s in sp_skills): 
                 self.validation_error = "SELECT SPECIES SKILL"
                 return False

        # Step 14: Schools (Now Abilities)
        elif self.wizard_step == 14:
             if len(self.builder.powers) < 2: 
                 self.validation_error = f"SELECT 2 ABILITIES ({len(self.builder.powers)}/2)"
                 return False

        return True

    def select_background_skill(self, skill_name):
        phases = [
             self.data.backgrounds["Origin"],
             self.data.backgrounds["Education"],
             self.data.armor_groups # Step 10 uses Armor Groups now
        ]
        if 8 <= self.wizard_step <= 10:
            current_csv = phases[self.wizard_step - 8]
            for row in current_csv:
                # Same logic as draw loop
                if self.wizard_step == 10:
                    s = f"Armor: {row.get('Family Name')}"
                else:
                    s = row.get("Skill Name") or row.get("Skill")
                
                if s in self.builder.skills:
                    self.builder.skills.remove(s)
            self.builder.skills.append(skill_name)
            
    def select_skill_exclusive(self, skill_name):
        groups = []
        if self.wizard_step == 11:
            weps = self.data.weapon_groups
            melee = [r['Family Name'] for r in weps if r.get("Type") == "Melee"]
            ranged = [r['Family Name'] for r in weps if r.get("Type") == "Ranged"]
            groups = [melee, ranged]
            
        elif self.wizard_step == 12:
            utils = [r['Skill Name'] for r in self.data.all_skills if r.get("Type") == "Utility"]
            tools = [r['Tool_Name'] for r in self.data.tool_types]
            groups = [utils, tools]
            
        for grp in groups:
            if skill_name in grp:
                for s in grp:
                    if s in self.builder.skills: self.builder.skills.remove(s)
                self.builder.skills.append(skill_name)
                break

    def select_trait(self, trait_name):
        cats = ["ANCESTRY", "DEFENSE", "OFFENSE", "SOCIAL", "ENVIRON", "ADAPT"]
        current_cat = cats[self.wizard_step - 2]
        sp_rows = self.data.evolutions.get(self.builder.species, [])
        valid_rows = [r for r in sp_rows if r["Category"] == current_cat]
        for r in valid_rows:
            tn = r["Choice Name"]
            if tn in self.builder.traits:
                self.builder.traits.remove(tn)
        self.builder.traits.append(trait_name)
        self.recalc_stats()

    def recalc_stats(self):
        self.builder.current_stats = self.builder.attributes.copy()
        self.builder.body_parts = []
        
        # Mapping for inconsistent CSV data (Abbreviation -> Full Name)
        attr_map = {
            "Endure": "Endurance",
            "Reflex": "Reflexes",
            "Will": "Willpower",
            "Fort": "Fortitude", 
            "Awar": "Awareness",
            "Intel": "Knowledge", # Just in case
            "Str": "Might"
        }
        
        sp_rows = self.data.evolutions.get(self.builder.species, [])
        for trait in self.builder.traits:
            row = next((r for r in sp_rows if r["Choice Name"] == trait), None)
            if row:
                s1 = row.get("Stat 1")
                s2 = row.get("Stat 2")
                bp = row.get("Body Part")
                
                # Normalize
                s1 = attr_map.get(s1, s1)
                s2 = attr_map.get(s2, s2)
                
                if s1 and s1 in self.builder.current_stats: self.builder.current_stats[s1] += 1
                if s2 and s2 in self.builder.current_stats: self.builder.current_stats[s2] += 1
                if bp and bp not in self.builder.body_parts:
                    self.builder.body_parts.append(bp)
        
        # Derived Stats
        stats = self.builder.current_stats
        def get(attr): return stats.get(attr, 0)
        
        hp = 10 + get("Might") + get("Reflexes") + get("Vitality")
        cmp = 10 + get("Willpower") + get("Logic") + get("Awareness")
        sp = get("Endurance") + get("Finesse") + get("Fortitude")
        fp = get("Knowledge") + get("Charm") + get("Intuition")
        
        raw_spd = get("Vitality") + get("Willpower")
        spd = 5 * round(raw_spd/5)
        if spd == 0: spd = 20
        
        self.builder.derived = {
            "HP": hp, "CMP": cmp, "SP": sp, "FP": fp, "Speed": spd
        }

    def save_character(self):
        filename = f"{self.builder.name or 'Unnamed'}.json"
        path = os.path.join(SAVE_DIR, filename)
        
        final_powers = self.builder.powers.copy()
        # Note: Powers list is now Names (e.g. "Push"), not "School".
            
        data = {
            "Name": self.builder.name,
            "Species": self.builder.species,
            "Stats": self.builder.current_stats,
            "Derived": getattr(self.builder, "derived", {}),
            "Traits": self.builder.traits,
            "BodyParts": self.builder.body_parts,
            "Skills": self.builder.skills,
            "Powers": final_powers,
            "Inventory": self.builder.inventory,
            "Gold": self.builder.money
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Saved to {path}")

    def setup_wizard_ui(self):
        self.buttons = []
        
        # Validation for Step 1
        can_proceed = True
        next_label = "NEXT >"
        # Pre-checks logic can be removed if we rely on validate_step 
        # But keeping it for label change is fine
        if self.wizard_step == 1 and not self.builder.species:
            can_proceed = False
            next_label = "SELECT SPECIES"
            
        # Nav Buttons
        # Character Sheet is at SCREEN_W - 350 (i.e., 850).
        # We must place Next button to the left of 850.
        # Let's align it right-justified against the sheet: 850 - 150 = 700.
        btn_x = SCREEN_W - 350 - 160 # 690
        btn_y = SCREEN_H - 80
        
        # If disabled, we can use a special tooltip or handling in draw
        self.buttons.append(Button((btn_x, btn_y, 140, 50), next_label, "NEXT", "Proceed to next step"))
        
        if self.wizard_step > 1:
            self.buttons.append(Button((30, btn_y, 140, 50), "< BACK", "BACK", "Go back"))

        # 1. BASICS
        if self.wizard_step == 1:
            y = 180
            for sp in self.data.species_stats.keys():
                self.buttons.append(Button((50, y, 250, 40), sp.upper(), f"SELECT_SPECIES_{sp}"))
                y += 50
            self.buttons.append(Button((50, 100, 400, 50), f"NAME: {self.builder.name}", "INPUT_NAME"))

        # 2-7. EVOLUTION
        elif 2 <= self.wizard_step <= 7:
            cats = ["ANCESTRY", "DEFENSE", "OFFENSE", "SOCIAL", "ENVIRON", "ADAPT"]
            step_title = f"EVOLUTION ({self.wizard_step-1}/6): {cats[self.wizard_step - 2]}"
            # Update title in draw_wizard, but here create buttons
            cat = cats[self.wizard_step - 2]
            sp_rows = self.data.evolutions.get(self.builder.species, [])
            opts = [r for r in sp_rows if r["Category"] == cat]
            
            x, y = 50, 150
            for i, row in enumerate(opts):
                label = row["Choice Name"]
                desc = f"{row.get('Option')} - Gets {row.get('Body Part')}"
                tooltip = f"{row.get('Stat 1')}+1, {row.get('Stat 2')}+1"
                self.buttons.append(Button((x, y, 350, 40), label, f"SELECT_TRAIT_{label}", tooltip))
                y += 60

        # 8-10. BACKGROUND
        elif 8 <= self.wizard_step <= 10:
             phases = [
                 {"title": "ORIGIN (Social Defense)", "key": "Origin", "csv": self.data.backgrounds["Origin"]},
                 {"title": "EDUCATION (Social Offense)", "key": "Education", "csv": self.data.backgrounds["Education"]},
                 # Adulthood maps to Armor Groups now
                 {"title": "ADULTHOOD (Armor Proficiency)", "key": "Adulthood", "csv": self.data.armor_groups}
             ]
             phase = phases[self.wizard_step - 8]
             narratives = [
                 # Origin
                 ["Orphaned - Left on your own, you learned to endure.", "Street Rat - You survived by dodging trouble.", "Noble Born - You were raised to be charming.", "Scholar - You hid behind your studies.", "Soldier - You were trained to follow orders.", "Outcast - You learned to read people."],
                 # Education
                 ["Bully - You learned to get your way through force.", "Wit - You used words as weapons.", "Commander - You applied relentless pressure.", "Debater - You dismantled arguments.", "Investigator - You learned to see lies.", "Performer - You learned to sway the crowd."],
                 # Adulthood (Mapped to Armor Groups: Plate, Light, Bio, Robes, Mail, Rigs)
                 # MAPPING: Survivor(Plate), Spy(Light), Socialite(Bio), Official(Robes), Zealot(Mail), Merchant(Rigs)
                 ["Survivor (Plate) - You carry your life on your back.", "Spy (Light) - You wear a mask to hide yourself.", "Socialite (Bio) - You dress to impress.", "Official (Robes) - You wear symbols of office.", "Zealot (Mail) - You are armored by faith.", "Merchant (Rigs) - You are prepared for anything."]
             ]
             current_noms = narratives[self.wizard_step - 8]
             
             x, y = 50, 150
             
             # Need specific mapping for Adulthood because CSV order doesn't match narrative order perfectly
             # Armor Groups CSV: Plate, Bio, Light, Robes, Mail, Rigs
             # Narrative Order: Survivor(Plate), Spy(Light), Socialite(Bio), Official(Robes), Zealot(Mail), Merchant(Rigs)
             
             if self.wizard_step == 10:
                 # Map Narrative Index to CSV Index
                 # Plate(0)->0, Light(2)->1, Bio(1)->2, Robes(3)->3, Mail(4)->4, Rigs(5)->5
                 idx_map = [0, 2, 1, 3, 4, 5]
             else:
                 idx_map = range(len(current_noms))
                 
             for i in range(len(current_noms)):
                 if i >= len(phase["csv"]): break
                 
                 datarow = phase["csv"][idx_map[i] if self.wizard_step == 10 else i]
                 
                 if self.wizard_step == 10:
                      skill_name = f"Armor: {datarow.get('Family Name')}"
                  # Origin/Education logic
                 else:
                     skill_name = datarow.get("Skill Name") or datarow.get("Skill")
                 
                 desc = current_noms[i]
                 label = f"{skill_name}: {desc}"
                 bid = f"SELECT_BG_{skill_name}"
                 self.buttons.append(Button((x, y, 900, 40), label, bid, datarow.get("Description") or datarow.get("Effect")))
                 y += 50
        
        # 11. TRAINING (Dynamic from Weapon_Groups.csv)
        elif self.wizard_step == 11:
            weps = self.data.weapon_groups
            melee = [r for r in weps if r.get("Type") == "Melee"]
            ranged = [r for r in weps if r.get("Type") == "Ranged"]
            
            m_labels = [f"{r['Family Name']} ({r['Examples']})" for r in melee]
            m_tags = [r['Family Name'] for r in melee]
            
            r_labels = [f"{r['Family Name']} ({r['Examples']})" for r in ranged]
            r_tags = [r['Family Name'] for r in ranged]
            
            self.draw_split_choice(
                "MELEE TRAINING", m_labels, m_tags,
                "RANGED TRAINING", r_labels, r_tags
            )
            
        # 12. CATALYST (Dynamic from Skills.csv and Tool_types.csv)
        elif self.wizard_step == 12:
            utils = [r for r in self.data.all_skills if r.get("Type") == "Utility"]
            tools = self.data.tool_types
            
            # Use 'Skill Name' for Utils
            u_labels = [f"{r['Skill Name']} ({r['Attribute']})" for r in utils]
            u_tags = [r['Skill Name'] for r in utils]
            
            # Use 'Tool_Name' for Tools
            t_labels = [f"{r['Tool_Name']} ({r['Attribute']})" for r in tools]
            t_tags = [r['Tool_Name'] for r in tools]
            
            self.draw_split_choice(
                "UTILITY SKILL", u_labels, u_tags,
                "TOOL PROFICIENCY", t_labels, t_tags
            )

        # 13. SPECIES SKILL
        elif self.wizard_step == 13:
             sp_skills = self.data.skills.get(self.builder.species, [])
             
             # Filter entries where the required body part matches one we have
             valid = []
             for r in sp_skills:
                 # CSV has mixed headers: "Body Part" (top half) vs "Required Body Part" (bottom half)
                 req = r.get("Body Part") or r.get("Required Body Part")
                 if req and req in self.builder.body_parts:
                     valid.append(r)
             
             x, y = 50, 150
             for r in valid:
                 skill = r.get("Skill Name") or r.get("Skill")
                 desc = r.get("Effect Description") or r.get("Effect")
                 part = r.get("Body Part") or r.get("Required Body Part")
                 
                 if skill and desc:
                     bid = f"SELECT_SPSKILL_{skill}"
                     label = f"[{part}] {skill}: {desc}"
                     self.buttons.append(Button((x, y, 900, 40), label[:80]+"...", bid, label))
                     y += 50
                 
        # 14. ABILITIES (Tier 1 Spells)
        elif self.wizard_step == 14:
            try:
                valid_powers = []
                
                # Check if data exists
                if "Schools" not in self.data.abilities:
                     with open("crash_log.txt", "a") as f: f.write("Step 14 Error: 'Schools' key missing in data.abilities\n")
                
                schools_data = self.data.abilities.get("Schools", [])
                
                for row in schools_data:
                    # Filter Tier 1
                    if str(row.get("Tier", "0")) != "1": continue
                    
                    sch = row.get("School")
                    attr = row.get("Attribute")
                    if not attr: continue 
                    
                    # Safe stat check
                    stat_val = self.builder.current_stats.get(attr, 0)
                    if stat_val >= 12:
                        valid_powers.append(row)
                
                x, y = 30, 150
                self.buttons.append(Button((x, y-40, 500, 30), "SELECT 2 TIER 1 ABILITIES (Stat >= 12):", "NONE"))
                
                y_offset = 0
                col = 0
                for row in valid_powers:
                    p_name = row.get("Name")
                    p_sch = row.get("School")
                    p_type = row.get("Type")
                    bid = f"SELECT_POWER_{p_name}"
                    label = f"{p_name} ({p_sch} {p_type})"
                    
                    bx = 30 + col * 340
                    by = 150 + y_offset
                    
                    desc = row.get("Description", "")
                    self.buttons.append(Button((bx, by, 330, 40), label, bid, desc))
                    
                    y_offset += 50
                    # Wrap column if full
                    if 150 + y_offset > SCREEN_H - 120:
                        y_offset = 0
                        col += 1
                        
            except Exception as e:
                import traceback
                with open("crash_log.txt", "a") as f:
                    f.write(f"Step 14 Crash: {e}\n")
                    traceback.print_exc(file=f)

        # 15. GEAR
        elif self.wizard_step == 15:
            x, y = 50, 120
            self.buttons.append(Button((x, y, 300, 30), f"GOLD: {self.builder.money}", "NONE"))
            y += 40
            for item in self.data.gear:
                # Handle potential BOM in keys or mismatched headers
                name = item.get("Name") or item.get("Item") or item.get("\ufeffName")
                if not name: continue
                
                cost_val = item.get("Cost") or item.get("Value") or "999"
                # Strip non-numeric chars (e.g. '50 gp' -> '50')
                import re
                c_clean = re.sub(r"[^0-9]", "", str(cost_val))
                try: 
                    cost = int(c_clean)
                except: 
                    cost = 999
                
                wtype = item.get("Type", "Unknown")
                
                if cost <= self.builder.money:
                    label = f"{name} ({cost}g) - {wtype}"
                    bid = f"BUY_{name}"
                    self.buttons.append(Button((x, y, 400, 30), label, bid))
                    y += 35
                    if y > SCREEN_H - 100: 
                        x += 420; y = 160

        # 16. SUMMARY
        elif self.wizard_step == 16:
             self.buttons.append(Button((SCREEN_W//2 - 100, SCREEN_H - 150, 200, 60), "SAVE & FINISH", "SAVE"))

    def draw_split_choice(self, title1, labels1, tags1, title2, labels2, tags2):
        x, y = 50, 120
        self.buttons.append(Button((x, y, 400, 30), f"--- {title1} ---", "NONE"))
        y += 40
        for i, lab in enumerate(labels1):
            tag = tags1[i]
            bid = f"SELECT_SKILL_{tag}"
            self.buttons.append(Button((x, y, 400, 40), lab, bid))
            y += 50
        x = 500
        y = 120
        self.buttons.append(Button((x, y, 400, 30), f"--- {title2} ---", "NONE"))
        y += 40
        for i, lab in enumerate(labels2):
            tag = tags2[i]
            bid = f"SELECT_SKILL_{tag}"
            self.buttons.append(Button((x, y, 400, 40), lab, bid))
            y += 50

    def generate_random(self):
        import random
        self.builder = CharacterBuilder()
        self.builder.name = f"Random_{random.randint(100,999)}"
        
        # 1. Species
        sps = list(self.data.species_stats.keys())
        if not sps: return
        self.builder.species = random.choice(sps)
        self.builder.init_stats(self.data.species_stats.get(self.builder.species, {}))
        
        # 2-7. Evolutions (6 categories, one choice each)
        evos = self.data.evolutions.get(self.builder.species, [])
        cats = {}
        for r in evos:
            c = r.get("Category")
            if c not in cats: cats[c] = []
            cats[c].append(r)
            
        for c in cats:
            if not cats[c]: continue
            choice = random.choice(cats[c])
            # Add the Choice Name to traits (recalc_stats will process stats + body parts)
            trait_name = choice.get("Choice Name")
            if trait_name:
                self.builder.traits.append(trait_name)
        
        # Apply all stat bonuses and body parts
        self.recalc_stats()
                    
        # 8-10. Backgrounds
        # Origin
        if self.data.backgrounds["Origin"]:
            bg = random.choice(self.data.backgrounds["Origin"])
            self.select_background_skill(bg.get("Skill Name") or bg.get("Skill"))

        # Education
        if self.data.backgrounds["Education"]:
             bg = random.choice(self.data.backgrounds["Education"])
             self.select_background_skill(bg.get("Skill Name") or bg.get("Skill"))
             
        # Adulthood
        if self.data.backgrounds["Adulthood"]:
            bg = random.choice(self.data.backgrounds["Adulthood"])
            grp = bg.get("Family Name")
            if grp: self.builder.armor_prof.append(grp)
            
        # 11. Training
        if self.data.weapon_groups:
             wg = random.sample(self.data.weapon_groups, min(2, len(self.data.weapon_groups)))
             for g in wg:
                 self.builder.skills.append(g.get("Family Name"))
                 
        # 12. Catalyst
        utils = [r for r in self.data.all_skills if r.get("Type") == "Utility"]
        if utils: self.builder.skills.append(random.choice(utils).get("Skill Name"))
        
        tools = self.data.tool_types
        if tools: self.builder.skills.append(random.choice(tools).get("Tool_Name"))
        
        # 13. Species Skill
        sp_skills = self.data.skills.get(self.builder.species, [])
        valid_sp = []
        for s in sp_skills:
            req = s.get("Body Part") or s.get("Required Body Part")
            if req and req in self.builder.body_parts:
                valid_sp.append(s)
        if valid_sp:
             self.builder.skills.append(random.choice(valid_sp).get("Skill Name"))
             
        # 14. Schools (Tier 1 Spells)
        schools = self.data.abilities.get("Schools", [])
        valid_t1 = []
        for s in schools:
             if str(s.get("Tier")) == "1":
                 attr = s.get("Attribute")
                 if self.builder.current_stats.get(attr, 0) >= 12:
                     p_name = s.get("Name")
                     if p_name: valid_t1.append(p_name)

        if valid_t1:
            picks = random.sample(valid_t1, min(2, len(valid_t1)))
            self.builder.powers.extend(picks)
            
        self.recalc_stats()
        
        self.state = "WIZARD"
        self.wizard_step = 16
        self.buttons = []
        self.setup_wizard_ui()

    def draw(self):
        self.screen.fill(COLOR_BG)
        if self.state == "MENU": self.draw_menu()
        elif self.state == "WIZARD": self.draw_wizard()
        elif self.state == "MANAGE": self.draw_manage()
        pygame.display.flip()

    def draw_manage(self):
        t = self.title_font.render("MANAGE CHARACTERS", True, COLOR_ACCENT)
        self.screen.blit(t, (SCREEN_W//2 - t.get_width()//2, 50))
        
        if not self.buttons:
             # Scan saves
             if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
             files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
             
             x, y = SCREEN_W//2 - 200, 150
             if not files:
                 self.buttons.append(Button((x, y, 400, 40), "NO SAVES FOUND", "NONE"))
             else:
                 for f in files:
                     self.buttons.append(Button((x, y, 300, 40), f, "NONE"))
                     # Delete button logic requires unique IDs, but let's keep it simple for now or use lambda-like ID
                     self.buttons.append(Button((x+310, y, 80, 40), "DEL", f"DEL_{f}"))
                     y += 50
             
             self.buttons.append(Button((50, 50, 100, 40), "BACK", "BACK"))
             
        for b in self.buttons: b.draw(self.screen, self.font)

    def draw_menu(self):
        t = self.title_font.render("CHARACTER WIZARD", True, COLOR_ACCENT)
        self.screen.blit(t, (SCREEN_W//2 - t.get_width()//2, 100))
        if not self.buttons:
            cx = SCREEN_W // 2
            self.buttons = [
                Button((cx - 150, 250, 300, 50), "NEW CHARACTER", "NEW_CHAR"),
                Button((cx - 150, 320, 300, 50), "RANDOM CHARACTER", "RANDOM"),
                Button((cx - 150, 390, 300, 50), "MANAGE CHARACTERS", "MANAGE"),
                Button((cx - 150, 550, 300, 50), "EXIT", "EXIT")
            ]
        for b in self.buttons: b.draw(self.screen, self.font)

    def draw_wizard(self):
        pygame.draw.rect(self.screen, COLOR_PANEL, (0,0,SCREEN_W, 80))
        step_title = "SETUP"
        if self.wizard_step == 1: step_title = "BASICS: Name & Species"
        elif 2 <= self.wizard_step <= 7:
            cats = ["ANCESTRY", "DEFENSE", "OFFENSE", "SOCIAL", "ENVIRON", "ADAPT"]
            step_title = f"EVOLUTION ({self.wizard_step-1}/6): {cats[self.wizard_step - 2]}"
        elif 8 <= self.wizard_step <= 10:
            ts = ["ORIGIN", "EDUCATION", "ADULTHOOD"]
            step_title = f"BACKGROUND: {ts[self.wizard_step - 8]}"
        elif self.wizard_step == 11: step_title = "TRAINING: Melee & Ranged"
        elif self.wizard_step == 12: step_title = "CATALYST: Utility & Tool"
        elif self.wizard_step == 13: step_title = "SPECIES SKILL"
        elif self.wizard_step == 14: step_title = "ABILITIES (Select 2 Tier 1)"
        elif self.wizard_step == 15: step_title = "GEAR SHOP"
        elif self.wizard_step == 16: step_title = "SUMMARY"
            
        h = self.title_font.render(step_title, True, COLOR_TEXT)
        self.screen.blit(h, (20, 20))
        
        for b in self.buttons:
            is_sel = False
            if b.action_id.startswith("SELECT_SPECIES_") and self.builder.species.upper() == b.text: is_sel = True
            if b.action_id.startswith("SELECT_TRAIT_"):
                 trait = b.action_id.replace("SELECT_TRAIT_", "")
                 if trait in self.builder.traits: is_sel = True
            if b.action_id.startswith("SELECT_BG_"):
                 sk = b.action_id.replace("SELECT_BG_", "")
                 if sk in self.builder.skills: is_sel = True
            if b.action_id.startswith("SELECT_SKILL_"):
                 sk = b.action_id.replace("SELECT_SKILL_", "")
                 if sk in self.builder.skills: is_sel = True
            if b.action_id.startswith("SELECT_SPSKILL_"):
                 sk = b.action_id.replace("SELECT_SPSKILL_", "")
                 if sk in self.builder.skills: is_sel = True
            if b.action_id.startswith("SELECT_POWER_"):
                 sk = b.action_id.replace("SELECT_POWER_", "")
                 if sk in self.builder.powers: is_sel = True
                 
            b.draw(self.screen, self.font, is_sel)

        self.draw_sheet()
        
        if self.hover_text:
            mx, my = pygame.mouse.get_pos()
            surf = self.font.render(self.hover_text, True, COLOR_HIGHLIGHT)
            pygame.draw.rect(self.screen, (0,0,0), (mx+10, my+10, surf.get_width()+10, 30))
            self.screen.blit(surf, (mx+15, my+15))
            
        if self.validation_error:
            # Draw centralized error message
            surf = self.title_font.render(self.validation_error, True, (255, 50, 50))
            rect = surf.get_rect(center=(SCREEN_W//2, SCREEN_H - 100))
            pygame.draw.rect(self.screen, (20,0,0), rect.inflate(20, 10))
            pygame.draw.rect(self.screen, (255,0,0), rect.inflate(20, 10), 2)
            self.screen.blit(surf, rect)
            
        if self.input_active:
             pygame.draw.rect(self.screen, (0,0,0), (0,0,SCREEN_W,SCREEN_H), 200)
             txt = self.title_font.render(self.input_text + "_", True, COLOR_ACCENT)
             self.screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H//2))

    def draw_sheet(self):
        p = pygame.Rect(SCREEN_W-350, 80, 350, SCREEN_H-80)
        pygame.draw.rect(self.screen, (30,30,35), p)
        pygame.draw.rect(self.screen, COLOR_ACCENT, p, 2)
        
        x, y = p.x + 20, p.y + 20
        self.screen.blit(self.title_font.render(self.builder.name, True, COLOR_HIGHLIGHT), (x, y)); y+=40
        self.screen.blit(self.font.render(self.builder.species, True, COLOR_TEXT), (x, y)); y+=30
        y += 10
        pygame.draw.line(self.screen, COLOR_PANEL, (x, y), (x+300, y)); y+=10
        
        # Stats
        for k, v in self.builder.current_stats.items():
            col = COLOR_TEXT
            if v > self.builder.attributes.get(k, 0): col = COLOR_SELECTED
            self.screen.blit(self.font.render(f"{k}: {v}", True, col), (x, y))
            y += 24
            
        y += 10
        # Derived
        der = getattr(self.builder, "derived", {})
        if der:
             line = f"HP:{der.get('HP')} SP:{der.get('SP')} FP:{der.get('FP')}"
             self.screen.blit(self.font.render(line, True, COLOR_HIGHLIGHT), (x, y)); y+=20
             line2 = f"CMP:{der.get('CMP')} SPD:{der.get('Speed')}"
             self.screen.blit(self.font.render(line2, True, COLOR_HIGHLIGHT), (x, y)); y+=20
        
        y += 10
        self.screen.blit(self.font.render("Body Parts:", True, COLOR_HIGHLIGHT), (x, y)); y+=25
        for bp in self.builder.body_parts:
            self.screen.blit(self.font.render(f" - {bp}", True, (180,180,180)), (x, y)); y+=20
            
        y += 10
        self.screen.blit(self.font.render("Skills:", True, COLOR_HIGHLIGHT), (x, y)); y+=25
        for sk in self.builder.skills:
            self.screen.blit(self.font.render(f" - {sk}", True, (150,200,150)), (x, y)); y+=20
            
        y += 10
        self.screen.blit(self.font.render("Powers:", True, COLOR_HIGHLIGHT), (x, y)); y+=25
        for p in self.builder.powers:
            self.screen.blit(self.font.render(f" - {p}", True, (200,150,255)), (x, y)); y+=20

if __name__ == "__main__":
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    App().run()
