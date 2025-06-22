#!/usr/bin/env python3
"""
Example usage of orchestration tools for timezone converter
===========================================================

This script demonstrates how orchestration agents can use the tools
to manage frontend styles and generate screenshots.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path to import tools
sys.path.append(str(Path(__file__).parent.parent))

from tools import (
    switch_frontend_style,
    generate_style_screenshot,
    generate_all_screenshots,
    get_available_styles,
    reset_to_default_style
)


def print_result(operation_name, result):
    """Pretty print operation result"""
    print(f"\n{'='*50}")
    print(f"OPERATION: {operation_name}")
    print(f"{'='*50}")
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    
    if 'current_style' in result:
        print(f"Current Style: {result['current_style']}")
    
    if 'style_info' in result and result['style_info']:
        style_info = result['style_info']
        print(f"Style Info:")
        print(f"  - Display Name: {style_info['display_name']}")
        print(f"  - Description: {style_info['description']}")
        print(f"  - Color Scheme: {style_info['color_scheme']}")
    
    if 'total_files' in result:
        print(f"Files Generated: {result['total_files']}")
    
    if 'screenshots' in result:
        print("Screenshots:")
        for screenshot_type, info in result['screenshots'].items():
            status = "✅" if info['success'] else "❌"
            print(f"  {status} {screenshot_type}: {info.get('file_path', 'N/A')}")


def example_orchestration_workflow():
    """
    Example workflow that an orchestration agent might follow
    """
    print("🤖 ORCHESTRATION AGENT WORKFLOW EXAMPLE")
    print("This demonstrates how Claude AI or other agents can use these tools")
    
    # 1. Get available styles
    print("\n1️⃣ Getting available styles...")
    styles_result = get_available_styles()
    print_result("Get Available Styles", styles_result)
    
    if styles_result['success']:
        print("\nAvailable Styles:")
        for name, info in styles_result['styles'].items():
            current = " (CURRENT)" if info['is_current'] else ""
            exists = "✅" if info['template_exists'] else "❌"
            print(f"  {exists} {name}: {info['display_name']}{current}")
    
    # 2. Switch to dark mode
    print("\n2️⃣ Switching to dark mode...")
    switch_result = switch_frontend_style("dark")
    print_result("Switch to Dark Mode", switch_result)
    
    # 3. Generate screenshot for current style
    print("\n3️⃣ Generating screenshots for dark mode...")
    screenshot_result = generate_style_screenshot("dark", include_demo=True)
    print_result("Generate Dark Mode Screenshots", screenshot_result)
    
    # 4. Switch to vibrant style
    print("\n4️⃣ Switching to vibrant style...")
    vibrant_result = switch_frontend_style("vibrant")
    print_result("Switch to Vibrant Style", vibrant_result)
    
    # 5. Generate all screenshots (this will restore original style)
    print("\n5️⃣ Generating all screenshots...")
    all_screenshots_result = generate_all_screenshots(include_demo=True)
    print_result("Generate All Screenshots", all_screenshots_result)
    
    if all_screenshots_result['success']:
        print(f"\nScreenshot Summary:")
        print(f"  - Total Files: {all_screenshots_result['total_files']}")
        print(f"  - Successful Styles: {', '.join(all_screenshots_result['successful_styles'])}")
        if all_screenshots_result['failed_styles']:
            print(f"  - Failed Styles: {', '.join(all_screenshots_result['failed_styles'])}")
    
    # 6. Reset to default
    print("\n6️⃣ Resetting to default style...")
    reset_result = reset_to_default_style()
    print_result("Reset to Default", reset_result)
    
    print(f"\n🎉 WORKFLOW COMPLETED!")
    print(f"This demonstrates how an orchestration agent can:")
    print(f"  - Query available styles")
    print(f"  - Switch between styles dynamically")
    print(f"  - Generate documentation screenshots")
    print(f"  - Handle errors gracefully")
    print(f"  - Restore original state")


def example_claude_integration():
    """
    Example of how Claude AI might integrate these tools
    """
    print("\n🧠 CLAUDE AI INTEGRATION EXAMPLE")
    
    def handle_user_request(user_message):
        """Simulated Claude AI request handler"""
        user_message = user_message.lower()
        
        if "switch to dark mode" in user_message or "dark theme" in user_message:
            return switch_frontend_style("dark")
        
        elif "switch to modern" in user_message or "modern style" in user_message:
            return switch_frontend_style("modern")
        
        elif "take screenshots" in user_message or "generate screenshots" in user_message:
            return generate_all_screenshots(include_demo=True)
        
        elif "what styles are available" in user_message or "list styles" in user_message:
            return get_available_styles()
        
        elif "reset" in user_message or "default style" in user_message:
            return reset_to_default_style()
        
        else:
            return {
                "success": False,
                "message": "I don't understand that request",
                "error": "Unknown user intent"
            }
    
    # Simulate user requests
    test_requests = [
        "Can you switch to dark mode?",
        "What styles are available?", 
        "Please take screenshots of all styles",
        "Switch to modern style",
        "Reset to default please"
    ]
    
    for request in test_requests:
        print(f"\nUser: {request}")
        result = handle_user_request(request)
        
        if result['success']:
            print(f"Claude: ✅ {result['message']}")
        else:
            print(f"Claude: ❌ {result['message']}")


def example_error_handling():
    """
    Example of error handling in orchestration tools
    """
    print("\n🚨 ERROR HANDLING EXAMPLES")
    
    # Test invalid style
    print("\n❌ Testing invalid style...")
    invalid_result = switch_frontend_style("nonexistent_style")
    print_result("Invalid Style Test", invalid_result)
    
    # Test without Flask app running (this might fail)
    print("\n❌ Testing screenshot without Flask app...")
    screenshot_result = generate_style_screenshot("default", include_demo=False)
    if not screenshot_result['success']:
        print(f"Expected error: {screenshot_result['error']}")
    else:
        print("Screenshot succeeded (Flask app is running)")


if __name__ == "__main__":
    print("🛠️ ORCHESTRATION TOOLS EXAMPLES")
    print("=====================================")
    
    try:
        # Main workflow example
        example_orchestration_workflow()
        
        # Claude integration example
        example_claude_integration()
        
        # Error handling examples
        example_error_handling()
        
    except KeyboardInterrupt:
        print("\n⏹️ Examples interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    
    print(f"\n📚 For more information, see tools/README.md")