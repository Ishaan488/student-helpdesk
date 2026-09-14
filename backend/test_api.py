import urllib.request
import json
import sys

try:
    req = urllib.request.Request("http://127.0.0.1:8000/api/v1/escalations/")
    # We aren't sending an auth token, so it should return 401 Unauthorized
    with urllib.request.urlopen(req) as response:
        with open("test_output.txt", "w") as f:
            f.write(response.read().decode())
except urllib.error.HTTPError as e:
    with open("test_output.txt", "w") as f:
        f.write(f"HTTPError: {e.code} {e.reason}\n{e.read().decode()}")
except urllib.error.URLError as e:
    with open("test_output.txt", "w") as f:
        f.write(f"URLError: {e.reason}")
except Exception as e:
    with open("test_output.txt", "w") as f:
        f.write(f"Exception: {e}")
