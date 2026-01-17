
export interface Species {
  Species: string;
  [key: string]: string | number;
}

export interface Skill {
  "Skill Name": string;
  Description?: string;
  [key: string]: any;
}

export class DataLoader {
  static async loadJSON<T>(filename: string): Promise<T[]> {
    try {
      // In Next.js public folder is served at root
      const res = await fetch(`/data/${filename}`);
      if (!res.ok) throw new Error(`Failed to load ${filename}`);
      return await res.json();
    } catch (e) {
      console.error(e);
      return [];
    }
  }

  static async loadSpecies(): Promise<Species[]> {
    return this.loadJSON("Species.json");
  }

  static async loadSpeciesSkills(species: string): Promise<Skill[]> {
    return this.loadJSON(`${species}_Skills.json`);
  }

  static async loadMagicSchools(): Promise<any[]> {
    return this.loadJSON("Schools of Power.json");
  }

  static async loadSocialOrigin(): Promise<any[]> {
    return this.loadJSON("Social_Def.json");
  }

  static async loadSocialEducation(): Promise<any[]> {
    return this.loadJSON("Social_Off.json");
  }

  static async loadSocialAdulthood(): Promise<any[]> {
    return this.loadJSON("Armor_Groups.json"); // Changed to match main.py logic (Background 3 uses Armor Groups)
  }

  static async loadWeaponGroups(): Promise<any[]> {
    return this.loadJSON("Weapon_Groups.json");
  }

  static async loadAllSkills(): Promise<any[]> {
    return this.loadJSON("Skills.json");
  }

  static async loadToolTypes(): Promise<any[]> {
    return this.loadJSON("Tool_types.json");
  }

  static async loadGear(): Promise<any[]> {
    return this.loadJSON("weapons_and_armor.json");
  }
}
