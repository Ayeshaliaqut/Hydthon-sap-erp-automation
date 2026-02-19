# agent.py - Returns ONLY top task in text mode, ALL steps in vision mode

import json
from datetime import datetime
from typing import List, Dict, Optional
import logging
from pathlib import Path
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, pdf_processor, vision_analyzer, rag_engine):
        self.pdf = pdf_processor
        self.vision = vision_analyzer
        self.rag = rag_engine
        self.tasks = []
        self.is_loaded = False
        
        # Thresholds
        self.relevance_threshold = 0.7
        self.vision_confidence_threshold = 0.7
        self.max_tasks_to_try = 3
        
        # Mode flags
        self.return_single_best_task = True
        self.log_vlm_calls = True
    
    def load_guide(self, pdf_path: str):
        """Load and index the guide"""
        try:
            logger.info(f"📖 Loading guide from {pdf_path}...")
            self.tasks = self.pdf.extract_by_tasks(pdf_path)
            
            if not self.tasks:
                logger.error("❌ No tasks extracted")
                return
            
            # Index in RAG
            self.rag.index_tasks(self.tasks)
            
            # Log statistics
            total_steps = sum(t['step_count'] for t in self.tasks)
            total_images = sum(t.get('image_count', 0) for t in self.tasks)
            
            logger.info(f"✅ Loaded {len(self.tasks)} tasks")
            logger.info(f"   - Total steps: {total_steps}")
            logger.info(f"   - Total images: {total_images}")
            logger.info(f"   - Avg steps per task: {total_steps/len(self.tasks):.1f}")
            
            self.is_loaded = True
            
        except Exception as e:
            logger.error(f"❌ Error loading guide: {e}")
            raise
    
    def troubleshoot(self, issue: str) -> Dict:
        """
        Find solution using text only (RAG)
        Returns ONLY the top relevant task (clean, focused results)
        """
        if not self._check_loaded():
            return self._error_response("No guide loaded")
        
        if not issue:
            return self._error_response("Issue description required")
        
        logger.info(f"🔍 Text-only search: '{issue}'")
        
        # Search RAG
        all_results = self.rag.search_tasks(issue, n_results=5)
        relevant_tasks = [t for t in all_results if t['relevance_score'] >= self.relevance_threshold]
        
        if not relevant_tasks:
            return {
                "issue": issue,
                "timestamp": datetime.now().isoformat(),
                "mode": "text_only",
                "status": "no_solution_found",
                "message": "No relevant tasks found. Try rephrasing your issue.",
                "steps": [],
                "tasks_used": []
            }
        
        # Take ONLY the top task
        top_task = relevant_tasks[0]
        logger.info(f"🎯 Selected top task: Task {top_task['task_number']} (score: {top_task['relevance_score']})")
        if len(relevant_tasks) > 1:
            logger.info(f"   (Excluded {len(relevant_tasks)-1} lower-scoring tasks)")
        
        # Collect steps from ONLY the top task
        all_steps = []
        tasks_used = []
        
        if top_task['has_steps'] and top_task['steps']:
            tasks_used.append({
                "task_number": top_task['task_number'],
                "title": top_task['title'],
                "step_count": top_task['step_count'],
                "relevance": top_task['relevance_score']
            })
            
            for step in top_task['steps']:
                step['task_number'] = top_task['task_number']
                step['task_title'] = top_task['title']
                step['relevance'] = top_task['relevance_score']
                all_steps.append(step)
        
        # Remove duplicates (if any within the task)
        all_steps = self._deduplicate_steps(all_steps)
        
        return {
            "issue": issue,
            "timestamp": datetime.now().isoformat(),
            "mode": "text_only",
            "status": "success" if all_steps else "no_solution_found",
            "total_tasks_found": len(all_results),
            "relevant_tasks_found": len(relevant_tasks),
            "tasks_used": tasks_used,
            "total_steps": len(all_steps),
            "steps": all_steps[:15],
            "message": f"Found {len(all_steps)} steps from Task {top_task['task_number']}"
        }
    
    def troubleshoot_with_screenshot(self, issue: str, user_screenshot: Image.Image) -> Dict:
        """
        Find solution using text + screenshot
        Tries multiple tasks but ONLY sends ONE task's images at a time to VLM
        Returns ALL remaining steps from current position
        """
        if not self._check_loaded():
            return self._error_response("No guide loaded")
        
        # Step 1: Find relevant tasks via RAG
        logger.info("🔍 Phase 1: Finding relevant tasks via RAG...")
        all_results = self.rag.search_tasks(issue, n_results=5)
        
        # Filter by threshold and take top N
        relevant_tasks = [
            t for t in all_results 
            if t['relevance_score'] >= self.relevance_threshold
        ][:self.max_tasks_to_try]
        
        if not relevant_tasks:
            logger.warning("❌ No relevant tasks found, falling back to text-only")
            return self.troubleshoot(issue)
        
        logger.info(f"📊 Found {len(relevant_tasks)} candidate tasks to try (in order of relevance):")
        for idx, t in enumerate(relevant_tasks, 1):
            logger.info(f"   {idx}. Task {t['task_number']}: {t['title'][:60]}... (score: {t['relevance_score']})")
        
        # Step 2: Try EACH task SEPARATELY with vision
        for task_idx, task in enumerate(relevant_tasks, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🎯 Attempt {task_idx}/{len(relevant_tasks)}: Trying Task {task['task_number']} ALONE")
            logger.info(f"{'='*60}")
            
            # Load ONLY this task's images
            guide_images = self._load_task_images(task['task_number'])
            if not guide_images:
                logger.warning(f"⚠️ No guide images for Task {task['task_number']}, skipping")
                continue
            
            # Log VLM call details
            if self.log_vlm_calls:
                logger.info(f"📤 VLM CALL DETAILS:")
                logger.info(f"   - Task: {task['task_number']} - {task['title'][:50]}...")
                logger.info(f"   - Guide images: {len(guide_images)} (from task {task['task_number']} only)")
                logger.info(f"   - User screenshot: 1")
                logger.info(f"   - TOTAL images in this call: {len(guide_images) + 1}")
                logger.info(f"   - Steps text: {len(task['steps'])} steps total")
                logger.info(f"   - NO images from other tasks included")
            
            # Prepare vision prompt with ONLY this task's steps
            steps_text = self._format_steps_for_prompt(task['steps'])
            
            # Run vision analysis with ONLY this task's context
            try:
                vision_result = self.vision.compare_screenshots(
                    task_steps=steps_text,
                    guide_images=guide_images,
                    user_screenshot=user_screenshot,
                    task_title=task['title'],
                    task_number=task['task_number']
                )
                
                # Check confidence
                confidence = vision_result.get('confidence', 0)
                remaining_steps = vision_result.get('remaining_steps_count', 0)
                actions_provided = len(vision_result.get('next_actions', []))
                
                logger.info(f"👁️ Vision analysis complete:")
                logger.info(f"   - Current step: {vision_result.get('current_step', 'unknown')}")
                logger.info(f"   - Confidence: {confidence:.2f}")
                logger.info(f"   - Remaining steps to complete: {remaining_steps}")
                logger.info(f"   - Actions provided: {actions_provided}")
                
                if confidence >= self.vision_confidence_threshold:
                    logger.info(f"✅✅✅ TASK {task['task_number']} MATCHED! (confidence: {confidence:.2f})")
                    logger.info(f"   Remaining steps to complete: {remaining_steps}")
                    if actions_provided < remaining_steps:
                        logger.warning(f"⚠️ Warning: Only {actions_provided}/{remaining_steps} steps provided")
                    
                    if task_idx < len(relevant_tasks):
                        logger.info(f"   Stopping - will NOT try remaining {len(relevant_tasks)-task_idx} tasks")
                    
                    return {
                        "issue": issue,
                        "timestamp": datetime.now().isoformat(),
                        "mode": "vision_enhanced",
                        "status": "success",
                        "attempts": task_idx,
                        "total_attempts": len(relevant_tasks),
                        "task_used": {
                            "task_number": task['task_number'],
                            "title": task['title'],
                            "relevance_score": task['relevance_score'],
                            "vision_confidence": confidence
                        },
                        "vision_analysis": vision_result,
                        "playwright_actions": self._format_for_playwright(
                            vision_result.get('next_actions', [])
                        ),
                        "remaining_steps": remaining_steps,
                        "message": f"Found solution using Task {task['task_number']} with visual confirmation. {remaining_steps} steps remaining to complete."
                    }
                else:
                    logger.info(f"⚠️ Confidence too low for Task {task['task_number']} ({confidence:.2f} < {self.vision_confidence_threshold})")
                    if task_idx < len(relevant_tasks):
                        logger.info(f"   Moving to next task...")
                    
            except Exception as e:
                logger.error(f"❌ Vision analysis failed for Task {task['task_number']}: {e}")
                continue
        
        # Step 3: If all tasks fail, fallback to text-only
        logger.warning("⚠️ All vision attempts failed, falling back to text-only")
        logger.info(f"   Tried {len(relevant_tasks)} tasks with vision, none met confidence threshold")
        return self.troubleshoot(issue)
    
    def _load_task_images(self, task_number: str) -> List[Image.Image]:
        """Load all guide images for a specific task"""
        try:
            # Find task in self.tasks
            task = next(
                (t for t in self.tasks if t['task_number'] == str(task_number)),
                None
            )
            
            if not task or 'image_folder' not in task:
                logger.warning(f"No image folder for Task {task_number}")
                return []
            
            image_folder = Path(task['image_folder'])
            if not image_folder.exists():
                logger.warning(f"Image folder not found: {image_folder}")
                return []
            
            # Load all PNG images
            images = []
            for img_path in sorted(image_folder.glob("*.png")):
                try:
                    img = Image.open(img_path)
                    images.append(img)
                except Exception as e:
                    logger.warning(f"Failed to load image {img_path}: {e}")
            
            if self.log_vlm_calls and images:
                logger.info(f"📂 Loaded {len(images)} images from {image_folder}")
            
            return images
            
        except Exception as e:
            logger.error(f"Error loading task images: {e}")
            return []
    
    def _format_steps_for_prompt(self, steps: List[Dict]) -> str:
        """Format steps nicely for vision prompt"""
        if not steps:
            return "No steps available"
        
        lines = []
        for i, step in enumerate(steps, 1):
            lines.append(f"{step['step']}. {step['instruction']} ({step['type']})")
        
        return "\n".join(lines)
    
    def _format_for_playwright(self, actions: List[Dict]) -> List[Dict]:
        """Format vision actions for Playwright execution"""
        playwright_actions = []
        
        for i, action in enumerate(actions):
            playwright_actions.append({
                "order": i + 1,
                "step_letter": action.get('step_letter', ''),
                "description": action.get('description', ''),
                "action_type": action.get('action_type', 'click'),
                "visual_target": action.get('visual_target', ''),
                "expected_result": action.get('expected_result', '')
            })
        
        return playwright_actions
    
    def _deduplicate_steps(self, steps: List[Dict]) -> List[Dict]:
        """Remove duplicate steps"""
        seen = set()
        unique = []
        
        for step in steps:
            key = step['instruction'][:100].lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(step)
        
        return unique
    
    def _check_loaded(self) -> bool:
        """Check if guide is loaded"""
        if not self.is_loaded:
            logger.error("No guide loaded")
            return False
        return True
    
    def _error_response(self, message: str) -> Dict:
        """Return error response"""
        return {
            "success": False,
            "error": message,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_task_by_number(self, task_number: str) -> Optional[Dict]:
        """Retrieve a specific task"""
        for task in self.tasks:
            if str(task['task_number']) == str(task_number):
                return task
        return None
    
    def reset(self):
        """Reset the agent"""
        self.tasks = []
        self.is_loaded = False
        self.rag.delete_collection()
        logger.info("🔄 Agent reset complete")
    
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        return {
            "tasks_loaded": len(self.tasks),
            "total_steps": sum(t['step_count'] for t in self.tasks),
            "total_images": sum(t.get('image_count', 0) for t in self.tasks),
            "relevance_threshold": self.relevance_threshold,
            "vision_confidence_threshold": self.vision_confidence_threshold,
            "max_tasks_to_try": self.max_tasks_to_try,
            "return_single_best_task": self.return_single_best_task
        }