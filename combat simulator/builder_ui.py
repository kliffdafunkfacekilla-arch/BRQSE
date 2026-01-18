
import pygame
import os
import csv
import json

# --- CONSTANTS ---
COLOR_BG = (20, 20, 30)
COLOR_PANEL = (40, 40, 50)
COLOR_TEXT = (220, 220, 220)
COLOR_ACCENT = (100, 200, 255)
COLOR_BTN = (60, 60, 70)
COLOR_BTN_HOVER = (80, 80, 100)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../Data")

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
        # 1. Species
        rows = self.load_csv("Species.csv")
        if rows:
            headers = [k for k in rows[0].keys() if k not in ["Attribute", "Reference", ""]]
            for sp in headers:
                self.species_stats[sp] = {}
                for row in rows:
                    attr = row.get("Attribute")
                    val = row.get(sp)
                    try: self.species_stats[sp][attr] = int(val)
                    except: pass
        
        # 2. Evolutions & Skills
        for sp in self.species_stats:
            self.evolutions[sp] = self.load_csv(f"{sp}.csv")
            self.skills[sp] = self.load_csv(f"{sp}_Skills.csv")
            
        # 3. Lists
        self.weapon_groups = self.load_csv("Weapon_Groups.csv")
        self.armor_groups = self.load_csv("Armor_Groups.csv")
        self.social_off = self.load_csv("Social_Off.csv")
        self.social_def = self.load_csv("Social_Def.csv")
        self.utility_skills = [r for r in self.load_csv("Skills.csv") if r.get("Type") == "Utility"]
        self.tool_skills = self.load_csv("Tool_types.csv")
        
        # 4. Powers
        self.spells_t1 = [r for r in self.load_csv("Schools of Power.csv") if str(r.get("Tier")) == "1"]
        self.power_power = [r for r in self.load_csv("Power_Power.csv") if str(r.get("Tier")) == "1"]
        self.power_shapes = [r for r in self.load_csv("Power_Shapes.csv") if str(r.get("Tier")) == "1"]
        self.power_targets = [r for r in self.load_csv("Power_Targets.csv") if str(r.get("Tier")) == "1"] # Speculated file name?
        
        # 5. Gear
        self.all_gear = self.load_csv("weapons_and_armor.csv")

class Dropdown:
    def __init__(self, x, y, w, h, options, placeholder="Select..."):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options # List of strings or dictionaries
        self.selected = None
        self.placeholder = placeholder
        self.is_open = False
        self.font = pygame.font.SysFont("Arial", 14)
        self.scroll = 0
        
    def draw(self, screen):
        # Main Box
        pygame.draw.rect(screen, COLOR_BTN, self.rect)
        pygame.draw.rect(screen, (200,200,200), self.rect, 1)
        
        txt = self.selected if self.selected else self.placeholder
        # If options are dicts, assumes they have 'Name' key, likely handled via helper? 
        # For simplicity, options should be strings here.
        
        surf = self.font.render(str(txt)[:25], True, COLOR_TEXT)
        screen.blit(surf, (self.rect.x + 5, self.rect.y + 5))
        
        # Dropdown List
        if self.is_open:
            h = len(self.options) * 25
            if h > 300: h = 300
            list_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.h, self.rect.w, h)
            pygame.draw.rect(screen, COLOR_PANEL, list_rect)
            pygame.draw.rect(screen, (100,100,100), list_rect, 1)
            
            for i, opt in enumerate(self.options):
                # Basic scroll not impl. Just clip.
                dy = i * 25
                if dy > 275: break
                
                opt_rect = pygame.Rect(list_rect.x, list_rect.y + dy, list_rect.w, 25)
                color = COLOR_BTN_HOVER if opt_rect.collidepoint(pygame.mouse.get_pos()) else COLOR_PANEL
                pygame.draw.rect(screen, color, opt_rect)
                
                s_txt = self.font.render(str(opt)[:30], True, COLOR_TEXT)
                screen.blit(s_txt, (opt_rect.x + 5, opt_rect.y + 2))
                
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.is_open:
                    # Check list clicks
                    h = min(len(self.options) * 25, 300)
                    list_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.h, self.rect.w, h)
                    if list_rect.collidepoint(event.pos):
                        idx = (event.pos[1] - list_rect.y) // 25
                        if 0 <= idx < len(self.options):
                            self.selected = self.options[idx]
                            self.is_open = False
                            return True # Changed
                    else:
                        self.is_open = False
                elif self.rect.collidepoint(event.pos):
                    self.is_open = not self.is_open
        return False

