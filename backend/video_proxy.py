import cv2
import time
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI()

RTSP_URL = "rtsp://172.160.225.181:8554/live/mystream/cam0?rtsptransport=tcp"

def connect_camera():
    """Try to open the RTSP stream with retries."""
    while True:
        cap = cv2.VideoCapture(RTSP_URL)
        if cap.isOpened():
            print("[INFO] Connected to RTSP stream.")
            return cap
        print("[WARN] Failed to open RTSP stream. Retrying in 3s...")
        cap.release()
        time.sleep(3)

def generate_mjpeg():
    cap = connect_camera()

    while True:
        success, frame = cap.read()
        if not success:
            print("[WARN] Frame read failed. Reconnecting...")
            cap.release()
            cap = connect_camera()
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
    uvicorn.run("video_proxy:app", host="0.0.0.0", port=6969)
