// Basic Data Loader for Shadowfall UI

export interface Item {
    name: string;
    type: string;
    cost?: string;
    weight?: string;
    description?: string;
    "Family Name"?: string; // For weapons/armor from CSV
    Effect?: string;
}

export async function loadGear(): Promise<Item[]> {
    try {
        const gearRes = await fetch('/data/Gear_Services.json');
        const gear = await gearRes.json();

        const wepRes = await fetch('/data/weapons_and_armor.json');
        const weapons = await wepRes.json();

        // Normalize data structure if needed
        const normalizedGear = gear.map((g: any) => ({
            name: g.Item || g.Name,
            type: g.Type || "Gear",
            cost: g.Cost,
            weight: g.Weight,
            description: g.Description || g.Effect
        }));

        const normalizedWeapons = weapons.map((w: any) => ({
            name: w["Family Name"] || w.Name,
            type: w.Type || "Weapon/Armor",
            cost: w.Cost,
            weight: w.Weight,
            description: w.Effect
        }));

        return [...normalizedGear, ...normalizedWeapons];
    } catch (e) {
        console.error("Failed to load gear:", e);
        return [];
    }
}
