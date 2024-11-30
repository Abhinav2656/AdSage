import os
import json
import requests
import base64
import logging
import faiss
import numpy as np
import random

from flask import Flask, request, jsonify
from flask_cors import CORS

# Web Scraping
from bs4 import BeautifulSoup

# AWS and Environment Management
import boto3
from dotenv import load_dotenv
from unidecode import unidecode

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class BedrockProcessor:
    def __init__(self, region_name: str = "us-west-2"):
        """
        Enhanced Bedrock Processor with FAISS Vector Store
        """
        # AWS Bedrock Clients
        self.bedrock_runtime = boto3.client(
            "bedrock-runtime", 
            region_name=region_name,
            config=boto3.session.Config(
                connect_timeout=10, 
                read_timeout=20,
                retries={'max_attempts': 5}
            )
        )
        
        # Model IDs with latest versions
        self.image_model_id = "amazon.titan-image-generator-v1"
        self.embedding_model_id = "amazon.titan-embed-text-v2:0"
        
        # FAISS Vector Store Initialization
        self.embedding_dimension = 1536  # Adjust based on Titan embedding dimension
        try:
            self.vector_index = faiss.IndexFlatL2(self.embedding_dimension)
            self.vector_metadata = []
        except Exception as e:
            logger.error(f"FAISS initialization error: {e}")
            self.vector_index = None
        
        # Enhanced Configuration
        self.max_prompt_length = 2048
        self.max_context_length = 1024

    def _clean_text(self, text: str) -> str:
        """
        Advanced text cleaning with Unicode normalization
        """
        cleaned_text = unidecode(str(text or '')).strip()
        return ' '.join(cleaned_text.split())  # Normalize whitespace

    def generate_embedding(self, text: str, max_length: int = None):
        """
        Robust embedding generation with advanced preprocessing
        """
        try:
            # Truncate and clean text
            max_length = max_length or self.max_prompt_length
            text = self._clean_text(text)[:max_length]
            
            request_body = json.dumps({
                "inputText": text
            })
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.embedding_model_id,
                contentType="application/json",
                body=request_body
            )
            
            model_response = json.loads(response["body"].read())
            embedding = model_response.get("embedding", [])
            
            return np.array(embedding, dtype='float32')
        
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return None

    def store_embedding(self, url: str, text: str, embedding: np.ndarray):
        """
        Store embedding in FAISS with robust error handling
        """
        if self.vector_index is None:
            logger.warning("Vector index not initialized")
            return None

        try:
            # Validate inputs
            if embedding is None:
                logger.warning("Cannot store None embedding")
                return None

            # Validate embedding dimensions
            if len(embedding) != self.embedding_dimension:
                logger.error(f"Embedding dimension mismatch. Expected {self.embedding_dimension}, got {len(embedding)}")
                return None

            # Normalize embedding
            embedding_normalized = embedding / np.linalg.norm(embedding)
            
            # Add to FAISS index
            self.vector_index.add(embedding_normalized.reshape(1, -1))
            
            # Store metadata
            self.vector_metadata.append({
                "url": url,
                "text": text[:1000],  # Truncate metadata text
                "embedding_id": len(self.vector_metadata)
            })
            
            return len(self.vector_metadata) - 1
        
        except Exception as e:
            logger.error(f"Vector storage error: {str(e)}")
            logger.error(f"Embedding details: {embedding}")
            return None

    def construct_image_prompt(self, context: str, user_prompt: str = "") -> str:
        """
        Sophisticated prompt engineering with strict length constraints
        """
        # Clean and prepare inputs
        context = self._clean_text(context)[:256]  # Limit context length
        user_prompt = self._clean_text(user_prompt)[:128]  # Limit user prompt
        
        # Concise prompt construction
        prompt_components = [
            "Ultra-realistic image:",
            context,
            "Creative direction: Professional, modern design.",
            "Technical specs: High-quality, crisp rendering."
        ]
        
        # Incorporate user-specific requirements if space permits
        if user_prompt:
            prompt_components.append(f"Requirements: {user_prompt}")
        
        # Combine and strictly truncate prompt
        full_prompt = " ".join(prompt_components)[:512]
        return full_prompt

    def generate_images(self, 
                    context: str = "", 
                    user_prompt: str = "", 
                    num_images: int = 1):
        """
        Advanced image generation with comprehensive error handling
        """
        # Create a concise, precise image generation prompt
        full_prompt = self.construct_image_prompt(context, user_prompt)
        logger.info(f"Image Generation Prompt: {full_prompt}")
        
        generated_images = []
        seed = random.randint(0, 2147483647)
        
        for _ in range(num_images):
            try:
                # Refined request structure for Titan Image Generator
                native_request = {
                    "taskType": "TEXT_IMAGE",
                    "textToImageParams": {
                        "text": full_prompt
                    },
                    "imageGenerationConfig": {
                        "numberOfImages": 1,
                        "quality": "standard",
                        "height": 1024,
                        "width": 1024,
                        "cfgScale": 10.0,
                        "seed": seed
                    }
                }
                
                # Serialize the request body
                request_body = json.dumps(native_request)
                
                # Invoke the model with the exact specification
                response = self.bedrock_runtime.invoke_model(
                    modelId=self.image_model_id, 
                    contentType="application/json",
                    accept="application/json",
                    body=request_body
                )
                
                # Safely parse the response
                model_response = json.loads(response["body"].read())
                
                # Extract and process images
                if "images" in model_response:
                    images = model_response["images"]
                    
                    # Validate and collect non-empty images
                    for img in images:
                        if img and len(img) > 0:
                            generated_images.append(img)
                            break  # Take the first valid image
            
            except Exception as e:
                # Comprehensive error logging
                logger.error(f"Image generation error: {e}")
                logger.error(f"Full error details: {type(e)}")
        
        # Final validation and logging
        if not generated_images:
            logger.error("No images were successfully generated across all attempts")
        
        return generated_images

    def search_similar_embeddings(self, query_embedding: np.ndarray, top_k: int = 3):
        """
        Advanced similarity search with comprehensive error handling
        """
        if self.vector_index is None:
            logger.warning("Vector index not initialized")
            return []

        try:
            # Validate query embedding
            if query_embedding is None or len(query_embedding) != self.embedding_dimension:
                logger.error(f"Invalid query embedding. Expected dimension {self.embedding_dimension}")
                return []

            # Normalize query embedding
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            
            # Perform similarity search
            D, I = self.vector_index.search(
                query_embedding.reshape(1, -1), 
                top_k
            )
            
            # Process and return results
            results = []
            for distance, idx in zip(D[0], I[0]):
                if 0 <= idx < len(self.vector_metadata):
                    metadata = self.vector_metadata[idx]
                    results.append({
                        'metadata': metadata,
                        'score': 1 / (1 + distance)  # Convert distance to similarity
                    })
            
            return results
        
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

