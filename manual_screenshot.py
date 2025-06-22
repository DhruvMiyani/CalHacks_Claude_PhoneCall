#!/usr/bin/env python3
"""
Manual screenshot script using macOS built-in screenshot tool
"""

import os
import time
import shutil
import subprocess

def switch_template(style_name, source_path):
    """Switch to a specific template"""
    if os.path.exists(source_path):
        shutil.copy(source_path, "templates/index.html")
        print(f"Switched to {style_name} style")
        return True
    else:
        print(f"Template not found: {source_path}")
        return False

def take_screenshot(style_name):
    """Take screenshot using macOS screencapture"""
    screenshot_path = f"screenshots/{style_name}.png"
    
    print(f"\n📸 Ready to take screenshot for {style_name.upper()} style")
    print("1. Open http://127.0.0.1:5000 in your browser")
    print("2. Fill in 'New York' and 'London' as sample cities")
    print("3. Press Enter when ready to take screenshot...")
    
    input("Press Enter to continue...")
    
    # Take screenshot of entire screen
    subprocess.run([
        "screencapture", 
        "-x",  # No sound
        "-i",  # Interactive selection
        screenshot_path
    ])
    
    print(f"Screenshot saved: {screenshot_path}")

def main():
    """Main function"""
    styles = [
        ("default", "templates/index.html"),
        ("modern", "templates/styles/modern.html"),
        ("dark", "templates/styles/dark.html"),
        ("vibrant", "templates/styles/vibrant.html"),
        ("corporate", "templates/styles/corporate.html"),
        ("retro", "templates/styles/retro.html")
    ]
    
    # Backup current template
    if os.path.exists("templates/index.html"):
        shutil.copy("templates/index.html", "templates/index_backup.html")
        print("Backed up current template")
    
    print("🚀 Manual Screenshot Process")
    print("Make sure your Flask app is running at http://127.0.0.1:5000")
    
    try:
        for style_name, template_path in styles:
            if style_name != "default":
                if not switch_template(style_name, template_path):
                    continue
                
                # Give Flask time to reload
                time.sleep(2)
            
            take_screenshot(style_name)
    
    finally:
        # Restore original template
        if os.path.exists("templates/index_backup.html"):
            shutil.move("templates/index_backup.html", "templates/index.html")
            print("Restored original template")

if __name__ == "__main__":
    main()