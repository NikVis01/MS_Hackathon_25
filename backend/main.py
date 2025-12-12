### Main app file

import cv2
# import predictor
import fastapi
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from infer import YOLODetector
from sound_detector import SoundDetector
from openai import OpenAI
from dotenv import load_dotenv

import uvicorn
import threading
import time
import numpy as np
from fastapi.responses import StreamingResponse
import sounddevice as sd
import librosa
import json
import os
import requests
from datetime import datetime

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

# Audio detection variables
audio_detector = None
audio_detection_enabled = False
audio_detection_lock = threading.Lock()
latest_audio_detections = {"success": True, "detections": []}
yamnet_categories_path = "yamnet_categories.json"
# WebSocket server URL - change if websocket_server.py runs on different port
# Note: websocket_server.py runs FastAPI on port 8000, but main.py also uses 8000
# You may need to change websocket_server.py port or run them separately
websocket_url = "http://localhost:8001/detection_output"  # WebSocket server HTTP endpoint (websocket_server.py runs on port 8001)

class ImageRequest(BaseModel):
    image_data: str

class PromptPayload(BaseModel):
    feed_id: str
    detection_mode: str
    prompt: str


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

@app.get("/latest-audio-detections")
async def get_latest_audio_detections():
    """Get the latest audio detection results"""
    with audio_detection_lock:
        return latest_audio_detections

@app.post("/audio-detection/enable")
async def enable_audio_detection():
    """Enable audio detection"""
    global audio_detection_enabled
    with audio_detection_lock:
        audio_detection_enabled = True
    return {"status": "enabled", "message": "Audio detection enabled"}

@app.post("/audio-detection/disable")
async def disable_audio_detection():
    """Disable audio detection"""
    global audio_detection_enabled
    with audio_detection_lock:
        audio_detection_enabled = False
    return {"status": "disabled", "message": "Audio detection disabled"}

@app.get("/audio-detection/status")
async def get_audio_detection_status():
    """Get audio detection status"""
    return {"enabled": audio_detection_enabled}

#### --- OpenAI prompt processing (from sound_AI.py) --- ###

# Load OpenAI client
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/recieve")
async def receive_prompt(payload: PromptPayload):
    """
    Process natural language prompt and generate YAMNet category names.
    Integrated from sound_AI.py
    """
    result = update_yamnet_categories(payload.prompt)
    return {
        "status": "OK",
        "received": payload.dict(),
        "ai_response": result
    }

