#!/usr/bin/env python3
"""
Screenshot automation script for timezone converter styles
Takes screenshots of each style running on localhost
"""

import os
import time
import subprocess
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class StyleScreenshotter:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5000"
        self.screenshot_dir = "screenshots"
        self.styles = [
            ("default", "templates/index.html"),
            ("modern", "templates/styles/modern.html"),
            ("dark", "templates/styles/dark.html"),
            ("vibrant", "templates/styles/vibrant.html"),
            ("corporate", "templates/styles/corporate.html"),
            ("retro", "templates/styles/retro.html")
        ]
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1200,800")
        chrome_options.add_argument("--disable-gpu")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            return False
    
    def backup_current_template(self):
        """Backup the current index.html"""
        if os.path.exists("templates/index.html"):
            shutil.copy("templates/index.html", "templates/index_backup.html")
            print("Backed up current template")
    
    def restore_template(self):
        """Restore the original template"""
        if os.path.exists("templates/index_backup.html"):
            shutil.move("templates/index_backup.html", "templates/index.html")
            print("Restored original template")
    
    def switch_template(self, source_path):
        """Switch to a specific template"""
        if os.path.exists(source_path):
            shutil.copy(source_path, "templates/index.html")
            return True
        return False
    
    def take_screenshot(self, style_name):
        """Take screenshot of the current style"""
        try:
            # Load the page
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).wait(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            
            # Fill in sample data
            city_a_input = self.driver.find_element(By.ID, "cityA")
            city_b_input = self.driver.find_element(By.ID, "cityB")
            
            city_a_input.clear()
            city_a_input.send_keys("New York")
            
            city_b_input.clear()
            city_b_input.send_keys("London")
            
            # Take screenshot before conversion
            screenshot_path = f"{self.screenshot_dir}/{style_name}_form.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")
            
            # Click convert button
            convert_btn = self.driver.find_element(By.ID, "convertBtn")
            convert_btn.click()
            
            # Wait for results
            try:
                WebDriverWait(self.driver, 15).wait(
                    EC.visibility_of_element_located((By.ID, "result"))
                )
                
                # Take screenshot with results
                result_screenshot_path = f"{self.screenshot_dir}/{style_name}_result.png"
                self.driver.save_screenshot(result_screenshot_path)
                print(f"Result screenshot saved: {result_screenshot_path}")
                
            except Exception as e:
                print(f"Could not capture result for {style_name}: {e}")
            
            return True
            
        except Exception as e:
            print(f"Error taking screenshot for {style_name}: {e}")
            return False
    
    def run_screenshots(self):
        """Run the complete screenshot process"""
        print("Starting screenshot automation...")
        
        # Setup driver
        if not self.setup_driver():
            print("Failed to setup Chrome driver")
            return False
        
        # Backup current template
        self.backup_current_template()
        
        try:
            # Take screenshots for each style
            for style_name, template_path in self.styles:
                print(f"\n--- Processing {style_name} style ---")
                
                # Switch template (skip for default)
                if style_name != "default":
                    if not self.switch_template(template_path):
                        print(f"Could not switch to {template_path}")
                        continue
                
                # Wait a moment for Flask to reload
                time.sleep(2)
                
                # Take screenshot
                self.take_screenshot(style_name)
                
                print(f"Completed {style_name} style")
            
        finally:
            # Cleanup
            if self.driver:
                self.driver.quit()
            
            # Restore original template
            self.restore_template()
            
        print(f"\nScreenshot automation completed!")
        print(f"Screenshots saved in: {self.screenshot_dir}/")
        
        return True

def main():
    """Main function"""
    screenshotter = StyleScreenshotter()
    screenshotter.run_screenshots()

if __name__ == "__main__":
    main()