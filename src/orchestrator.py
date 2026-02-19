import sys
import json
import logging
from pathlib import Path
from PIL import Image
from datetime import datetime
from typing import Dict, Any

# Add src to path
sys.path.append('src')

from pdf_processor import PDFProcessor
from vision_analyzer import VisionAnalyzer
from rag_engine import RAGEngine
from agent import Agent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """Centralized configuration management"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_defaults()
        self._load_from_file()
    
    def _load_defaults(self) -> Dict[str, Any]:
        """Load default configuration values"""
        return {
            # Paths
            "guide_path": "data/guides/SuccessFactors_Scenarios.pdf",
            "chroma_path": "./chroma_db",
            "screenshots_dir": "data/screenshots",
            
            # RAG settings
            "text_search_results": 5,
            "vision_search_results": 5,
            "max_vision_attempts": 3,
            
            # Thresholds
            "relevance_threshold": 0.7,
            "vision_confidence_threshold": 0.7,
            
            # Output settings
            "max_steps_in_response": 15,
            "save_results": True,
            "results_dir": "results"
        }
    
    def _load_from_file(self):
        """Load configuration from JSON file if exists"""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                    logger.info(f"✅ Loaded config from {self.config_path}")
            except Exception as e:
                logger.warning(f"⚠️ Could not load config file: {e}")
    
    def get(self, key: str, default=None):
        """Get config value with fallback"""
        return self.config.get(key, default)
    
    def __getitem__(self, key):
        return self.config[key]
    
    def __contains__(self, key):
        return key in self.config


class TroubleshootingEngine:
    """Main engine that orchestrates the entire troubleshooting process"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.agent = None
        self.initialized = False
    
    def initialize(self) -> bool:
        """Initialize all components and load the guide"""
        try:
            logger.info("🚀 Initializing troubleshooting engine...")
            
            # Initialize components
            pdf = PDFProcessor(
                screenshots_base_dir=self.config["screenshots_dir"]
            )
            vision = VisionAnalyzer()
            rag = RAGEngine()
            
            # Create agent with config values
            self.agent = Agent(pdf, vision, rag)
            self.agent.relevance_threshold = self.config["relevance_threshold"]
            self.agent.vision_confidence_threshold = self.config["vision_confidence_threshold"]
            self.agent.max_tasks_to_try = self.config["max_vision_attempts"]
            
            # Load guide
            guide_path = self.config["guide_path"]
            if not Path(guide_path).exists():
                logger.error(f"❌ Guide not found: {guide_path}")
                return False
            
            self.agent.load_guide(guide_path)
            self.initialized = True
            logger.info("✅ Engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    def troubleshoot_text(self, issue: str) -> Dict[str, Any]:
        """Text-only troubleshooting"""
        if not self._check_initialized():
            return self._error_response("Engine not initialized")
        
        logger.info(f"🔍 Text troubleshooting: '{issue}'")
        result = self.agent.troubleshoot(issue)
        
        # Add metadata
        result["engine_version"] = "1.0"
        result["config"] = {
            "relevance_threshold": self.config["relevance_threshold"],
            "mode": "text_only"
        }
        
        self._save_result(result, "text")
        return result
    
    def troubleshoot_with_screenshot(self, issue: str, screenshot_path: str) -> Dict[str, Any]:
        """Screenshot-enhanced troubleshooting"""
        if not self._check_initialized():
            return self._error_response("Engine not initialized")
        
        # Load screenshot
        try:
            if not Path(screenshot_path).exists():
                return self._error_response(f"Screenshot not found: {screenshot_path}")
            
            screenshot = Image.open(screenshot_path)
            logger.info(f"📸 Loaded screenshot: {screenshot_path}")
            
        except Exception as e:
            return self._error_response(f"Failed to load screenshot: {e}")
        
        # Run vision-enhanced troubleshooting
        logger.info(f"🔍 Vision troubleshooting: '{issue}'")
        result = self.agent.troubleshoot_with_screenshot(issue, screenshot)
        
        # Add metadata
        result["engine_version"] = "1.0"
        result["config"] = {
            "relevance_threshold": self.config["relevance_threshold"],
            "vision_confidence_threshold": self.config["vision_confidence_threshold"],
            "max_vision_attempts": self.config["max_vision_attempts"],
            "mode": "vision_enhanced",
            "screenshot_used": screenshot_path
        }
        
        self._save_result(result, "vision")
        return result
    
    def _check_initialized(self) -> bool:
        """Check if engine is initialized"""
        if not self.initialized or not self.agent:
            logger.error("❌ Engine not initialized")
            return False
        return True
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "error": message,
            "timestamp": datetime.now().isoformat(),
            "engine_version": "1.0"
        }
    
    def _save_result(self, result: Dict[str, Any], mode: str):
        """Save result to disk if enabled"""
        if not self.config.get("save_results", True):
            return
        
        try:
            results_dir = Path(self.config.get("results_dir", "results"))
            results_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = results_dir / f"troubleshoot_{mode}_{timestamp}.json"
            
            with open(filename, "w") as f:
                json.dump(result, f, indent=2, default=str)
            
            logger.info(f"📁 Result saved: {filename}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save result: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status"""
        return {
            "initialized": self.initialized,
            "config": self.config.config,
            "tasks_loaded": len(self.agent.tasks) if self.agent else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset(self):
        """Reset the engine"""
        if self.agent:
            self.agent.reset()
        self.initialized = False
        logger.info("🔄 Engine reset")