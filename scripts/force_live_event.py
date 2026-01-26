
import requests
import json
import time

API_URL = "http://localhost:5001/api"

def force_event():
    print("Forcing event via API...")
    # We can try to force a tension event by 'waiting' repeatedly
    # OR we can try to use the debug endpoint if we added one (we didn't add a dedicated event debug, only combat)
    
    # Let's use the game action 'wait' which triggers tension
    # We can also hack it by manually setting tension threshold if we could, but we can't via API.
    
    # Actually, simpler: The GameLoop has logic to trigger events.
    # Let's try to 'move' to a new room if possible, or just spam wait.
    
    for i in range(20):
        print(f"Action: WAIT ({i+1})")
        resp = requests.post(f"{API_URL}/game/action", json={"action": "wait", "x": 0, "y": 0})
        data = resp.json()
        
        # Check if event triggered
        log = data.get("result", {}).get("log", "")
        print(f"Log: {log}")
        
        if "GOAL:" in log:
            print("\nSUCCESS: AI Goal detected in log!")
            print(log)
            return True
            
        if "The air ripples" in log and "GOAL:" not in log:
             print("\nFAILURE: Default event text detected without Goal!")
             return False
             
        time.sleep(0.5)
        
    print("No event triggered after 20 waits.")
    return False

if __name__ == "__main__":
    force_event()
