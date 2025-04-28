
import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TerminalProps {
  messages: string[];
}

const Terminal = ({ messages }: TerminalProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <div className="bg-black text-white p-2 font-medium">
        Detection Output
      </div>
      <ScrollArea className="flex-1 overflow-y-auto">
        <div 
          ref={scrollRef} 
          className="p-3 terminal-text bg-black text-green-400 max-h-full overflow-y-auto"
        >
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
      </ScrollArea>
    </div>
  );
};

export default Terminal;