class BuilderUI:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Courier New", 16)
        self.data = DataManager()
        
        # State
        self.name = "Hero"
        self.points_remaining = 12
        self.stats = {
            "Might": 10, "Reflexes": 10, "Endurance": 10, "Vitality": 10,
            "Fortitude": 10, "Knowledge": 10, "Logic": 10, "Awareness": 10,
            "Intuition": 10, "Charm": 10, "Willpower": 10, "Finesse": 10
        }
        self.allocations = {k:0 for k in self.stats}
        
        # Dropdowns
        self.dd_species = Dropdown(100, 50, 150, 30, list(self.data.species_stats.keys()), "Species")
        
        # Traits (6)
        self.dd_traits = [Dropdown(50 + i*160, 350, 150, 30, [], f"Trait {i+1}") for i in range(6)]
        
        # Skills (7)
        self.dd_skills = {
            "Melee": Dropdown(50, 450, 150, 30, [x['Family Name'] for x in self.data.weapon_groups if x['Type'] == 'Melee'], "Melee Skill"),
            "Ranged": Dropdown(210, 450, 150, 30, [x['Family Name'] for x in self.data.weapon_groups if x['Type'] == 'Ranged'], "Ranged Skill"),
            "Soc Off": Dropdown(370, 450, 150, 30, [x['Skill Name'] for x in self.data.social_off], "Social Off"),
            "Soc Def": Dropdown(530, 450, 150, 30, [x['Skill Name'] for x in self.data.social_def], "Social Def"),
            "Armor": Dropdown(690, 450, 150, 30, [x['Family Name'] for x in self.data.armor_groups], "Armor Skill"),
            "Utility": Dropdown(50, 500, 150, 30, [x['Skill Name'] for x in self.data.utility_skills], "Utility"),
            "Tool": Dropdown(210, 500, 150, 30, [x['Tool_Name'] for x in self.data.tool_skills], "Tool"),
            "Species": Dropdown(370, 500, 200, 30, [], "Species Ability"),
        }
        
        # Spells (2)
        self.dd_spells = [Dropdown(50 + i*250, 600, 240, 30, [], f"Spell {i+1}") for i in range(2)]
        
        # Gear
        self.dd_gear = {
            "Weapon": Dropdown(600, 600, 200, 30, [x['Name'] for x in self.data.all_gear if x.get('Type') == 'Weapon'], "Weapon"),
            "Armor": Dropdown(810, 600, 200, 30, [x['Name'] for x in self.data.all_gear if x.get('Type') == 'Armor'], "Armor"),
        }
        
        self.active_dd = None # To handle click blocking

    def update_stats(self):
        # Reset to base
        sp = self.dd_species.selected
        if not sp: return
        
        base = self.data.species_stats.get(sp, {})
        for k in self.stats:
            self.stats[k] = base.get(k, 10) + self.allocations[k]
            
        # Update Trait Options based on Species
        # Categories: Ancestry, Defense, Offense, Social, Environ, Adapt
        cats = ["ANCESTRY", "DEFENSE", "OFFENSE", "SOCIAL", "ENVIRON", "ADAPT"]
        sp_traits = self.data.evolutions.get(sp, [])
        
        for i, dd in enumerate(self.dd_traits):
            if i < len(cats):
                opts = [r["Choice Name"] for r in sp_traits if r["Category"] == cats[i]]
                dd.options = opts
                if dd.selected not in opts: dd.selected = None

        # Update Species Ability Options
        # Based on Body Parts from Traits
        # Need to calc body parts first
        body_parts = []
        for dd in self.dd_traits:
            if dd.selected:
                row = next((r for r in sp_traits if r["Choice Name"] == dd.selected), None)
                if row and row.get("Body Part"):
                    body_parts.append(row.get("Body Part"))
        
        sp_skills = self.data.skills.get(sp, [])
        valid_sp = []
        for s in sp_skills:
             req = s.get("Body Part") or s.get("Required Body Part")
             if req in body_parts:
                 valid_sp.append(s.get("Skill Name") or s.get("Skill"))
        
        self.dd_skills["Species"].options = valid_sp

        # Update Spells (Stat >= 12)
        valid_spells = []
        for r in self.data.spells_t1:
            attr = r.get("Attribute")
            if self.stats.get(attr, 0) >= 12:
                valid_spells.append(f"{r['Name']} ({attr})")
        for dd in self.dd_spells:
            dd.options = valid_spells


    def draw(self):
        self.screen.fill(COLOR_BG)
        # Name Input
        nm_surf = self.font.render(f"Name: {self.name}", True, COLOR_TEXT)
        self.screen.blit(nm_surf, (50, 20))
        
        # Species
        self.dd_species.draw(self.screen)
        
        # Stats
        y = 100
        x = 50
        pts_surf = self.font.render(f"Pool: {self.points_remaining}", True, COLOR_HIGHLIGHT)
        self.screen.blit(pts_surf, (50, 80))
        
        for k, v in self.stats.items():
            s_str = f"{k}: {v}"
            self.screen.blit(self.font.render(s_str, True, COLOR_TEXT), (x, y))
            
            # Buttons [-] [+]
            # Handled in event loop usually, but for simple UI logic:
            # We draw rects and check in event loop
            # Just visualization here
            pygame.draw.rect(self.screen, (100,50,50), (x+120, y, 20, 20)) # -
            pygame.draw.rect(self.screen, (50,100,50), (x+145, y, 20, 20)) # +
            
            if x > 500: 
                x = 50; y += 30
            else:
                x += 200
        
        # Traits
        for dd in self.dd_traits: dd.draw(self.screen)
            
        # Skills
        for k, dd in self.dd_skills.items():
            self.screen.blit(self.font.render(k, True,(150,150,150)), (dd.rect.x, dd.rect.y-15))
            dd.draw(self.screen)
            
        # Spells
        for i, dd in enumerate(self.dd_spells): dd.draw(self.screen)
        
        # Gear
        for k, dd in self.dd_gear.items(): dd.draw(self.screen)

        # Spawn Button
        rgb = (50, 200, 50) if self.points_remaining == 0 else (100,100,100)
        pygame.draw.rect(self.screen, rgb, (800, 700, 200, 50))
        self.screen.blit(self.font.render("SPAWN", True, (0,0,0)), (850, 715))

    def handle_event(self, event):
        # 1. Spawn Click
        if event.type == pygame.MOUSEBUTTONDOWN:
            if 800 <= event.pos[0] <= 1000 and 700 <= event.pos[1] <= 750:
                 return self.finalize()

            # 2. Stat Buttons
            # Hacky grid check
            y = 100; x = 50
            for k in self.stats:
                # [-]
                if pygame.Rect(x+120, y, 20, 20).collidepoint(event.pos):
                    if self.allocations[k] > -2: # Min check logic? (Base+Alloc >= 8) Usually Base=10 so -2=8.
                        self.allocations[k] -= 1
                        self.points_remaining += 1
                        self.update_stats()
                # [+]
                if pygame.Rect(x+145, y, 20, 20).collidepoint(event.pos):
                     if self.points_remaining > 0 and self.stats[k] < 18:
                         self.allocations[k] += 1
                         self.points_remaining -= 1
                         self.update_stats()
                
                if x > 500: x = 50; y += 30
                else: x += 200
        
        # 3. Dropdowns (Check Active first?)
        # Simple loop
        all_dds = [self.dd_species] + self.dd_traits + list(self.dd_skills.values()) + self.dd_spells + list(self.dd_gear.values())
        
        # Close others if opening one?
        # Just loop them. If one handles it, break?
        for dd in reversed(all_dds): # Draw order reverse for clicks
            if dd.handle_event(event):
                if dd == self.dd_species:
                    self.allocations = {k:0 for k in self.stats} # Reset points on species change
                    self.points_remaining = 12
                    self.update_stats()
                else:
                    self.update_stats() # Update filters
                break
        
        # 4. Name Input
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE: self.name = self.name[:-1]
            elif event.key == pygame.K_RETURN: pass
            else: self.name += event.unicode
            
    def finalize(self):
        # Validate?
        # Construct Combatant Data
        skills = []
        for dd in self.dd_skills.values():
            if dd.selected: skills.append(dd.selected.split(" (")[0]) # Remove parens if added
            
        traits = [dd.selected for dd in self.dd_traits if dd.selected]
        powers = [dd.selected.split(" (")[0] for dd in self.dd_spells if dd.selected]
        
        # Basic Derived (Mechanics will recalc, but good to set)
        
        data = {
            "Name": self.name,
            "Species": self.dd_species.selected,
            "Stats": self.stats.copy(),
            "Traits": traits,
            "Skills": skills,
            "Powers": powers,
            "Inventory": [
                self.dd_gear["Weapon"].selected,
                self.dd_gear["Armor"].selected
            ]
        }
        return data

