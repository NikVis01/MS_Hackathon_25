### Main app file

import cv2
import infer
import predictor
import fastapi
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from infer import YOLODetector
import uvicorn
import threading
import time
import numpy as np
from fastapi.responses import StreamingResponse
import io

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize YOLO detector
yolo_detector = YOLODetector()
latest_detections = {"success": True, "detections": []}
latest_lock = threading.Lock()

# Global for video streaming
video_frame_lock = threading.Lock()
video_frame = None

class ImageRequest(BaseModel):
    image_data: str

@app.post("/detect")
async def detect_objects(request: ImageRequest):
    """
    Process an image and return YOLO detection results
    """
    try:
        results = yolo_detector.process_image(request.image_data)
        if not results["success"]:
            raise HTTPException(status_code=400, detail=results["error"])
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

@app.get("/latest-detections")
async def get_latest_detections():
    with latest_lock:
        return latest_detections

def camera_motion_yolo_thread(motion_threshold=50000):
    global latest_detections, video_frame
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    prev_gray = None
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        annotated_frame = frame.copy()
        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            motion_score = cv2.countNonZero(thresh)
            if motion_score > motion_threshold:
                results = yolo_detector.model(frame)
                detections = []
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        confidence = box.conf[0].item()
                        class_id = int(box.cls[0].item())
                        class_name = yolo_detector.model.names[class_id]
                        detections.append({
                            "bbox": [x1, y1, x2, y2],
                            "confidence": confidence,
                            "class": class_name,
                            "class_id": class_id
                        })
                        # Draw on annotated_frame
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0,255,0), 2)
                        label = f"{class_name} {confidence:.2f}"
                        cv2.putText(annotated_frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
                with latest_lock:
                    latest_detections = {"success": True, "detections": detections}
        prev_gray = gray
        # Always update the latest video frame
        with video_frame_lock:
            video_frame = annotated_frame.copy()
        time.sleep(0.05)  # ~20 FPS
    cap.release()

def mjpeg_streamer():
    global video_frame
    while True:
        with video_frame_lock:
            frame = video_frame.copy() if video_frame is not None else None
        if frame is not None:
            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            buf = jpeg.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf + b'\r\n')
        time.sleep(0.05)

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(mjpeg_streamer(), media_type='multipart/x-mixed-replace; boundary=frame')

# Start the camera thread on app startup
@app.on_event("startup")
def start_camera_thread():
    t = threading.Thread(target=camera_motion_yolo_thread, daemon=True)
    t.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
