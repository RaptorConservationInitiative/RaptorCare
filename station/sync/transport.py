import requests

SERVER = "http://SERVER_IP:8000"

def send_event(event):

    r = requests.post(
        SERVER + "/sync/event",
        json=event,
        timeout=15
    )

    return r.status_code == 200
