### Main app file

import cv2
# import predictor
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

app = FastAPI()

### --- Middleware --- ###
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#### --- Inits and global variables --- ###
yolo_detector = YOLODetector()
latest_detections = {"success": True, "detections": []}
latest_lock = threading.Lock()

video_frame_lock = threading.Lock()
video_frame = None

class ImageRequest(BaseModel):
    image_data: str


#### --- YOLO inference --- ###
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


#### --- FastAPI endpoints --- ####
"""
Camera_motion_yolo_thread:
    - Captures frames from the camera using cv2.VideoCapture(0)
    - Runs continuous motion detection with Yolo v8
    - Prcessed frame stored in video_frame global variable
Frontend integration:
    - /latest-detections: returns the latest detections
    - /video_feed: returns the latest frame with bounding boxes overlayed

    - So when client requests /video_feed, it gets the latest frame from video_frame with Yolo v8 bounding boxes overlayed

Ideas for stuff to add:
    - When streaming to cloud vm for YOLO, we only stream changes in the frame, keeping old frames and their detections in the frontend if no motion is detected
    - Compress img frame files before sending to VM
"""
@app.get("/latest-detections")
async def get_latest_detections():
    with latest_lock:
        return latest_detections

def camera_motion_yolo_thread():
    global latest_detections, video_frame
    cap = cv2.VideoCapture("rtsp://172.160.224.28:8889/live/mystream")

    if not cap.isOpened():
        print("Cannot open camera")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
            
        # Run YOLO detection on every frame
        results = yolo_detector.model(frame)
        detections = []
        annotated_frame = frame.copy()

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

        with video_frame_lock:
            video_frame = annotated_frame.copy()
        time.sleep(0.05)  # ~20 FPS
    cap.release()


#### --- Video streaming --- ###
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