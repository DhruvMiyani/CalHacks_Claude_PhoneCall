"""
Interactive Agent Tools for Cursor Terminal Integration
======================================================

This module provides high-level functions that combine orchestration
capabilities with terminal response functionality for interactive agents.
"""

import sys
from typing import Dict, List, Optional, Any, Union
from .cursor_terminal import CursorTerminalResponder
from .orchestration_tools import (
    switch_frontend_style as _switch_style,
    generate_style_screenshot as _generate_screenshot,
    generate_all_screenshots as _generate_all_screenshots,
    get_available_styles as _get_styles,
    reset_to_default_style as _reset_style
)

# Global terminal responder instance
_terminal_responder = None

def get_terminal_responder() -> CursorTerminalResponder:
    """Get or create the global terminal responder instance"""
    global _terminal_responder
    if _terminal_responder is None:
        _terminal_responder = CursorTerminalResponder()
    return _terminal_responder


def send_terminal_response(content: str, message_type: str = "info", 
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Send a response to the Cursor terminal chat window
    
    Args:
        content: Message content to send
        message_type: Type of message (info, success, warning, error, etc.)
        metadata: Optional metadata to include
        
    Returns:
        True if message sent successfully, False otherwise
        
    Example:
        >>> send_terminal_response("Frontend style switched to dark mode!", "success")
        >>> send_terminal_response("Error: Invalid style name", "error")
    """
    responder = get_terminal_responder()
    return responder.send_message(content, message_type, metadata)


def send_style_showcase() -> bool:
    """
    Send a formatted showcase of all available styles to the terminal
    
    Returns:
        True if showcase sent successfully, False otherwise
        
    Example:
        >>> send_style_showcase()
        # Displays formatted list of all available styles with current status
    """
    try:
        styles_info = _get_styles()
        responder = get_terminal_responder()
        return responder.send_style_showcase(styles_info)
    except Exception as e:
        return send_terminal_response(f"Error getting styles: {str(e)}", "error")


def send_screenshot_report(screenshot_results: Dict[str, Any]) -> bool:
    """
    Send a formatted screenshot generation report to the terminal
    
    Args:
        screenshot_results: Results from screenshot generation functions
        
    Returns:
        True if report sent successfully, False otherwise
        
    Example:
        >>> result = generate_all_screenshots()
        >>> send_screenshot_report(result)
    """
    responder = get_terminal_responder()
    return responder.send_screenshot_report(screenshot_results)


def send_progress_update(task: str, progress: int, total: int, 
                        details: Optional[str] = None) -> bool:
    """
    Send a progress update to the terminal
    
    Args:
        task: Name of the task
        progress: Current progress (0-total)
        total: Total items/steps
        details: Optional additional details
        
    Returns:
        True if update sent successfully, False otherwise
        
    Example:
        >>> send_progress_update("Generating Screenshots", 3, 6, "Processing dark mode")
    """
    responder = get_terminal_responder()
    return responder.send_progress_update(task, progress, total, details)


def interactive_style_switch(style_name: str, send_response: bool = True) -> Dict[str, Any]:
    """
    Switch frontend style with interactive terminal feedback
    
    Args:
        style_name: Style to switch to
        send_response: Whether to send response to terminal (default: True)
        
    Returns:
        Dictionary with operation results
        
    Example:
        >>> interactive_style_switch("dark")
        # Switches to dark mode and sends success/error message to terminal
    """
    try:
        if send_response:
            send_terminal_response(f"🔄 Switching to {style_name} style...", "progress")
        
        result = _switch_style(style_name)
        
        if send_response:
            responder = get_terminal_responder()
            responder.send_formatted_response(result)
        
        return result
        
    except Exception as e:
        error_result = {
            "success": False,
            "message": f"Unexpected error during style switch: {str(e)}",
            "error": str(e)
        }
        
        if send_response:
            send_terminal_response(f"💥 Error switching style: {str(e)}", "error")
        
        return error_result


def interactive_screenshot_generation(style_name: Optional[str] = None, 
                                    include_demo: bool = True,
                                    send_progress: bool = True) -> Dict[str, Any]:
    """
    Generate screenshots with interactive terminal feedback
    
    Args:
        style_name: Specific style to screenshot (None for all styles)
        include_demo: Whether to include demo screenshots
        send_progress: Whether to send progress updates
        
    Returns:
        Dictionary with operation results
        
    Example:
        >>> interactive_screenshot_generation()  # All styles
        >>> interactive_screenshot_generation("dark")  # Just dark mode
    """
    try:
        if style_name:
            # Single style screenshot
            if send_progress:
                send_terminal_response(f"📸 Generating screenshots for {style_name} style...", "progress")
            
            result = _generate_screenshot(style_name, include_demo)
            
            if send_progress:
                send_screenshot_report(result)
        else:
            # All styles screenshots
            if send_progress:
                send_terminal_response("📸 Generating screenshots for all styles...", "progress")
            
            result = _generate_all_screenshots(include_demo)
            
            if send_progress:
                send_screenshot_report(result)
        
        return result
        
    except Exception as e:
        error_result = {
            "success": False,
            "message": f"Unexpected error during screenshot generation: {str(e)}",
            "error": str(e)
        }
        
        if send_progress:
            send_terminal_response(f"💥 Error generating screenshots: {str(e)}", "error")
        
        return error_result


def interactive_reset_to_default(send_response: bool = True) -> Dict[str, Any]:
    """
    Reset to default style with interactive terminal feedback
    
    Args:
        send_response: Whether to send response to terminal
        
    Returns:
        Dictionary with operation results
    """
    try:
        if send_response:
            send_terminal_response("🔄 Resetting to default style...", "progress")
        
        result = _reset_style()
        
        if send_response:
            responder = get_terminal_responder()
            responder.send_formatted_response(result)
        
        return result
        
    except Exception as e:
        error_result = {
            "success": False,
            "message": f"Unexpected error during reset: {str(e)}",
            "error": str(e)
        }
        
        if send_response:
            send_terminal_response(f"💥 Error resetting style: {str(e)}", "error")
        
        return error_result


class InteractiveAgent:
    """
    Interactive orchestration agent with terminal feedback
    
    This class combines all orchestration capabilities with automatic
    terminal feedback for interactive use in Cursor chat.
    """
    
    def __init__(self, auto_feedback: bool = True):
        """
        Initialize interactive agent
        
        Args:
            auto_feedback: Whether to automatically send terminal feedback
        """
        self.auto_feedback = auto_feedback
        self.responder = get_terminal_responder()
        self.session_actions = []
    
    def greet(self) -> None:
        """Send a greeting message to the terminal"""
        if self.auto_feedback:
            self.responder.send_message(
                "🤖 Interactive Orchestration Agent Ready!\n"
                "   Available commands: switch_style, generate_screenshots, show_styles, reset",
                "info"
            )
    
    def switch_style(self, style_name: str) -> Dict[str, Any]:
        """Switch style with automatic feedback"""
        result = interactive_style_switch(style_name, self.auto_feedback)
        self.session_actions.append(f"switch_style:{style_name}")
        return result
    
    def generate_screenshots(self, style_name: Optional[str] = None, 
                           include_demo: bool = True) -> Dict[str, Any]:
        """Generate screenshots with automatic feedback"""
        result = interactive_screenshot_generation(style_name, include_demo, self.auto_feedback)
        self.session_actions.append(f"generate_screenshots:{style_name or 'all'}")
        return result
    
    def show_styles(self) -> Dict[str, Any]:
        """Show available styles with automatic feedback"""
        if self.auto_feedback:
            send_style_showcase()
        
        result = _get_styles()
        self.session_actions.append("show_styles")
        return result
    
    def reset_to_default(self) -> Dict[str, Any]:
        """Reset to default style with automatic feedback"""
        result = interactive_reset_to_default(self.auto_feedback)
        self.session_actions.append("reset_to_default")
        return result
    
    def handle_user_command(self, command: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Handle user commands with automatic parsing and execution
        
        Args:
            command: Command to execute
            args: Optional arguments
            
        Returns:
            Dictionary with operation results
        """
        args = args or []
        command = command.lower().strip()
        
        try:
            if command in ["switch", "style", "switch_style"]:
                if not args:
                    return {"success": False, "error": "Style name required"}
                return self.switch_style(args[0])
            
            elif command in ["screenshot", "screenshots", "generate"]:
                style_name = args[0] if args else None
                return self.generate_screenshots(style_name)
            
            elif command in ["styles", "list", "show"]:
                return self.show_styles()
            
            elif command in ["reset", "default"]:
                return self.reset_to_default()
            
            elif command in ["help", "commands"]:
                if self.auto_feedback:
                    self.responder.send_message(
                        "📋 Available Commands:\n"
                        "   • switch <style_name> - Switch to a style\n"
                        "   • screenshots [style_name] - Generate screenshots\n"
                        "   • styles - Show available styles\n"
                        "   • reset - Reset to default style\n"
                        "   • help - Show this help message",
                        "info"
                    )
                return {"success": True, "message": "Help displayed"}
            
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
        
        except Exception as e:
            if self.auto_feedback:
                self.responder.send_error_report(str(e), {"command": command, "args": args})
            return {"success": False, "error": str(e)}
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session"""
        return {
            "actions_performed": len(self.session_actions),
            "actions": self.session_actions,
            "message_history": len(self.responder.get_message_history()),
            "auto_feedback": self.auto_feedback
        }


def create_interactive_agent(auto_feedback: bool = True) -> InteractiveAgent:
    """
    Create and initialize an interactive orchestration agent
    
    Args:
        auto_feedback: Whether to automatically send terminal feedback
        
    Returns:
        Configured InteractiveAgent instance
        
    Example:
        >>> agent = create_interactive_agent()
        >>> agent.greet()
        >>> agent.switch_style("dark")
        >>> agent.generate_screenshots()
    """
    agent = InteractiveAgent(auto_feedback)
    agent.greet()
    return agent