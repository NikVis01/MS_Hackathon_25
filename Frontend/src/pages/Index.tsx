// Updated index.tsx using native WebSocket (no socket.io)
import { useState, useEffect, useRef } from "react";
import { ChevronLeft, ChevronRight, AlertTriangle } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import VideoFeed from "@/components/VideoFeed";
import Terminal from "@/components/Terminal";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable";
import { Alert, AlertDescription } from "@/components/ui/alert";

export interface FeedData {
  id: string;
  name: string;
  url: string;
  active: boolean;
  detectionMode: string;
  prompts?: Record<string, string>;
  totalFeeds?: number;
  feedIndex?: number;
}

const Index = () => {
  const [feeds, setFeeds] = useState<FeedData[]>([]);
  const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
  const [activeFeeds, setActiveFeeds] = useState<string[]>([]);
  const [currentFeedIndex, setCurrentFeedIndex] = useState(0);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const { toast } = useToast();
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:1234"); {/* ÄNDRA WEBSOCKET SERVER HÄR!!!!!!!!! */}
    socketRef.current = socket;

    socket.onopen = () => {
      setIsConnected(true);
      addTerminalMessage("WebSocket connected.");
    };

    socket.onclose = () => {
      setIsConnected(false);
      addTerminalMessage("WebSocket disconnected.");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleDetectionNotification(data);
      } catch (e) {
        console.error("Invalid JSON:", event.data);
      }
    };

    return () => {
      socket.close();
    };
  }, []);

  const handleDetectionNotification = (data: any) => {
    const { event, timestamp, feedId, videoUrl, probability, type } = data;
    const feedName = feeds.find(f => f.id === feedId)?.name || `Feed ${feedId}`;
    
    // Format message based on detection type
    let message: string;
    if (type === "audio") {
      const probStr = probability ? ` (${(probability * 100).toFixed(1)}%)` : '';
      message = JSON.stringify({
        event: `${event}${probStr}`,
        timestamp,
        feedId: feedId || "audio",
        type: "audio"
      });
    } else {
      message = JSON.stringify({
        event: `${event} on ${feedName}`,
        timestamp,
        videoUrl: videoUrl || feeds.find(f => f.id === feedId)?.url
      });
    }
    
    addTerminalMessage(message);
    toast({
      title: "Detection Alert",
      description: type === "audio" 
        ? `${event} detected${probability ? ` (${(probability * 100).toFixed(1)}% confidence)` : ''}`
        : `${event} detected on ${feedName} at ${timestamp}`,
    });
  };

  const addTerminalMessage = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    if (message.startsWith("{") && message.includes("}")) {
      setTerminalOutput(prev => [...prev, message]);
    } else {
      setTerminalOutput(prev => [...prev, `[${timestamp}] ${message}`]);
    }
  };

  useEffect(() => {
    setFeeds([
      {
        id: "1",
        name: "Front Door",
        url: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        active: true,
        detectionMode: "none"
      },
      {
        id: "2",
        name: "Back Yard",
        url: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        active: false,
        detectionMode: "none"
      },
    ]);
    setActiveFeeds(["1"]);
  }, []);

  const displayedFeed = feeds.find(feed => feed.id === activeFeeds[currentFeedIndex]);
  const feedsForTerminal = feeds.map(feed => ({ id: feed.id, url: feed.url }));

  return (
    <ResizablePanelGroup direction="horizontal" className="min-h-screen">
      <ResizablePanel defaultSize={20} minSize={15} maxSize={30}>
        <Sidebar
          feeds={feeds}
          activeFeeds={activeFeeds}
          onToggleFeed={(id) => {
            setActiveFeeds(prev => prev.includes(id) ? prev.filter(fid => fid !== id) : [...prev, id]);
            setCurrentFeedIndex(0);
          }}
          onUpdateFeedName={(id, newName) => {
            setFeeds(prev => prev.map(feed => feed.id === id ? { ...feed, name: newName } : feed));
            addTerminalMessage(`Camera feed ${id} renamed to: ${newName}`);
          }}
          onUpdateFeedUrl={(id, newUrl) => {
            setFeeds(prev => prev.map(feed => feed.id === id ? { ...feed, url: newUrl } : feed));
            addTerminalMessage(`Updated URL for feed ${id}`);
          }}
        />
      </ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel defaultSize={55} minSize={40}>
        <div className="flex-1 flex flex-col p-4 h-full">
          <div className="relative flex-1 min-h-[300px]">
            {displayedFeed ? (
              <VideoFeed feed={{ ...displayedFeed, totalFeeds: activeFeeds.length, feedIndex: currentFeedIndex }} onChangeDetectionMode={() => {}} />
            ) : (
              <Card className="flex flex-col h-full items-center justify-center text-center p-6 bg-muted/20">
                <Alert variant="destructive" className="max-w-md mb-4 bg-destructive/10">
                  <AlertTriangle className="h-5 w-5 mr-2" />
                  <AlertDescription>No active camera feeds available</AlertDescription>
                </Alert>
                <div className="mt-4 text-muted-foreground">
                  <p>Activate a camera feed from the sidebar to view the stream</p>
                </div>
              </Card>
            )}
          </div>
        </div>
      </ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel defaultSize={25} minSize={20} maxSize={40}>
        <Card className="h-full">
          <Terminal
            messages={terminalOutput}
            feeds={feedsForTerminal}
            isConnected={isConnected}
          />
        </Card>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
};

export default Index;
