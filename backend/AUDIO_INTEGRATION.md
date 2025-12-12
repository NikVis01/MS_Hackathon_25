# Audio Detection Integration Guide

## Full Pipeline Integration

The complete audio detection pipeline is now integrated:

```
LLM (OpenAI) → YAMNet Categories → YAMNet Classification → WebSocket Output
```

## How It Works

### 1. **LLM Generates Categories** (`sound_AI.py`)
- User sends natural language prompt to `/recieve` endpoint
- OpenAI GPT-3.5 analyzes prompt and generates relevant YAMNet category names
- Categories saved to `yamnet_categories.json`

### 2. **YAMNet Classification** (`main.py` + `yamnet_detector.py`)
- `main.py` continuously monitors microphone input
- Audio is resampled to 16kHz (YAMNet requirement)
- YAMNet model classifies audio into 521 possible categories
- Results filtered to only show categories from `yamnet_categories.json`
- Detections above threshold (0.3) are processed

### 3. **WebSocket Output** (`websocket_server.py`)
- When sounds are detected, events sent to WebSocket server
- Frontend receives real-time notifications
- Terminal shows detection alerts

## Setup

### 1. Start WebSocket Server
```bash
cd Frontend
python websocket_server.py
```
This runs:
- WebSocket server on `ws://localhost:1234`
- HTTP API on `http://localhost:8001`

### 2. Start Main Backend
```bash
cd backend
python main.py
```
This runs:
- FastAPI server on `http://localhost:8000`
- Video detection (YOLO)
- Audio detection thread (disabled by default)

### 3. Enable Audio Detection
```bash
curl -X POST http://localhost:8000/audio-detection/enable
```

Or use the frontend to enable it.

## API Endpoints

### Audio Detection Control
- `POST /audio-detection/enable` - Enable audio detection
- `POST /audio-detection/disable` - Disable audio detection
- `GET /audio-detection/status` - Check if audio detection is enabled
- `GET /latest-audio-detections` - Get latest audio detection results

### Category Generation
- `POST /recieve` (in `sound_AI.py`) - Generate YAMNet categories from prompt
  - Body: `{"feed_id": "string", "detection_mode": "string", "prompt": "string"}`

## Automatic Category Reload

The system automatically reloads `yamnet_categories.json` when it's updated:
- File modification time is monitored
- When categories change, detector reinitializes with new categories
- No restart required!

## Detection Flow Example

1. User sends prompt: `"Detect glass breaking and crashes"`
2. OpenAI generates: `["Glass", "Crash", "Impact", "Shatter"]`
3. Categories saved to `yamnet_categories.json`
4. Audio detector reloads categories automatically
5. Microphone monitors for these sounds
6. When detected (probability > 0.3):
   - Event sent to WebSocket: `{"event": "Glass", "probability": 0.65, ...}`
   - Frontend shows alert notification
   - Terminal logs the detection

## Configuration

- **Detection Threshold**: 0.3 (default, can be changed in code)
- **Detection Cooldown**: 2 seconds (prevents spam for same sound)
- **Sample Rate**: 16kHz (YAMNet requirement, auto-resampled)
- **Block Duration**: 0.5 seconds (processing chunks)

## Troubleshooting

### Audio detection not working?
1. Check if enabled: `GET /audio-detection/status`
2. Enable it: `POST /audio-detection/enable`
3. Check microphone permissions
4. Verify WebSocket server is running

### Categories not updating?
- Check `yamnet_categories.json` file exists
- Verify file permissions
- Check console logs for reload messages

### WebSocket not receiving events?
- Verify websocket_server.py is running on port 8001
- Check frontend WebSocket connection (port 1234)
- Look for connection errors in console

