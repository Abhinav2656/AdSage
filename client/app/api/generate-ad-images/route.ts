import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { url, user_prompt } = await request.json();

    // Allow empty strings, but ensure url is defined
    if (url === undefined) {
      return NextResponse.json(
        { error: 'URL is required' }, 
        { status: 400 }
      );
    }

    // Forward the request to your backend service
    const backendResponse = await fetch('http://localhost:5001/generate-ad-images', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        url: url || '',  // This can now be an empty string
        user_prompt 
      }),
    });

    const data = await backendResponse.json();

    if (!backendResponse.ok) {
      throw new Error(data.error || 'Failed to generate images');
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Image generation error:', error);
    return NextResponse.json(
      { 
        error: error instanceof Error ? error.message : 'Unexpected error',
        images: [] 
      }, 
      { status: 500 }
    );
  }
}