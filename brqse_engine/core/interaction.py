from brqse_engine.core.oracle import DungeonOracle # NEW IMPORT

class InteractionEngine:
    def __init__(self, logger, sensory_layer=None):
        self.logger = logger
        self.oracle = DungeonOracle(sensory_layer)

    def interact(self, actor, target):
        """
        The Universal 'Use' Function.
        """
        if not target:
            return "Nothing there."

        # 1. Is it a pickup?
        if target.has_tag("pickup"):
            return self._handle_pickup(actor, target)

        # 2. Is it a container?
        if target.has_tag("container"):
            return self._handle_container(actor, target)

        # 3. Is it a door/gate?
        if target.has_tag("door"):
            return self._handle_door(actor, target)

        return f"You touch the {target.name}, but nothing happens."

    def examine(self, target, room_history=None):
        """
        Detailed look using the Oracle.
        """
        if not target:
            return "You see nothing of interest."
            
        return self.oracle.inspect_entity(target, room_history)

    def _handle_pickup(self, actor, item):
        # Ensure actor has inventory
        if not hasattr(actor, "inventory"):
            actor.inventory = []
            
        actor.inventory.append(item)
        # Remove from world (handled by game loop usually, but mark here)
        item.add_tag("carried") 
        return f"You picked up {item.name}."

    def _handle_container(self, actor, container):
        if container.has_tag("locked"):
            # Check if actor has the specific key tag
            key_id = container.data.get("required_key")
            
            # Search actor's inventory for an item with tag: key_id
            # NOTE: We assume inventory items are Entity objects too
            has_key = False
            if hasattr(actor, "inventory"):
               has_key = any(i.data.get("id") == key_id for i in actor.inventory)
               # Fallback: check if item has tag matching key_id if key_id is a tag
               if not has_key and key_id:
                   has_key = any(i.has_tag(key_id) for i in actor.inventory)

            if has_key:
                container.remove_tag("locked")
                container.add_tag("open")
                return f"Click! You unlock and open the {container.name}."
            else:
                return f"The {container.name} is locked. You need a key."
        
        container.add_tag("open")
        return f"You open the {container.name}."

    def _handle_door(self, actor, door):
        return self._handle_container(actor, door) # Reuse logic for now
