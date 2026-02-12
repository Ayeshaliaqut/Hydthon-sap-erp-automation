import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError


def delete_old_screenshots(screenshots_dir):
    """Delete all existing screenshots in the directory"""
    if not screenshots_dir.exists():
        return
    
    # Get all screenshot files
    screenshot_files = list(screenshots_dir.glob('erp_*.png'))
    
    if screenshot_files:
        print(f"\n{'='*60}")
        print(f"Found {len(screenshot_files)} existing screenshot(s)")
        print(f"{'='*60}")
        
        for screenshot in screenshot_files:
            try:
                print(f"Deleting: {screenshot.name}")
                screenshot.unlink()
                print(f"✓ Deleted")
            except Exception as e:
                print(f"✗ Failed to delete {screenshot.name}: {e}")
        
        print(f"\n✓ All old screenshots deleted")
        print(f"{'='*60}\n")
    else:
        print("\nNo existing screenshots found\n")


def close_popup_if_exists(page):
    """Close the 'Explore updated home page' popup if it appears"""
    try:
        # Wait a bit for popup to appear
        time.sleep(2)
        
        # Try to find the close button (X button) in the popup
        close_button_selectors = [
            'button[aria-label="Close"]',
            'button.close',
            'button:has-text("×")',
            '[class*="close"]',
            'button[title="Close"]',
            '[aria-label*="close" i]'
        ]
        
        for selector in close_button_selectors:
            try:
                close_btn = page.locator(selector).first
                if close_btn.is_visible(timeout=2000):
                    print(f"✓ Found popup close button: {selector}")
                    close_btn.click()
                    time.sleep(1)
                    print("✓ Popup closed")
                    return True
            except:
                continue
        
        # If we can't find a close button, try pressing Escape
        print("Trying Escape key to close popup...")
        page.keyboard.press('Escape')
        time.sleep(1)
        print("✓ Pressed Escape")
        return True
        
    except Exception as e:
        print(f"No popup found or already closed: {e}")
        return False


