def predict_release(data):

    weight = data.get("weight", 0)

    score = min(weight * 0.01, 1.0)

    return {
        "release_probability": score,
        "decision": "READY" if score > 0.75 else "NOT_READY"
    }