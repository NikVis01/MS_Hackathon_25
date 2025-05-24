### 2025 SSE Business lab x Microsoft x KTH AI Society Hackathon

## Core idea & Functionality:
Cameras will stream live feeds to a website that will send warning signals to the user if the cameras detect the elements of a prompt fed in by the user.

![image](https://github.com/user-attachments/assets/a0eef878-031f-4fc7-a067-e872b65041c6)

# Setting up stream from ubuntu (might be diff for debian):
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