class WebContentExtractor:
    @staticmethod
    def extract_website_content(url: str, max_paragraphs: int = 10) -> str:
        """
        Extract textual content from a website
        """
        try:
            response = requests.get(url, timeout=10, 
                                    headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract key content
            title = soup.title.string if soup.title else ''
            paragraphs = [p.get_text() for p in soup.find_all('p')[:max_paragraphs]]
            
            return ' '.join([title] + paragraphs)
        
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return ''


def create_flask_app():
    """
    Create and configure Flask application
    """
    app = Flask(__name__)
    CORS(app)
    
    # Initialize Bedrock Processor
    bedrock_processor = BedrockProcessor()

    @app.route('/generate-ad-images', methods=['POST'])
    def generate_ad_images():
        """
        Generate ad images with robust error handling
        """
        data = request.json or {}
        url = data.get('url')
        user_prompt = data.get('user_prompt', '')
        
        # Default content if no URL
        content = 'Professional marketing design'
        
        if url:
            content = WebContentExtractor.extract_website_content(url) or content
        
        try:
            # Optional: Generate and store embedding
            content_embedding = bedrock_processor.generate_embedding(content)
            if url and content_embedding is not None:
                bedrock_processor.store_embedding(url, content, content_embedding)
            
            # Generate images
            generated_images = bedrock_processor.generate_images(
                context=content,
                user_prompt=user_prompt
            )
            
            # Ensure images is always a list
            safe_images = generated_images if generated_images else []
            
            return jsonify({
                "images": safe_images,
                "success": len(safe_images) > 0
            })
        
        except Exception as e:
            logger.error(f"Comprehensive image generation error: {e}")
            return jsonify({
                "error": "Image generation failed", 
                "details": str(e),
                "images": [],
                "success": False
            }), 500

    @app.route('/search-similar-content', methods=['POST'])
    def search_similar_content():
        """
        Search for similar content based on query
        """
        data = request.json or {}
        query = data.get('query', '')
        top_k = data.get('top_k', 3)
        
        try:
            # Generate embedding for query
            query_embedding = bedrock_processor.generate_embedding(query)
            
            if not query_embedding:
                return jsonify({"error": "Failed to generate embedding"}), 400
            
            # Search similar content
            similar_results = bedrock_processor.search_similar_embeddings(
                query_embedding, 
                top_k=top_k
            )
            
            return jsonify({
                "similar_content": [
                    {
                        "url": result.metadata.get('url', ''),
                        "text": result.metadata.get('text', ''),
                        "similarity_score": result.score
                    } for result in similar_results
                ]
            })
        
        except Exception as e:
            logger.error(f"Content search error: {e}")
            return jsonify({
                "error": "Content search failed",
                "details": str(e)
            }), 500

    return app

def main():
    app = create_flask_app()
    app.run(debug=True, port=5001)

if __name__ == '__main__':
    main()