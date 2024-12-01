import os
import json
import requests
import base64
import logging
import faiss
import numpy as np
import random

# Web Framework and Middleware
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
    def _init_(self, region_name: str = "us-west-2"):
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
        self.image_model_id = "amazon.titan-image-generator-v2:0"
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

    def _construct_image_prompt(self, context: str, user_prompt: str = "") -> str:
        """
        Sophisticated prompt engineering with strict length control
        """
        # Clean and prepare inputs
        context = self._clean_text(context)
        user_prompt = self._clean_text(user_prompt)
        
        # Create a concise, focused prompt
        prompt_parts = [
            "Professional design:",
            context[:200],  # Limit context
            "Creative direction: Modern, visually striking.",
            "Style: Clean, impactful imagery."
        ]
        
        # Incorporate user-specific requirements if space allows
        if user_prompt and len(user_prompt) < 200:
            prompt_parts.insert(0, f"Specific focus: {user_prompt}")
        
        # Combine and strictly truncate to 512 characters
        full_prompt = " ".join(prompt_parts)[:512]
        
        return full_prompt

    def summarize_text(self, text: str, max_length: int = 1000):
        """
        Summarize text using Bedrock's Claude model
        """
        try:
            # Truncate input to model's max context length
            text = text[:self.max_prompt_length]
            
            request_body = json.dumps({
                "prompt": f"Summarize the following text concisely, capturing the key points. Keep the summary under {max_length} characters:\n\n{text}",
                "max_tokens_to_sample": 300,
                "temperature": 0.3
            })
            
            response = self.bedrock_runtime.invoke_model(
                modelId="anthropic.claude-v2:1",
                contentType="application/json",
                body=request_body
            )
            
            model_response = json.loads(response["body"].read())
            summary = model_response.get("completion", "").strip()
            
            return summary[:max_length]
        
        except Exception as e:
            logger.error(f"Text summarization error: {e}")
            # Fallback to simple truncation if summarization fails
            return text[:max_length]

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
        Store embedding in FAISS with rich metadata
        """
        if self.vector_index is None:
            logger.warning("Vector index not initialized")
            return None

        try:
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            # Add to FAISS index
            self.vector_index.add(embedding.reshape(1, -1))
            
            # Store metadata
            self.vector_metadata.append({
                "url": url,
                "text": text[:1000],  # Truncate metadata text
                "embedding_id": len(self.vector_metadata)
            })
            
            return len(self.vector_metadata) - 1
        
        except Exception as e:
            logger.error(f"Vector storage error: {e}")
            return None

    def generate_images(self, 
                    context: str = "", 
                    user_prompt: str = "", 
                    num_images: int = 2):
        """
        Generate multiple diverse images with robust error handling
        """
        # Create a comprehensive, nuanced image generation prompt
        full_prompt = self._construct_image_prompt(context, user_prompt)
        logger.info(f"Image Generation Prompt: {full_prompt}")
        
        generated_images = []
        
        for _ in range(num_images):
            try:
                # Generate a random seed for each image to ensure diversity
                seed = random.randint(1, 1000000)
                
                native_request = {
                    "taskType": "TEXT_IMAGE",
                    "textToImageParams": {
                        "text": full_prompt,
                        "negativeText": "low quality, blurry, unprofessional, amateur"
                    },
                    "imageGenerationConfig": {
                        "numberOfImages": 1,
                        "quality": "premium",
                        "cfgScale": 10,  # Creativity scale
                        "height": 1024,
                        "width": 1024,
                        "seed": seed  # Add random seed for variation
                    }
                }
                
                response = self.bedrock_runtime.invoke_model(
                    modelId=self.image_model_id, 
                    body=json.dumps(native_request)
                )
                
                # Safely parse the response
                model_response = json.loads(response["body"].read())
                image_data = model_response.get("images", [])
                
                # Ensure image_data is a list and has content
                if isinstance(image_data, list) and image_data:
                    generated_images.append(image_data[0])
                else:
                    logger.warning("No images generated in this iteration")
            
            except Exception as e:
                # More detailed logging
                logger.error(f"Image generation error: {str(e)}")
        
        return generated_images

    def generate_ad_images(self, url: str = None, user_prompt: str = '', max_text_length: int = 2000):
        """
        Comprehensive method to generate images from website content
        """
        # Default content if no URL
        content = 'Generic advertisement design'
        
        if url:
            # Extract website content
            content = WebContentExtractor.extract_website_content(url)
            
            # Summarize if content is too long
            if len(content) > max_text_length:
                content = self.summarize_text(content)
        
        # Combine with user prompt
        full_context = f"{user_prompt} {content}".strip()
        
        try:
            # Generate and store embedding of summarized/processed content
            content_embedding = self.generate_embedding(full_context)
            if url and content_embedding is not None:
                self.store_embedding(url, full_context, content_embedding)
            
            # Generate diverse images
            generated_images = self.generate_images(
                context=full_context,
                num_images=2
            )
            
            return generated_images
        
        except Exception as e:
            logger.error(f"Image generation process error: {e}")
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
        data = request.json or {}
        url = data.get('url')
        user_prompt = data.get('user_prompt', '')
        
        generated_images = bedrock_processor.generate_ad_images(
            url=url, 
            user_prompt=user_prompt
        )
        
        return jsonify({
            "images": generated_images
        })

    return app

def main():
    app = create_flask_app()
    app.run(debug=True, port=5001)

if __name__ == '__main__':
    main()