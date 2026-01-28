import csv
import json
import os
import requests

class Arbiter:
    """
    The Rules Lawyer. Intercepts player messages to determine if game mechanics (Skill Checks) are required.
    """
    def __init__(self, api_url="http://localhost:5001/generate"):
        self.api_url = api_url
        self.valid_skills, self.skill_map = self._load_skills()

    def _load_skills(self):
        """Loads allowed skill names and their attributes from CSV."""
        skills = []
        skill_map = {}
        # Path relative to engine root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(base_dir, "Data", "Skills.csv")
        
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        s_name = row['Skill_Name']
                        skills.append(s_name)
                        skill_map[s_name] = row['Attribute']
            except Exception as e:
                print(f"[Arbiter] Failed to load skills: {e}")
                
        # Return loaded skills + map, or fallback
        if not skills:
            skills = ["Athletics", "Stealth", "Perception", "Arcana", "Might", "Persuasion"]
            # Fallback map
            skill_map = {
                "Athletics": "MIGHT", "Stealth": "REFLEXES", "Perception": "AWARENESS", 
                "Arcana": "KNOWLEDGE", "Might": "MIGHT", "Persuasion": "CHARM"
            }
            
        return skills, skill_map

    def judge_intent(self, player_input, game_state):
        """
        Asks the AI: 'Does this action need a dice roll?'
        Returns: None (if no roll) OR dict {'skill': 'Athletics', 'dc': 15}
        """
        
        skills_str = ", ".join(self.valid_skills)
        
        system_prompt = f"""
        [ROLE]
        You are the Rules Arbiter for a tabletop RPG. You do not speak. You only output JSON.
        
        [VALID SKILLS]
        {skills_str}
        
        [TASK]
        Analyze the PLAYER_INPUT in the context of the game. 
        1. Is the player attempting a risky action that could fail (climbing, attacking, lying, deciphering)?
        2. If YES, determine the Skill and Difficulty Class (DC 5=Easy, 15=Hard, 25=Impossible).
        3. If NO (just talking, looking, or impossible), return {{ "check_needed": false }}.
        
        [OUTPUT FORMAT]
        Return ONLY valid JSON. 
        Example Check: {{ "check_needed": true, "skill": "Athletics", "dc": 15, "reason": "Climbing a slippery wall" }}
        Example No Check: {{ "check_needed": false }}
        """

        prompt = f"System: {system_prompt}\nUser: PLAYER_INPUT: \"{player_input}\"\nAssistant: JSON:"
        
        try:
            # We use a lower temperature (0.1) because we need logic, not creativity
            # Note: Using port 5001 as seen in simple_api.py
            payload = {"prompt": prompt, "temperature": 0.1, "max_new_tokens": 100}
            response = requests.post(self.api_url, json=payload, timeout=2)
            
            if response.status_code == 200:
                text = response.json().get("response", "").strip()
                # Clean up potential AI chatter around the JSON
                if "{" in text and "}" in text:
                    json_str = text[text.find("{"):text.rfind("}")+1]
                    try:
                        data = json.loads(json_str)
                        if data.get("check_needed"):
                            # Enrich with Attribute
                            skill_name = data.get("skill")
                            # Try exact match, or case insensitive
                            attr = self.skill_map.get(skill_name)
                            if not attr:
                                # Try case insensitive scan
                                for k, v in self.skill_map.items():
                                    if k.lower() == str(skill_name).lower():
                                        attr = v
                                        break
                            data["attribute"] = attr or "Unknown"
                            return data
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"[Arbiter Error]: {e}")
            
        return None
