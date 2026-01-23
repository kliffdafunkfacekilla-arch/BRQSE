import random
from typing import Dict, List, Optional, Any

class EncounterTable:
    """
    Maps biomes and chaos levels to specific encounters (beasts, hazards, loot, etc.).
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

    # Probability weights for different encounter types per biome
    # Format: { BIOME: { TYPE: WEIGHT } }
    ENCOUNTER_TYPE_WEIGHTS = {
        "DUNGEON": {"AMBUSH": 40, "HAZARD": 30, "TREASURE": 15, "SOCIAL": 5, "FLAVOR": 10},
        "CAVE": {"AMBUSH": 30, "HAZARD": 50, "TREASURE": 5, "SOCIAL": 5, "FLAVOR": 10},
        "FOREST": {"AMBUSH": 50, "HAZARD": 15, "TREASURE": 10, "SOCIAL": 15, "FLAVOR": 10},
        "RUINS": {"AMBUSH": 35, "HAZARD": 15, "TREASURE": 25, "SOCIAL": 15, "FLAVOR": 10},
        "AQUATIC": {"AMBUSH": 45, "HAZARD": 25, "TREASURE": 10, "SOCIAL": 10, "FLAVOR": 10}
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
        Filters the full beast list based on biome and selects one.
        """
        candidates = EncounterTable.get_candidate_families(biome)
        
        # Filter beasts by family
        pool = [b for b in beast_list if b.get("Family_Name") in candidates]
        
        if not pool:
            return random.choice(beast_list) if beast_list else None
            
        # Select one
        return random.choice(pool)

    @staticmethod
    def get_random_encounter(biome: str, level: int = 1) -> Dict[str, Any]:
        """
        Returns a structured dictionary defining a random encounter.
        """
        b = biome.upper()
        weights = EncounterTable.ENCOUNTER_TYPE_WEIGHTS.get("DUNGEON") # Default
        for key in EncounterTable.ENCOUNTER_TYPE_WEIGHTS:
            if key in b:
                weights = EncounterTable.ENCOUNTER_TYPE_WEIGHTS[key]
                break
        
        # Weighted selection of type
        choices = list(weights.keys())
        counts = list(weights.values())
        etype = random.choices(choices, weights=counts, k=1)[0]

        encounter = {"type": etype, "biome": biome, "level": level}

        if etype == "AMBUSH":
            encounter["log"] = "Something predatory stalks towards you from the darkness!"
        elif etype == "HAZARD":
            hazard_types = ["Toxic Bile", "Spike Trap", "Crumbling Floor", "Doom Slime"]
            encounter["subtype"] = random.choice(hazard_types)
            encounter["log"] = f"Danger! You trigger a {encounter['subtype']}!"
        elif etype == "TREASURE":
            loot_types = ["Ancient Crate", "Lost Satchel", "Shiny Bauble", "Hidden Cache"]
            encounter["subtype"] = random.choice(loot_types)
            encounter["log"] = f"Your keen eyes spot an {encounter['subtype']} tucked away."
        elif etype == "SOCIAL":
            social_types = ["Abandoned Statue", "Mystic Fountain", "Wandering Merchant", "Prayer Altar"]
            encounter["subtype"] = random.choice(social_types)
            encounter["log"] = f"You come across an {encounter['subtype']}."
        else: # FLAVOR
            flavor_texts = [
                "The air grows suddenly cold, and a distant scream echoes.",
                "You feel eyes watching you from the high rafters.",
                "The shadows seem to writhe and stretch unnaturally.",
                "A faint smell of ozone and rot fills the room."
            ]
            encounter["log"] = random.choice(flavor_texts)
            encounter["subtype"] = "FLAVOR"

        return encounter
