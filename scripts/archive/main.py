import pygame
import sys
import os
import random

# Fix imports relative to script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from char_engine import Character
from brqse_engine.combat.mechanics import CombatEngine, Combatant
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
        
        # Init Combat Engine
        self.combat_engine = CombatEngine()
        # Note: In a real app, we'd sync player/enemy to combat engine entities
        # For this visualizer, we might need to wrap them or just use the engine for resolution.
        # But wait, mechanics.py uses internal state extensively.
        # Ideally main.py should defer ALL logic to game_loop.py, but that's a bigger refactor.
        # For now, let's instantiate a Combatant wrapper for the player.
        self.c_player = Combatant(data={"Name": "Player", "Stats": self.player.attributes})
        self.combat_engine.add_combatant(self.c_player, 5, 5)

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
                        # Use Engine
                        # Need to update wrapper stats from legacy char object? (Skipping for brevity, assuming sync)
                        
                        # We need an enemy combatant in the engine
                        if not any(c.name == self.enemy.species_name for c in self.combat_engine.combatants):
                             # Lazy add enemy to engine
                             self.c_enemy = Combatant(data={"Name": self.enemy.species_name, "Stats": self.enemy.attributes})
                             self.combat_engine.add_combatant(self.c_enemy, 6, 5) # Adjacent
                        
                        # Execute Attack
                        log = self.combat_engine.attack_target(self.c_player, self.c_enemy)
                        self.log(f"Action: {log[-1]}") # Log last line
                        
                        # Check for Clash in log
                        if any("CLASH" in l for l in log):
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
                    # We need to manually invoke the resolve_physical_clash method since it's internal to attack_target usually.
                    # mechanics.py doesn't expose "resolve_clash_effect" directly as a public stateless utility.
                    # It relies on internal state or immediate resolution.
                    
                    # WORKAROUND: Call execute_clash_technique directly
                    if event.key == pygame.K_1: # PRESS (Weapon Stat)
                        effect = self.combat_engine.execute_clash_technique(self.c_player, self.c_enemy, "MIGHT")
                        self.log(f"PRESS: {effect}")
                        self.state = "COMBAT"
                    elif event.key == pygame.K_2: # DISENGAGE (Armor Stat)
                        effect = self.combat_engine.execute_clash_technique(self.c_player, self.c_enemy, "REFLEXES")
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
