import sys
import json
from pathlib import Path

# Add src to path
sys.path.append('src')

from orchestrator import Config, TroubleshootingEngine


def display_result(result):
    """Display troubleshooting result"""
    print("\n" + "="*60)
    print("📊 TROUBLESHOOTING RESULT")
    print("="*60)
    
    if not result.get("success", True):
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        return
    
    print(f"Mode: {result.get('mode', 'unknown')}")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Message: {result.get('message', 'No message')}")
    
    if result.get('mode') == 'vision_enhanced':
        vision = result.get('vision_analysis', {})
        print(f"\n👁️ Vision Analysis:")
        print(f"   Current Step: {vision.get('current_step', 'unknown')}")
        print(f"   Issue: {vision.get('issue', 'unknown')}")
        print(f"   Confidence: {vision.get('confidence', 0):.2f}")
        
        actions = result.get('playwright_actions', [])
        if actions:
            print(f"\n🎭 Playwright Actions ({len(actions)}):")
            for i, action in enumerate(actions, 1):
                print(f"\n   {i}. [{action['action_type'].upper()}]")
                print(f"      Target: {action['visual_target']}")
                print(f"      Description: {action['description']}")
    
    else:
        steps = result.get('steps', [])
        if steps:
            print(f"\n📋 Steps ({len(steps)}):")
            for i, step in enumerate(steps[:5], 1):
                print(f"\n   {i}. [{step['type'].upper()}] {step['instruction'][:100]}...")


def run_test_suite(engine):
    """Run built-in test suite"""
    print("\n" + "="*60)
    print("🧪 RUNNING TEST SUITE")
    print("="*60)
    
    test_cases = [
        "Admin cannot access Proxy Management",
        "User cannot see another user in search",
        "Workflow not triggering on address change"
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {query}")
        result = engine.troubleshoot_text(query)
        print(f"   ✓ Found {result.get('total_steps', 0)} steps")
        print(f"   ✓ Tasks used: {len(result.get('tasks_used', []))}")


def main():
    """Main entry point for CLI usage"""
    print("\n" + "="*60)
    print("🤖 SUCCESSFACTORS TROUBLESHOOTING ENGINE v1.0")
    print("="*60)
    print("📸 Vision-Enhanced | 🎭 Playwright-Ready | 🔍 RAG-Powered")
    print("="*60)
    
    # Load configuration
    config = Config()
    
    # Initialize engine
    engine = TroubleshootingEngine(config)
    if not engine.initialize():
        print("\n❌ Failed to initialize engine. Exiting.")
        return
    
    # Print status
    status = engine.get_status()
    print(f"\n📊 Engine Status:")
    print(f"   - Initialized: {status['initialized']}")
    print(f"   - Tasks loaded: {status['tasks_loaded']}")
    print(f"   - Screenshots dir: {config['screenshots_dir']}")
    
    # Interactive menu
    while True:
        print("\n" + "="*60)
        print("SELECT MODE:")
        print("1. Text-only troubleshooting")
        print("2. Troubleshoot with screenshot")
        print("3. Run test suite")
        print("4. Show engine status")
        print("5. Reset engine")
        print("6. Exit")
        print("="*60)
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            issue = input("\n📝 Describe the issue: ").strip()
            if issue:
                result = engine.troubleshoot_text(issue)
                display_result(result)
        
        elif choice == '2':
            issue = input("\n📝 Describe the issue: ").strip()
            if not issue:
                print("❌ Issue description required")
                continue
            
            screenshot_path = input("📸 Path to screenshot: ").strip()
            if screenshot_path:
                result = engine.troubleshoot_with_screenshot(issue, screenshot_path)
                display_result(result)
        
        elif choice == '3':
            run_test_suite(engine)
        
        elif choice == '4':
            status = engine.get_status()
            print("\n📊 Engine Status:")
            print(json.dumps(status, indent=2))
        
        elif choice == '5':
            engine.reset()
            print("\n🔄 Engine reset. Reinitializing...")
            engine.initialize()
        
        elif choice == '6':
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()