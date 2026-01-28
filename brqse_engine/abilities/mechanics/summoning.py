def handle_summon(match, ctx):
    if "log" in ctx: ctx["log"].append("Summoning Ally.")

def handle_create_terrain(match, ctx):
    type_ = match.group(1)
    if "log" in ctx: ctx["log"].append(f"Creating Terrain: {type_}.")

def handle_create_hazard(match, ctx):
    type_ = match.group(1)
    ele = match.group(2) or "Generic"
    if "log" in ctx: ctx["log"].append(f"Creating Hazard: {type_} ({ele}).")

def handle_create_wall(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Wall.")

def handle_create_construct(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Construct Automaton.")

def handle_animate_plant(match, ctx):
    if "log" in ctx: ctx["log"].append("Animating Plant.")

def handle_clone(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Clone.")

def handle_swarm_form(match, ctx):
    if "log" in ctx: ctx["log"].append("Transforming into Swarm.")

def handle_create_land(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating New Land.")

def handle_entomb(match, ctx):
    if "log" in ctx: ctx["log"].append("Entombing Target.")

def handle_fortress(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Fortress.")

def handle_web_shot(match, ctx):
    if "log" in ctx: ctx["log"].append("Shooting Web (Create Hazard).")

def handle_spore_cloud(match, ctx):
    if "log" in ctx: ctx["log"].append("Releasing Spore Cloud.")
