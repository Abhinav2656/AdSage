"use client";

import { useState } from "react";
import { ChatSidebar } from "./ChatSidebar";
import { ChatMessages } from "./ChatMessage";
import { ImageGeneratorInput } from "./ImageGeneratorInput";

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  url?: string;
  content: string;
  images?: string[];
  error?: string;
}

export const ImageGeneratorWrapper = ({ url }: { url?: string }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);

  const handleGenerateImages = async (userPrompt: string) => {
    const newUserMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: userPrompt,
      url: url || undefined,
    };

    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);

    try {
      const response = await fetch("/api/generate-ad-images", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          url: url || '', 
          user_prompt: userPrompt 
        }),
      });

      const data = await response.json();

      const newAssistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: userPrompt,
        url: url || undefined,
        images: data.images || [],
        error: !response.ok ? (data.error || "Failed to generate images") : undefined,
      };

      setMessages(prev => [...prev, newAssistantMessage]);
    } catch (err) {
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: userPrompt,
        url: url || undefined,
        error: err instanceof Error ? err.message : "An unexpected error occurred",
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-zinc-900">
      <ChatSidebar 
        conversations={messages} 
        selectedConversation={selectedConversation}
        onSelectConversation={setSelectedConversation}
      />
      <div className="flex flex-col flex-1">
        <ChatMessages 
          messages={messages} 
          url={url}
        />
        <ImageGeneratorInput 
          onGenerateImages={handleGenerateImages} 
          isLoading={isLoading} 
          placeholderText={url && url !== '' 
            ? "Add additional details..." 
            : "Describe the image you want to generate"}
        />
      </div>
    </div>
  );
};