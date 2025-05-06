import { useRef, useEffect, useState } from "react";
import { Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import VideoPlayback from "./VideoPlayback";

// Define the structure for detection messages
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
  apiEndpoint?: string;
  isConnected?: boolean;
  onNewDetection?: (data: any) => void;
}

const Terminal = ({ messages, feeds = [], apiEndpoint, isConnected = false, onNewDetection }: TerminalProps) => {
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const [activePlayback, setActivePlayback] = useState<{timestamp: string, url: string} | null>(null);
  const [parsedMessages, setParsedMessages] = useState<DetectionMessage[]>([]);
  // Store the original fetch function in a ref so it's accessible in the cleanup function
  const originalFetchRef = useRef<typeof window.fetch | null>(null);
  
  // This effect sets up the event listener for POST requests to /detection_output
  useEffect(() => {
    // Create a function to handle the custom event
    const handleDetectionData = (event: CustomEvent) => {
      console.log("Detection data received:", event.detail);
      if (onNewDetection && event.detail) {
        onNewDetection(event.detail);
      }
    };

    // Register event listener for our custom event
    window.addEventListener('detection-data-received' as any, handleDetectionData as EventListener);

    // Set up detection endpoint handler
    if (window.location.pathname === '/') {
      // Save the original fetch function in our ref
      originalFetchRef.current = window.fetch;
      
      // Override fetch to intercept requests to /detection_output
      window.fetch = function(input: RequestInfo | URL, init?: RequestInit) {
        if (input && typeof input === 'string' && input.endsWith('/detection_output')) {
          return new Promise(async (resolve) => {
            if (init?.method === 'POST' && init?.body) {
              try {
                // Parse the POST data
                const data = JSON.parse(init.body.toString());
                
                // Dispatch a custom event with the detection data
                window.dispatchEvent(new CustomEvent('detection-data-received', {
                  detail: data
                }));
                
                // Respond with a success status
                resolve(new Response(JSON.stringify({ success: true }), {
                  status: 200,
                  headers: { 'Content-Type': 'application/json' }
                }));
              } catch (error) {
                console.error("Error processing detection data:", error);
                resolve(new Response(JSON.stringify({ error: "Invalid JSON data" }), {
                  status: 400,
                  headers: { 'Content-Type': 'application/json' }
                }));
              }
            } else {
              // If not a POST request, return a method not allowed error
              resolve(new Response(JSON.stringify({ error: "Method not allowed" }), {
                status: 405,
                headers: { 'Content-Type': 'application/json' }
              }));
            }
          });
        }
        
        // For all other requests, use the original fetch
        return originalFetchRef.current!.apply(window, [input, init as any]);
      };
    }

    return () => {
      // Cleanup: restore original fetch and remove event listener
      if ('fetch' in window && originalFetchRef.current) {
        window.fetch = originalFetchRef.current;
      }
      window.removeEventListener('detection-data-received' as any, handleDetectionData as EventListener);
    };
  }, [onNewDetection]);

  // This effect will handle scrolling to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
    
    // Try to parse detection messages from raw message strings
    const parsed = messages.map((msg, idx) => {
      const idBase = `msg-${idx}`;
      
      // Check if it's a JSON message
      try {
        if (msg.includes('{') && msg.includes('}')) {
          // Extract the JSON part from the message
          const jsonMatch = msg.match(/\{.*\}/s);
          
          if (jsonMatch) {
            const jsonData = JSON.parse(jsonMatch[0]);
            
            // Check if JSON contains necessary video information
            if (jsonData.event && jsonData.timestamp) {
              const displayText = `[${jsonData.timestamp}] ${jsonData.event}`;
              
              // Check if this JSON has a valid video URL
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
      
      // Default case - just a regular message
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
          {isConnected && apiEndpoint && (
            <span className="text-green-400 flex items-center">
              <span className="h-2 w-2 rounded-full bg-green-400 mr-1"></span>
              API Connected
            </span>
          )}
          {!isConnected && (
            <span className="text-red-400 flex items-center">
              <span className="h-2 w-2 rounded-full bg-red-400 mr-1"></span>
              API Disconnected
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
        <p>Send detection data to: {window.location.origin}/detection_output</p>
        <p>Format: {"{ event: 'Detection event', timestamp: 'HH:MM:SS', feedId: '1', videoUrl: 'url' }"}</p>
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
