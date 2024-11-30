import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import boto3
from dotenv import load_dotenv
import base64
import textwrap
from unidecode import unidecode

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Bedrock Image Generator
class BedrockImageGenerator:
    def __init__(self, region_name: str = "us-west-2"):
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.model_id = "amazon.titan-image-generator-v2:0"
        self.max_prompt_length = 1024  # Leave room for additional prompt
    
    def _summarize_text(self, text: str, max_length=400) -> str:
        """
        Summarize text while preserving key information
        """
        # Clean the text first
        text = unidecode(str(text or '')).strip()
        
        # If text is already short, return it
        if len(text) <= max_length:
            return text
        
        # Split into sentences
        sentences = text.split('.')
        
        # Accumulate sentences while staying under max length
        summary = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip() + '.'
            if current_length + len(sentence) <= max_length:
                summary.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        # If no sentences work, truncate
        return ' '.join(summary) if summary else text[:max_length]
    
    def generate_images(self, 
                 context: str = "", 
                 user_prompt: str = "", 
                 num_images: int = 1):
        """
        Generate images based on context and user prompt
        """
        # Ensure context is not None or empty
        if not context:
            context = "Generic advertisement design"
        
        # Summarize context to fit within model constraints
        summarized_context = self._summarize_text(context)
        print(f"Summarized Context: {summarized_context}")
        
        full_prompt = self._construct_prompt(summarized_context, user_prompt)
        print(f"Generated Prompt: {full_prompt}")
        
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
                }
            }
            
            try:
                response = self.client.invoke_model(
                    modelId=self.model_id, 
                    body=json.dumps(native_request)
                )
                
                model_response = json.loads(response["body"].read())
                
                # More robust image extraction
                image_data = model_response.get("images", [])
                if image_data:
                    generated_images.append(image_data[0])
            except Exception as e:
                print(f"Image generation error: {e}")

        return generated_images
    
    def _construct_prompt(self, context: str, user_prompt: str = "") -> str:
        """
        Construct a detailed prompt for image generation
        """
        # Ensure context and user_prompt are strings, default to empty string if None
        context = unidecode(str(context or ''))
        user_prompt = unidecode(str(user_prompt or ''))
        
        base_prompt = f"Create an advertisement image based on: {context}. "
        
        if user_prompt:
            base_prompt += f"User specific requirements: {user_prompt}. "
        
        base_prompt += "Style: Modern, professional, visually engaging design."
        
        # Ensure final prompt is within length limit
        return base_prompt[:self.max_prompt_length]

# Initialize Bedrock Image Generator
bedrock_generator = BedrockImageGenerator()

def extract_website_content(url: str):
    """
    Extract textual content from a website
    """
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract key content
        title = soup.title.string if soup.title else ''
        paragraphs = [p.get_text() for p in soup.find_all('p')[:10]]
        
        return ' '.join([title] + paragraphs)
    
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return ''
    
def save_base64_image(base64_string, output_path):
    try:
        # Decode the Base64 string
        image_data = base64.b64decode(base64_string)
        
        # Write the binary data to an image file
        with open(output_path, 'wb') as image_file:
            image_file.write(image_data)
        
        print(f"Image saved successfully at {output_path}")
    except Exception as e:
        print(f"Error saving image: {e}")
    

@app.route('/generate-ad-images', methods=['POST'])
def generate_ad_images():
    """
    Generate ad images based on website content
    """
    data = request.json or {}
    url = data.get('url', '')
    user_prompt = data.get('user_prompt', '')
    
    if not url:
        return jsonify({
            "error": "URL is required", 
            "images": []
        }), 400
    
    # Extract content
    content = extract_website_content(url) or 'Generic website content'
    
    # Summarize content to leave room for user prompt
    summarized_content = bedrock_generator._summarize_text(content)
    
    try:
        # Generate images using summarized website content
        generated_images = bedrock_generator.generate_images(
            context=summarized_content,
            user_prompt=user_prompt
        )
        if generated_images:
            save_base64_image(
                generated_images[0], 
                output_path="output_image.png"
            )
        
        return jsonify({
            "images": generated_images
        })
    
    except Exception as e:
        print(f"Image generation error: {e}")
        return jsonify({
            "error": "Image generation failed", 
            "details": str(e),
            "images": []
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)