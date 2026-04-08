import json
import os
import sys

# Ensure the root directory is in the python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from tasks.easy import get_config as get_easy_config
from tasks.medium import get_config as get_medium_config
from tasks.hard import get_config as get_hard_config
from graders.easy_grader import grade as easy_grade
from graders.medium_grader import grade as medium_grade
from graders.hard_grader import grade as hard_grade

app = FastAPI()

# Load city map
CITY_MAP_PATH = os.path.join(ROOT_DIR, "data", "city_map.json")
with open(CITY_MAP_PATH, "r") as f:
    CITY_MAP = json.load(f)

# Global State
current_state = {}
current_task = None
step_count = 0

class ResetRequest(BaseModel):
    task_id: str = "easy"

class ActionParams(BaseModel):
    ambulance_id: str
    emergency_id: str

class StepRequest(BaseModel):
    action: Optional[ActionParams] = None

class StepResponse(BaseModel):
    observation: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]

@app.get("/")
def home():
    return {
        "message": "Ambulance Dispatch Optimizer Environment is ACTIVE",
        "tasks": ["easy", "medium", "hard"]
    }

@app.post("/reset", response_model=Dict[str, Any])
def reset_env(req: ResetRequest = ResetRequest()):
    global current_state, current_task, step_count
    task_id = req.task_id
    current_task = task_id
    step_count = 0

    if task_id == "easy":
        current_state = get_easy_config()
    elif task_id == "medium":
        current_state = get_medium_config()
    elif task_id == "hard":
        current_state = get_hard_config()
    else:
        raise HTTPException(status_code=400, detail="Invalid task_id")

    # Add extra state trackers
    for amb in current_state["ambulances"].values():
        amb["eta"] = 0
        amb["destination"] = None

    return current_state

@app.get("/state", response_model=Dict[str, Any])
def get_state():
    return current_state

@app.post("/step", response_model=StepResponse)
def step_env(req: StepRequest = StepRequest()):
    global current_state, step_count, current_task
    
    if not current_state:
        raise HTTPException(status_code=400, detail="Environment not reset")

    step_count += 1
    feedback = {"events": []}
    
    # Check dynamic events (Hard mode)
    events = current_state.get("dynamic_events", [])
    for event in events:
        if event.get("step") == step_count:
            if event["type"] == "traffic_spike":
                current_state["time_of_day"] = event["time_of_day"]
                feedback["events"].append("Traffic condition changed to " + event["time_of_day"])
            elif event["type"] == "breakdown":
                amb_id = event["ambulance_id"]
                if amb_id in current_state["ambulances"]:
                    current_state["ambulances"][amb_id]["status"] = "broken"
                    current_state["ambulances"][amb_id]["destination"] = None
                    feedback["events"].append(f"Ambulance {amb_id} broke down!")
            elif event["type"] == "new_emergencies":
                for e_id, e_data in event["emergencies"].items():
                    current_state["emergencies"][e_id] = e_data
                feedback["events"].append("New critical emergencies strictly reported!")

    # Process Action
    action_dict = None
    if req.action:
        amb_id = req.action.ambulance_id
        em_id = req.action.emergency_id
        action_dict = {"ambulance_id": amb_id, "emergency_id": em_id}
        
        if amb_id in current_state["ambulances"] and em_id in current_state["emergencies"]:
            amb = current_state["ambulances"][amb_id]
            em = current_state["emergencies"][em_id]
            
            if amb["status"] == "available" and em["status"] == "active":
                amb["status"] = "dispatched"
                amb["destination"] = em_id
                
                # Calculate ETA
                dist = CITY_MAP["distances"][amb["location"]][em["location"]]
                mult = CITY_MAP["traffic_multipliers"][current_state["time_of_day"]]
                amb["eta"] = max(1, int(dist * mult))

    # Evaluate Reward
    if current_task == "easy":
        reward = easy_grade(current_state, action_dict, CITY_MAP)
    elif current_task == "medium":
        reward = medium_grade(current_state, action_dict, CITY_MAP)
    elif current_task == "hard":
        reward = hard_grade(current_state, action_dict, CITY_MAP)
    else:
        reward = 0.01

    # Advance Simulation Time
    for e_id, em in current_state["emergencies"].items():
        if em["status"] == "active":
            em["time_since_call"] += 1
            
    for amb_id, amb in current_state["ambulances"].items():
        if amb["status"] == "dispatched":
            amb["eta"] -= 1
            if amb["eta"] <= 0:
                # Reached Emergency
                amb["status"] = "available"
                amb["location"] = current_state["emergencies"][amb["destination"]]["location"]
                current_state["emergencies"][amb["destination"]]["status"] = "handled"
                amb["destination"] = None

    done = all(em["status"] == "handled" for em in current_state["emergencies"].values()) or step_count >= 20

    return StepResponse(
        reward=reward,
        done=done,
        info=feedback,
        observation=current_state
    )

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
