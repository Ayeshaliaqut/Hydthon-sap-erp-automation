# vision_analyzer.py - Updated to return ALL remaining steps

from dotenv import load_dotenv
from google import genai
import json
from PIL import Image
from typing import Dict, Any, List
import os

load_dotenv()

class VisionAnalyzer:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        # New SDK initialization
        self.client = genai.Client(api_key=api_key)
        
        # Using gemini-2.5-flash (available in your list)
        self.model = "gemini-2.5-flash"
        print(f"🤖 Using {self.model} for vision")
    
    def compare_screenshots(self, 
                           task_steps: str,
                           guide_images: List[Image.Image], 
                           user_screenshot: Image.Image,
                           task_title: str,
                           task_number: str) -> Dict[str, Any]:
        """
        Compare guide images with user screenshot to identify issue
        Returns ALL remaining steps from current position to completion
        """
        try:
            prompt = f"""You are analyzing a SAP SuccessFactors issue.

TASK {task_number}: {task_title}

COMPLETE EXPECTED STEPS (in order):
{task_steps}

INSTRUCTIONS:
I'm giving you:
1. Multiple GUIDE IMAGES - these show the EXPECTED UI at different steps IN ORDER
2. One USER SCREENSHOT - this is the ACTUAL screen showing the problem

CRITICAL REQUIREMENTS:
1. First, identify which step the user is CURRENTLY on by comparing their screenshot to the guide images
2. Then, provide EVERY remaining step from that point forward until the issue is COMPLETELY resolved
3. DO NOT stop at just the next step - include ALL steps needed to finish the fix

ANALYSIS PROCESS:
- Compare user screenshot to each guide image to find the closest match
- If user is before the first step, indicate "before a" or "before 1"
- Look for what's MISSING, WRONG, or different from expected
- Map out the complete path from current state to resolution

Return a JSON with this exact structure:
{{
    "current_step": "step identifier (e.g., 'a', '1', or 'before a' if before first step)",
    "step_description": "detailed description of where user is and what's wrong",
    "issue": "what's wrong and why (be specific)",
    "confidence": 0.0-1.0,
    "remaining_steps_count": integer,  // Total number of steps remaining to complete
    "next_actions": [
        {{
            "step_letter": "the step identifier (e.g., 'b', 'c', '2')",
            "description": "clear action description",
            "visual_target": "exactly what to look for/click (e.g., 'blue Proxy Management tile', 'Save button at bottom right')",
            "action_type": "click|fill|verify|navigate|save",
            "expected_result": "what should happen after this action"
        }}
        // ⚠️ IMPORTANT: Include EVERY remaining step from current position to completion
        // Do NOT stop at just the next step - include all steps until issue is fixed
        // The number of actions here should match remaining_steps_count
    ]
}}

Be extremely specific about visual targets so Playwright can find them.
Remember: Include ALL remaining steps, not just the immediate next one.
"""
            
            # Prepare content for new SDK
            contents = [prompt]
            
            # Add guide images in order
            for idx, img in enumerate(guide_images):
                contents.append(img)
            
            # Add user screenshot last
            contents.append(user_screenshot)
            
            # Log what we're sending
            print(f"\n📤 VLM Request:")
            print(f"   - Task: {task_number}")
            print(f"   - Guide images: {len(guide_images)}")
            print(f"   - User screenshot: 1")
            print(f"   - Total images: {len(guide_images) + 1}")
            
            # Generate response with new SDK
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents
            )
            
            response_text = response.text.strip()
            
            # Parse JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            result = json.loads(response_text)
            
            # Add metadata
            result['task_number'] = task_number
            result['task_title'] = task_title
            
            # Validate we got all steps
            if 'remaining_steps_count' in result:
                actual_steps = len(result.get('next_actions', []))
                expected = result['remaining_steps_count']
                
                if actual_steps < expected:
                    print(f"⚠️ Warning: Expected {expected} steps but got {actual_steps}")
                elif actual_steps > expected:
                    print(f"⚠️ Warning: Got {actual_steps} steps but expected {expected}")
                else:
                    print(f"✅ Got all {expected} remaining steps")
            
            print(f"✅ VLM Analysis complete - Confidence: {result.get('confidence', 0):.2f}")
            return result
            
        except Exception as e:
            print(f"⚠️ Vision analysis failed: {e}")
            return {
                "current_step": "unknown",
                "step_description": "Analysis failed",
                "issue": "Could not analyze screenshot",
                "confidence": 0.0,
                "remaining_steps_count": 0,
                "next_actions": [],
                "task_number": task_number,
                "task_title": task_title,
                "error": str(e)
            }
    
    def analyze_screenshot(self, screenshot: Image.Image) -> Dict[str, Any]:
        """Simple screenshot analysis (original method)"""
        try:
            prompt = """You are analyzing a SAP SuccessFactors ERP screenshot.
            
            Identify:
            1. What screen/page is this?
            2. What UI elements are visible?
            3. What might be wrong based on common issues?
            
            Return JSON: {screen_type, visible_elements[], possible_issues[]}"""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt, screenshot]
            )
            
            response_text = response.text.strip()
            
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            
            return json.loads(response_text)
            
        except Exception as e:
            print(f"⚠️ Vision analysis failed: {e}")
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
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
            
        except Exception as e:
            print(f"⚠️ Solution generation failed: {e}")
            return "Please use RBP Troubleshooting tool in SuccessFactors."