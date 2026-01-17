import pygame
import sys
import os
import random

# Fix imports relative to script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from char_engine import Character
from combat_engine import resolve_attack, resolve_clash_effect, resolve_channeling
from world_engine import ChaosManager, SceneStack

# CONSTANTS
SCREEN_W, SCREEN_H = 800, 600
C_BG = (20, 20, 30)
C_ARENA = (40, 40, 50)
C_PLAYER = (50, 150, 255)
C_ENEMY = (255, 50, 50)
C_TEXT = (200, 200, 200)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("CHAOS ENGINE V4: VISUAL")
        self.font = pygame.font.SysFont("Courier New", 18)
        self.clock = pygame.time.Clock()
        
        self.state = "EXPLORE" # EXPLORE, COMBAT, CLASH
        self.logs = ["Welcome to the Chaos Engine."]
        
        # Init Engines
        self.chaos = ChaosManager()
        self.world = SceneStack(self.chaos)
        self.world.generate_quest()
        
        # Create Player
        self.player = Character("Mammal", "Greatsword", "Plate")
        self.enemy = None
        self.current_scene = self.world.advance()

    def log(self, text):
        self.logs.append(text)
        if len(self.logs) > 6: self.logs.pop(0)

    def run(self):
        while True:
            self.handle_input()
            self.draw()
            self.clock.tick(30)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            if event.type == pygame.KEYDOWN:
                
                # --- STATE: EXPLORE ---
                if self.state == "EXPLORE":
                    if event.key == pygame.K_SPACE:
                        # Advance Scene
                        self.current_scene = self.world.advance()
                        self.log(f"Entered: {self.current_scene.text}")
                        
                        if self.current_scene.encounter_type == "COMBAT":
                            self.state = "COMBAT"
                            # Hydrate Enemy from Data
                            edata = self.current_scene.enemy_data
                            # Fix: Char params are species, weapon, armor. Map 'edata' keys.
                            self.enemy = Character(edata["Species"], edata["Weapon"], edata["Armor"])
                            self.log(f"Enemy: {self.enemy.species_name} w/ {self.enemy.weapon_name}!")
                            
                    elif event.key == pygame.K_r:
                        res = self.chaos.roll_tension()
                        self.log(f"Resting... {res}")
                        if res != "SAFE":
                            self.log("AMBUSH!")
                            self.state = "COMBAT"
                            self.enemy = Character("Insect", "Unarmed", "Exoskeleton") # Ambush spawn

                # --- STATE: COMBAT ---
                elif self.state == "COMBAT":
                    if event.key == pygame.K_a: # Attack
                        res = resolve_attack(self.player, self.enemy)
                        
                        if res["outcome"] == "THE CLASH":
                            self.state = "CLASH"
                            self.log("!!! CLASH TRIGGERED !!!")
                            self.log("Press [1] PRESS or [2] DISENGAGE")
                        else:
                            self.log(f"You: {res['desc']}")
                            self.enemy.current_hp -= res["damage"]
                            if self.enemy.current_hp <= 0:
                                self.log("VICTORY!")
                                self.state = "EXPLORE"
                                self.enemy = None
                            else:
                                # Enemy Turn (Simple)
                                e_res = resolve_attack(self.enemy, self.player)
                                self.log(f"Enemy: {e_res['desc']}")
                                self.player.current_hp -= e_res["damage"]

                # --- STATE: CLASH ---
                elif self.state == "CLASH":
                    if event.key == pygame.K_1: # PRESS (Weapon Stat)
                        effect = resolve_clash_effect("MIGHT", self.player, self.enemy)
                        self.log(f"PRESS: {effect}")
                        self.state = "COMBAT"
                    elif event.key == pygame.K_2: # DISENGAGE (Armor Stat)
                        effect = resolve_clash_effect("REFLEXES", self.player, self.enemy)
                        self.log(f"DISENGAGE: {effect}")
                        self.state = "COMBAT"

    def draw(self):
        self.screen.fill(C_BG)
        
        # HUD
        self.draw_text(f"HP: {self.player.current_hp}/{self.player.derived.get('HP', 10)}", 20, 20, (200, 50, 50))
        self.draw_text(f"Chaos: {self.chaos.chaos_level}", 300, 20, (200, 100, 255))
        
        # MAIN VIEW
        if self.state == "EXPLORE":
            pygame.draw.rect(self.screen, (50, 50, 60), (200, 150, 400, 300)) # Card
            self.draw_text(self.current_scene.text, 220, 280, C_TEXT)
            self.draw_text("[SPACE] Advance", 220, 400)
            
        elif self.state in ["COMBAT", "CLASH"]:
            # Arena
            pygame.draw.rect(self.screen, C_ARENA, (150, 100, 500, 400))
            
            # Entities
            pygame.draw.rect(self.screen, C_PLAYER, (200, 250, 50, 50)) # Player
            pygame.draw.rect(self.screen, C_ENEMY, (550, 250, 50, 50))  # Enemy
            
            # Enemy HP
            if self.enemy:
                self.draw_text(f"{self.enemy.species_name}", 530, 220, C_ENEMY)
                self.draw_text(f"HP: {self.enemy.current_hp}", 550, 310, C_ENEMY)

            if self.state == "CLASH":
                pygame.draw.rect(self.screen, (0, 0, 0), (150, 200, 500, 100))
                self.draw_text("THE CLASH!", 350, 220, (255, 255, 0))
                self.draw_text("[1] PRESS (Might)", 200, 260)
                self.draw_text("[2] DISENGAGE (Reflex)", 450, 260)

        # LOGS
        pygame.draw.rect(self.screen, (10, 10, 20), (0, 500, SCREEN_W, 100))
        for i, line in enumerate(self.logs):
            self.draw_text(line, 20, 510 + i*15, (150, 150, 150))

        pygame.display.flip()

    def draw_text(self, text, x, y, col=(255,255,255)):
        img = self.font.render(text, True, col)
        self.screen.blit(img, (x, y))

if __name__ == "__main__":
    Game().run()
