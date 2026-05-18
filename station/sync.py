import requests
import time

SERVER = "http://SERVER_IP:8000"


def sync_loop(buffer):

    while True:

        for e in buffer:
            try:
                requests.post(SERVER + "/event", json=e)
            except:
                pass

        time.sleep(30)