"use client";

import { useState } from "react";
import { Images } from "./Images";
import { ImageGeneratorInput } from "./ImageGeneratorInput";

export const ImageGeneratorWrapper = ({ url }: { url?: string }) => {
  const [images, setImages] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateImages = async (userPrompt: string) => {
    setImages([]);
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch("/api/generate-ad-images", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          url: url || '', // Send empty string if no URL is provided
          user_prompt: userPrompt 
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to generate images");
      }

      setImages(data.images);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-zinc-900">
      {url && url !== '' && (
        <div className="text-white p-4 text-sm">
          Generating images based on website: {url}
        </div>
      )}
      <Images images={images} url={url} error={error} />
      <ImageGeneratorInput 
        onGenerateImages={handleGenerateImages} 
        isLoading={isLoading} 
        placeholderText={url && url !== '' 
          ? "Add additional details..." 
          : "Describe the image you want to generate"}
      />
    </div>
  );
};