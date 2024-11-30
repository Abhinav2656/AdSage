"use client";

import { useState } from "react";
import { Button, Input } from "@nextui-org/react";
import { Send, Loader2 } from "lucide-react";

interface ImageGeneratorInputProps {
  onGenerateImages: (prompt: string) => Promise<void>;
  isLoading: boolean;
  placeholderText?: string;
}

export const ImageGeneratorInput = ({
  onGenerateImages,
  isLoading,
  placeholderText = "Type your prompt here...",
}: ImageGeneratorInputProps) => {
  const [userPrompt, setUserPrompt] = useState("");

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (isLoading || !userPrompt.trim()) return;
    
    onGenerateImages(userPrompt);
    setUserPrompt("");
  };

  return (
    <div className="fixed bottom-0 left-0 w-full bg-zinc-800 p-4 flex items-center gap-2">
      <form onSubmit={handleSubmit} className="flex flex-1">
        <Input
          type="text"
          value={userPrompt}
          onChange={(e) => setUserPrompt(e.target.value)}
          placeholder={placeholderText}
          className="flex-1 bg-zinc-900 text-white px-4 py-2 rounded-lg"
        />
        <Button
          size="sm"
          type="submit"
          isDisabled={isLoading || !userPrompt.trim()}
          className="ml-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          {isLoading ? <Loader2 className="animate-spin" /> : <Send />}
        </Button>
      </form>
    </div>
  );
};