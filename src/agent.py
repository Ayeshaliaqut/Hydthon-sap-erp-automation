import json
from datetime import datetime
import re

class Agent:
    def __init__(self, pdf_processor, vision_analyzer, rag_engine):
        self.pdf = pdf_processor
        self.vision = vision_analyzer
        self.rag = rag_engine
        self.tasks = []
    
    def load_guide(self, pdf_path):
        """Load guide with ENDOFTASK separators"""
        self.tasks = self.pdf.extract_by_tasks(pdf_path)
        self.rag.create_collection()
        self.rag.index_tasks(self.tasks)
        print(f"Loaded {len(self.tasks)} tasks")
    
    def troubleshoot(self, screenshot, issue: str) -> dict:
        """Find solution in tasks"""
        # Analyze screenshot
        screen_data = self.vision.analyze_screenshot(screenshot)
        
        # Search tasks
        query = f"{issue} {screen_data.get('screen_type', '')}"
        results = self.rag.search_tasks(query, n_results=3)
        
        # Extract steps from matching tasks
        all_steps = []
        tasks_used = []
        
        for result in results:
            if result["has_steps"]:
                steps = self._extract_steps_from_task(result["text"])
                
                if steps:
                    all_steps.extend(steps)
                    tasks_used.append({
                        "task": result["task_number"],
                        "page": result["page"],
                        "steps_found": len(steps),
                        "task_id": result["task_id"]
                    })
        
        return {
            "issue": issue,
            "timestamp": datetime.now().isoformat(),
            "screen_analysis": screen_data,
            "tasks_used": tasks_used,
            "total_steps": len(all_steps),
            "steps": all_steps[:15],  # Limit steps
            "status": "success" if all_steps else "no_steps_found"
        }
    
    def _extract_steps_from_task(self, task_text: str):
        """Extract steps from task text"""
        steps = []
        
        # Look for lettered steps (a., b., c., etc.)
        pattern = r'([a-z])[\.\)]\s*(.+?)(?=(?:[a-z][\.\)]|\d+[\.\)]|$))'
        matches = re.findall(pattern, task_text, re.DOTALL | re.IGNORECASE)
        
        for letter, content in matches:
            content = content.strip()
            content = re.sub(r'\s+', ' ', content)
            
            if content and len(content) > 10:
                steps.append({
                    "step": letter.upper(),
                    "instruction": content[:250],
                    "type": self._get_step_type(content)
                })
        
        return steps
    
    def _get_step_type(self, instruction: str) -> str:
        """Categorize step type"""
        instruction = instruction.lower()
        
        if any(word in instruction for word in ['go to', 'navigate', 'open']):
            return "navigation"
        elif any(word in instruction for word in ['click', 'select', 'press']):
            return "click"
        elif any(word in instruction for word in ['search', 'find', 'look']):
            return "search"
        elif any(word in instruction for word in ['check', 'verify', 'ensure']):
            return "verification"
        elif any(word in instruction for word in ['type', 'enter', 'input']):
            return "input"
        elif any(word in instruction for word in ['save', 'apply', 'submit']):
            return "save"
        elif any(word in instruction for word in ['logout', 'login', 'proxy']):
            return "auth"
        else:
            return "action"
        
    