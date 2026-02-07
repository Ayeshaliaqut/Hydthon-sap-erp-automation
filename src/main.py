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
    
    # Load guide
    guide_path = "data/guides/SuccessFactors_Scenarios.pdf"
    if os.path.exists(guide_path):
        print("Loading guide...")
        agent.load_guide(guide_path)
        print(f"Loaded {len(agent.guide)} pages")
    else:
        print("Guide not found, using minimal data")
        # Minimal dummy data
        agent.guide = [{"page_number": 1, "text": "a. Step one\nb. Step two", "images": []}]
        rag.create_collection()
        rag.index_guide_pages(agent.guide)
    
    # HARDCODED paths
    screenshot_path = "/home/abdullah/Desktop/successfactors-vision-rag/screenshots/test.png"
    issue = "Admin cannot access Proxy Management"
    
    # Load screenshot
    if os.path.exists(screenshot_path):
        screenshot = Image.open(screenshot_path)
        print(f"Loaded screenshot: {screenshot.size}")
    else:
        print("Creating dummy screenshot...")
        screenshot = Image.new('RGB', (800, 600), color='white')
    
    # Analyze
    print(f"Issue: {issue}")
    print("Analyzing...")
    
    result = agent.troubleshoot(screenshot, issue)
    
    # Display results
    print(f"\nFound {result['total_steps']} steps from pages: {result['pages_used']}")
    print("\nFIRST 5 STEPS:")
    for i, step in enumerate(result['steps'][:5], 1):
        print(f"{step['step']}. {step['instruction'][:80]}...")
    
    # Save full JSON
    with open("multi_page_result.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\nFull result saved to: multi_page_result.json")

if __name__ == "__main__":
    main()