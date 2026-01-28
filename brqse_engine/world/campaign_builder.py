import os
import json
import uuid
import datetime
import shutil

    # Correct import paths based on project structure
from brqse_engine.world.donjon_generator import DonjonGenerator, Cell
from brqse_engine.world.story_director import StoryDirector
from brqse_engine.world.story_weaver import StoryWeaver
from scripts.world_engine import SceneStack, ChaosManager

class CampaignBuilder:
    """
    The Architect.
    Generates a full 'Chain of Rooms' campaign from a SceneStack.
    Saves the entire run as a sequence of linked JSON map files.
    """
    def __init__(self, sensory_layer=None):
        self.chaos = ChaosManager()
        self.stack_gen = SceneStack(self.chaos)
        self.director = StoryDirector(sensory_layer=sensory_layer)
        self.weaver = StoryWeaver(sensory_layer=sensory_layer)
        self.save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Saves", "Campaigns")

    def generate_campaign(self, biome="Dungeon", quest_template=None):
        """
        1. Generates a SceneStack (The Plot).
        2. Creates a unique Campaign Folder.
        3. Generates and links N maps (one per scene).
        4. Weaves the story across them (StoryWeaver).
        5. Saves files.
        Returns: campaign_id, start_scene_path
        """
        # 1. Generate the Plot
        self.stack_gen.generate_quest(biome=biome)
        scenes = list(self.stack_gen.stack) 
        scenes.reverse() # [Start, ..., Finale]
        
        # 2. Setup Folder
        campaign_id = f"Campaign_{uuid.uuid4().hex[:8]}"
        camp_path = os.path.join(self.save_dir, campaign_id)
        os.makedirs(camp_path, exist_ok=True)
        
        # Save Quest Meta
        meta = {
            "id": campaign_id,
            "title": self.stack_gen.quest_title,
            "description": self.stack_gen.quest_description,
            "created_at": str(datetime.datetime.now()),
            "total_scenes": len(scenes)
        }
        with open(os.path.join(camp_path, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

        print(f"[CampaignBuilder] Building '{meta['title']}' ({len(scenes)} Scenes)...")

        # 3. Build Chain (Geometry Only)
        map_chain = []
        for i, scene in enumerate(scenes):
            map_data = self._build_scene_map(scene, i, biome)
            
            # LINKING LOGIC
            if i > 0:
                self._add_link(map_data, "entrance", target_scene=i-1)
            
            if i < len(scenes) - 1:
                self._add_link(map_data, "exit", target_scene=i+1)
            else:
                self._add_link(map_data, "exit", target_scene="CAMPAIGN_COMPLETE")
            
            map_chain.append(map_data)

        # 4. Weave Story (The Weaver)
        quest_params = {
            "title": self.stack_gen.quest_title,
            "desc": self.stack_gen.quest_description,
            "length": len(scenes)
        }
        self.weaver.weave_campaign(map_chain, quest_params)
        
        # 5. Enrich Assets (Flavor Text)
        self.weaver.enrich_assets(map_chain, quest_params)

        # 6. Save Files
        for i, map_data in enumerate(map_chain):
            fname = f"scene_{i}.json"
            fpath = os.path.join(camp_path, fname)
            with open(fpath, "w") as f:
                json.dump(map_data, f, indent=2)
            print(f"  - Saved Scene {i}: {map_data['scene_title']}")

        return campaign_id, f"scene_0.json"

    def _build_scene_map(self, scene, index, biome):
        # 1. Generate Physical Grid
        # Small map for single scene? Or variable?
        # User said "Keep current size" (21x21).
        dg = DonjonGenerator()
        map_data = dg.generate(width=21, height=21)
        map_data["scene_index"] = index
        map_data["biome"] = biome
        
        # 2. Inject Narrative (Director)
        # We need a new/modified method or re-use direct_scene with context
        # For now, I'll manually inject the basics here, 
        # or call a helper in Director if I update it.
        # Let's keep Director logic inside Director.
        self.director.inject_scene_context(map_data, scene)
        
        return map_data

    def _add_link(self, map_data, link_type, target_scene):
        """
        Adds a semantic Exit/Entrance object to the map.
        Prioritizes locations marked by DonjonGenerator (STAIR_UP/DN).
        """
        grid = map_data["grid"]
        h = map_data["height"]
        w = map_data["width"]
        rooms = list(map_data["rooms"].values())
        if not rooms: return

        chosen_pos = None

        if link_type == "entrance":
            # Search for STAIR_UP
            for r in range(h):
                for c in range(w):
                    if grid[r][c] & Cell.STAIR_UP:
                        chosen_pos = (c, r)
                        break
            
            # Fallback
            if not chosen_pos:
                chosen_pos = rooms[0]["center"]

            obj = {
                "id": f"link_prev",
                "type": "zone_transition",
                "name": "Way Back",
                "x": chosen_pos[0], "y": chosen_pos[1],
                "target_scene": target_scene,
                "tags": ["entrance", "transition"]
            }
            map_data.setdefault("objects", []).append(obj)
            
        elif link_type == "exit":
            # Search for STAIR_DN
            for r in range(h):
                for c in range(w):
                    if grid[r][c] & Cell.STAIR_DN:
                        chosen_pos = (c, r)
                        break
            
            # Fallback
            if not chosen_pos:
                chosen_pos = rooms[-1]["center"]

            obj = {
                "id": f"link_next",
                "type": "zone_transition",
                "name": "Way Forward",
                "x": chosen_pos[0], "y": chosen_pos[1],
                "target_scene": target_scene,
                "tags": ["exit", "transition"]
            }
            map_data.setdefault("objects", []).append(obj)
