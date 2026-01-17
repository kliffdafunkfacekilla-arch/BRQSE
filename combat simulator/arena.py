import pygame
import sys
import os
import mechanics

# Constants
SCREEN_W, SCREEN_H = 1000, 700
COLOR_BG = (20, 20, 30)
COLOR_PANEL = (40, 40, 50)
COLOR_TEXT = (220, 220, 220)
COLOR_BTN = (60, 60, 80)
COLOR_BTN_HOVER = (80, 80, 100)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVES_DIR = os.path.join(BASE_DIR, "../Saves")

class Button:
    def __init__(self, rect, text, callback, args=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.args = args or []
        self.hover = False

    def draw(self, screen, font):
        col = COLOR_BTN_HOVER if self.hover else COLOR_BTN
        pygame.draw.rect(screen, col, self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 1)
        
        surf = font.render(self.text, True, COLOR_TEXT)
        rect = surf.get_rect(center=self.rect.center)
        screen.blit(surf, rect)

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback(*self.args)

class ArenaApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Combat Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier New", 16)
        
        self.state = "SELECT" # SELECT, COMBAT
        self.buttons = []
        
        self.engine = mechanics.CombatEngine()
        self.fighter1 = None
        self.fighter2 = None
        
        self.log_lines = []
        self.winner_text = ""

    def run(self):
        self.scan_saves()
        while True:
            self.handle_input()
            self.draw()
            self.clock.tick(30)

    def scan_saves(self):
        self.buttons = []
        if not os.path.exists(SAVES_DIR):
            os.makedirs(SAVES_DIR)
        
        files = [f for f in os.listdir(SAVES_DIR) if f.endswith(".json")]
        
        if self.state == "SELECT":
            y = 100
            for f in files:
                path = os.path.join(SAVES_DIR, f)
                # Left Button (Fighter 1)
                self.buttons.append(Button((50, y, 300, 40), f"P1: {f}", self.select_fighter, [1, path]))
                # Right Button (Fighter 2)
                self.buttons.append(Button((400, y, 300, 40), f"P2: {f}", self.select_fighter, [2, path]))
                y += 50
                
            if self.fighter1 and self.fighter2:
                self.buttons.append(Button((300, y+50, 200, 50), "START COMBAT", self.start_combat))

        elif self.state == "COMBAT":
            self.buttons.append(Button((SCREEN_W//2 - 100, SCREEN_H - 100, 200, 50), "NEXT ROUND", self.next_round))
            self.buttons.append(Button((20, 20, 100, 30), "RESET", self.reset))

    def select_fighter(self, slot, path):
        c = mechanics.Combatant(path)
        if slot == 1: self.fighter1 = c
        else: self.fighter2 = c
        self.scan_saves() # Refresh buttons to maybe show selection (would need more logic, but this is fine)

    def start_combat(self):
        if not self.fighter1 or not self.fighter2: return
        self.engine = mechanics.CombatEngine()
        self.engine.add_combatant(self.fighter1)
        self.engine.add_combatant(self.fighter2)
        
        # Roll Initiative
        self.fighter1.roll_initiative()
        self.fighter2.roll_initiative()
        
        self.log_lines = ["Combat Started!", f"{self.fighter1.name} Init: {self.fighter1.initiative}", f"{self.fighter2.name} Init: {self.fighter2.initiative}"]
        self.state = "COMBAT"
        self.scan_saves()

    def reset(self):
        self.fighter1 = None
        self.fighter2 = None
        self.winner_text = ""
        self.state = "SELECT"
        self.scan_saves()

    def next_round(self):
        if self.winner_text: return
        
        results = self.engine.resolve_round()
        self.log_lines.extend(results)
        
        if len(self.log_lines) > 14:
            self.log_lines = self.log_lines[-14:]
            
        # Check Win
        if not self.fighter1.is_alive(): self.winner_text = f"{self.fighter2.name} WINS!"
        elif not self.fighter2.is_alive(): self.winner_text = f"{self.fighter1.name} WINS!"

    def handle_input(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEMOTION:
                for b in self.buttons: b.hover = b.rect.collidepoint(mouse_pos)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for b in self.buttons: b.check_click(mouse_pos)

    def draw(self):
        self.screen.fill(COLOR_BG)
        
        if self.state == "SELECT":
            t = self.font.render("SELECT FIGHTERS", True, COLOR_TEXT)
            self.screen.blit(t, (50, 20))
            if self.fighter1:
                self.screen.blit(self.font.render(f"P1: {self.fighter1.name}", True, (100,255,100)), (50, 60))
            if self.fighter2:
                self.screen.blit(self.font.render(f"P2: {self.fighter2.name}", True, (100,255,100)), (400, 60))
                
        elif self.state == "COMBAT":
            # Draw Fighters
            self.draw_char(self.fighter1, 50, 100)
            self.draw_char(self.fighter2, 600, 100)
            
            # Draw Log
            pygame.draw.rect(self.screen, (0,0,0), (50, 300, 900, 300))
            y = 310
            for line in self.log_lines:
                self.screen.blit(self.font.render(line, True, COLOR_TEXT), (60, y))
                y += 20
                
            if self.winner_text:
                s = pygame.font.SysFont("Arial", 48, bold=True).render(self.winner_text, True, (255, 50, 50))
                self.screen.blit(s, (SCREEN_W//2 - s.get_width()//2, 50))

        for b in self.buttons:
            b.draw(self.screen, self.font)
            
        pygame.display.flip()

    def draw_char(self, char, x, y):
        # Name
        self.screen.blit(self.font.render(char.name, True, (255,200,50)), (x, y))
        y += 25
        # HP Bar
        hp_pct = max(0, char.current_hp / char.max_hp)
        pygame.draw.rect(self.screen, (50,0,0), (x, y, 200, 20))
        pygame.draw.rect(self.screen, (0,200,0), (x, y, 200*hp_pct, 20))
        self.screen.blit(self.font.render(f"{char.current_hp}/{char.max_hp}", True, (255,255,255)), (x+80, y))
        y += 30
        
        # Stats
        for k, v in char.stats.items():
            self.screen.blit(self.font.render(f"{k}: {v}", True, (150,150,150)), (x, y))
            y += 20

if __name__ == "__main__":
    ArenaApp().run()
