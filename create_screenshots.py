#!/usr/bin/env python3
"""
Create screenshots using HTML to image conversion
"""

import os
import shutil
import time
import html2image
from pathlib import Path

class ScreenshotGenerator:
    def __init__(self):
        self.screenshot_dir = "screenshots"
        self.styles = [
            ("default", "templates/index.html"),
            ("modern", "templates/styles/modern.html"),
            ("dark", "templates/styles/dark.html"),
            ("vibrant", "templates/styles/vibrant.html"),
            ("corporate", "templates/styles/corporate.html"),
            ("retro", "templates/styles/retro.html")
        ]
        
        # Create screenshots directory
        Path(self.screenshot_dir).mkdir(exist_ok=True)
        
        # Initialize html2image
        self.hti = html2image.Html2Image()
        self.hti.size = (1200, 800)
    
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
        if os.path.exists(source_path):
            shutil.copy(source_path, "templates/index.html")
            print(f"🎨 Switched to {style_name} style")
            return True
        else:
            print(f"❌ Template not found: {source_path}")
            return False
    
    def create_screenshot(self, style_name):
        """Create screenshot of the current style"""
        try:
            # Wait for Flask to reload
            time.sleep(2)
            
            # Create screenshot from localhost
            screenshot_path = f"{self.screenshot_dir}/{style_name}.png"
            self.hti.screenshot(
                url="http://127.0.0.1:5000",
                save_as=f"{style_name}.png",
                size=(1200, 800)
            )
            
            print(f"📸 Screenshot created: {screenshot_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating screenshot: {e}")
            return False
    
    def generate_all_screenshots(self):
        """Generate screenshots for all styles"""
        print("🚀 Starting screenshot generation...")
        print("📝 Make sure Flask app is running at http://127.0.0.1:5000")
        
        # Backup current template
        self.backup_template()
        
        try:
            for style_name, template_path in self.styles:
                print(f"\n--- Processing {style_name.upper()} style ---")
                
                # Switch template (skip for default)
                if style_name != "default":
                    if not self.switch_template(style_name, template_path):
                        continue
                
                # Create screenshot
                self.create_screenshot(style_name)
                print(f"✅ Completed {style_name} style")
        
        except KeyboardInterrupt:
            print("\n⏹️ Process interrupted")
        
        except Exception as e:
            print(f"❌ Error during generation: {e}")
        
        finally:
            # Restore original template
            self.restore_template()
            print(f"\n🎉 Screenshot generation completed!")
            print(f"📁 Screenshots saved in: {self.screenshot_dir}/")

def main():
    """Main function"""
    generator = ScreenshotGenerator()
    generator.generate_all_screenshots()

if __name__ == "__main__":
    main()