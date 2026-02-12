import json
import sys
import os
from PIL import Image

sys.path.append('src')

from pdf_processor import PDFProcessor
from vision_analyzer import VisionAnalyzer
from rag_engine import RAGEngine
from agent import Agent

def main():
    # Initialize
    pdf = PDFProcessor()
    vision = VisionAnalyzer()
    rag = RAGEngine()
    agent = Agent(pdf, vision, rag)
    
    # Load guide with ENDOFTASK
    guide_path = "data/guides/SuccessFactors_Scenarios.pdf"
    if os.path.exists(guide_path):
        print("Loading tasks from PDF...")
        agent.load_guide(guide_path)
    else:
        print("PDF not found")
        return
    
    # Test
    screenshot = Image.new('RGB', (800, 600), color='white')#intended for dynamic
    issue = "Admin cannot access Proxy Management" #intended for dynamic
    
    # Get solution
    result = agent.troubleshoot(screenshot, issue)
    
    # Output
    print(f"\nFound {result['total_steps']} steps from {len(result['tasks_used'])} tasks")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()