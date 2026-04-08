import requests
import json
import time

URL = "http://localhost:7860"

def test_easy():
    print("Testing Easy Reset")
    res = requests.post(f"{URL}/reset", json={"task_id": "easy"})
    state = res.json()
    print("Initial State:", json.dumps(state, indent=2))
    
    # action 1
    print("\nTesting Step Action")
    res = requests.post(f"{URL}/step", json={"action": {"ambulance_id": "amb_1", "emergency_id": "em_1"}})
    step_data = res.json()
    print("Step 1:", json.dumps(step_data, indent=2))

def test_hard():
    print("\nTesting Hard Task dynamically")
    res = requests.post(f"{URL}/reset", json={"task_id": "hard"})
    
    # Do 4 steps without action
    for i in range(1, 6):
        res = requests.post(f"{URL}/step", json={"action": {}})
        print(f"Step {i} Hard:")
        print("Feedback:", res.json().get("feedback"))
        
if __name__ == "__main__":
    time.sleep(2)
    test_easy()
    test_hard()
    print("All tests successfully completed.")
