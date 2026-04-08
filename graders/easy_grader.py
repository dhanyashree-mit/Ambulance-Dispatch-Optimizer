def grade(state, action, city_map):
    if not action:
        return 0.01
    amb_id = action.get("ambulance_id")
    em_id = action.get("emergency_id")
    if amb_id in state["ambulances"] and em_id in state["emergencies"]:
        if state["emergencies"][em_id]["status"] == "active":
            return 0.99
    return 0.01
