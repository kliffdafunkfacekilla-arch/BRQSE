import re

with open('effects_registry.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Magic Missile pattern after Auto-Hit
old_patterns = '''        self.register_pattern(r"Auto-Hit", self._handle_auto_hit)
        self.register_pattern(r"Auto-Crit", self._handle_auto_crit)'''

new_patterns = '''        self.register_pattern(r"Auto-Hit", self._handle_auto_hit)
        self.register_pattern(r"Magic Missile", self._handle_magic_missile)
        self.register_pattern(r"Auto-Crit", self._handle_auto_crit)'''

# Add the handler after _handle_auto_hit
old_handler = '''    def _handle_auto_hit(self, match, ctx):
        ctx["auto_hit"] = True
        ctx["log"].append("Effect: Auto-Hit!")'''

new_handler = '''    def _handle_auto_hit(self, match, ctx):
        ctx["auto_hit"] = True
        ctx["log"].append("Effect: Auto-Hit!")

    def _handle_magic_missile(self, match, ctx):
        """
        Magic Missile - auto-hit arcane damage spell.
        Deals tier-based damage automatically without attack roll.
        """
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        
        if target and attacker:
            import random
            tier = ctx.get("tier", 2)  # Default tier 2 for Bolt
            
            # Get damage from Power_Power.csv
            from .data_loader import DataLoader
            loader = DataLoader()
            dice_str = loader.get_tier_damage(tier)
            
            # Parse and roll dice
            dmg = 0
            if "d" in dice_str.lower():
                parts = dice_str.lower().split("d")
                num = int(parts[0]) if parts[0] else 1
                sides = int(parts[1]) if len(parts) > 1 else 6
                dmg = sum(random.randint(1, sides) for _ in range(num))
            else:
                dmg = int(dice_str) if dice_str.isdigit() else 2
            
            # Add stat modifier (Knowledge for arcane)
            stat_val = attacker.data.get("Stats", {}).get("Knowledge", 10)
            mod = (stat_val - 10) // 2
            dmg = max(1, dmg + mod)
            
            # Apply damage - auto hit, no attack roll needed
            target.hp -= dmg
            if "log" in ctx:
                ctx["log"].append(f"{dmg} Arcane damage to {target.name}! (Auto-hit)")'''

success_count = 0
if old_patterns in content:
    content = content.replace(old_patterns, new_patterns)
    success_count += 1
    print("SUCCESS: Added Magic Missile pattern")
else:
    print("FAIL: Pattern registration not found")

if old_handler in content:
    content = content.replace(old_handler, new_handler)
    success_count += 1
    print("SUCCESS: Added Magic Missile handler")
else:
    print("FAIL: Handler location not found")

if success_count == 2:
    with open('effects_registry.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("\nFile saved successfully!")
