import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { cn } from "@/lib/utils";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "AI Image Generator",
  description:
    "Generate stunning images using AWS Bedrock models and website content analysis.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={cn(
          "min-h-screen bg-zinc-900 text-white font-sans antialiased flex flex-col",
          inter.className
        )}
      >
        {/* Header */}
        <header className="bg-zinc-800 py-4 shadow-md">
          <div className="container mx-auto px-4 flex justify-between items-center">
            <h1 className="text-xl font-bold text-blue-500">
              AI Image Generator
            </h1>
            <nav>
              <a
                href="/generate"
                className="text-sm text-white hover:text-blue-400"
              >
                Generate Images
              </a>
            </nav>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 container mx-auto px-4">{children}</main>

        {/* Footer */}
        <footer className="bg-zinc-800 py-4 text-center text-zinc-400 text-sm">
          <p>
            © {new Date().getFullYear()} AI Image Generator. Built with AWS
            Bedrock.
          </p>
        </footer>
      </body>
    </html>
  );
}
