import requests

payload = {
    "event": "Motion detected",
    "timestamp": "69:69:69",
    "feedId": "1",
    "videoUrl": "http://majsssss.com/clip.mp4"
}

response = requests.post("http://localhost:8000/detection_output", json=payload)
print(response.json())