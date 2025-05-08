import cv2
import atexit
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI()

# Connect to MediaMTX RTSP stream
camera = cv2.VideoCapture("rtsp://localhost:8554/live/mystream")

def release_camera():
    if camera.isOpened():
        camera.release()

atexit.register(release_camera)

def generate_mjpeg():
    while True:
        success, frame = camera.read()
        if not success:
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() + b'\r\n')

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_mjpeg(), media_type="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    # Equivalent to Flask's app.run(host="0.0.0.0", port=8000)
    uvicorn.run("video_proxy:app", host="0.0.0.0", port=6969)
