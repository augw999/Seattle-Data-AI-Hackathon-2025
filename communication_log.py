import json

def log_message(message, filename="ai_message_log.json"):
    # Serialize the message to remove circular references.
    serialized_message = serialize_task(message)
    with open(filename, "w") as f:
        json.dump(serialized_message, f, indent=4)
    print(f"Message logged to {filename}")

# Include the serialize_task function here or import it from another module.
def serialize_task(task):
    return {
        "agent": {
            "x": task["agent"].x,
            "y": task["agent"].y,
            "remaining_life": task["agent"].remaining_life
        },
        "victim": {
            "x": task["victim"].x,
            "y": task["victim"].y,
            "remaining_life": task["victim"].remaining_life
        },
        "priority": task.get("priority"),
        "target": task.get("target"),
        "score": task.get("score"),
        "route": task.get("route")
    }