def login_to_erp(max_retries=3):
   
    # Load env variables
    load_dotenv()
    
    # Get credentials from environment
    username = os.getenv('ERP_USERNAME')
    password = os.getenv('ERP_PASSWORD')
    
    # Validate if they are loaded 
    if not username or not password:
        raise ValueError("Missing credentials. Please check your .env file for ERP_USERNAME and ERP_PASSWORD")
    
    print(f"Username loaded: Yes")
    print(f"Password loaded: Yes")
    
    # Create screenshots dir
    screenshots_dir = Path('screenshots')
    screenshots_dir.mkdir(exist_ok=True)
    
    # Delete old screenshots first
    delete_old_screenshots(screenshots_dir)
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n{'='*60}")
            print(f"Attempt {attempt} of {max_retries}")
            print(f"{'='*60}\n")
            
            with sync_playwright() as p:
                # Launch browser in headed mode
                browser = p.chromium.launch(
                    headless=False,
                    args=['--start-maximized']
                )
                
                # Create new browser context (this will use stored cookies/session)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    no_viewport=False
                )
                page = context.new_page()
                
                # Increase default timeout
                page.set_default_timeout(60000)
                
                print("Navigating to login page...")
                try:
                    page.goto(
                        'https://hcm-us20-sales.hr.cloud.sap/login?company=SFCPART002468',
                        wait_until='load',
                        timeout=60000
                    )
                except PlaywrightTimeoutError:
                    print("Warning: Page load timeout, but continuing...")
                except PlaywrightError as e:
                    if "ERR_NAME_NOT_RESOLVED" in str(e):
                        print("DNS Error: Cannot resolve hostname. Check your internet/VPN connection.")
                        browser.close()
                        if attempt < max_retries:
                            print(f"Retrying in 5 seconds...")
                            time.sleep(5)
                            continue
                        else:
                            raise
                    raise
                
                time.sleep(3)
                
                # Check if already logged in
                current_url = page.url
                print(f"Current URL after navigation: {current_url}")
                
                # Check if we're still on the login page or already logged in
                is_on_login_page = 'login' in current_url.lower()
                
                if is_on_login_page:
                    print("\n Login page detected - performing login...")
                    
                    # Check if login form exists
                    try:
                        username_field = page.locator('#j_username')
                        if username_field.count() > 0:
                            print("Entering credentials...")
                            
                            # Fill username
                            username_field.wait_for(state='visible', timeout=15000)
                            username_field.click()
                            username_field.fill(username)
                            print("Username entered")
                            
                            time.sleep(1)
                            
                            # Fill password
                            password_field = page.locator('#j_password')
                            password_field.wait_for(state='visible', timeout=15000)
                            password_field.click()
                            password_field.fill(password)
                            print("Password entered")
                            
                            time.sleep(1)
                            
                            # Submit login
                            print("Submitting login form...")
                            password_field.press('Enter')
                            
                            # Wait for navigation after login
                            print("Waiting for post-login redirect...")
                            try:
                                page.wait_for_url(lambda url: 'login' not in url.lower(), timeout=30000)
                                print(" Login successful - redirected from login page")
                            except PlaywrightTimeoutError:
                                print(" Warning: Still on login page after submission")
                        else:
                            print(" Login form not found - may already be authenticated")
                    
                    except Exception as e:
                        print(f"Error during login: {e}")
                        # Continue anyway to try capturing screenshot
                
                else:
                    print("\n Already logged in - skipping login process")
                
                # Wait for page to fully load
                print("\nWaiting for page content to load...")
                time.sleep(5)
                
                # Close popup if it exists
                print("\nChecking for popups...")
                close_popup_if_exists(page)
                
                try:
                    page.wait_for_load_state('networkidle', timeout=20000)
                    print("✓ Network idle")
                except PlaywrightTimeoutError:
                    print("Network not fully idle, continuing...")
                
                try:
                    page.wait_for_load_state('domcontentloaded', timeout=15000)
                    print("✓ DOM loaded")
                except PlaywrightTimeoutError:
                    print("DOM load incomplete, continuing...")
                
                # Additional wait for dynamic content
                time.sleep(3)
                
                # Scroll to load all lazy content
                print("\nScrolling to load all content...")
                try:
                    # Scroll to bottom
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
                    
                    # Scroll to top
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(2)
                    
                    page_height = page.evaluate("document.body.scrollHeight")
                    print(f"Page height: {page_height}px")
                except Exception as e:
                    print(f"Could not scroll: {e}")
                
                # Display current state
                current_url = page.url
                page_title = page.title()
                print(f"\nCurrent URL: {current_url}")
                print(f"Page title: {page_title}")
                
                # Generate timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_filename = f'erp_fullpage_test.png'
                screenshot_path = screenshots_dir / screenshot_filename
                
                print("\n Capturing full-page screenshot...")
                
                # Capture full page screenshot
                page.screenshot(
                    path=str(screenshot_path),
                    full_page=True,
                    animations='disabled'
                )
                print(f" Screenshot saved: {screenshot_path.absolute()}")
                
                file_size = screenshot_path.stat().st_size / 1024
                print(f"  File size: {file_size:.2f} KB")
                
                # Viewport screenshot for comparison
                viewport_screenshot = screenshots_dir / f'erp_viewport_test.png'
                page.screenshot(
                    path=str(viewport_screenshot),
                    full_page=False
                )
                print(f" Viewport screenshot: {viewport_screenshot.absolute()}")
                
                # Keep browser open
                print(f"\n{'='*60}")
                print("Browser open for 20 seconds - verify content")
                print(f"{'='*60}\n")
                time.sleep(20)
                
                browser.close()
                print(" Automation completed successfully\n")
                return screenshot_path
                
        except PlaywrightTimeoutError as e:
            print(f"\nTimeout error on attempt {attempt}: {e}")
            if attempt < max_retries:
                print(f"Retrying in 5 seconds...")
                time.sleep(5)
            else:
                raise
                
        except PlaywrightError as e:
            print(f"\nPlaywright error on attempt {attempt}: {e}")
            if attempt < max_retries:
                print(f"Retrying in 5 seconds...")
                time.sleep(5)
            else:
                raise
                
        except Exception as e:
            print(f"\nUnexpected error on attempt {attempt}: {e}")
            if attempt < max_retries:
                print(f"Retrying in 5 seconds...")
                time.sleep(5)
            else:
                raise


if __name__ == '__main__':
    try:
        screenshot_path = login_to_erp(max_retries=3)
        print(f"\n{'='*60}")
        print(f"Final screenshot path: {screenshot_path}")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"FINAL ERROR: All attempts failed")
        print(f"{'='*60}")
        print(f"Error: {e}")