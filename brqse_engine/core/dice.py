import random
import re
from typing import Tuple, List, Dict

class Dice:
    """
    Static utility class for dice rolling operations.
    Supports standard notation (e.g., "1d20", "2d6+3", "1d8-1").
    """
    
    @staticmethod
    def roll(expression: str) -> Tuple[int, List[int], str]:
        """
        Rolls dice based on a string expression.
        Returns: (Total, Individual Rolls as List, Breakdown String)
        Example: roll("2d6+3") -> (10, [3, 4], "2d6+3: [3, 4] + 3 = 10")
        """
        expression = expression.lower().replace(" ", "")
        
        # Parse expression: XdY or XdY+Z or XdY-Z
        match = re.match(r"(\d+)d(\d+)([\+\-]\d+)?", expression)
        
        if not match:
            # Maybe it's just a flat number?
            try:
                val = int(expression)
                return val, [], str(val)
            except:
                return 0, [], "Invalid Expression"
        
        count = int(match.group(1))
        sides = int(match.group(2))
        modifier = match.group(3)
        mod_val = int(modifier) if modifier else 0
        
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + mod_val
        
        # Format breakdown
        roll_str = f"[{', '.join(map(str, rolls))}]"
        breakdown = f"{expression}: {roll_str}"
        if mod_val != 0:
            op = "+" if mod_val > 0 else ""
            breakdown += f" {op}{mod_val}"
        breakdown += f" = {total}"
        
        return total, rolls, breakdown

    @staticmethod
    def roll_advantage() -> Tuple[int, int, int]:
        """Rolls 2d20 and keeps higher. Returns (Result, Roll1, Roll2)"""
        r1 = random.randint(1, 20)
        r2 = random.randint(1, 20)
        return max(r1, r2), r1, r2

    @staticmethod
    def roll_disadvantage() -> Tuple[int, int, int]:
        """Rolls 2d20 and keeps lower. Returns (Result, Roll1, Roll2)"""
        r1 = random.randint(1, 20)
        r2 = random.randint(1, 20)
        return min(r1, r2), r1, r2
