"""
Cursor Terminal Response Tool for Orchestration Agents
======================================================

This module provides functionality for orchestration agents to respond
back to the Cursor terminal chat window with formatted messages.
"""

import sys
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class TerminalMessage:
    """Represents a message to be sent to the terminal"""
    content: str
    message_type: str = "info"  # info, success, warning, error, debug
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class CursorTerminalResponder:
    """Handles responses back to Cursor terminal chat window"""
    
    def __init__(self, output_stream=None):
        """
        Initialize the terminal responder
        
        Args:
            output_stream: Output stream to write to (default: sys.stdout)
        """
        self.output_stream = output_stream or sys.stdout
        self.message_queue = []
        self.session_id = f"session_{int(time.time())}"
        
        # Message formatting templates
        self.formatters = {
            "info": "ℹ️  {content}",
            "success": "✅ {content}",
            "warning": "⚠️  {content}",
            "error": "❌ {content}",
            "debug": "🔍 {content}",
            "progress": "⏳ {content}",
            "result": "📊 {content}",
            "action": "🚀 {content}",
            "task": "📋 {content}",
            "update": "🔄 {content}"
        }
    
    def send_message(self, content: str, message_type: str = "info", 
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a message to the Cursor terminal
        
        Args:
            content: Message content to send
            message_type: Type of message (info, success, warning, error, etc.)
            metadata: Optional metadata to include
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            message = TerminalMessage(
                content=content,
                message_type=message_type,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            # Format and send the message
            formatted_message = self._format_message(message)
            
            # Write to output stream
            self.output_stream.write(formatted_message + "\n")
            self.output_stream.flush()
            
            # Add to message queue for history
            self.message_queue.append(message)
            
            return True
            
        except Exception as e:
            # Fallback error message
            try:
                self.output_stream.write(f"❌ Error sending message: {str(e)}\n")
                self.output_stream.flush()
            except:
                pass
            return False
    
    def send_formatted_response(self, response_data: Dict[str, Any]) -> bool:
        """
        Send a formatted response based on operation results
        
        Args:
            response_data: Dictionary containing operation results
            
        Returns:
            True if response sent successfully, False otherwise
        """
        try:
            if response_data.get("success", False):
                message_type = "success"
                content = response_data.get("message", "Operation completed successfully")
            else:
                message_type = "error"
                content = response_data.get("error", response_data.get("message", "Operation failed"))
            
            # Add additional context if available
            if "style_info" in response_data and response_data["style_info"]:
                style_info = response_data["style_info"]
                content += f"\n   Style: {style_info.get('display_name', 'Unknown')}"
                content += f"\n   Description: {style_info.get('description', 'No description')}"
            
            if "total_files" in response_data:
                content += f"\n   Files generated: {response_data['total_files']}"
            
            return self.send_message(content, message_type, response_data)
            
        except Exception as e:
            return self.send_message(f"Error formatting response: {str(e)}", "error")
    
    def send_progress_update(self, task: str, progress: int, total: int, 
                           details: Optional[str] = None) -> bool:
        """
        Send a progress update message
        
        Args:
            task: Name of the task
            progress: Current progress (0-total)
            total: Total items/steps
            details: Optional additional details
            
        Returns:
            True if message sent successfully, False otherwise
        """
        percentage = int((progress / total) * 100) if total > 0 else 0
        progress_bar = self._create_progress_bar(percentage)
        
        content = f"{task}: {progress_bar} {progress}/{total} ({percentage}%)"
        if details:
            content += f"\n   {details}"
        
        return self.send_message(content, "progress")
    
    def send_status_report(self, operation: str, status: Dict[str, Any]) -> bool:
        """
        Send a comprehensive status report
        
        Args:
            operation: Name of the operation
            status: Status information dictionary
            
        Returns:
            True if message sent successfully, False otherwise
        """
        content = f"📊 {operation} Status Report\n"
        content += "=" * 40 + "\n"
        
        for key, value in status.items():
            if isinstance(value, dict):
                content += f"{key}:\n"
                for sub_key, sub_value in value.items():
                    content += f"  • {sub_key}: {sub_value}\n"
            elif isinstance(value, list):
                content += f"{key}: {', '.join(map(str, value))}\n"
            else:
                content += f"{key}: {value}\n"
        
        return self.send_message(content, "result")
    
    def send_style_showcase(self, styles_info: Dict[str, Any]) -> bool:
        """
        Send a formatted showcase of available styles
        
        Args:
            styles_info: Styles information from get_available_styles()
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not styles_info.get("success", True):
            return self.send_message("Failed to get styles information", "error")
        
        content = "🎨 Available Frontend Styles\n"
        content += "=" * 40 + "\n"
        
        current_style = styles_info.get("current_style", "unknown")
        
        for name, info in styles_info.get("styles", {}).items():
            status_icon = "👉" if name == current_style else "   "
            exists_icon = "✅" if info.get("template_exists", False) else "❌"
            
            content += f"{status_icon} {exists_icon} {name}: {info.get('display_name', 'Unknown')}\n"
            content += f"     {info.get('description', 'No description')}\n"
            content += f"     Color Scheme: {info.get('color_scheme', 'N/A')}\n\n"
        
        content += f"Total Styles: {styles_info.get('total_styles', 0)}\n"
        content += f"Current Style: {current_style}"
        
        return self.send_message(content, "result")
    
    def send_screenshot_report(self, screenshot_results: Dict[str, Any]) -> bool:
        """
        Send a formatted screenshot generation report
        
        Args:
            screenshot_results: Results from screenshot generation
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not screenshot_results.get("success", False):
            return self.send_message(
                f"Screenshot generation failed: {screenshot_results.get('error', 'Unknown error')}", 
                "error"
            )
        
        content = "📸 Screenshot Generation Report\n"
        content += "=" * 40 + "\n"
        
        total_files = screenshot_results.get("total_files", 0)
        content += f"Total Files Generated: {total_files}\n"
        
        if "successful_styles" in screenshot_results:
            successful = screenshot_results["successful_styles"]
            failed = screenshot_results.get("failed_styles", [])
            
            content += f"Successful Styles: {', '.join(successful)}\n"
            if failed:
                content += f"Failed Styles: {', '.join(failed)}\n"
        
        if "screenshots" in screenshot_results:
            content += "\nScreenshot Details:\n"
            for screenshot_type, info in screenshot_results["screenshots"].items():
                status = "✅" if info.get("success", False) else "❌"
                file_path = info.get("file_path", "N/A")
                file_size = info.get("file_size_mb", 0)
                content += f"  {status} {screenshot_type}: {file_path} ({file_size}MB)\n"
        
        return self.send_message(content, "result")
    
    def send_action_confirmation(self, action: str, details: Dict[str, Any]) -> bool:
        """
        Send a confirmation message for an action taken
        
        Args:
            action: Action that was performed
            details: Details about the action
            
        Returns:
            True if message sent successfully, False otherwise
        """
        content = f"🚀 Action Performed: {action}\n"
        
        if details:
            for key, value in details.items():
                content += f"   {key}: {value}\n"
        
        return self.send_message(content, "action")
    
    def send_error_report(self, error: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a detailed error report
        
        Args:
            error: Error message
            context: Optional context information
            
        Returns:
            True if message sent successfully, False otherwise
        """
        content = f"💥 Error: {error}"
        
        if context:
            content += "\n\nContext:"
            for key, value in context.items():
                content += f"\n   {key}: {value}"
        
        return self.send_message(content, "error")
    
    def _format_message(self, message: TerminalMessage) -> str:
        """Format a message for display"""
        formatter = self.formatters.get(message.message_type, "{content}")
        formatted = formatter.format(content=message.content)
        
        # Add timestamp if enabled
        if message.timestamp:
            timestamp_str = message.timestamp.strftime("%H:%M:%S")
            formatted = f"[{timestamp_str}] {formatted}"
        
        return formatted
    
    def _create_progress_bar(self, percentage: int, width: int = 20) -> str:
        """Create a text-based progress bar"""
        filled = int(width * percentage / 100)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def get_message_history(self) -> List[TerminalMessage]:
        """Get the message history for this session"""
        return self.message_queue.copy()
    
    def clear_history(self) -> None:
        """Clear the message history"""
        self.message_queue.clear()
    
    def export_session_log(self, file_path: str) -> bool:
        """
        Export session messages to a log file
        
        Args:
            file_path: Path to save the log file
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                f.write(f"Cursor Terminal Session Log\n")
                f.write(f"Session ID: {self.session_id}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n\n")
                
                for message in self.message_queue:
                    f.write(f"[{message.timestamp.isoformat()}] ")
                    f.write(f"[{message.message_type.upper()}] ")
                    f.write(f"{message.content}\n")
                    
                    if message.metadata:
                        f.write(f"   Metadata: {json.dumps(message.metadata, indent=2)}\n")
                    
                    f.write("\n")
            
            return True
            
        except Exception:
            return False