# pdf_processor.py - With image saving to disk

import fitz
import os
import re
import json
from typing import List, Dict, Optional
import hashlib
import base64
from pathlib import Path

class PDFProcessor:
    def __init__(self, screenshots_base_dir: str = "data/screenshots"):
        """
        Initialize PDF Processor
        
        Args:
            screenshots_base_dir: Base directory to save extracted images
        """
        self.screenshots_base_dir = screenshots_base_dir
        # Create base directory if it doesn't exist
        Path(screenshots_base_dir).mkdir(parents=True, exist_ok=True)
    
    def extract_by_tasks(self, pdf_path: str) -> List[Dict]:
        """Extract tasks with images and save images to disk"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        
        # First, extract all images from the PDF
        all_images = self._extract_all_images(doc)
        
        # Build full text with page markers
        full_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            full_text += f"\n--- Page {page_num + 1} ---\n{text}"
        
        doc.close()
        
        # Split into tasks
        tasks = self._split_by_endoftask(full_text, all_images)
        
        # Save images to disk and update task objects
        tasks = self._save_task_images(tasks)
        
        print(f"✅ Extracted {len(tasks)} tasks with images saved to {self.screenshots_base_dir}")
        return tasks
    
    def _extract_all_images(self, doc) -> Dict:
        """Extract all images from the PDF and store by page"""
        all_images = {}
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            page_images = []
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                # Convert to PNG bytes
                if pix.n - pix.alpha < 4:
                    img_data = pix.tobytes("png")
                else:
                    pix2 = fitz.Pixmap(fitz.csRGB, pix)
                    img_data = pix2.tobytes("png")
                    pix2 = None
                
                # Get image location
                bbox = self._find_image_bbox(page, xref)
                
                # Generate image ID
                img_id = hashlib.md5(img_data).hexdigest()[:12]
                
                page_images.append({
                    "id": f"img_p{page_num+1}_{img_index}_{img_id}",
                    "page": page_num + 1,
                    "xref": xref,
                    "bbox": bbox,
                    "data_base64": base64.b64encode(img_data).decode('utf-8'),
                    "width": pix.width,
                    "height": pix.height,
                    "size": len(img_data),
                    "filename": f"page_{page_num+1}_{img_index}_{img_id}.png"
                })
                
                pix = None
            
            if page_images:
                all_images[page_num + 1] = page_images
        
        return all_images
    
    def _save_task_images(self, tasks: List[Dict]) -> List[Dict]:
        """Save images for each task to disk and update task objects"""
        for task in tasks:
            task_num = task['task_number']
            
            # Create task folder
            task_folder = Path(self.screenshots_base_dir) / f"task_{task_num}"
            task_folder.mkdir(exist_ok=True)
            
            # Save each image
            saved_images = []
            for img in task['images']:
                # Decode base64
                img_data = base64.b64decode(img['data_base64'])
                
                # Save to disk
                img_path = task_folder / img['filename']
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                
                # Create image info with path (remove base64 to keep task object light)
                saved_images.append({
                    "id": img['id'],
                    "page": img['page'],
                    "width": img['width'],
                    "height": img['height'],
                    "size": img['size'],
                    "path": str(img_path),  # Filesystem path
                    "filename": img['filename']
                })
            
            # Replace images list with saved images info (no base64)
            task['images'] = saved_images
            task['image_folder'] = str(task_folder)
            task['image_count'] = len(saved_images)
        
        return tasks
    
    def _find_image_bbox(self, page, xref: int) -> List[float]:
        """Find image bounding box"""
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") == 1:  # Image block
                if block.get("xref") == xref:
                    return block["bbox"]
        return []
    
    def _split_by_endoftask(self, full_text: str, all_images: Dict) -> List[Dict]:
        """Split text by ENDOFTASK markers and assign images"""
        
        # Split by ENDOFTASK
        if "## ENDOFTASK" in full_text:
            task_blocks = full_text.split("## ENDOFTASK")
        elif "# ENDOFTASK" in full_text:
            task_blocks = full_text.split("# ENDOFTASK")
        else:
            task_blocks = full_text.split("ENDOFTASK")
        
        tasks = []
        
        for i, block in enumerate(task_blocks):
            block = block.strip()
            if not block or len(block) < 100:
                continue
            
            # Extract page numbers from this block
            page_markers = re.findall(r'--- Page (\d+) ---', block)
            pages_in_task = [int(p) for p in page_markers]
            
            # Collect images from these pages
            task_images = []
            for page_num in pages_in_task:
                if page_num in all_images:
                    task_images.extend(all_images[page_num])
            
            # Remove page markers
            block = re.sub(r'--- Page \d+ ---\n', '', block)
            
            # Extract task number and title
            task_num, task_title = self._extract_task_info(block)
            
            # Clean the block
            clean_block = self._clean_task_text(block)
            
            # Extract steps (excluding task description)
            steps = self._extract_clean_steps(clean_block, task_title)
            
            tasks.append({
                "id": f"task_{task_num}",
                "task_number": task_num,
                "title": task_title,
                "text": clean_block,
                "has_steps": len(steps) > 0,
                "step_count": len(steps),
                "steps": steps,
                "images": task_images,  # Will be replaced with saved paths later
                "image_count": len(task_images),
                "pages": pages_in_task
            })
        
        # Sort by task number
        tasks.sort(key=lambda x: int(x['task_number']) if x['task_number'].isdigit() else 999)
        
        return tasks
    
    def _extract_task_info(self, text: str) -> tuple:
        """Extract task number and title"""
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            # Match pattern like "1) Admin is unable to access Proxy management"
            match = re.match(r'^(\d+)\)\s+(.+)', line)
            if match:
                return match.group(1), match.group(2).strip()
        return str(len(text)), "Unknown Task"
    
    def _clean_task_text(self, text: str) -> str:
        """Clean up task text"""
        # Remove image markers
        text = re.sub(r'image\[\[\d+,\d+,\d+,\d+\]\]', '', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove HTML-like tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove "=====" separators
        text = re.sub(r'={5,}', '', text)
        
        return text.strip()
    
    def _extract_clean_steps(self, text: str, task_title: str) -> List[Dict]:
        """Extract steps, excluding the task title and description"""
        steps = []
        lines = text.split('\n')
        
        # Skip the first line if it contains the task title
        start_idx = 0
        if lines and task_title in lines[0]:
            start_idx = 1
        
        for line in lines[start_idx:]:
            line = line.strip()
            if not line:
                continue
            
            # Skip lines that are too short or are headers
            if len(line) < 10:
                continue
            if line.startswith('#'):
                continue
            
            # Pattern for lettered steps (a., b., c.)
            letter_match = re.match(r'^([a-z])[\.\)]\s+(.+)', line, re.IGNORECASE)
            # Pattern for numbered steps (1., 2., 3.)
            number_match = re.match(r'^(\d+)[\.\)]\s+(.+)', line)
            
            if letter_match:
                letter, instruction = letter_match.groups()
                instruction = instruction.strip()
                # Clean up instruction
                instruction = re.sub(r'\s+', ' ', instruction)
                if len(instruction) > 10:
                    steps.append({
                        "step": letter.upper(),
                        "instruction": instruction,
                        "type": self._get_step_type(instruction)
                    })
            elif number_match:
                number, instruction = number_match.groups()
                number_val = int(number)
                # Only include if it's a reasonable step number (1-20)
                if 1 <= number_val <= 20:
                    instruction = instruction.strip()
                    instruction = re.sub(r'\s+', ' ', instruction)
                    if len(instruction) > 10:
                        steps.append({
                            "step": number,
                            "instruction": instruction,
                            "type": self._get_step_type(instruction)
                        })
        
        return steps
    
    def _get_step_type(self, instruction: str) -> str:
        """Categorize step type"""
        instruction_lower = instruction.lower()
        
        if any(word in instruction_lower for word in ['go to', 'navigate', 'search', 'find']):
            return "navigation"
        elif any(word in instruction_lower for word in ['click', 'select', 'press', 'choose']):
            return "click"
        elif any(word in instruction_lower for word in ['check', 'verify', 'ensure', 'see']):
            return "verification"
        elif any(word in instruction_lower for word in ['type', 'enter', 'input', 'fill']):
            return "input"
        elif any(word in instruction_lower for word in ['save', 'apply', 'submit']):
            return "save"
        elif any(word in instruction_lower for word in ['logout', 'login', 'proxy']):
            return "auth"
        else:
            return "action"
    
    def get_task_images(self, task_number: str) -> List[Dict]:
        """Helper method to get images for a specific task"""
        task_folder = Path(self.screenshots_base_dir) / f"task_{task_number}"
        if not task_folder.exists():
            return []
        
        images = []
        for img_path in task_folder.glob("*.png"):
            images.append({
                "path": str(img_path),
                "filename": img_path.name
            })
        
        return sorted(images, key=lambda x: x['filename'])