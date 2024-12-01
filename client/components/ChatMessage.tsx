import Image from "next/image";
import { ChatMessage } from "./ImageGeneratorWrapper";
import { ImageIcon } from "lucide-react";

interface ChatMessagesProps {
  messages: ChatMessage[];
  url?: string;
}

export const ChatMessages = ({ messages, url }: ChatMessagesProps) => {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-zinc-500">
          <ImageIcon className="size-12 text-blue-500" />
          <h3 className="font-semibold text-xl text-white mt-2">Image Generator</h3>
          <p className="text-sm">
            Enter a prompt to generate AI images
          </p>
        </div>
      ) : (
        messages.map((message) => (
          <div 
            key={message.id} 
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div 
              className={`max-w-2xl p-4 rounded-lg ${
                message.role === 'user' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-zinc-800 text-white'
              }`}
            >
              {message.url && (
                <p className="text-xs mb-2 opacity-70">
                  Website: {message.url}
                </p>
              )}
              <p className="mb-2">{message.content}</p>
              
              {message.error && (
                <div className="text-red-300 text-sm">{message.error}</div>
              )}
              
              {message.images && message.images.length > 0 && (
                <div className="grid grid-cols-2 gap-4 mt-4">
                  {message.images.map((image, index) => (
                    <Image
                      key={index}
                      src={`data:image/png;base64,${image}`}
                      alt={`Generated image ${index + 1}`}
                      width={384}
                      height={384}
                      className="rounded-lg shadow-md"
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
};