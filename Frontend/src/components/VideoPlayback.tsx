
import { useState, useEffect, useRef } from "react";
import { X } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { calculateTimeOffset, formatVideoUrlWithTimestamp } from "@/utils/timeUtils";

interface VideoPlaybackProps {
  url: string;
  timestamp: string;
  onClose: () => void;
}

const VideoPlayback = ({ url, timestamp, onClose }: VideoPlaybackProps) => {
  const [loading, setLoading] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);
  
  // Calculate the start and end times for the clip
  const startTime = calculateTimeOffset(timestamp, -30); // 30 seconds before
  const endTime = calculateTimeOffset(timestamp, 10);   // 10 seconds after
  
  // Format the video URL with timestamp parameters
  const videoUrlWithTimestamp = formatVideoUrlWithTimestamp(url, startTime, timestamp);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1500);
    
    return () => clearTimeout(timer);
  }, []);
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="relative w-full max-w-3xl rounded-lg overflow-hidden">
        <div className="bg-card p-3 flex justify-between items-center border-b">
          <h3 className="font-medium">Event Playback: {timestamp}</h3>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X size={18} />
          </Button>
        </div>
        
        <div className="relative aspect-video bg-black">
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="h-8 w-8 rounded-full border-4 border-primary border-t-transparent animate-spin"></div>
            </div>
          ) : null}
          
          <video 
            ref={videoRef}
            className="w-full h-full object-contain"
            controls
            autoPlay
            onCanPlay={() => setLoading(false)}
          >
            <source src={videoUrlWithTimestamp} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>
        
        <div className="bg-card p-3 text-sm text-muted-foreground">
          <p>Playing clip from {startTime} to {endTime}</p>
          <p className="text-xs mt-1">Event detected at {timestamp}</p>
        </div>
      </Card>
    </div>
  );
};

export default VideoPlayback;
