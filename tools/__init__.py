"""
Orchestration Tools for Timezone Converter Web App
==================================================

This package contains tools that can be called by orchestration agents
to manage frontend styles and generate screenshots.
"""

from .style_manager import StyleManager
from .screenshot_generator import ScreenshotGenerator
from .cursor_terminal import CursorTerminalResponder
from .orchestration_tools import (
    switch_frontend_style,
    generate_style_screenshot,
    generate_all_screenshots,
    get_available_styles,
    reset_to_default_style
)
from .interactive_agent import (
    send_terminal_response,
    send_style_showcase,
    send_screenshot_report,
    send_progress_update,
    create_interactive_agent
)

__version__ = "1.0.0"
__all__ = [
    "StyleManager",
    "ScreenshotGenerator",
    "CursorTerminalResponder",
    "switch_frontend_style",
    "generate_style_screenshot",
    "generate_all_screenshots",
    "get_available_styles",
    "reset_to_default_style",
    "send_terminal_response",
    "send_style_showcase", 
    "send_screenshot_report",
    "send_progress_update",
    "create_interactive_agent"
]