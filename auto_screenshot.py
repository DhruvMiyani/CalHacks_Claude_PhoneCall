#!/usr/bin/env python3
"""
Automated screenshot script using pyautogui and template switching
"""

import os
import time
import shutil
import pyautogui
import webbrowser
from pathlib import Path

class AutoScreenshotter:
    def __init__(self):
        self.screenshot_dir = "screenshots"
        self.styles = [
            ("current", "templates/index.html"),
            ("modern", "templates/styles/modern.html"),
            ("dark", "templates/styles/dark.html"),
            ("vibrant", "templates/styles/vibrant.html"),
            ("corporate", "templates/styles/corporate.html"),
            ("retro", "templates/styles/retro.html")
        ]
        
        # Create screenshots directory
        Path(self.screenshot_dir).mkdir(exist_ok=True)
        
        # Disable pyautogui failsafe
        pyautogui.FAILSAFE = False
        
    def backup_template(self):
        """Backup current template"""
        if os.path.exists("templates/index.html"):
            shutil.copy("templates/index.html", "templates/index_backup.html")
            print("✅ Backed up current template")
    
    def restore_template(self):
        """Restore original template"""
        if os.path.exists("templates/index_backup.html"):
            shutil.move("templates/index_backup.html", "templates/index.html")
            print("✅ Restored original template")
    
    def switch_template(self, style_name, source_path):
        """Switch to specific template"""
        if style_name == "current":
            print(f"📱 Using current template")
            return True
            
        if os.path.exists(source_path):
            shutil.copy(source_path, "templates/index.html")
            print(f"📱 Switched to {style_name} style")
            return True
        else:
            print(f"❌ Template not found: {source_path}")
            return False
    
    def take_browser_screenshot(self, style_name):
        """Take screenshot of browser window"""
        try:
            # Give time for page to load
            time.sleep(3)
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_path = f"{self.screenshot_dir}/{style_name}.png"
            screenshot.save(screenshot_path)
            
            print(f"📸 Screenshot saved: {screenshot_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error taking screenshot: {e}")
            return False
    
    def run_automated_screenshots(self):
        """Run automated screenshot process"""
        print("🚀 Starting automated screenshot process...")
        print("📝 Make sure:")
        print("   1. Flask app is running at http://127.0.0.1:5000")
        print("   2. Close other browser windows/tabs")
        print("   3. Don't move mouse during screenshot process")
        
        input("\n⏳ Press Enter when ready...")
        
        # Backup current template
        self.backup_template()
        
        # Open browser to localhost
        print("🌐 Opening browser...")
        webbrowser.open("http://127.0.0.1:5000")
        time.sleep(5)  # Wait for browser to load
        
        try:
            for style_name, template_path in self.styles:
                print(f"\n--- Processing {style_name.upper()} style ---")
                
                # Switch template
                if not self.switch_template(style_name, template_path):
                    continue
                
                # Refresh browser
                print("🔄 Refreshing browser...")
                pyautogui.keyDown('cmd')
                pyautogui.press('r')
                pyautogui.keyUp('cmd')
                time.sleep(3)
                
                # Fill form with sample data
                print("📝 Filling form...")
                
                # Click on first input and clear it
                pyautogui.click(600, 400)  # Approximate location of first input
                time.sleep(0.5)
                pyautogui.keyDown('cmd')
                pyautogui.press('a')
                pyautogui.keyUp('cmd')
                pyautogui.write("New York")
                
                # Click on second input
                pyautogui.press('tab')
                time.sleep(0.5)
                pyautogui.write("London")
                
                # Take screenshot of form
                self.take_browser_screenshot(f"{style_name}_form")
                
                # Click convert button
                print("🔄 Converting timezone...")
                pyautogui.press('tab')
                pyautogui.press('tab')
                pyautogui.press('enter')
                time.sleep(5)  # Wait for API response
                
                # Take screenshot of results
                self.take_browser_screenshot(f"{style_name}_result")
                
                print(f"✅ Completed {style_name} style")
        
        except KeyboardInterrupt:
            print("\n⏹️ Screenshot process interrupted")
        
        except Exception as e:
            print(f"❌ Error during automation: {e}")
        
        finally:
            # Restore original template
            self.restore_template()
            print(f"\n🎉 Screenshot process completed!")
            print(f"📁 Screenshots saved in: {self.screenshot_dir}/")

def main():
    """Main function"""
    screenshotter = AutoScreenshotter()
    screenshotter.run_automated_screenshots()

if __name__ == "__main__":
    main()