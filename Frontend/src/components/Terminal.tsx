
import { useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TerminalProps {
  messages: string[];
}

const Terminal = ({ messages }: TerminalProps) => {
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // This effect will handle scrolling to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <div className="bg-black text-white p-2 font-medium">
        Detection Output
      </div>
      <div 
        className="flex-1 bg-black overflow-auto" 
        style={{ maxHeight: "calc(100vh - 200px)" }}
        ref={scrollAreaRef}
      >
        <div className="p-3 terminal-text text-green-400 min-h-[200px]">
          {messages.length > 0 ? (
            messages.map((message, index) => (
              <div key={index} className="py-1">
                {message}
              </div>
            ))
          ) : (
            <div className="text-muted-foreground">No detection data available</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Terminal;
