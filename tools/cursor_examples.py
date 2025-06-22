#!/usr/bin/env python3
"""
Cursor Terminal Integration Examples
====================================

This script demonstrates how orchestration agents can interact with
the Cursor terminal chat window using the terminal response tools.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path to import tools
sys.path.append(str(Path(__file__).parent.parent))

from tools import (
    send_terminal_response,
    send_style_showcase,
    send_progress_update,
    create_interactive_agent,
    interactive_style_switch,
    interactive_screenshot_generation
)


def example_basic_responses():
    """Example of basic terminal responses"""
    print("🔗 BASIC TERMINAL RESPONSES")
    print("=" * 40)
    
    # Different message types
    send_terminal_response("Starting orchestration examples...", "info")
    time.sleep(1)
    
    send_terminal_response("Task completed successfully!", "success")
    time.sleep(1)
    
    send_terminal_response("Warning: This is a demo warning", "warning")
    time.sleep(1)
    
    send_terminal_response("Error: This is a demo error", "error")
    time.sleep(1)
    
    send_terminal_response("Debug info: Checking system status", "debug")
    time.sleep(1)


def example_progress_updates():
    """Example of progress updates"""
    print("\n📊 PROGRESS UPDATES")
    print("=" * 40)
    
    task_name = "Processing Frontend Styles"
    total_steps = 6
    
    for i in range(total_steps + 1):
        send_progress_update(
            task_name, 
            i, 
            total_steps, 
            f"Processing step {i} of {total_steps}"
        )
        time.sleep(0.5)


def example_style_showcase():
    """Example of style showcase"""
    print("\n🎨 STYLE SHOWCASE")
    print("=" * 40)
    
    send_terminal_response("Displaying available frontend styles...", "info")
    time.sleep(1)
    
    send_style_showcase()


def example_interactive_operations():
    """Example of interactive operations with feedback"""
    print("\n⚡ INTERACTIVE OPERATIONS")
    print("=" * 40)
    
    # Interactive style switching
    send_terminal_response("Demonstrating interactive style switching...", "info")
    time.sleep(1)
    
    result = interactive_style_switch("modern")
    time.sleep(2)
    
    # Switch back
    result = interactive_style_switch("dark")
    time.sleep(2)


def example_interactive_agent():
    """Example of using the interactive agent"""
    print("\n🤖 INTERACTIVE AGENT")
    print("=" * 40)
    
    # Create an agent
    agent = create_interactive_agent()
    time.sleep(2)
    
    # Simulate user commands
    commands = [
        ("styles", []),
        ("switch", ["retro"]),
        ("switch", ["default"]),
        ("help", [])
    ]
    
    for command, args in commands:
        send_terminal_response(f"Simulating command: {command} {' '.join(args)}", "debug")
        agent.handle_user_command(command, args)
        time.sleep(2)


def example_claude_integration():
    """
    Example showing how Claude AI might use these tools
    """
    print("\n🧠 CLAUDE AI INTEGRATION EXAMPLE")
    print("=" * 40)
    
    def simulate_claude_response(user_message):
        """Simulate how Claude might respond to user messages"""
        user_message = user_message.lower()
        
        send_terminal_response(f"Claude received: '{user_message}'", "debug")
        time.sleep(1)
        
        if "switch to dark mode" in user_message:
            send_terminal_response("I'll switch the frontend to dark mode for you.", "info")
            result = interactive_style_switch("dark")
            return result
        
        elif "show me the styles" in user_message:
            send_terminal_response("Here are all the available frontend styles:", "info")
            send_style_showcase()
            return {"success": True, "message": "Styles displayed"}
        
        elif "take screenshots" in user_message:
            send_terminal_response("I'll generate screenshots of all frontend styles.", "info")
            result = interactive_screenshot_generation()
            return result
        
        elif "reset to default" in user_message:
            send_terminal_response("I'll reset the frontend to the default style.", "info")
            result = interactive_style_switch("default")
            return result
        
        else:
            send_terminal_response("I'm not sure how to help with that request.", "warning")
            return {"success": False, "error": "Unknown request"}
    
    # Simulate user interactions
    user_messages = [
        "Can you show me the styles?",
        "Please switch to dark mode",
        "Take screenshots of all styles",
        "Reset to default please"
    ]
    
    for message in user_messages:
        send_terminal_response(f"User: {message}", "info")
        result = simulate_claude_response(message)
        time.sleep(3)


def example_error_handling():
    """Example of error handling with terminal feedback"""
    print("\n🚨 ERROR HANDLING")
    print("=" * 40)
    
    # Test with invalid style
    send_terminal_response("Testing error handling with invalid style...", "info")
    time.sleep(1)
    
    result = interactive_style_switch("nonexistent_style")
    time.sleep(2)
    
    # Test with valid style to show recovery
    send_terminal_response("Recovering with valid style...", "info")
    result = interactive_style_switch("modern")


def example_session_workflow():
    """Example of a complete session workflow"""
    print("\n🔄 COMPLETE SESSION WORKFLOW")
    print("=" * 40)
    
    agent = create_interactive_agent()
    time.sleep(1)
    
    # Simulate a complete workflow
    workflow_steps = [
        ("Show current styles", lambda: agent.show_styles()),
        ("Switch to vibrant style", lambda: agent.switch_style("vibrant")),
        ("Generate screenshots", lambda: agent.generate_screenshots("vibrant")),
        ("Switch to corporate style", lambda: agent.switch_style("corporate")),
        ("Reset to default", lambda: agent.reset_to_default()),
        ("Show session summary", lambda: send_terminal_response(
            f"Session Summary: {agent.get_session_summary()}", "result"
        ))
    ]
    
    for step_name, step_func in workflow_steps:
        send_terminal_response(f"Step: {step_name}", "task")
        time.sleep(1)
        step_func()
        time.sleep(2)


def main():
    """Run all examples"""
    print("🛠️ CURSOR TERMINAL INTEGRATION EXAMPLES")
    print("=========================================")
    print("This demonstrates how orchestration agents can interact with Cursor terminal\n")
    
    try:
        # Run examples
        example_basic_responses()
        example_progress_updates()
        example_style_showcase()
        example_interactive_operations()
        example_interactive_agent()
        example_claude_integration()
        example_error_handling()
        example_session_workflow()
        
        # Final message
        send_terminal_response(
            "🎉 All examples completed! These tools enable rich interaction between "
            "orchestration agents and the Cursor terminal chat window.", 
            "success"
        )
        
    except KeyboardInterrupt:
        send_terminal_response("Examples interrupted by user", "warning")
    except Exception as e:
        send_terminal_response(f"Error during examples: {str(e)}", "error")


if __name__ == "__main__":
    main()