import { ChatMessage } from "./ImageGeneratorWrapper";
import { MessageCircle, Plus } from "lucide-react";

interface ChatSidebarProps {
  conversations: ChatMessage[];
  selectedConversation: string | null;
  onSelectConversation: (id: string | null) => void;
}

export const ChatSidebar = ({ 
  conversations, 
  selectedConversation, 
  onSelectConversation 
}: ChatSidebarProps) => {
  // Group conversations by unique prompts
  const uniqueConversations = conversations
    .filter((msg) => msg.role === 'user')
    .reduce((acc, msg) => {
      const existingConv = acc.find(conv => conv.content === msg.content);
      if (!existingConv) {
        acc.push(msg);
      }
      return acc;
    }, [] as ChatMessage[]);

  return (
    <div className="w-64 bg-zinc-950 p-4 border-r border-zinc-800">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-white font-semibold">Conversations</h2>
        <button 
          onClick={() => onSelectConversation(null)}
          className="text-white bg-zinc-800 p-2 rounded-full hover:bg-zinc-700"
        >
          <Plus size={16} />
        </button>
      </div>
      <div className="space-y-2">
        {uniqueConversations.map((conv) => (
          <button
            key={conv.id}
            onClick={() => onSelectConversation(conv.id)}
            className={`w-full text-left p-2 rounded-lg flex items-center gap-2 ${
              selectedConversation === conv.id 
                ? 'bg-zinc-700' 
                : 'hover:bg-zinc-800'
            }`}
          >
            <MessageCircle size={16} className="text-blue-500" />
            <span className="text-white text-sm truncate">
              {conv.content.length > 30 
                ? `${conv.content.slice(0, 30)}...` 
                : conv.content}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};