import requests
from bs4 import BeautifulSoup
from upstash_vector import Index
import boto3
import base64
import json
import random
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

class WebContentVectorizer:
    def __init__(self, 
                 upstash_url: str, 
                 upstash_token: str, 
                 embedding_model: str = 'all-MiniLM-L6-v2'):
        """
        Initialize WebContentVectorizer with Upstash Vector and Embedding Model
        
        Args:
            upstash_url (str): Upstash Vector database URL
            upstash_token (str): Upstash authentication token
            embedding_model (str): Sentence Transformer model for embeddings
        """
        # Initialize Upstash Vector Index
        self.vector_index = Index(
            url=process.env.UPSTASH_VECTOR_REST_UR,
            token=upstash_token
        )
        
        # Initialize Sentence Transformer for embeddings
        self.embedding_model = SentenceTransformer(embedding_model)
    
    def extract_website_content(self, url: str) -> dict:
        """
        Extract content from a given website URL
        
        Args:
            url (str): Website URL to scrape
        
        Returns:
            Dict of extracted website content
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            content = {
                'title': soup.title.string if soup.title else '',
                'meta_description': soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else '',
                'headings': [h.get_text() for h in soup.find_all(['h1', 'h2'])],
                'text_content': ' '.join([p.get_text() for p in soup.find_all('p')[:10]])
            }
            
            return content
        
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return {}
    
    def generate_embeddings(self, content: dict) -> np.ndarray:
        """
        Generate embeddings from website content
        
        Args:
            content (dict): Extracted website content
        
        Returns:
            Numpy array of embeddings
        """
        # Combine content into a single text
        combined_text = ' '.join([
            content.get('title', ''),
            content.get('meta_description', ''),
            ' '.join(content.get('headings', [])),
            content.get('text_content', '')
        ])
        
        return self.embedding_model.encode(combined_text)
    
    def store_vector_embedding(self, url: str, embedding: np.ndarray):
        """
        Store vector embedding in Upstash Vector database
        
        Args:
            url (str): Source URL
            embedding (np.ndarray): Generated embedding vector
        """
        try:
            # Convert numpy array to list for Upstash
            embedding_list = embedding.tolist()
            
            # Store vector with URL as metadata
            self.vector_index.upsert(
                vectors=[{
                    "id": url,
                    "vector": embedding_list,
                    "metadata": {"source_url": url}
                }]
            )
            print(f"Embedding for {url} stored successfully")
        
        except Exception as e:
            print(f"Error storing embedding: {e}")
    
    def retrieve_similar_vectors(self, query_embedding: np.ndarray, top_k: int = 5):
        """
        Retrieve similar vectors from Upstash Vector database
        
        Args:
            query_embedding (np.ndarray): Query embedding vector
            top_k (int): Number of similar vectors to retrieve
        
        Returns:
            List of similar vector results
        """
        try:
            # Convert numpy array to list for Upstash
            query_list = query_embedding.tolist()
            
            # Perform similarity search
            similar_vectors = self.vector_index.query(
                vector=query_list,
                top_k=top_k,
                include_metadata=True
            )
            
            return similar_vectors
        
        except Exception as e:
            print(f"Error retrieving similar vectors: {e}")
            return []

class BedrockImageGenerator:
    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize Bedrock Image Generator
        
        Args:
            region_name (str): AWS Region for Bedrock service
        """
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.model_id = "amazon.titan-image-generator-v1"
    
    def generate_images(self, 
                         content: dict, 
                         query_embedding: np.ndarray = None, 
                         user_prompt: str = "", 
                         num_images: int = 3) -> list:
        """
        Generate images based on website content and vector embedding context
        
        Args:
            content (dict): Extracted website content
            query_embedding (np.ndarray): Optional query embedding for context
            user_prompt (str): Additional user-specified prompt
            num_images (int): Number of images to generate
        
        Returns:
            List of base64 encoded images
        """
        # Construct prompt with vector embedding context
        full_prompt = self._construct_prompt(content, query_embedding, user_prompt)
        
        generated_images = []
        
        for _ in range(num_images):
            native_request = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {"text": full_prompt},
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "quality": "standard",
                    "cfgScale": 8.0,
                    "height": 512,
                    "width": 512,
                    "seed": random.randint(0, 2147483647)
                }
            }
            
            try:
                response = self.client.invoke_model(
                    modelId=self.model_id, 
                    body=json.dumps(native_request)
                )
                
                model_response = json.loads(response["body"].read())
                generated_images.append(model_response["images"][0])
            
            except Exception as e:
                print(f"Image generation error: {e}")
        
        return generated_images
    
    def _construct_prompt(self, 
                           content: dict, 
                           query_embedding: np.ndarray = None, 
                           user_prompt: str = "") -> str:
        """
        Construct a detailed prompt for image generation with vector context
        
        Args:
            content (dict): Extracted website content
            query_embedding (np.ndarray): Optional query embedding
            user_prompt (str): Additional user-specified prompt
        
        Returns:
            Constructed prompt string
        """
        base_prompt = f"Create an advertisement image for a website with title '{content.get('title', '')}'. "
        base_prompt += f"Key description: {content.get('meta_description', '')}. "
        
        # Add vector embedding context if available
        if query_embedding is not None:
            base_prompt += "Context from similar content: Relevant and contextually aligned visual representation. "
        
        if user_prompt:
            base_prompt += f"User specific requirements: {user_prompt}. "
        
        # Add style and creative direction
        base_prompt += "Style: Modern, professional, eye-catching advertisement design."
        
        return base_prompt

# Example Usage
def process_website_for_ads(url: str, upstash_url: str, upstash_token: str):
    """
    Comprehensive workflow to process website, generate embeddings, 
    and create advertisement images
    
    Args:
        url (str): Website URL to process
        upstash_url (str): Upstash Vector database URL
        upstash_token (str): Upstash authentication token
    """
    # Initialize services
    vectorizer = WebContentVectorizer(upstash_url, upstash_token)
    image_generator = BedrockImageGenerator()
    
    # Extract website content
    content = vectorizer.extract_website_content(url)
    
    # Generate embeddings
    embedding = vectorizer.generate_embeddings(content)
    
    # Store vector embedding
    vectorizer.store_vector_embedding(url, embedding)
    
    # Retrieve similar vectors (optional context for image generation)
    similar_vectors = vectorizer.retrieve_similar_vectors(embedding)
    
    # Generate images using website content and optional vector context
    generated_images = image_generator.generate_images(
        content, 
        query_embedding=embedding if similar_vectors else None
    )
    
    return {
        'content': content,
        'embedding': embedding.tolist(),
        'similar_vectors': similar_vectors,
        'generated_images': generated_images
    }

# Main execution example
@app.route('/generate-ad-images', methods=['POST'])
def generate_ad_images():
    """
    Endpoint to generate advertisement images with vector embedding
    
    Expects JSON payload:
    {
        "url": "https://example.com",
        "user_prompt": "Optional additional prompt"
    }
    """
    data = request.json
    url = data.get('url')
    user_prompt = data.get('user_prompt', '')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        # Replace with your actual Upstash Vector database credentials
        UPSTASH_URL = os.getenv('UPSTASH_VECTOR_URL')
        UPSTASH_TOKEN = os.getenv('UPSTASH_VECTOR_TOKEN')
        
        # Process website and generate images
        result = process_website_for_ads(
            url, 
            UPSTASH_URL, 
            UPSTASH_TOKEN
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to generate ad images"
        }), 500