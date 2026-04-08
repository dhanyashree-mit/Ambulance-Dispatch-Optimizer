def calculate_manhattan(z1, z2):
    r1 = ord(z1[0]) - ord('A')
    c1 = int(z1[1]) - 1
    r2 = ord(z2[0]) - ord('A')
    c2 = int(z2[1]) - 1
    return abs(r1 - r2) + abs(c1 - c2)

def grade(state, action, city_map):
    # Calculate the composite reward based on the specified formula
    reward = 0.0
    
    severity_weights = {3: 1.0, 2: 0.6, 1: 0.3}

    for em_id, em in state["emergencies"].items():
        em_reward = 0.0
        is_dispatched_to = False
        dispatched_amb = None
        
        # Check if any ambulance is dispatched to this emergency
        dispatched_amb_id = None
        for amb_id, amb in state["ambulances"].items():
            if amb.get("destination") == em_id:
                is_dispatched_to = True
                dispatched_amb = amb
                dispatched_amb_id = amb_id
                break
                
        if is_dispatched_to and dispatched_amb_id:
            em_reward += 0.4
            
            # Check if it was the closest available
            # Note: since this evaluates at step level, we approximate "closest available" 
            # by checking if any other currently available ambulance is closer.
            closest = True
            dist_to_em = calculate_manhattan(dispatched_amb["location"], em["location"])
            
            for other_id, other_amb in state["ambulances"].items():
                if other_id != dispatched_amb_id and other_amb["status"] == "available":
                    other_dist = calculate_manhattan(other_amb["location"], em["location"])
                    if other_dist < dist_to_em:
                        closest = False
                        break
            
            if closest:
                em_reward += 0.3
                
            em_reward += 0.3 * severity_weights.get(em["severity"], 0.3)
            
        else:
            if em["severity"] == 3: # Critical
                em_reward -= 0.2
                em_reward -= 0.1 * em["time_since_call"]
                
        reward += em_reward

    return max(0.0, min(1.0, reward))
