import json

QUEUE = []


def write_event(event):

    QUEUE.append(event)

    with open("wal.log", "a") as f:
        f.write(json.dumps(event) + "\n")


def flush_queue():

    global QUEUE

    synced = len(QUEUE)

    QUEUE = []

    return {
        "synced": synced
    }