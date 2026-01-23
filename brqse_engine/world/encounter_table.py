import random
import os
import csv
from typing import Dict, List, Optional, Any

class EncounterTable:
    """
    Maps biomes and chaos levels to specific encounters (beasts, hazards, loot, etc.).
    Loads structure and setup data from CSV files.
    """
    
    # Biome-specific beast mappings
    BIOME_MAPPINGS = {
        "DUNGEON": ["Predator", "Scavenger", "Vermin", "Insect"],
        "CAVE": ["Reptile", "Vermin", "Insect", "Predator"],
        "FOREST": ["Predator", "Grazer", "Raptor", "Plant"],
        "RUINS": ["Scavenger", "Vermin", "Raptor", "Reptile"],
        "AQUATIC": ["Aquatic", "Reptile", "Predator"]
    }

    # Updated weights including PUZZLE and SAFE_HAVEN
    ENCOUNTER_TYPE_WEIGHTS = {
        "DUNGEON": {"AMBUSH": 30, "HAZARD": 25, "TREASURE": 15, "SOCIAL": 5, "FLAVOR": 10, "PUZZLE": 10, "SAFE_HAVEN": 5},
        "CAVE": {"AMBUSH": 25, "HAZARD": 40, "TREASURE": 5, "SOCIAL": 5, "FLAVOR": 10, "PUZZLE": 10, "SAFE_HAVEN": 5},
        "FOREST": {"AMBUSH": 40, "HAZARD": 10, "TREASURE": 10, "SOCIAL": 15, "FLAVOR": 10, "PUZZLE": 10, "SAFE_HAVEN": 5},
        "RUINS": {"AMBUSH": 30, "HAZARD": 10, "TREASURE": 20, "SOCIAL": 15, "FLAVOR": 10, "PUZZLE": 10, "SAFE_HAVEN": 5},
        "AQUATIC": {"AMBUSH": 40, "HAZARD": 20, "TREASURE": 10, "SOCIAL": 10, "FLAVOR": 10, "PUZZLE": 5, "SAFE_HAVEN": 5}
    }

    # Data cache
    _TABLES: Dict[str, List[Dict]] = {}

    @classmethod
    def _ensure_data_loaded(cls):
        if cls._TABLES: return
        
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Data")
        mapping = {
            "AMBUSH": "Encounters_Combat.csv",
            "SOCIAL": "Encounters_Social.csv",
            "PUZZLE": "Encounters_Puzzle.csv",
            "FLAVOR": "Encounters_Flavor.csv",
            "TREASURE": "Encounters_Treasure.csv",
            "SAFE_HAVEN": "Encounters_Boon.csv",
            "HAZARD": "Encounters_Hazard.csv",
            "CHAOS_TWIST": "Chaos_Twists.csv"
        }
        
        for key, filename in mapping.items():
            path = os.path.join(data_dir, filename)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    cls._TABLES[key] = list(reader)
            else:
                cls._TABLES[key] = []

    @staticmethod
    def get_candidate_families(biome: str) -> List[str]:
        b = biome.upper()
        for key in EncounterTable.BIOME_MAPPINGS:
            if key in b: return EncounterTable.BIOME_MAPPINGS[key]
        return ["Predator", "Scavenger"]

    @staticmethod
    def get_weighted_beast(beast_list: List[Dict], biome: str, chaos_level: int) -> Optional[Dict]:
        candidates = EncounterTable.get_candidate_families(biome)
        pool = [b for b in beast_list if b.get("Family_Name") in candidates]
        if not pool: return random.choice(beast_list) if beast_list else None
        return random.choice(pool)

    @classmethod
    def get_random_encounter(cls, biome: str, level: int = 1, force_type: str = None) -> Dict[str, Any]:
        """
        Returns a structured dictionary defining a random encounter.
        If force_type is provided, skips weighted rolling.
        """
        cls._ensure_data_loaded()
        b = biome.upper()
        
        if force_type:
            etype = force_type
        else:
            weights = cls.ENCOUNTER_TYPE_WEIGHTS.get("DUNGEON")
            for key in cls.ENCOUNTER_TYPE_WEIGHTS:
                if key in b:
                    weights = cls.ENCOUNTER_TYPE_WEIGHTS[key]
                    break
            choices = list(weights.keys())
            counts = list(weights.values())
            etype = random.choices(choices, weights=counts, k=1)[0]

        encounter = {"type": etype, "biome": biome, "level": level}
        
        # Pull from CSV tables
        table_key = etype
        if etype == "SAFE_HAVEN": table_key = "SAFE_HAVEN"
        
        table = cls._TABLES.get(table_key, [])
        if table:
            row = random.choice(table)
            encounter["subtype"] = row.get("Encounter_Structure") or row.get("Domain") or "Generic"
            encounter["log"] = row.get("Suggested_Setup") or row.get("Description") or "Something happens."
        else:
            encounter["subtype"] = "Unknown"
            encounter["log"] = "The air is still."

        return encounter

    @classmethod
    def get_chaos_twist(cls) -> Dict[str, Any]:
        cls._ensure_data_loaded()
        table = cls._TABLES.get("CHAOS_TWIST", [])
        if table:
            return random.choice(table)
        return {"Domain": "Unknown", "Description": "Reality flickers."}
