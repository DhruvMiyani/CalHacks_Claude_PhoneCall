#!/usr/bin/env python3
"""
Create demo screenshots with filled forms and results
"""

import os
import shutil
import time
import requests
from pathlib import Path

def create_demo_html(style_path, style_name):
    """Create demo HTML with pre-filled form and results"""
    
    # Read the template
    with open(style_path, 'r') as f:
        html_content = f.read()
    
    # Add demo data with JavaScript
    demo_script = '''
    <script>
        window.addEventListener('load', function() {
            // Fill the form
            document.getElementById('cityA').value = 'New York';
            document.getElementById('cityB').value = 'London';
            
            // Show results after a delay
            setTimeout(function() {
                showResult({
                    city_a: "New York",
                    city_b: "London", 
                    time_a: "2025-06-21 16:45:38 EDT",
                    time_b: "2025-06-21 21:45:38 BST",
                    timezone_a: "America/New_York",
                    timezone_b: "Europe/London"
                });
            }, 1000);
        });
    </script>
    '''
    
    # Insert the demo script before closing body tag
    html_content = html_content.replace('</body>', demo_script + '</body>')
    
    # Write demo HTML file
    demo_path = f"screenshots/demo_{style_name}.html"
    with open(demo_path, 'w') as f:
        f.write(html_content)
    
    return demo_path

def create_demo_screenshots():
    """Create demo screenshots with results"""
    styles = [
        ("default", "templates/index.html"),
        ("modern", "templates/styles/modern.html"),
        ("dark", "templates/styles/dark.html"),
        ("vibrant", "templates/styles/vibrant.html"),
        ("corporate", "templates/styles/corporate.html"),
        ("retro", "templates/styles/retro.html")
    ]
    
    try:
        import html2image
        hti = html2image.Html2Image()
        hti.size = (1200, 1000)  # Taller to show results
        
        for style_name, template_path in styles:
            print(f"📸 Creating demo screenshot for {style_name.upper()} style...")
            
            # Create demo HTML with filled form and results
            demo_path = create_demo_html(template_path, style_name)
            
            # Create screenshot
            hti.screenshot(
                html_file=demo_path,
                save_as=f"{style_name}_demo.png",
                size=(1200, 1000)
            )
            
            print(f"✅ Created {style_name}_demo.png")
        
        # Move screenshots to screenshots directory
        os.system("mv *_demo.png screenshots/ 2>/dev/null")
        
        print(f"\n🎉 Demo screenshots created!")
        print(f"📁 Check screenshots/ directory for both empty and demo versions")
        
    except ImportError:
        print("❌ html2image not available for demo screenshots")

if __name__ == "__main__":
    create_demo_screenshots()