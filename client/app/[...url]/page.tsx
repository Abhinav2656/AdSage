"use client";

import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import Image from 'next/image'

interface PageProps {
  params: {
    url: string[];
  };
}

function reconstructUrl({ url }: { url: string[] }) {
  const decodedComponents = url.map((component) => decodeURIComponent(component));
  return decodedComponents.join("//");
}

const ImageGeneratorPage = ({ params }: PageProps) => {
  const reconstructedUrl = reconstructUrl({ url: params.url });
  const [userPrompt, setUserPrompt] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateImages = async () => {
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
          url: reconstructedUrl, 
          user_prompt: userPrompt 
        }),
      });

      const data = await response.json();
      console.log(data);

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
    <div className="container mx-auto p-6">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>AI Image Generator</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="text-sm text-muted-foreground mb-4">
              URL: {reconstructedUrl}
            </div>
            
            <Input 
              type="text"
              placeholder="Optional: Additional Prompt (e.g., style, theme)"
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              className="w-full"
            />
            
            <Button 
              onClick={handleGenerateImages} 
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating Images...
                </>
              ) : (
                'Generate Images'
              )}
            </Button>

            {error && (
              <div className="text-red-500 text-sm mt-2">
                {error}
              </div>
            )}

            {images.length > 0 && (
              <div className="grid grid-cols-3 gap-4 mt-4">
                {images.map((image, index) => (
                <Image
                    key={index}
                    src={`data:image/png;base64,${image}`}
                    blurDataURL={`data:image/png;base64,${image}`}
                    alt={`Generated image ${index + 1}`}
                    width={512} // Adjust size as needed
                    height={512}
                    className="rounded-lg shadow-md"
                />
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ImageGeneratorPage;