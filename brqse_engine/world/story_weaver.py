
import json
import random
from typing import List, Dict, Any

class StoryWeaver:
    """
    The Architect of the Campaign's Narrative.
    
    Bridging the gap between "Geometry" (DonjonGenerator) and "Story" (LLM).
    It takes a set of raw maps and a high-level Quest Prompt, and uses an LLM
    to distribute story assets (Keys, Bosses, Lore) across the maps intelligently.
    """
    
    def __init__(self, sensory_layer=None):
        self.sensory_layer = sensory_layer
    
    def weave_campaign(self, maps: List[Dict[str, Any]], quest_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Main entry point.
        1. Summarizes the topology of the provided maps.
        2. Prompts the LLM to distribute assets based on quest_params.
        3. Injects the returned assets into the map dictionaries.
        """
        print(f"[StoryWeaver] Weaving story for {len(maps)} maps...")
        
        # 1. Summarize Topology
        topology_summary = self._summarize_campaign(maps)
        
        # 2. Prompt LLM
        # For prototype, we might mock this or use a very structured prompt.
        distribution_plan = self._prompt_llm(topology_summary, quest_params)
        
        # 3. Distribute Assets
        self._distribute_assets(maps, distribution_plan)
        
        return maps

    def _summarize_campaign(self, maps: List[Dict[str, Any]]) -> str:
        """
        Creates a token-efficient summary of the campaign's physical layout.
        Example:
        "Map 0 (Forest): 12 Rooms. Notable: Room 4 (Exit), Room 0 (Entry).
         Map 1 (Cave): 8 Rooms. Notable: Room 7 (Exit)."
        """
        summary = []
        for i, m in enumerate(maps):
            room_count = len(m.get("rooms", {}))
            
            # Identify Key Rooms (Entrance/Exit) based on existing tags/links
            notable = []
            if "objects" in m:
                for obj in m["objects"]:
                    if obj.get("type") == "zone_transition":
                        room_id = self._find_room_id(m, obj["x"], obj["y"])
                        notable.append(f"Room {room_id} ({obj['name']})")
                        
            summary.append(f"Map {i}: {room_count} Rooms. Notable: {', '.join(notable)}.")
            
        return "\n".join(summary)

    def _find_room_id(self, map_data, x, y):
        # Helper to find which room a coordinate is in
        for r_id, r in map_data.get("rooms", {}).items():
            if r["x"] <= x < r["x"] + r["w"] and r["y"] <= y < r["y"] + r["h"]:
                return r_id
        return "?"

    def _prompt_llm(self, summary: str, quest_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Asks the LLM to populate the world.
        Returns a list of placement instructions.
        """
        prompt = f"""
You are the Dungeon Master. I have generated a dungeon layout. 
You must populate it with Story Assets (Keys, Clues, Traps, Bosses) based on this Quest:

QUEST: {quest_params.get('title', 'Unknown')}
DESCRIPTION: {quest_params.get('desc', 'Explore.')}
LENGTH: {quest_params.get('length', 1)} Maps.

CAMPAIGN TOPOLOGY:
{summary}

INSTRUCTIONS:
Distribute Story Assets to create a pacing curve.
1. MAIN PLOT (3-5 items): Clues, Keys, Bosses.
2. FILLER EVENTS: Scattered minor encounters to flesh out the world.
   - Traps (Physical/Magical)
   - Social Encounters (Remnant Spirits, Non-Hostile NPCs)
   - Treasure (Chests, Loot)
   - Atmosphere (Flavor text objects)

Output a JSON List.
Example:
[
  {{"map_index": 0, "room_id": "random", "type": "clue", "name": "Scrawled Note", "desc": "Mentions a dark ritual."}},
  {{"map_index": 0, "room_id": "random", "type": "trap", "name": "Tripwire", "desc": "A rusty wire."}},
  {{"map_index": 1, "room_id": "last", "type": "enemy", "name": "Gatekeeper", "desc": "A heavy guard."}},
  {{"map_index": 1, "room_id": "random", "type": "social", "name": "Lost Spirit", "desc": "A ghost asking for help."}},
  {{"map_index": -1, "room_id": "last", "type": "boss", "name": "The Lich", "desc": "The target."}}
]
"""
        response_text = ""
        
        # 1. Call AI
        if self.sensory_layer:
            try:
                # Use SensoryLayer (Local RAG/LLM)
                response_text = self.sensory_layer.consult_oracle("You are a system that outputs JSON.", prompt)
            except Exception as e:
                print(f"[StoryWeaver] AI Error: {e}")
        else:
            # Fallback Mock if no layer provided (Testing)
            print("[StoryWeaver] No SensoryLayer. Using Mock.")
            return [
                 {"map_index": 0, "room_id": "random", "type": "clue", "name": "Mock Clue", "desc": "Auto-generated clue."},
                 {"map_index": -1, "room_id": "last", "type": "boss", "name": "Mock Boss", "desc": "Auto-generated boss."}
            ]

        # 2. Parse JSON (Fuzzy)
        try:
            # Strip potential markdown code blocks
            clean_text = response_text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0]
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0]
            
            # Find list bracket
            start = clean_text.find("[")
            end = clean_text.rfind("]")
            if start != -1 and end != -1:
                json_str = clean_text[start:end+1]
                data = json.loads(json_str)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"[StoryWeaver] JSON Parse Error: {e} \nRaw: {response_text}")
            
        print("[StoryWeaver] Failed to get valid JSON from AI. Using empty list.")
        return []

    def _distribute_assets(self, maps, plan):
        """
        Injects the assets into the map files.
        """
        for item in plan:
            # Resolve Map Index
            map_idx = item.get("map_index", 0)
            if map_idx < 0: map_idx = len(maps) + map_idx # Handle -1 for last map
            
            if 0 <= map_idx < len(maps):
                target_map = maps[map_idx]
                
                # Resolve Room
                room_id = item.get("room_id")
                target_room = None
                
                if room_id == "random":
                    target_room = random.choice(list(target_map["rooms"].values()))
                elif room_id == "last":
                    # Heuristic: Highest ID is usually widely separated from 0 via Donjon algo
                    target_room = target_map["rooms"][list(target_map["rooms"].keys())[-1]]
                else:
                    # Specific ID
                    target_room = target_map["rooms"].get(room_id)
                    if not target_room: 
                         target_room = random.choice(list(target_map["rooms"].values())) # Fallback
                
                if target_room:
                    # Calculate position (center of room)
                    cx, cy = target_room["center"]
                    
                    if item["type"] in ["enemy", "boss"]:
                        ent = {
                            "type": "enemy",
                            "name": item["name"],
                            "x": cx, "y": cy,
                            "tags": ["hostile", "quest_target"] if item["type"] == "boss" else ["hostile"],
                            "ai_context": {"role": "boss" if item["type"] == "boss" else "minion"}
                        }
                        target_map.setdefault("entities", []).append(ent)
                    else:
                        obj = {
                            "type": item["type"],
                            "name": item["name"],
                            "description": item.get("desc", ""),
                            "x": cx, "y": cy,
                            "tags": ["quest_item"] if item["type"] == "key" else ["scenery"]
                        }
                        # Add specific tags based on type
                        if item["type"] == "trap": obj["tags"].append("trap")
                        if item["type"] == "social": obj["tags"].append("npc")
                        
                        target_map.setdefault("objects", []).append(obj)
                        print(f"[StoryWeaver] Placed {item['name']} in Map {map_idx} Room {target_room.get('id')}")

    def enrich_assets(self, maps: List[Dict[str, Any]], quest_params):
        """
        Iterates through ALL assets, collects them, and generates flavor text in batches.
        """
        print("[StoryWeaver] Enriching assets with AI descriptions (Batch Mode)...")
        
        items_to_process = [] # List of (ref_obj, context_str)
        
        for m_idx, m in enumerate(maps):
            biome = m.get("biome", "Dungeon")
            
            # 1. Collect Objects
            for obj in m.get("objects", []):
                if not obj.get("description") or len(obj["description"]) < 5: # Lower threshold to catch '.'
                    context = f"Object: {obj['name']} ({obj['type']}). Location: {biome}."
                    items_to_process.append({"ref": obj, "ctx": context})
                    
            # 2. Collect Entities
            for ent in m.get("entities", []):
                if not ent.get("description") or len(ent["description"]) < 5:
                     context = f"Entity: {ent['name']} ({ent['type']}). Location: {biome}."
                     items_to_process.append({"ref": ent, "ctx": context})
                     
        # 3. Process in Batches
        BATCH_SIZE = 5
        for i in range(0, len(items_to_process), BATCH_SIZE):
            batch = items_to_process[i:i+BATCH_SIZE]
            print(f"  - Processing batch {i//BATCH_SIZE + 1} ({len(batch)} items)...")
            self._batch_generate_flavor(batch, quest_params.get('title'))

    def _batch_generate_flavor(self, batch, quest_title):
        """
        Sends a bulk prompt to the LLM.
        """
        if not self.sensory_layer:
            # Mock Fallback
            for item in batch:
                item["ref"]["description"] = f"Mock description for {item['ref']['name']}."
            return

        # Construct Bulk Prompt
        prompt = f"""
You are a flavor text generator for a Dark Fantasy RPG. 
Quest: {quest_title}

Describe the following {len(batch)} items. 1 sentence each. Atmospheric.
Items:
"""
        for idx, item in enumerate(batch):
            prompt += f"{idx+1}. {item['ctx']}\n"
            
        prompt += "\nReturn a JSON List of strings. Example: [\"Desc 1\", \"Desc 2\"]"
        
        try:
            response = self.sensory_layer.consult_oracle("You return JSON lists.", prompt)
            
            # Fuzzy JSON Parse
            clean_text = response.strip()
            if "```" in clean_text:
                clean_text = clean_text.split("```")[1]
                if clean_text.startswith("json"): clean_text = clean_text[4:]
            
            start = clean_text.find("[")
            end = clean_text.rfind("]")
            if start != -1 and end != -1:
                desc_list = json.loads(clean_text[start:end+1])
                
                # Apply descriptions
                for j, desc in enumerate(desc_list):
                    if j < len(batch):
                        batch[j]["ref"]["description"] = desc
        except Exception as e:
            print(f"[StoryWeaver] Batch Error: {e}")
            # Fallback
            for item in batch:
                item["ref"]["description"] = "A silent presence."
