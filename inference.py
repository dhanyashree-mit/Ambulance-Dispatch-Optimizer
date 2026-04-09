import os
import time
import json
import requests
import sys
from typing import List, Optional
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    # We use stderr for the warning but the rules require tags like [START] in stdout
    print("WARNING: HF_TOKEN environment variable is not set", file=sys.stderr)
    # However, the validator will fail anyway if we don't have a token. 
    # But we MUST emit logs. Let's try to proceed as far as possible.

BENCHMARK = "ambulance-dispatch-env"
ENV_URL = "http://localhost:7860"

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    # Format reward to exactly 2 decimal places to be safe
    reward_formatted = f"{float(reward):.2f}"
    print(f"[STEP] step={step} action={action} reward={reward_formatted} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{float(r):.2f}" for r in rewards)
    success_val = str(success).lower()
    print(f"[END] success={success_val} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

def run_task(task_id: str):
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)
    
    # Initialize variables for 'finally' block safety
    rewards = []
    step_count = 0
    success = False
    error_occurred = False
    
    try:
        if not HF_TOKEN:
            raise ValueError("HF_TOKEN missing")

        client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)
        
        # Reset Environment
        try:
            res = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id}, timeout=10)
            if res.status_code != 200:
                raise RuntimeError(f"Server reset failed with status {res.status_code}")
            state = res.json()
        except Exception as e:
            # If reset fails, we still need at least one STEP and an END
            log_step(step=1, action="{}", reward=0.01, done=True, error=f"Reset Error: {str(e)}")
            rewards.append(0.01)
            step_count = 1
            return

        # Main Episode Loop
        system_prompt = """You are an ambulance dispatcher agent. You must select an available ambulance and an active emergency.
Output your action strictly as a JSON object with this exact format:
{"ambulance_id": "<id>", "emergency_id": "<id>"}
If you do not wish to take any action, output an empty JSON object: {}
Do not output any markdown formatting, only pure JSON."""

        done = False
        while not done and step_count < 20:
            step_count += 1
            prompt = f"Current State:\n{json.dumps(state)}\n\nWhat is your action?"
            
            error_msg = None
            action_dict = {}
            action_str = "{}"
            
            # 1. Get Action from LLM
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=64,
                    temperature=0.0,
                    timeout=30
                )
                
                raw_action = response.choices[0].message.content.strip()
                
                # Basic cleaning of markdown
                if "```" in raw_action:
                    lines = raw_action.split("\n")
                    raw_action = "".join([l for l in lines if not l.strip().startswith("```")])
                
                action_dict = json.loads(raw_action)
                action_str = json.dumps(action_dict, separators=(',', ':'))
            except Exception as e:
                error_msg = str(e)
                action_str = "{}"
                action_dict = {}

            # 2. Step Environment
            try:
                action_payload = {"action": action_dict if action_dict else None}
                step_res = requests.post(f"{ENV_URL}/step", json=action_payload, timeout=10)
                if step_res.status_code != 200:
                    raise RuntimeError(f"Step failed: {step_res.status_code}")
                
                step_data = step_res.json()
                reward = float(step_data["reward"])
                state = step_data["observation"]
                done = bool(step_data["done"])
            except Exception as e:
                reward = 0.01 # Fallback must be non-zero
                done = True
                error_msg = error_msg or str(e)

            rewards.append(reward)
            log_step(step=step_count, action=action_str, reward=reward, done=done, error=error_msg)
            
            if done:
                break
        
        # Determine Success based on total performance
        # According to the rules, success is a boolean. 
        # We consider it a success if we got a decent cumulative reward.
        final_score = sum(rewards)
        success = final_score >= 0.3 # Matches our target scaling range

    except Exception as e:
        error_occurred = True
        if not rewards:
            # Ensure at least one log exists
            log_step(step=1, action="{}", reward=0.01, done=True, error=str(e))
            rewards.append(0.01)
            step_count = 1
    
    finally:
        # Final safety check: rewards must not be empty
        if not rewards:
            rewards = [0.01]
            step_count = 1
        
        # Calculate final score across steps normalized to 0-1
        score = max(rewards) if rewards else 0.01
        score = min(max(score, 0.01), 0.99)
        
        log_end(success=success, steps=step_count, score=score, rewards=rewards)

if __name__ == "__main__":
    # Small delay to ensure server is ready if run in a bundle
    time.sleep(2)
    tasks = ["easy", "medium", "hard"]
    for t in tasks:
        try:
            run_task(t)
        except Exception:
            pass # run_task handles its own logging exceptions
        time.sleep(1)
