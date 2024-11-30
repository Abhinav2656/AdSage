"use client";

import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

const HomePage = () => {
  const router = useRouter();

  const handleNavigate = () => {
    router.push("/generate");
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-900 text-white px-4">
      <div className="max-w-2xl text-center space-y-6">
        <h1 className="text-4xl font-bold text-blue-500">Welcome to ImgSage</h1>
        <p className="text-lg text-zinc-300">
          ImgSage uses <strong>AWS Bedrock Models</strong> to generate stunning images based on your prompts. 
          Our app also allows you to provide a URL as a parameter (e.g., 
          <code className="bg-zinc-800 px-2 py-1 rounded-md text-blue-400">http://localhost:3000/generate/https://example.com/</code>), 
          where we extract webpage content using <strong>Beautiful Soup</strong> and pass it along with your prompt to the model for image generation.
        </p>
        <p className="text-md text-zinc-400">
          Start exploring the endless possibilities of AI-generated imagery today!
        </p>
        <Button
          onClick={handleNavigate}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg text-lg"
        >
          Get Started
        </Button>
      </div>
    </div>
  );
};

export default HomePage;
