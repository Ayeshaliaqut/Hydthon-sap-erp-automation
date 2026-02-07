import json
from datetime import datetime
import re

class Agent:
    def __init__(self, pdf_processor, vision_analyzer, rag_engine):
        self.pdf = pdf_processor
        self.vision = vision_analyzer
        self.rag = rag_engine
        self.guide = []
    
    def load_guide(self, pdf_path):
        """Load guide PDF"""
        self.guide = self.pdf.extract_pages_with_images(pdf_path)  # FIXED METHOD NAME
        self.rag.create_collection()
        self.rag.index_guide_pages(self.guide)
    
    def troubleshoot(self, screenshot, issue: str) -> dict:
        """MAIN: screenshot + issue -> JSON with steps from MULTIPLE pages"""
        
        # 1. Analyze screenshot
        screen_data = self.vision.analyze_screenshot(screenshot)
        
        # 2. Search guide - get MORE results
        query = f"{issue} {screen_data.get('screen_type', '')}"
        results = self.rag.search(query, n_results=5)  # Get 5 pages
        
        # 3. Extract steps from ALL relevant pages
        all_steps = []
        pages_used = []
        
        for result in results:
            page_num = result["page"]
            guide_text = result["text"]
            
            # Extract steps from this page
            steps = self._extract_steps(guide_text)
            
            if steps:  # Only add if we found steps
                all_steps.extend(steps)
                pages_used.append(page_num)
            
            # Stop if we have enough steps
            if len(all_steps) >= 15:
                break
        
        # 4. Remove duplicate steps (by first 50 chars)
        unique_steps = self._remove_duplicate_steps(all_steps)
        
        # 5. Build response
        return {
            "issue": issue,
            "timestamp": datetime.now().isoformat(),
            "screen_analysis": screen_data,
            "pages_used": pages_used[:3],  # Show which pages we used
            "total_steps": len(unique_steps),
            "steps": unique_steps[:20],  # Max 20 steps
            "status": "success" if unique_steps else "no_steps_found"
        }
    
    def _extract_steps(self, text: str):
        """Extract steps a. through z. from text"""
        steps = []
        
        # Pattern: letter + dot + content until next letter+dot or end
        pattern = r'([a-z])[\.\)]\s*(.+?)(?=(?:[a-z][\.\)]|\Z))'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for letter, content in matches:
            # Clean the step
            content = content.strip()
            content = re.sub(r'\s+', ' ', content)  # Fix spacing
            content = content.replace('\n', ' ')    # Remove line breaks
            
            if content and len(content) > 10:  # Only meaningful steps
                steps.append({
                    "step": letter.upper(),
                    "instruction": content[:300],
                    "source_page": "extracted"
                })
        
        return steps
    
    def _remove_duplicate_steps(self, steps):
        """Remove duplicate steps"""
        seen = set()
        unique_steps = []
        
        for step in steps:
            # Create a key from first 50 chars of instruction
            key = step["instruction"][:50].lower().strip()
            
            if key not in seen:
                seen.add(key)
                unique_steps.append(step)
        
        return unique_steps