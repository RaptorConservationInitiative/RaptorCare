def classify(state: dict):

    if state.get("medical", 0) > 2:
        return "IN_CARE"

    if state.get("flight_score", 0) > 0.7:
        return "RELEASE_READY"

    return "OBSERVATION"