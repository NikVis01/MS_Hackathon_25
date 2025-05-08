import requests

payload = {
    "event": "dsajdsadsa detected",
    "timestamp": "19:69:69",
    "feedId": "1",
    "videoUrl": "http://majsssss.com/clip.mp4"
}

response = requests.post("http://172.160.224.28:1234/detection_output", json=payload)
print(response.json())