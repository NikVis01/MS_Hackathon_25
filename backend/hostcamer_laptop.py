import cv2
from flask import Flask, Response
import threading
import atexit

app = Flask(__name__)
camera = cv2.VideoCapture(0)

def release_camera():
    if camera.isOpened():
        camera.release()
atexit.register(release_camera)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    # Run only locally; Nginx handles HTTPS externally
    app.run(host="127.0.0.1", port=5173, threaded=True)
