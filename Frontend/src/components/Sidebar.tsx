
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { FeedData } from "@/pages/Index";
import { Button } from "@/components/ui/button";
import { Pencil } from "lucide-react";

interface SidebarProps {
  feeds: FeedData[];
  activeFeeds: string[];
  onToggleFeed: (id: string) => void;
  onUpdateFeedName: (id: string, newName: string) => void;
}

const Sidebar = ({ feeds, activeFeeds, onToggleFeed, onUpdateFeedName }: SidebarProps) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");

  const handleEditClick = (feed: FeedData) => {
    setEditingId(feed.id);
    setEditName(feed.name);
  };

  const handleSaveName = (id: string) => {
    if (editName.trim()) {
      onUpdateFeedName(id, editName.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="w-full md:w-64 bg-secondary p-4">
      <h2 className="text-xl font-bold mb-4">Camera Feeds</h2>
      
      <div className="space-y-3">
        {feeds.map((feed) => (
          <Card key={feed.id} className="p-3">
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
