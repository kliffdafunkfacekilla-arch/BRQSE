
from Events.eventmanager import generator, EventType, ChaosModifier

# Disable chaos for this test
generator.chaos_chance = 0

print("=" * 50)
print("10 PURE EVENTS (No Chaos)")
print("=" * 50)

for i in range(10):
    enc = generator.generate()
    event = enc['event']
    chaos = enc['chaos']
    
    print(f"\n[{i+1}] {event['name']}")
    print(f"    Type: {event['type']}")
    
    # Show relevant details based on type
    if 'danger' in event:
        print(f"    Danger: {event['danger']}, Check: {event['skill_check']}")
    if 'difficulty' in event:
        print(f"    Difficulty: {event['difficulty']}, Check: {event['skill_check']}")
    if 'tier' in event:
        print(f"    Tier: {event['tier']}, Count: {event['count']}, AI: {event['behavior']}")
    if 'disposition' in event:
        print(f"    Disposition: {event['disposition']}, Reward: {event.get('reward')}")
    if 'loot_tier' in event:
        print(f"    Loot Tier: {event['loot_tier']}")
    if 'safety' in event:
        print(f"    Safety: {event['safety']}, Bonus: {event['bonus']}")
    
    print(f"    Chaos: {chaos}")
