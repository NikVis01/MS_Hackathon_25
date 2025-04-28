import React from "react";

const CameraFeed = () => (
  <div className="w-full flex justify-center">
    <img
      src="http://localhost:8000/video_feed"
      alt="Camera Feed"
      className="rounded shadow max-w-full"
      style={{ maxHeight: 400 }}
    />
  </div>
);

export default CameraFeed; 