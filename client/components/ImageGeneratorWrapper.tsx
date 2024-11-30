"use client";

import { useState } from 'react';
import { Images } from "./Images";
import { ImageGeneratorInput } from "./ImageGeneratorInput";

export const ImageGeneratorWrapper = ({ url }: { url: string }) => {
  const [images, setImages] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateImages = async (userPrompt: string) => {
    // Reset previous state
    setImages([]);
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch('/api/generate-ad-images', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          url, 
          user_prompt: userPrompt 
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate images');
      }

      setImages(data.images);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-full bg-zinc-900 flex divide-y divide-zinc-700 flex-col justify-between gap-2">
      <div className="flex-1 text-black bg-zinc-800 justify-between flex flex-col">
        <Images images={images} url={url} error={error} />
      </div>

      <ImageGeneratorInput 
        onGenerateImages={handleGenerateImages} 
        isLoading={isLoading}
      />
    </div>
  );
};