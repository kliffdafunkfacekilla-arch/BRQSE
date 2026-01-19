try:
    from .constants import Conditions
except ImportError:
    # Fallback if run as script or path issue
    from brqse_engine.core.constants import Conditions

class StatusManager:
    def __init__(self, owner):
        self.owner = owner
        # Set for fast lookups: {"prone", "blinded"}
        self._active_conditions = set()
        # List for tracking durations: [{"name": "Prone", "duration": 1, "on_expire": None}]
        self.timed_effects = []

    def add_condition(self, name, duration=1, on_expire=None):
        """
        Apply a condition. If it exists, refresh duration to the max.
        duration: -1 for permanent, else rounds.
        """
        clean_name = name.capitalize()
        
        # Check if we update existing
        for eff in self.timed_effects:
            if eff["name"] == clean_name:
                if duration == -1:
                    eff["duration"] = -1
                elif eff["duration"] != -1:
                    eff["duration"] = max(eff["duration"], duration)
                return

        # Add new
        self.timed_effects.append({
            "name": clean_name,
            "duration": duration,
            "on_expire": on_expire
        })
        self._active_conditions.add(clean_name)
        # Log if possible
        # print(f"Applied {clean_name} to {self.owner.name}")

    def remove_condition(self, name):
        clean_name = name.capitalize()
        if clean_name in self._active_conditions:
            self._active_conditions.remove(clean_name)
            # Remove from timed list
            self.timed_effects = [e for e in self.timed_effects if e["name"] != clean_name]

    def has(self, name):
        """Check if condition is active. Case insensitive-ish."""
        return name.capitalize() in self._active_conditions

    def clear_all(self):
        self._active_conditions.clear()
        self.timed_effects.clear()
        
    def add_timed_effect(self, name, duration, on_expire=None):
        """Alias for add_condition to match legacy API expectations if needed"""
        self.add_condition(name, duration, on_expire)

    def tick(self):
        """
        Call at start/end of turn. Decrements durations.
        Returns list of expired effect names.
        """
        expired = []
        remaining = []

        for eff in self.timed_effects:
            if eff["duration"] == -1:
                remaining.append(eff)
                continue

            eff["duration"] -= 1
            if eff["duration"] <= 0:
                expired.append(eff["name"])
                self._active_conditions.discard(eff["name"])
                
                # Handle callbacks if you have them implemented later
                if eff["on_expire"] and hasattr(self.owner, eff["on_expire"]):
                     # If method, call it. If property, do nothing (removed from set).
                     cb = getattr(self.owner, eff["on_expire"])
                     if callable(cb): cb()
            else:
                remaining.append(eff)
        
        self.timed_effects = remaining
        return expired
