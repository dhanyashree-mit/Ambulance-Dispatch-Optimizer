def get_config():
    return {
        "ambulances": {
            "amb_1": {"status": "available", "location": "A1", "destination": None}
        },
        "emergencies": {
            "em_1": {"location": "A2", "severity": 2, "time_since_call": 0, "status": "active"}
        },
        "time_of_day": "normal",
        "dynamic_events": []
    }
