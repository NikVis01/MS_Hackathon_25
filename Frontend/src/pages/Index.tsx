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
  const [apiEndpoint, setApiEndpoint] = useState<string>("");
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const { toast } = useToast();
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Set initial API endpoint based on environment
  useEffect(() => {
    // Default to localhost:8000/api/detections which is common for API endpoints
    const defaultApiUrl = `http://${window.location.hostname}:8000/api/detections`;
    setApiEndpoint(defaultApiUrl);
  }, []);

  // This handles incoming JSON notifications from the API
  const handleDetectionNotification = (data: any) => {
    console.log("Received detection data:", data);
    if (data && data.event) {
      const { event, timestamp, feedId, videoUrl } = data;
      const feedName = feeds.find(f => f.id === feedId)?.name || `Feed ${feedId}`;
      
      // Create a proper JSON string for the terminal
      const jsonData = JSON.stringify({
        event: `${event} on ${feedName}`,
        timestamp,
        videoUrl: videoUrl || feeds.find(f => f.id === feedId)?.url
      });
      
      // Add the JSON message to the terminal
      addTerminalMessage(`${jsonData}`);
      
      // Show toast for important events
      toast({
        title: "Detection Alert",
        description: `${event} detected on ${feedName} at ${timestamp}`,
      });
    }
  };

  // Function to connect to API endpoint
  const connectApiEndpoint = () => {
    if (!apiEndpoint) {
      addTerminalMessage("API endpoint URL is not specified");
      return;
    }
    
    // Clear any existing polling interval
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    
    addTerminalMessage(`Connecting to API endpoint at: ${apiEndpoint}`);
    console.log(`Attempting to connect to API endpoint at: ${apiEndpoint}`);
    
    // Test connection with initial fetch
    fetch(apiEndpoint)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log("API connection successful:", data);
        setIsConnected(true);
        addTerminalMessage("Connected to detection service API");
        toast({
          title: "API Connected",
          description: "Successfully connected to detection service API",
        });
        
        // Process any initial data
        if (Array.isArray(data)) {
          data.forEach(item => handleDetectionNotification(item));
        } else if (data) {
          handleDetectionNotification(data);
        }
        
        // Setup polling for new data
        pollingIntervalRef.current = setInterval(() => {
          fetchLatestDetections();
        }, 5000); // Poll every 5 seconds
      })
      .catch(error => {
        console.error("API connection error:", error);
        addTerminalMessage(`Error connecting to detection service API: ${error.message}`);
        setIsConnected(false);
        toast({
          title: "API Connection Error",
          description: "Failed to connect to detection service API",
          variant: "destructive",
        });
      });
  };

  // Function to fetch latest detection data
  const fetchLatestDetections = () => {
    if (!apiEndpoint || !isConnected) return;
    
    fetch(apiEndpoint)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        // Process any new detection data
        if (Array.isArray(data)) {
          data.forEach(item => handleDetectionNotification(item));
        } else if (data) {
          handleDetectionNotification(data);
        }
      })
      .catch(error => {
        console.error("Error fetching detection data:", error);
        setIsConnected(false);
        toast({
          title: "API Connection Lost",
          description: "Failed to fetch latest detection data",
          variant: "destructive",
        });
        
        // Clear polling interval on error
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      });
  };

  // Setup the detection_output endpoint listener
  useEffect(() => {
    // Create a simple endpoint path for external devices to send detection data to
    const setupDetectionEndpoint = () => {
      // In a real environment, this would be handled by a server
      // For demonstration, we'll show what the endpoint would be in the terminal
      const detectionEndpointUrl = `${window.location.origin}/detection_output`;
      addTerminalMessage(`Detection output endpoint available at: ${detectionEndpointUrl}`);
      addTerminalMessage(`Send JSON data to this endpoint to display in the terminal`);
      
      // Automatically connect to the API endpoint
      setApiEndpoint(`http://${window.location.hostname}:8000/api/detections`);
      setTimeout(() => {
        connectApiEndpoint();
      }, 1000);
    };
    
    setupDetectionEndpoint();
    
    return () => {
      // Cleanup on component unmount
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // Disconnect API endpoint
  const disconnectApiEndpoint = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setIsConnected(false);
    addTerminalMessage("Disconnected from detection service API");
  };

  // Handle API connection toggle
  const handleApiConnect = () => {
    if (isConnected) {
      disconnectApiEndpoint();
    } else {
      connectApiEndpoint();
    }
  };

  // Update API endpoint URL
  const handleUpdateApiEndpoint = (url: string) => {
    setApiEndpoint(url);
    if (isConnected) {
      disconnectApiEndpoint();
    }
  };

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

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

    // Initialize example feeds but without adding terminal messages
    const mockBackendUpdates = [
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
    ];

    mockBackendUpdates.forEach((feed) => {
      setFeeds(prev => {
        const feedExists = prev.some(f => f.id === feed.id);
        if (!feedExists) {
          return [...prev, feed];
        }
        return prev;
      });
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

  // Function to validate API endpoint URL
  const validateApiEndpoint = (url: string): boolean => {
    if (!url) return false;
    
    try {
      const parsedUrl = new URL(url);
      return parsedUrl.protocol === 'http:' || parsedUrl.protocol === 'https:';
    } catch (e) {
      // If URL parsing fails, check if it might be an IP without protocol
      const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}(:[0-9]+)?(\/[\w.\-~:/?#[\]@!$&'()*+,;=]*)?$/;
      if (ipRegex.test(url)) {
        // It looks like an IP without protocol, consider it valid
        // But we'll need to add the http:// protocol
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
    // If the message is already JSON, don't add timestamp
    if (message.startsWith('{') && message.includes('}')) {
      setTerminalOutput(prev => [...prev, message]);
    } else {
      setTerminalOutput(prev => [...prev, `[${timestamp}] ${message}`]);
    }
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

  // Extract feed urls for terminal playback functionality
  const feedsForTerminal = feeds.map(feed => ({
    id: feed.id,
    url: feed.url
  }));

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
          <Terminal 
            messages={terminalOutput} 
            feeds={feedsForTerminal}
            apiEndpoint={apiEndpoint}
            isConnected={isConnected}
            onNewDetection={handleDetectionNotification}
          />
        </Card>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
};

export default Index;
