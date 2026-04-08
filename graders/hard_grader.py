from graders.medium_grader import grade as medium_grade

def grade(state, action, city_map):
    base_reward = medium_grade(state, action, city_map)

    # Extra penalty if broken ambulances left critical emergencies unserved
    broken_ambs = [a for a in state["ambulances"].values() if a["status"] == "broken"]
    unserved_critical = [
        e for e in state["emergencies"].values()
        if e["status"] == "active" and e["severity"] == 3
    ]

    penalty = len(broken_ambs) * len(unserved_critical) * 0.05
    return max(0.01, min(0.99, base_reward - penalty))
