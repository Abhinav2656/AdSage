import { ImageGeneratorWrapper } from "@/components/ImageGeneratorWrapper";

interface PageProps {
  params: {
    url?: string[];
  };
}

function reconstructUrl({ url }: { url?: string[] }) {
  // If no URL is provided, return an empty string instead of undefined
  if (!url || url.length === 0) {
    return '';
  }
  const decodedComponents = url.map((component) => decodeURIComponent(component));
  return decodedComponents.join("//");
}

const Page = ({ params }: PageProps) => {
  const reconstructedUrl = reconstructUrl({ url: params.url });

  return <ImageGeneratorWrapper url={reconstructedUrl} />;
};

export default Page;