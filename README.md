### 2025 SSE Business lab x Microsoft x KTH AI Society Hackathon

## Core idea:
Cameras will stream livefeeds to a website that will sent warning signals to the user if the cameras detect scertain movement/objects/objects moving in a scertain way according to a prompt by the user (in natural language) that will be fed into the backend.

# SEtting up stream from ubuntu (might be diff for debian):
1. make sure mediaMTX is downloaded on streamer platform (VM already set up to listen to mediaMTX streams)
2. ping VM with ping <vm-public-ip> this is realistically what mediaMTX is working with (will be slower)
3. Stream to VM thru RTMP:
in local terminal:
ffmpeg -f v4l2 -input_format mjpeg -video_size 640x480 -framerate 25 -i /dev/video0   -vcodec libx264 -preset veryfast -tune zerolatency -f flv rtmp://<vm-public-ip>/live/mystream
4. SSH into VM
5. Listen thru vm at port 1935 for RTMP input
in vm/MS_Hackathon_25/backend:
./mediamtx
- This should open the feed at 8554 for webRTC so u can connect main.py to this
6. run main.py on VM make sure u have: cv2.VideoCapture("rtsp://<vm-public-ip>:8554/live/mystream") where webRTC opened the stream
7. Check latency of main.py video output:
in local terminal: 
curl -o /dev/null -w '%{time_starttransfer}\n' http://172.160.224.28:8000/video_feed
THIS IS THE MAIN ISSUE CURRENTLY, ITS KINDA SLOW THIS PART


#### ChatGPT ideer för vad som blockar:
# Bottlenecks and Fixes for High Latency in `/video_feed`

## 🧨 Bottlenecks

- **MJPEG viewed in browser**
  - Browsers don’t natively support `multipart/x-mixed-replace` streams well.
  - Results in scrambled or garbled image output.

- **No frame drop mechanism**
  - The `video_frame` is copied and sent even if the client can’t keep up.
  - Leads to backpressure and growing latency in the HTTP stream.

- **Fixed frame rate with `time.sleep(0.05)`**
  - Forces ~20 FPS streaming even when the client can’t consume that fast.
  - Unnecessary waiting causes lag buildup.

- **Synchronous JPEG encoding**
  - `cv2.imencode()` runs inside the generator and blocks the stream.
  - Each frame takes time to encode, slowing down delivery.

- **No adaptive buffering**
  - There’s no queue or mechanism to manage fast frame production and slow consumption.
  - Causes either dropped frames or stream stalls depending on load.

- **Streaming over distant network (Azure VM → local machine)**
  - High round-trip time exacerbates the issues above.
  - Polling or naive streaming becomes visibly sluggish.

---

## ✅ Fixes

- **Use a proper MJPEG viewer**
  - Use `ffplay`, `VLC`, or `<img src="...">` in HTML for MJPEG streams instead of pasting the URL into the browser address bar.

- **Remove fixed frame rate sleep**
  - Only sleep if `video_frame` is `None`, not every iteration.
  - This improves responsiveness and avoids unnecessary delay.

- **Throttle frame rate explicitly**
  - Add `time.sleep(0.1)` (max 10 FPS) after each frame if needed.
  - Or use a `Queue(maxsize=1)` to drop old frames and push latest only.


- **Use a single-item frame queue**
  - Push the latest frame to a `queue.Queue(maxsize=1)`:
    - Drop stale frames automatically
    - Keep stream live with freshest data

- **Move JPEG encoding to a thread (optional enhancement)**
  - Offload `cv2.imencode()` to a worker thread or separate process if throughput is still an issue.

- **Use WebSocket for modern delivery**
  - Replace MJPEG with WebSocket:
    - Push base64-encoded JPEG + JSON bbox metadata
    - Frontend renders with `<canvas>` or `<img>` as needed

- **Deploy frontend close to backend**
  - Avoid cross-region traffic (e.g., local React → Azure backend).
  - Host the frontend on the same VM for development/testing.

- **Monitor with `curl -w '%{time_starttransfer}'`**
  - Continuously test `/video_feed` for latency spikes.
  - Target: under `0.2` seconds for stream startup.


# Multi-Protocol Streaming: Quick Bottlenecks & Fixes

## 🚨 Bottlenecks

- **CPU overload**: Multiple protocols = high encoding/decoding load.
- **Socket bloat**: Slow clients fill buffers, stall upstream.
- **Duplicate decoding**: Pulling same stream twice wastes CPU.
- **Frame races**: Shared `video_frame` without locks = torn frames.
- **Backpressure**: No frame drop = growing latency.

## ✅ Fixes

- 🔇 Disable unused protocols during debug.
- 🧵 Use `Lock` or `Queue(maxsize=1)` for `video_frame`.
- 🔁 Let MediaMTX ingest once; don’t decode twice.
- 🧼 Throttle MJPEG (≤10fps), drop stale frames.
- 📡 One protocol per stream path when possible.

## 🛠 Tools

- `netstat -tulpn` — active protocols
- `htop` / `atop` — resource usage
- `curl -w '%{time_starttransfer}'` — stream latency


# Preliminary code structure:

<div align="center">
  <div class="mermaid">
    graph TD
      YOLO --> ML --> PYTHON
      YOLO --> PYTHON
      Cams --> PYTHON
      PYTHON -- FastAPI --> JavaScript --> HTML
      JavaScript --> cssTailwind[CSS & Tailwind]
      JavaScript --> Cams
      JavaScript --> prompts --> encode --> weightsbiases[weights & biases] --> vekdat[vector data]
      weightsbiases --> output

  </div>
</div>

## Important Steps

1. Online platform with FIGMA
2. Finish RB-track
3. Connect input data, CAWS/Azure
4. Meta SAM implementation

