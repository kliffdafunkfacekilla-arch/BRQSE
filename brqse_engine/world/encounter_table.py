import random
from typing import Dict, List, Optional

class EncounterTable:
    """
    Maps biomes and chaos levels to specific beast encounters.
    """
    
    # Biome-specific beast mappings
    # Families: Predator, Grazer, Scavenger, Raptor, Reptile, Vermin, Aquatic, Insect, Plant
    BIOME_MAPPINGS = {
        "DUNGEON": ["Predator", "Scavenger", "Vermin", "Insect"],
        "CAVE": ["Reptile", "Vermin", "Insect", "Predator"],
        "FOREST": ["Predator", "Grazer", "Raptor", "Plant"],
        "RUINS": ["Scavenger", "Vermin", "Raptor", "Reptile"],
        "AQUATIC": ["Aquatic", "Reptile", "Predator"]
    }

    @staticmethod
    def get_candidate_families(biome: str) -> List[str]:
        # Normalize biome string
        b = biome.upper()
        for key in EncounterTable.BIOME_MAPPINGS:
            if key in b:
                return EncounterTable.BIOME_MAPPINGS[key]
        return ["Predator", "Scavenger"] # Fallback

    @staticmethod
    def get_weighted_beast(beast_list: List[Dict], biome: str, chaos_level: int) -> Optional[Dict]:
        """
        Filters the full beast list based on biome and chaos-scaled level (if applicable).
        """
        candidates = EncounterTable.get_candidate_families(biome)
        
        # Filter beasts by family
        pool = [b for b in beast_list if b.get("Family_Name") in candidates]
        
        if not pool:
            return random.choice(beast_list) if beast_list else None
            
        # Select one
        return random.choice(pool)
