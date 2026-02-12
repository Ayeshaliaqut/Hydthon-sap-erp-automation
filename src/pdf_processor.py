import fitz
import os
import re
from typing import List, Dict

class PDFProcessor:
    def __init__(self):
        pass
    
    def extract_by_tasks(self, pdf_path: str) -> List[Dict]:
        """Extract tasks separated by ENDOFTASK"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        all_tasks = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            if not text.strip():
                continue
            
            # Extract tasks using ENDOFTASK separator
            tasks = self._split_by_endoftask(text, page_num + 1)
            all_tasks.extend(tasks)
        
        doc.close()
        return all_tasks
    
    def _split_by_endoftask(self, text: str, page_num: int) -> List[Dict]:
        """Split text by ENDOFTASK markers"""
        tasks = []
        
        # Clean text: remove extra whitespace but keep ENDOFTASK
        text = re.sub(r'\s+', ' ', text)
        
        # Split by ENDOFTASK (case insensitive, with optional spacing)
        # Keep everything between ENDOFTASK markers
        chunks = re.split(r'\bENDOFTASK\b', text, flags=re.IGNORECASE)
        
        task_counter = 1
        
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk or len(chunk) < 20:  # Skip very short chunks
                continue
            
            # Extract task info
            task_num = self._extract_task_number(chunk)
            has_steps = self._has_steps(chunk)
            
            tasks.append({
                "id": f"task_{task_num or task_counter}_page_{page_num}",
                "task_number": task_num or task_counter,
                "page": page_num,
                "text": chunk,
                "has_steps": has_steps,
                "step_count": self._count_steps(chunk) if has_steps else 0,
                "is_complete": True  # Always complete with ENDOFTASK separator
            })
            task_counter += 1
        
        return tasks
    
    def _extract_task_number(self, text: str) -> int:
        """Extract task number from text (e.g., '1) ...' or 'Task 1: ...')"""
        # Look for patterns in first 200 chars
        first_part = text[:200]
        
        patterns = [
            r'(\d+)\)',           # 1)
            r'Task\s+(\d+)',      # Task 1
            r'Step\s+(\d+)',      # Step 1
            r'(\d+)\.\s',         # 1.
            r'Issue\s+(\d+)'      # Issue 1
        ]
        
        for pattern in patterns:
            match = re.search(pattern, first_part, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0
    
    def _has_steps(self, text: str) -> bool:
        """Check if task contains steps (a., b., c. or 1., 2., 3.)"""
        # Check for lettered steps
        if re.search(r'[a-z][\.\)]\s+', text, re.IGNORECASE):
            return True
        
        # Check for numbered steps (but not task numbers)
        if re.search(r'(?<!\d\.)\d[\.\)]\s+', text):
            return True
        
        return False
    
    def _count_steps(self, text: str) -> int:
        """Count number of steps in task"""
        # Count lettered steps (a., b., c., etc.)
        letter_steps = len(re.findall(r'[a-z][\.\)]\s+', text, re.IGNORECASE))
        
        # Count numbered steps (but exclude task numbers like "1)")
        numbered_steps = len(re.findall(r'(?<!\d\.)\d[\.\)]\s+', text))
        
        return max(letter_steps, numbered_steps)