def update_yamnet_categories(prompt: str):
    """Generate YAMNet categories from prompt using OpenAI"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI that analyzes prompts and returns a JSON list of YAMNet sound categories that are relevant to the prompt. Return a JSON array of strings."
                },
                {
                    "role": "user",
                    "content": f"Prompt: {prompt}. Generate a JSON list of relevant YAMNet categories. Please create approximately 5 categories, preferably well-trained and common ones. JUST print the list, nothing else, not even a json tag. If the prompt you recieved has more than one argument, try not to generalize"
                }
            ]
        )

        raw_content = response.choices[0].message.content
        try:
            categories = json.loads(raw_content)
            print(f"Generated YAMNet categories: {categories}")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"JSON error: {e}")
            print(f"Content: {raw_content}")
            return {
                "status": "error",
                "message": "Invalid JSON from OpenAI",
                "yamnet_categories": []
            }

        # Save result to file
        with open(yamnet_categories_path, 'w') as f:
            json.dump(categories, f, indent=4)

        # Trigger reload of categories in audio detector
        reload_yamnet_categories()

        return {
            "status": "success",
            "message": "YAMNet categories updated successfully",
            "yamnet_categories": categories
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "yamnet_categories": []
        }

def camera_motion_yolo_thread():
    global latest_detections, video_frame
    # Get camera URL from environment variable or use default
    camera_url = os.getenv("CAMERA_FEED_URL")
    if camera_url is None:
        camera_url = 0  # Default to 0 (local webcam) if not set
    elif camera_url.isdigit():
        camera_url = int(camera_url)  # Convert to int if it's a device index
    cap = cv2.VideoCapture(camera_url)

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

#### --- Audio detection functions --- ###

def send_detection_to_websocket(event_name: str, probability: float, feed_id: str = "audio"):
    """Send detection event to WebSocket server"""
    try:
        data = {
            "event": event_name,
            "timestamp": datetime.now().isoformat(),
            "feedId": feed_id,
            "probability": probability,
            "type": "audio"
        }
        # Send to WebSocket server HTTP endpoint
        requests.post(websocket_url, json=data, timeout=1)
    except Exception as e:
        print(f"Failed to send detection to WebSocket: {e}")

def reload_yamnet_categories():
    """Reload YAMNet categories from file and reinitialize detector"""
    global audio_detector
    try:
        if os.path.exists(yamnet_categories_path):
            with open(yamnet_categories_path, 'r') as f:
                categories = json.load(f)
            print(f"Reloaded YAMNet categories: {categories}")
            
            # Reinitialize detector with new categories
            if audio_detector is None or audio_detection_enabled:
                audio_detector = SoundDetector(
                    use_yamnet=True,
                    yamnet_categories_path=yamnet_categories_path
                )
                print("Audio detector reinitialized with new categories")
            return True
    except Exception as e:
        print(f"Error reloading YAMNet categories: {e}")
    return False

def audio_detection_thread():
    """Continuous audio detection thread using microphone"""
    global audio_detector, latest_audio_detections, audio_detection_enabled
    
    # Initialize detector
    try:
        audio_detector = SoundDetector(
            use_yamnet=True,
            yamnet_categories_path=yamnet_categories_path
        )
        print("Audio detector initialized with YAMNet")
    except Exception as e:
        print(f"Failed to initialize audio detector: {e}")
        return
    
    sample_rate = 16000
    block_duration = 0.5  # Process 0.5 second chunks
    last_detection_time = {}
    detection_cooldown = 2.0  # Minimum seconds between same detection
    
    # Track file modification time to reload categories
    last_file_mtime = 0
    if os.path.exists(yamnet_categories_path):
        last_file_mtime = os.path.getmtime(yamnet_categories_path)
    
    def audio_callback(indata, frames, time_info, status):
        nonlocal last_detection_time, last_file_mtime
        
        if not audio_detection_enabled:
            return
        
        if status:
            print(f"Audio status: {status}")
        
        # Check if categories file was updated
        if os.path.exists(yamnet_categories_path):
            current_mtime = os.path.getmtime(yamnet_categories_path)
            if current_mtime > last_file_mtime:
                last_file_mtime = current_mtime
                reload_yamnet_categories()
        
        # Convert to mono if stereo
        if len(indata.shape) > 1:
            audio_data = np.mean(indata, axis=1)
        else:
            audio_data = indata.flatten()
        
        # Resample to 16kHz if needed (YAMNet requirement)
        device_sr = int(sd.query_devices(sd.default.device[0])['default_samplerate'])
        if device_sr != sample_rate:
            audio_data = librosa.resample(
                audio_data.astype(np.float32),
                orig_sr=device_sr,
                target_sr=sample_rate
            )
        
        # Normalize
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        # Run detection
        try:
            if audio_detector:
                results = audio_detector.detect_sounds_from_stream(audio_data, threshold=0.3)
                
                if results:
                    current_time = time.time()
                    detections = []
                    
                    for result in results:
                        event_name = result['class']
                        prob = result['probability']
                        
                        # Cooldown check
                        if event_name not in last_detection_time or \
                           current_time - last_detection_time[event_name] >= detection_cooldown:
                            
                            last_detection_time[event_name] = current_time
                            detections.append({
                                "class": event_name,
                                "probability": prob,
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            # Send to WebSocket
                            send_detection_to_websocket(event_name, prob)
                    
                    # Update latest detections
                    with audio_detection_lock:
                        latest_audio_detections = {
                            "success": True,
                            "detections": detections,
                            "timestamp": datetime.now().isoformat()
                        }
                        
        except Exception as e:
            print(f"Audio detection error: {e}")
    
    try:
        # Get default input device
        default_device = sd.query_devices(kind='input')
        device_sr = int(default_device['default_samplerate'])
        
        print(f"Starting audio detection on device: {default_device['name']}")
        print(f"Sample rate: {device_sr} Hz (will resample to {sample_rate} Hz)")
        
        # Start recording
        with sd.InputStream(
            callback=audio_callback,
            channels=1,
            samplerate=device_sr,
            blocksize=int(device_sr * block_duration),
            device=None
        ):
            print("Audio detection thread running...")
            while True:
                sd.sleep(100)
                
    except Exception as e:
        print(f"Audio detection thread error: {e}")
        import traceback
        traceback.print_exc()

# Start the camera thread on app startup
@app.on_event("startup")
def start_threads():
    # Start camera thread
    camera_thread = threading.Thread(target=camera_motion_yolo_thread, daemon=True)
    camera_thread.start()
    
    # Start audio detection thread (will wait for enable)
    audio_thread = threading.Thread(target=audio_detection_thread, daemon=True)
    audio_thread.start()
    print("Audio detection thread started (disabled by default, use /audio-detection/enable to activate)")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)