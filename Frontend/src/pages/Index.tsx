
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

export interface DetectionMode {
  id: string;
  name: string;
  description: string;
}

const Index = () => {
  const [feeds, setFeeds] = useState<FeedData[]>([]);
  const [detectionModes, setDetectionModes] = useState<DetectionMode[]>([]);
  const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
  const [activeFeeds, setActiveFeeds] = useState<string[]>([]);
  const [currentFeedIndex, setCurrentFeedIndex] = useState(0);
  const { toast } = useToast();

  useEffect(() => {
    const mockDetectionModes: DetectionMode[] = [
      { id: "none", name: "None", description: "No detection" },
      { id: "motion", name: "Motion Detection", description: "Detects movement in the frame" },
      { id: "person", name: "Person Detection", description: "Identifies people in the frame" },
      { id: "vehicle", name: "Vehicle Detection", description: "Identifies vehicles in the frame" },
      { id: "object", name: "Object Detection", description: "Identifies various objects in the frame" },
    ];
    
    setDetectionModes(mockDetectionModes);
    setActiveFeeds(["1"]);

    addTerminalMessage("System initialized. Ready for detection.");

    const mockBackendUpdates = [
      { 
        id: "1", 
        name: "Front Door", 
        url: "", // Empty URL initially
        active: true, 
        detectionMode: "none" 
      },
      { 
        id: "2", 
        name: "Back Yard", 
        url: "", // Empty URL initially
        active: false, 
        detectionMode: "none" 
      },
    ];

    mockBackendUpdates.forEach((feed, index) => {
      setTimeout(() => {
        handleNewFeed(feed);
      }, index * 1000);
    });
  }, []);

  const validateUrl = (url: string): boolean => {
    // Basic URL validation, but more permissive for internal network addresses
    if (!url) return false;
    
    try {
      // Try to create a URL object to validate basic URL structure
      new URL(url);
      return true;
    } catch (e) {
      // If URL parsing fails, check if it might be an IP without protocol
      const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}(:[0-9]+)?(\/[\w.\-~:/?#[\]@!$&'()*+,;=]*)?$/;
      if (ipRegex.test(url)) {
        // It looks like an IP without protocol, consider it valid
        return true;
      }
      return false;
    }
  };

  const handleNewFeed = (newFeed: FeedData) => {
    // Make sure URL has protocol if it's not empty
    let processedUrl = newFeed.url;
    
    if (processedUrl) {
      // Add http:// if it's missing and looks like an IP address
      if (!processedUrl.startsWith('http://') && !processedUrl.startsWith('https://') && 
          /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}/.test(processedUrl)) {
        processedUrl = `http://${processedUrl}`;
        newFeed.url = processedUrl;
      }
      
      // Basic URL validation before adding
      if (!validateUrl(processedUrl)) {
        addTerminalMessage(`Warning: Feed URL format for ${newFeed.name} may not be supported`);
      }
    }
    
    setFeeds(prevFeeds => {
      const feedExists = prevFeeds.some(feed => feed.id === newFeed.id);
      if (!feedExists) {
        addTerminalMessage(`New camera feed connected: ${newFeed.name}`);
        
        // Don't call toast during render, defer it
        setTimeout(() => {
          toast({
            title: "New Camera Connected",
            description: `${newFeed.name} has been added to available feeds.`,
          });
        }, 0);
        
        return [...prevFeeds, newFeed];
      }
      return prevFeeds;
    });
  };

  const updateFeedName = (id: string, newName: string) => {
    setFeeds(prevFeeds =>
      prevFeeds.map(feed =>
        feed.id === id
          ? { ...feed, name: newName }
          : feed
      )
    );
    addTerminalMessage(`Camera feed ${id} renamed to: ${newName}`);
  };

  const updateFeedUrl = (id: string, newUrl: string) => {
    // Make sure URL has protocol
    let processedUrl = newUrl;
    
    // Add http:// if it's missing and looks like an IP address
    if (!processedUrl.startsWith('http://') && !processedUrl.startsWith('https://') && 
        /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}/.test(processedUrl)) {
      processedUrl = `http://${processedUrl}`;
    }
    
    if (!validateUrl(processedUrl)) {
      toast({
        title: "Invalid URL format",
        description: "Please enter a valid stream URL or IP address",
        variant: "destructive",
      });
      return;
    }
    
    setFeeds(prevFeeds =>
      prevFeeds.map(feed =>
        feed.id === id
          ? { ...feed, url: processedUrl }
          : feed
      )
    );
    
    const feedName = feeds.find(feed => feed.id === id)?.name || id;
    addTerminalMessage(`Updated URL for ${feedName}: ${processedUrl}`);
    
    toast({
      title: "Feed URL Updated",
      description: `URL for ${feedName} has been updated.`,
    });
  };

  const addTerminalMessage = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setTerminalOutput(prev => [...prev, `[${timestamp}] ${message}`]);
  };

  const toggleFeed = (id: string) => {
    if (activeFeeds.includes(id)) {
      setActiveFeeds(prev => prev.filter(feedId => feedId !== id));
    } else {
      if (activeFeeds.length >= 5) {
        toast({
          title: "Maximum feeds reached",
          description: "You can have a maximum of 5 active feeds",
          variant: "destructive",
        });
        return;
      }
      setActiveFeeds(prev => [...prev, id]);
    }
    
    setCurrentFeedIndex(0);
  };

  const changeDetectionMode = async (feedId: string, modeId: string, prompt?: string) => {
    try {
      setFeeds(prev => 
        prev.map(feed => 
          feed.id === feedId 
            ? { 
                ...feed, 
                detectionMode: modeId,
                prompts: {
                  ...feed.prompts,
                  [modeId]: prompt !== undefined ? prompt : feed.prompts?.[modeId] || ''
                }
              } 
            : feed
        )
      );

      const feed = feeds.find(feed => feed.id === feedId);
      
      if (feed) {
        if (modeId !== feed.detectionMode) {
          addTerminalMessage(`Set detection mode for ${feed.name} to ${modeId}`);
        }
        
        if (prompt !== undefined) {
          addTerminalMessage(`Updated ${modeId} prompt for ${feed.name}: ${prompt}`);
          
          if (modeId !== 'none') {
            setTimeout(() => {
              const detections = ["person (87%)", "backpack (63%)"];
              addTerminalMessage(`Detection results for ${feed.name}: ${detections.join(", ")}`);
            }, 2000);
          }
        }
      }
    } catch (error) {
      console.error("Error changing detection mode:", error);
      toast({
        title: "Error",
        description: "Failed to change detection mode",
        variant: "destructive",
      });
    }
  };

  const handleNextFeed = () => {
    if (activeFeeds.length > 1) {
      setCurrentFeedIndex((prev) => (prev + 1) % activeFeeds.length);
    }
  };

  const handlePrevFeed = () => {
    if (activeFeeds.length > 1) {
      setCurrentFeedIndex((prev) => (prev - 1 + activeFeeds.length) % activeFeeds.length);
    }
  };

  const displayedFeed = feeds.find(feed => feed.id === activeFeeds[currentFeedIndex]);
  const enhancedDisplayedFeed = displayedFeed 
    ? {
        ...displayedFeed,
        totalFeeds: activeFeeds.length,
        feedIndex: currentFeedIndex
      }
    : null;

  return (
    <ResizablePanelGroup direction="horizontal" className="min-h-screen">
      <ResizablePanel defaultSize={20} minSize={15} maxSize={30}>
        <Sidebar 
          feeds={feeds}
          activeFeeds={activeFeeds}
          onToggleFeed={toggleFeed}
          onUpdateFeedName={updateFeedName}
          onUpdateFeedUrl={updateFeedUrl}
        />
      </ResizablePanel>

      <ResizableHandle withHandle />

      <ResizablePanel defaultSize={55} minSize={40}>
        <div className="flex-1 flex flex-col p-4 h-full">
          <div className="relative flex-1 min-h-[300px]">
            {activeFeeds.length > 1 && (
              <>
                <Button 
                  variant="secondary" 
                  size="icon" 
                  className="absolute left-2 top-1/2 -translate-y-1/2 z-10 bg-black/40 hover:bg-black/60"
                  onClick={handlePrevFeed}
                >
                  <ChevronLeft />
                </Button>
                <Button 
                  variant="secondary" 
                  size="icon" 
                  className="absolute right-2 top-1/2 -translate-y-1/2 z-10 bg-black/40 hover:bg-black/60"
                  onClick={handleNextFeed}
                >
                  <ChevronRight />
                </Button>
              </>
            )}

            {enhancedDisplayedFeed ? (
              <VideoFeed 
                feed={enhancedDisplayedFeed}
                onChangeDetectionMode={changeDetectionMode}
              />
            ) : (
              <Card className="flex flex-col h-full items-center justify-center text-center p-6 bg-muted/20">
                <Alert variant="destructive" className="max-w-md mb-4 bg-destructive/10">
                  <AlertTriangle className="h-5 w-5 mr-2" />
                  <AlertDescription>
                    No active camera feeds available
                  </AlertDescription>
                </Alert>
                <div className="mt-4 text-muted-foreground">
                  <p>Activate a camera feed from the sidebar to view the stream</p>
                  <div className="w-full h-48 mt-6 bg-muted rounded-md flex items-center justify-center">
                    <img 
                      src="https://images.unsplash.com/photo-1518770660439-4636190af475" 
                      alt="No camera feed" 
                      className="max-h-full max-w-full object-contain opacity-20"
                    />
                  </div>
                </div>
              </Card>
            )}
          </div>
        </div>
      </ResizablePanel>

      <ResizableHandle withHandle />

      <ResizablePanel defaultSize={25} minSize={20} maxSize={40}>
        <Card className="h-full">
          <Terminal messages={terminalOutput} />
        </Card>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
};

export default Index;
