import pygame
import sys
import os
import mechanics
import enemy_spawner

# Add parent path for AI module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from AI.enemy_ai import EnemyAI, Behavior

# Constants
SCREEN_W, SCREEN_H = 1000, 700
TILE_SIZE = 50
GRID_COLS, GRID_ROWS = 12, 12
OFFSET_X, OFFSET_Y = 50, 50

COLOR_BG = (20, 20, 30)
COLOR_GRID = (60, 60, 70)
COLOR_TILE_HOVER = (80, 80, 100)
COLOR_P1 = (100, 200, 100)
COLOR_P2 = (200, 100, 100)
COLOR_TURN = (255, 255, 100)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVES_DIR = os.path.join(BASE_DIR, "../Saves")

class Button:
    def __init__(self, rect, text, callback, args=None, active=True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.args = args or []
        self.hover = False
        self.active = active

    def draw(self, screen, font):
        if not self.active: return
        col = (80, 80, 100) if self.hover else (60, 60, 80)
        pygame.draw.rect(screen, col, self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 1)
        surf = font.render(self.text, True, (220, 220, 220))
        rect = surf.get_rect(center=self.rect.center)
        screen.blit(surf, rect)

    def check_click(self, pos):
        if self.active and self.rect.collidepoint(pos):
            self.callback(*self.args)

class ArenaApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Tactical Combat Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier New", 14)
        self.header_font = pygame.font.SysFont("Courier New", 20, bold=True)
        
        self.state = "SELECT"
        self.buttons = []
        self.engine = mechanics.CombatEngine()
        self.fighter1 = None
        self.fighter2 = None
        self.selected_tile = None
        self.log_lines = []
        self.pending_ability = None
        
        # Enemy Spawner
        self.ai_templates = enemy_spawner.get_ai_templates()
        self.selected_ai_template = self.ai_templates[0] if self.ai_templates else "Aggressive"
        
        # AI Controller (initialized when combat starts)
        self.ai = None
        
    def run(self):
        self.scan_saves()
        while True:
            self.handle_input()
            self.draw()
            self.clock.tick(30)

    def scan_saves(self):
        self.buttons = []
        if self.state == "SELECT":
            if not os.path.exists(SAVES_DIR): os.makedirs(SAVES_DIR)
            files = [f for f in os.listdir(SAVES_DIR) if f.endswith(".json")]
            y = 100
            for f in files:
                path = os.path.join(SAVES_DIR, f)
                self.buttons.append(Button((50, y, 300, 40), f"P1: {f}", self.select_fighter, [1, path]))
                self.buttons.append(Button((400, y, 300, 40), f"P2: {f}", self.select_fighter, [2, path]))
                y += 50
            
            # AI Template Selection
            y += 30
            self.buttons.append(Button((50, y, 180, 40), f"AI: {self.selected_ai_template}", self.cycle_ai_template))
            self.buttons.append(Button((250, y, 200, 40), "Spawn Enemy (P2)", self.spawn_enemy))
            
            if self.fighter1 and self.fighter2:
                self.buttons.append(Button((500, y, 200, 50), "START MAP", self.start_combat))

        elif self.state == "COMBAT":
            self.buttons.append(Button((800, 50, 150, 40), "End Turn", self.end_turn))
            self.buttons.append(Button((800, 100, 150, 40), "Reset", self.reset))

            if self.engine.clash_active:
                 self.buttons.append(Button((SCREEN_W//2 - 150, SCREEN_H//2, 100, 50), "PRESS", self.resolve_clash, ["PRESS"]))
                 self.buttons.append(Button((SCREEN_W//2 + 50, SCREEN_H//2, 100, 50), "DEFEND", self.resolve_clash, ["DEFEND"]))
            else:
                 # Active Powers
                 active_char = self.engine.get_active_char()
                 if active_char:
                     # Check Powers for "Active" keyword? Or just list all Powers?
                     # Let's list all "Powers" for now.
                     y_off = 200
                     for p_name in active_char.powers:
                         self.buttons.append(Button((800, y_off, 180, 40), p_name, self.activate_power_click, [active_char, p_name]))
                         y_off += 50
                     for t_name in active_char.traits:
                         if "Active" in t_name: # Convention? Or just list?
                             self.buttons.append(Button((800, y_off, 180, 40), t_name, self.activate_power_click, [active_char, t_name]))
                             y_off += 50

    def activate_power_click(self, char, power_name):
         # Enter Targeting Mode
         # We could check if ability is "Self" only, but for now let's allow targeting for everything
         # or heuristic check based on "Attack" vs "Heal".
         # Simplest: Enter TARGETING mode, prompt "Select Target".
         self.state = "TARGETING"
         self.pending_ability = (char, power_name)
         self.log_lines.append(f"Select Target for {power_name}...")

    def activate_power_execute(self, target):
         char, power_name = self.pending_ability
         res = self.engine.activate_ability(char, power_name, target)
         self.log_lines.extend(res)
         self.state = "COMBAT"
         self.pending_ability = None
         self.scan_saves()

    def select_fighter(self, slot, path):
        c = mechanics.Combatant(path)
        if slot == 1: self.fighter1 = c
        else: self.fighter2 = c
        self.scan_saves()

    def cycle_ai_template(self):
        idx = self.ai_templates.index(self.selected_ai_template)
        self.selected_ai_template = self.ai_templates[(idx + 1) % len(self.ai_templates)]
        self.scan_saves()

    def spawn_enemy(self):
        path = enemy_spawner.spawner.generate(self.selected_ai_template)
        c = mechanics.Combatant(path)
        self.fighter2 = c
        self.log_lines.append(f"Spawned: {c.name} (AI: {self.selected_ai_template})")
        self.scan_saves()

    def start_combat(self):
        self.engine = mechanics.CombatEngine()
        # Initial positions
        self.engine.add_combatant(self.fighter1, 3, 3)
        self.engine.add_combatant(self.fighter2, 8, 8)
        
        # Initialize AI controller
        self.ai = EnemyAI(self.engine)
        
        self.log_lines = self.engine.start_combat()
        self.state = "COMBAT"
        self.scan_saves()

    def reset(self):
        self.fighter1 = None; self.fighter2 = None
        self.state = "SELECT"
        self.engine = mechanics.CombatEngine()
        self.scan_saves()

    def end_turn(self):
        if self.engine.clash_active: return
        res = self.engine.end_turn()
        self.log_lines.extend(res)
        
        # Check if new active char is AI-controlled
        active = self.engine.get_active_char()
        if active and active.data.get("AI"):
            # Map AI template to Behavior
            ai_template = active.data.get("AI", "Aggressive")
            behavior_map = {
                "Aggressive": Behavior.AGGRESSIVE,
                "Defensive": Behavior.CAMPER,
                "Ranged": Behavior.RANGED,
                "Berserker": Behavior.AGGRESSIVE,
                "Caster": Behavior.CASTER,
                "Spellblade": Behavior.SPELLBLADE,
            }
            behavior = behavior_map.get(ai_template, Behavior.AGGRESSIVE)
            
            # Execute AI turn using full EnemyAI module
            ai_log = self.ai.take_turn(active, behavior)
            self.log_lines.extend(ai_log)
            
            # Automatically end their turn
            res = self.engine.end_turn()
            self.log_lines.extend(res)
        
        self.scan_saves() # Refresh buttons

    def resolve_clash(self, choice):
        res = self.engine.resolve_clash(choice)
        self.log_lines.extend(res)
        self.scan_saves()

    def handle_grid_click(self, gx, gy):
        if self.state == "TARGETING":
            # Find target
            target = None
            for c in self.engine.combatants:
                 if c.is_alive() and c.x == gx and c.y == gy:
                     target = c; break
            if target:
                self.activate_power_execute(target)
            else:
                self.log_lines.append("Invalid Target! Click a unit.")
            return

        if self.state != "COMBAT": return
        if self.engine.clash_active: return
        
        actor = self.engine.get_active_char()
        if not actor: return

        # Check if clicked on enemy -> Attack
        target = None
        for c in self.engine.combatants:
            if c.is_alive() and c.x == gx and c.y == gy:
                target = c
                break
        
        if target:
            if target == actor: return # self click
            res = self.engine.attack_target(actor, target)
            self.log_lines.extend(res)
            self.scan_saves() # update if clash
        else:
            # Move
            success, msg = self.engine.move_char(actor, gx, gy)
            self.log_lines.append(msg)
            self.scan_saves() # Refresh buttons for movement update if needed

    def handle_input(self):
        mx, my = pygame.mouse.get_pos()
        # Map Grid Selection
        gx = (mx - OFFSET_X) // TILE_SIZE
        gy = (my - OFFSET_Y) // TILE_SIZE
        self.selected_tile = (gx, gy) if 0 <= gx < GRID_COLS and 0 <= gy < GRID_ROWS else None

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEMOTION:
                for b in self.buttons: b.hover = b.rect.collidepoint((mx, my))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # UI Buttons
                clicked_btn = False
                for b in self.buttons:
                    if b.rect.collidepoint((mx, my)):
                        b.check_click((mx, my))
                        clicked_btn = True
                        break
                # Map Click
                if not clicked_btn and self.selected_tile:
                    self.handle_grid_click(*self.selected_tile)
                
                # Right Click to Cancel Targeting
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if self.state == "TARGETING":
                    self.state = "COMBAT"
                    self.log_lines.append("Targeting Cancelled.")


    def draw(self):
        self.screen.fill(COLOR_BG)
        
        if self.state == "COMBAT":
            # 1. Draw Grid
            for y in range(GRID_ROWS):
                for x in range(GRID_COLS):
                    rect = (OFFSET_X + x*TILE_SIZE, OFFSET_Y + y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    col = COLOR_GRID
                    if self.selected_tile == (x,y) and not self.engine.clash_active:
                        col = COLOR_TILE_HOVER
                    pygame.draw.rect(self.screen, col, rect, 1)

            # 2. Draw Combatants
            for c in self.engine.combatants:
                if not c.is_alive(): continue
                cx = OFFSET_X + c.x * TILE_SIZE
                cy = OFFSET_Y + c.y * TILE_SIZE
                
                # Active Highlight
                if c == self.engine.get_active_char():
                    pygame.draw.rect(self.screen, COLOR_TURN, (cx+2, cy+2, TILE_SIZE-4, TILE_SIZE-4), 2)
                    
                col = COLOR_P1 if c == self.fighter1 else COLOR_P2
                pygame.draw.circle(self.screen, col, (cx + TILE_SIZE//2, cy + TILE_SIZE//2), TILE_SIZE//3)
                
                # HP Bar
                pct = c.hp / c.max_hp
                pygame.draw.rect(self.screen, (255,0,0), (cx+5, cy-8, 40, 5))
                pygame.draw.rect(self.screen, (0,255,0), (cx+5, cy-8, 40*pct, 5))
                
                # Status Effect Icons (compact text)
                status_icons = []
                if c.is_stunned: status_icons.append("STN")
                if c.is_poisoned: status_icons.append("PSN")
                if c.is_frightened: status_icons.append("FRG")
                if c.is_charmed: status_icons.append("CHM")
                if c.is_paralyzed: status_icons.append("PRL")
                if c.is_prone: status_icons.append("PRN")
                if c.is_blinded: status_icons.append("BLD")
                if c.is_grappled: status_icons.append("GRP")
                if c.is_restrained: status_icons.append("RST")
                if c.is_sanctuary: status_icons.append("SNC")
                if c.is_confused: status_icons.append("CNF")
                if c.is_berserk: status_icons.append("BRK")
                
                if status_icons:
                    status_text = " ".join(status_icons[:3]) # Limit to 3 shown
                    status_surf = self.font.render(status_text, True, (255, 200, 50))
                    self.screen.blit(status_surf, (cx, cy + TILE_SIZE - 10))

            # 3. HUD
            pygame.draw.rect(self.screen, (10,10,20), (0, 600, SCREEN_W, 100))
            for i, line in enumerate(reversed(self.log_lines[-6:])):
                col = (255,255,255)
                if "HIT" in line: col = (255,100,100)
                if "CLASH" in line: col = (255,255,100)
                img = self.font.render(line, True, col)
                self.screen.blit(img, (20, 680 - i*15))

            if self.engine.clash_active:
                 s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                 s.fill((0,0,0,180))
                 self.screen.blit(s, (0,0))
                 self.screen.blit(self.header_font.render("CLASH TRIGGERED!", True, (255,50,50)), (400, 300))

        # Buttons
        if self.state == "SELECT":
             self.screen.blit(self.header_font.render("Select Map Layout", True, (255,255,255)), (50, 20))

        for b in self.buttons: b.draw(self.screen, self.font)
        
        pygame.display.flip()

if __name__ == "__main__":
    ArenaApp().run()
