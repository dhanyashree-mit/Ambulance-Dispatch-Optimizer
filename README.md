---
title: Ambulance Dispatch Optimizer
emoji: 🚑
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
tags:
  - openenv
---
# Ambulance Dispatch Optimizer (OpenEnv)

### 🔗 Quick Links
- **Interactive API Docs**: [Direct Swagger UI](https://dhanyamit-ambulance-dispatch-env.hf.space/docs)
- **Environment Status**: [Healthy Check](https://dhanyamit-ambulance-dispatch-env.hf.space/)

## Overview
This is an OpenEnv reinforcement learning environment that simulates a city's ambulance fleet management. The agent acts as a city dispatcher: it observes ambulance availabilities, dynamic traffic conditions across a realistic grid, and incoming medical emergencies of varying severities. Its goal is to minimize response times and prioritize critical cases to maximize lives saved.

## Motivation
Ambulance fleet logistics is a deeply complex, life-or-death decision-making problem. Managing ETAs, dynamic traffic multipliers, and vehicle break-down recoveries tests an agent's spatial, temporal, and strategic planning capabilities far better than simple text classification tasks or deterministic game trees.

## Mechanics

### Observation Space
Detailed as a JSON block via the `/state` endpoint, containing:
* `step_count`: The current episode step.
* `time_of_day`: Influences traffic multipliers (`normal`, `rush_hour`, `night`).
* `ambulances`: Dict of id -> dict (`status`: `available`, `dispatched`, `broken`; `location`: str zone ID; `eta`: turns until arrival).
* `emergencies`: Dict of id -> dict (`location`: str zone ID; `severity`: 1-3; `status`: `active`, `handled`; `time_since_call`: steps waited).

### Action Space
A single JSON payload representing a dispatch decision:
```json
{
  "ambulance_id": "amb_1",
  "emergency_id": "em_2"
}
```
If no valid dispatch is possible or needed, an empty object `{}` is considered a no-op action.

### Reward Logic
Bounded strictly between `0.0` and `1.0`. Evaluated per step contextually:
For each emergency:
  * `+ 0.4` if an ambulance is dispatched to it.
  * `+ 0.3` if that ambulance is the closest available option.
  * `+ 0.3` * severity weight (minor=0.3, serious=0.6, critical=1.0).
  * `- 0.2` flat penalty for critical (severity 3) emergencies unserved.
  * `- 0.1` scaling penalty per step of delay on critical cases.

The total sum across all emergencies is clamped to `0.0 - 1.0` before being returned.

## City Simulation
The city is modelled as a 4x4 grid of 16 named zones (A1–D4).
* **Grid**: Travel times are pre-computed between all zone pairs based on Manhattan distance.
* **Traffic Multipliers**: 
  * `normal`: 1.0x
  * `rush_hour`: 1.8x
  * `night`: 0.7x

## Tasks
* **easy** (Difficulty: Easy): 1 ambulance, 1 emergency. Agent must pick the correct match.
* **medium** (Difficulty: Medium): 3 ambulances, 5 emergencies in multiple zones. Standard multi-agent routing.
* **hard** (Difficulty: Hard): 3 ambulances, 5 emergencies initials, dynamically injecting a traffic spike, ambulance breakdown, and 2 new critical cases mid-episode to force recalculation.

## Baseline Scores (using gpt-4o via inference.py)
* **easy**: ~1.0 (Optimal action successfully taken out of the gate)
* **medium**: ~0.5 (Near optimal sequential assignments mapped)
* **hard**: ~0.3 (Fractional penalty dropoffs due to exact dynamic breakdown and rush hour delays)

## How to Run Locally

### 1. Requirements
Ensure you have Python 3.10+ installed. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Start the Environment Server
```bash
uvicorn environment:app --host 0.0.0.0 --port 7860
```

### 3. Run Inference (Compliance Check)
The `inference.py` script strictly follows the mandatory OpenEnv sample format, including structured stdout logging (`[START]`, `[STEP]`, `[END]`). To run it, ensure the following environment variables are set:

| Variable | Description |
| :--- | :--- |
| `API_BASE_URL` | The API endpoint for the LLM. |
| `MODEL_NAME` | The model identifier to use (e.g., `gpt-4o`). |
| `HF_TOKEN` | Your authentication token (Hugging Face or OpenAI). |

```powershell
# Windows Example
$env:API_BASE_URL="https://api.openai.com/v1"
$env:MODEL_NAME="gpt-4o"
$env:HF_TOKEN="your_key_here"
python inference.py
```

```bash
# Linux/Mac Example
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your_token_here"
python inference.py
```

## Deploying to Hugging Face Spaces
This framework complies natively with Hugging Face OpenEnv constraints.
1. Create a new "Docker" Space on Hugging Face.
2. Push this repository's files into the Space.
3. The Space will automatically build `Dockerfile` and serve `uvicorn` on port `7860`.
4. It will correctly index the tasks and logic using the provided `openenv.yaml`.
