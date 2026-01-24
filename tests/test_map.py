from brqse_engine.world.map_generator import MapGenerator
gen = MapGenerator()
layout = gen.generate_map('HALLWAY')
print(f"Hallway Walls: {len(layout['walls'])}")
print(f"Objects: {layout['objects']}")
print(f"Hazards: {layout['hazards']}")
