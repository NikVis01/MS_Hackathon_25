// Updated Terminal.tsx for WebSocket-based data input from parent component
import { useRef, useEffect, useState } from "react";
import { Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import VideoPlayback from "./VideoPlayback";

interface DetectionMessage {
  id: string;
  text: string;
  timestamp?: string;
  videoUrl?: string;
  hasVideo?: boolean;
}

interface TerminalProps {
  messages: string[];
  feeds: Array<{ id: string; url: string }>;
  isConnected?: boolean;
}

const Terminal = ({ messages, feeds = [], isConnected = false }: TerminalProps) => {
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const [activePlayback, setActivePlayback] = useState<{ timestamp: string, url: string } | null>(null);
  const [parsedMessages, setParsedMessages] = useState<DetectionMessage[]>([]);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }

    const parsed = messages.map((msg, idx) => {
      const idBase = `msg-${idx}`;
      try {
        if (msg.includes("{") && msg.includes("}")) {
          const jsonMatch = msg.match(/\{.*\}/s);
          if (jsonMatch) {
            const jsonData = JSON.parse(jsonMatch[0]);
            if (jsonData.event && jsonData.timestamp) {
              const displayText = `[${jsonData.timestamp}] ${jsonData.event}`;
              const hasVideo = !!jsonData.videoUrl;
              return {
                id: `${idBase}-json-detection`,
                text: displayText,
                timestamp: jsonData.timestamp,
                videoUrl: jsonData.videoUrl,
                hasVideo
              };
            }
          }
        }
      } catch (e) {
        console.error("Failed to parse message:", e);
      }

      return {
        id: idBase,
        text: msg
      };
    });

    setParsedMessages(parsed);
  }, [messages, feeds]);

  const handlePlayVideo = (timestamp: string, url: string) => {
    setActivePlayback({ timestamp, url });
  };

  const closePlayback = () => {
    setActivePlayback(null);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="bg-black text-white p-2 font-medium flex justify-between items-center">
        <div>Detection Output</div>
        <div className="text-xs">
          {isConnected ? (
            <span className="text-green-400 flex items-center">
              <span className="h-2 w-2 rounded-full bg-green-400 mr-1"></span>
              WebSocket Connected
            </span>
          ) : (
            <span className="text-red-400 flex items-center">
              <span className="h-2 w-2 rounded-full bg-red-400 mr-1"></span>
              Disconnected
            </span>
          )}
        </div>
      </div>
      <div
        className="flex-1 bg-black overflow-auto"
        style={{ maxHeight: "calc(100vh - 200px)" }}
        ref={scrollAreaRef}
      >
        <div className="p-3 terminal-text text-green-400 min-h-[200px]">
          {parsedMessages.length > 0 ? (
            parsedMessages.map((message) => (
              <div key={message.id} className="py-1 flex items-center justify-between">
                <div>{message.text}</div>
                {message.hasVideo && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-6 px-2 bg-transparent text-green-400 border-green-400 hover:bg-green-400/10"
                    onClick={() => handlePlayVideo(message.timestamp!, message.videoUrl!)}
                  >
                    <Play size={14} className="mr-1" />
                    <span className="text-xs">Playback</span>
                  </Button>
                )}
              </div>
            ))
          ) : (
            <div className="text-muted-foreground">No detection data available</div>
          )}
        </div>
      </div>
      <div className="bg-black text-xs text-muted-foreground p-2 border-t border-gray-800">
        <p>Send detection data via WebSocket to: ws://localhost:3000</p>
        <p>Format: {"{ event: '...', timestamp: 'HH:MM:SS', videoUrl: '...' }"}</p>
      </div>
      {activePlayback && (
        <VideoPlayback
          url={activePlayback.url}
          timestamp={activePlayback.timestamp}
          onClose={closePlayback}
        />
      )}
    </div>
  );
};

export default Terminal;
