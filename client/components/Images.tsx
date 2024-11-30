import Image from "next/image";
import { ImageIcon } from "lucide-react";

interface ImagesProps {
  images: string[];
  url?: string;
  error: string | null;
}

export const Images = ({ images, url, error }: ImagesProps) => {
  return (
    <div className="flex max-h-[calc(100vh-3.5rem-7rem)] flex-1 flex-col overflow-y-auto">
      {images.length ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6 p-6">
          {images.map((image, index) => (
            <Image
              key={index}
              src={`data:image/png;base64,${image}`}
              blurDataURL={`data:image/png;base64,${image}`}
              alt={`Generated image ${index + 1}`}
              width={768} // Increased width
              height={768} // Increased height
              className="rounded-lg shadow-md"
            />
          ))}
        </div>
      ) : error ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-2 text-red-500">
          <p className="text-sm">{error}</p>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center gap-2">
          <ImageIcon className="size-12 text-blue-500" />
          <h3 className="font-semibold text-xl text-white">Generate Images</h3>
          <p className="text-zinc-500 text-sm">URL: {url}</p>
          <p className="text-zinc-500 text-sm">
            Enter a prompt to generate AI images.
          </p>
        </div>
      )}
    </div>
  );
};
