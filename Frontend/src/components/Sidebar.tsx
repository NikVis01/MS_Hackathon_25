
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { FeedData } from "@/pages/Index";
import { Button } from "@/components/ui/button";
import { Pencil, Link, Send } from "lucide-react";

interface SidebarProps {
  feeds: FeedData[];
  activeFeeds: string[];
  onToggleFeed: (id: string) => void;
  onUpdateFeedName: (id: string, newName: string) => void;
  onUpdateFeedUrl: (id: string, newUrl: string) => void;
}

const Sidebar = ({ feeds, activeFeeds, onToggleFeed, onUpdateFeedName, onUpdateFeedUrl }: SidebarProps) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editingUrlId, setEditingUrlId] = useState<string | null>(null);
  const [editUrl, setEditUrl] = useState("");

  const handleEditClick = (feed: FeedData) => {
    setEditingId(feed.id);
    setEditName(feed.name);
  };

  const handleEditUrlClick = (feed: FeedData) => {
    setEditingUrlId(feed.id);
    setEditUrl(feed.url);
  };

  const handleSaveName = (id: string) => {
    if (editName.trim()) {
      onUpdateFeedName(id, editName.trim());
    }
    setEditingId(null);
  };

  const handleSaveUrl = (id: string) => {
    if (editUrl.trim()) {
      onUpdateFeedUrl(id, editUrl.trim());
    }
    setEditingUrlId(null);
  };

  return (
    <div className="w-full md:w-64 bg-secondary p-4">
      <h2 className="text-xl font-bold mb-4">Camera Feeds</h2>
      
      <div className="space-y-3">
        {feeds.map((feed) => (
          <Card key={feed.id} className="p-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                {editingId === feed.id ? (
                  <div className="flex-1 flex gap-2">
                    <Input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="flex-1"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleSaveName(feed.id);
                        }
                      }}
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleSaveName(feed.id)}
                    >
                      Save
                    </Button>
                  </div>
                ) : (
                  <>
                    <Label htmlFor={`feed-${feed.id}`} className="cursor-pointer flex-1">
                      {feed.name}
                    </Label>
                    <button
                      onClick={() => handleEditClick(feed)}
                      className="p-1 hover:bg-secondary-foreground/10 rounded"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                  </>
                )}
                <Switch
                  id={`feed-${feed.id}`}
                  checked={activeFeeds.includes(feed.id)}
                  onCheckedChange={() => onToggleFeed(feed.id)}
                />
              </div>
              
              <div className="flex items-center gap-2">
                {editingUrlId === feed.id ? (
                  <div className="flex-1 flex gap-2">
                    <Input
                      value={editUrl}
                      onChange={(e) => setEditUrl(e.target.value)}
                      className="flex-1"
                      placeholder="Enter URL"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleSaveUrl(feed.id);
                        }
                      }}
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleSaveUrl(feed.id)}
                    >
                      <Send size={16} />
                    </Button>
                  </div>
                ) : (
                  <>
                    <div className="text-xs text-muted-foreground truncate flex-1">
                      {feed.url || "No URL set"}
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleEditUrlClick(feed)}
                      className="p-1 h-auto"
                    >
                      <Link className="h-4 w-4" />
                    </Button>
                  </>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
      
      <div className="mt-6 text-sm text-muted-foreground">
        <p>Active feeds: {activeFeeds.length}/5</p>
      </div>
    </div>
  );
};

export default Sidebar;
