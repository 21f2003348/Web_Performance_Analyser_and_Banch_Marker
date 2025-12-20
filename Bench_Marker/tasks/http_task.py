import requests
import httpx

URL = "https://jsonplaceholder.typicode.com/todos/1"
TIMEOUT = 5  # seconds


def fetch_requests(_):
    response = requests.get(URL, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def fetch_httpx(_):
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.get(URL)
        response.raise_for_status()
        return response.json()
