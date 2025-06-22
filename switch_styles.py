#!/usr/bin/env python3
"""
Simple script to switch between styles for manual screenshot taking
"""

import os
import shutil
import time

def backup_template():
    """Backup current template"""
    if os.path.exists("templates/index.html"):
        shutil.copy("templates/index.html", "templates/index_backup.html")
        print("✅ Backed up current template")

def restore_template():
    """Restore original template"""
    if os.path.exists("templates/index_backup.html"):
        shutil.move("templates/index_backup.html", "templates/index.html")
        print("✅ Restored original template")

def switch_to_style(style_name, template_path):
    """Switch to a specific style"""
    if os.path.exists(template_path):
        shutil.copy(template_path, "templates/index.html")
        print(f"🎨 Switched to {style_name.upper()} style")
        print(f"🌐 Refresh http://127.0.0.1:5000 to see changes")
        return True
    else:
        print(f"❌ Template not found: {template_path}")
        return False

def main():
    """Main function"""
    styles = [
        ("current", "templates/index.html", "Current/Default Style"),
        ("modern", "templates/styles/modern.html", "Modern/Minimalist - Purple gradient with glass effects"),
        ("dark", "templates/styles/dark.html", "Dark Mode - Neon colors with dark background"),
        ("vibrant", "templates/styles/vibrant.html", "Colorful/Vibrant - Rainbow gradients and animations"),
        ("corporate", "templates/styles/corporate.html", "Professional/Corporate - Clean business design"),
        ("retro", "templates/styles/retro.html", "Retro/Vintage - 80s terminal style with scanlines")
    ]
    
    print("🎨 TIMEZONE CONVERTER STYLE SWITCHER")
    print("="*50)
    print("Make sure your Flask app is running at: http://127.0.0.1:5000")
    print()
    
    # Backup current template
    backup_template()
    
    try:
        for i, (style_id, template_path, description) in enumerate(styles, 1):
            print(f"\n{i}. {description}")
            print("-" * 40)
            
            if style_id == "current":
                print("📱 This is your current template")
            else:
                if switch_to_style(style_id, template_path):
                    print("⏳ Waiting for 3 seconds for Flask to reload...")
                    time.sleep(3)
            
            print("\n📸 READY FOR SCREENSHOT!")
            print("1. Go to http://127.0.0.1:5000")
            print("2. Fill in 'New York' and 'London'")
            print("3. Take a screenshot and save as:")
            print(f"   screenshots/{style_id}_form.png (before conversion)")
            print("4. Click Convert, then take another screenshot:")
            print(f"   screenshots/{style_id}_result.png (after conversion)")
            
            input("\n⏳ Press Enter when you've taken both screenshots...")
            print(f"✅ Completed {style_id} style")
    
    except KeyboardInterrupt:
        print("\n⏹️ Process interrupted")
    
    finally:
        # Restore original template
        restore_template()
        print(f"\n🎉 All styles processed!")
        print("📁 Your screenshots should be in the screenshots/ directory")

if __name__ == "__main__":
    main()