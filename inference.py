import os
import time
import json
import requests
from typing import List, Optional
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN environment variable is not set")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME") # Optional for Docker testing

BENCHMARK = "ambulance-dispatch-env"
ENV_URL = "http://localhost:7860"

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP]  step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END]   success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

def run_task(task_id: str):
    client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)
    
    res = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id})
    if res.status_code != 200:
        print(f"Failed to reset task {task_id}")
        return
        
    state = res.json()
    
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)
    
    step_count = 0
    done = False
    
    rewards = []
    
    system_prompt = """You are an ambulance dispatcher agent. You must select an available ambulance and an active emergency.
Output your action strictly as a JSON object with this exact format:
{"ambulance_id": "<id>", "emergency_id": "<id>"}
If you do not wish to take any action, output an empty JSON object: {}
Do not output any markdown formatting, only pure JSON."""

    while not done:
        prompt = f"Current State:\n{json.dumps(state)}\n\nWhat is your action?"
        step_count += 1
        
        error = None
        action_dict = {}
        action_str = "{}"
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=64,
                temperature=0.0
            )
            
            raw_action = response.choices[0].message.content.strip()
            
            if raw_action.startswith("```json"):
                raw_action = raw_action[7:]
            if raw_action.endswith("```"):
                raw_action = raw_action[:-3]
                
            action_dict = json.loads(raw_action)
            action_str = json.dumps(action_dict, separators=(',', ':'))
        except Exception as e:
            error = str(e)
            action_str = "{}"

        action_payload = {"action": action_dict if action_dict else None}
        
        try:
            step_res = requests.post(f"{ENV_URL}/step", json=action_payload)
            step_data = step_res.json()
            
            reward = step_data["reward"]
            state = step_data["observation"]
            done = step_data["done"]
        except Exception as e:
            reward = 0.0
            done = True
            error = error or str(e)

        rewards.append(reward)
        
        log_step(step=step_count, action=action_str, reward=reward, done=done, error=error)
        
        if done or step_count >= 20:
            break

    # Calculate final score across steps normalized to 0-1
    score = max(rewards) if rewards else 0.0
    score = min(max(score, 0.0), 1.0)
    success = score >= 0.5

    log_end(success=success, steps=step_count, score=score, rewards=rewards)

if __name__ == "__main__":
    tasks = ["easy", "medium", "hard"]
    for t in tasks:
        run_task(t)
        time.sleep(1)
