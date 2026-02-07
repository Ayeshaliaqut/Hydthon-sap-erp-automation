# src/vision_analyzer.py - CORRECTED
from dotenv import load_dotenv
import google.generativeai as genai
import json
from PIL import Image
from typing import Dict, Any
import os
load_dotenv()
class VisionAnalyzer:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        genai.configure(api_key=api_key)
        
        # CORRECT: Use vision-capable models
        print("🤖 Using gemini-2.5-flash for vision")
        self.vision_model = genai.GenerativeModel('gemini-2.5-flash')
        self.text_model = genai.GenerativeModel('gemini-2.5-flash')  # Same model works for text too
    
    def analyze_screenshot(self, screenshot: Image.Image) -> Dict[str, Any]:
        """Analyze SuccessFactors screenshot"""
        try:
            prompt = """You are analyzing a SAP SuccessFactors ERP screenshot.
            
            Identify:
            1. What screen/page is this?
            2. What UI elements are visible?
            3. What might be wrong based on common issues?
            
            Return JSON: {screen_type, visible_elements[], possible_issues[]}"""
            
            response = self.vision_model.generate_content([prompt, screenshot])
            response_text = response.text.strip()
            
            # Parse JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            
            return json.loads(response_text)
            
        except Exception as e:
            print(f"⚠️  Vision analysis failed: {e}")
            return {
                "screen_type": "Unknown SuccessFactors Screen",
                "visible_elements": [],
                "possible_issues": ["Analysis failed"]
            }
    
    def generate_solution(self, issue: str, context: str = "") -> str:
        """Generate troubleshooting steps"""
        try:
            prompt = f"""As a SuccessFactors expert, solve this issue:
            
            ISSUE: {issue}
            
            CONTEXT: {context}
            
            Provide clear step-by-step instructions."""
            
            response = self.text_model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"⚠️  Solution generation failed: {e}")
            return "Please use RBP Troubleshooting tool in SuccessFactors."