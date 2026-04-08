def get_config():
    return {
        "ambulances": {
            "amb_1": {"status": "available", "location": "A1", "destination": None},
            "amb_2": {"status": "available", "location": "B3", "destination": None},
            "amb_3": {"status": "available", "location": "D4", "destination": None}
        },
        "emergencies": {
            "em_1": {"location": "A4", "severity": 3, "time_since_call": 0, "status": "active"},
            "em_2": {"location": "B1", "severity": 1, "time_since_call": 0, "status": "active"},
            "em_3": {"location": "C2", "severity": 2, "time_since_call": 0, "status": "active"},
            "em_4": {"location": "D1", "severity": 3, "time_since_call": 0, "status": "active"},
            "em_5": {"location": "C4", "severity": 2, "time_since_call": 0, "status": "active"}
        },
        "time_of_day": "normal",
        "dynamic_events": [
            {
                "step": 3,
                "type": "traffic_spike",
                "time_of_day": "rush_hour"
            },
            {
                "step": 3,
                "type": "breakdown",
                "ambulance_id": "amb_2"
            },
            {
                "step": 3,
                "type": "new_emergencies",
                "emergencies": {
                    "em_6": {"location": "A2", "severity": 3, "time_since_call": 0, "status": "active"},
                    "em_7": {"location": "D3", "severity": 3, "time_since_call": 0, "status": "active"}
                }
            }
        ]
    }
