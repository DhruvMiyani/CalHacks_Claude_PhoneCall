# 💬 Cursor Terminal Integration

This document explains how orchestration agents can respond back to the Cursor terminal chat window using the terminal response tools.

## 🎯 Purpose

The cursor terminal integration allows orchestration agents like Claude AI to:
- Send formatted responses back to the Cursor chat window
- Provide real-time progress updates
- Display interactive status reports
- Handle errors gracefully with user feedback
- Create rich, interactive experiences

## 🚀 Quick Start

### Basic Usage

```python
from tools import send_terminal_response

# Send different types of messages
send_terminal_response("Operation completed!", "success")
send_terminal_response("Warning: Check your configuration", "warning")
send_terminal_response("Error: Invalid style name", "error")
```

### Interactive Agent

```python
from tools import create_interactive_agent

# Create an interactive agent that responds to terminal
agent = create_interactive_agent()

# Agent automatically sends greetings and feedback
agent.switch_style("dark")  # Sends progress and result messages
agent.generate_screenshots()  # Shows progress and results
agent.show_styles()  # Displays formatted style showcase
```

## 📨 Message Types

### Available Message Types
- `info` ℹ️ - General information
- `success` ✅ - Successful operations
- `warning` ⚠️ - Warnings and cautions
- `error` ❌ - Error messages
- `debug` 🔍 - Debug information
- `progress` ⏳ - Progress updates
- `result` 📊 - Operation results
- `action` 🚀 - Actions performed
- `task` 📋 - Task notifications

### Message Formatting

All messages are automatically formatted with:
- Timestamps (e.g., `[17:35:12]`)
- Type-specific emojis
- Proper spacing and alignment

## 🛠️ Available Functions

### Core Functions

#### `send_terminal_response(content, message_type, metadata)`
Send any message to the terminal with optional metadata.

```python
send_terminal_response(
    "Frontend style switched to dark mode!", 
    "success",
    {"style": "dark", "timestamp": "2025-06-21"}
)
```

#### `send_style_showcase()`
Display a formatted showcase of all available styles with current status.

```python
send_style_showcase()
# Shows:
# 🎨 Available Frontend Styles
# ========================================
# 👉 ✅ dark: Dark Mode
#      Futuristic dark theme with neon accents...
```

#### `send_progress_update(task, progress, total, details)`
Send progress updates with visual progress bars.

```python
send_progress_update("Generating Screenshots", 3, 6, "Processing dark mode")
# Shows: ⏳ Generating Screenshots: [███████████░░░░░░░░░] 3/6 (50%)
#        Processing dark mode
```

### Interactive Functions

#### `interactive_style_switch(style_name)`
Switch styles with automatic terminal feedback.

```python
result = interactive_style_switch("dark")
# Automatically sends:
# ⏳ Switching to dark style...
# ✅ Successfully switched to 'Dark Mode' style
```

#### `interactive_screenshot_generation(style_name, include_demo)`
Generate screenshots with progress updates and result reports.

```python
result = interactive_screenshot_generation("modern", include_demo=True)
# Shows progress and detailed results
```

### Agent Class

#### `InteractiveAgent`
Full-featured agent with command handling and automatic feedback.

```python
from tools import InteractiveAgent

agent = InteractiveAgent(auto_feedback=True)
agent.greet()  # Sends welcome message

# Handle commands
agent.handle_user_command("switch", ["dark"])
agent.handle_user_command("screenshots")
agent.handle_user_command("styles")
agent.handle_user_command("help")
```

## 🤖 Orchestration Agent Integration

### For Claude AI

```python
def claude_response_handler(user_message):
    """How Claude might handle user requests"""
    from tools import create_interactive_agent
    
    agent = create_interactive_agent()
    
    if "switch to dark mode" in user_message.lower():
        agent.switch_style("dark")
        return "Switched to dark mode successfully!"
    
    elif "show styles" in user_message.lower():
        agent.show_styles()
        return "Displayed available styles"
    
    elif "take screenshots" in user_message.lower():
        result = agent.generate_screenshots()
        return f"Generated {result['total_files']} screenshots"
```

### For Other Agents

```python
def generic_agent_handler(command_data):
    """Generic handler for any orchestration agent"""
    from tools import (
        send_terminal_response, 
        interactive_style_switch,
        interactive_screenshot_generation
    )
    
    action = command_data.get("action")
    params = command_data.get("parameters", {})
    
    if action == "switch_style":
        style = params.get("style_name")
        send_terminal_response(f"Agent switching to {style}...", "info")
        result = interactive_style_switch(style)
        return result
    
    elif action == "generate_screenshots":
        send_terminal_response("Agent generating screenshots...", "info")
        result = interactive_screenshot_generation()
        return result
```

## 📊 Advanced Features

### Progress Tracking

```python
from tools import send_progress_update

# Multi-step operation with progress
steps = ["Analyzing", "Processing", "Generating", "Finalizing"]
for i, step in enumerate(steps):
    send_progress_update("Complex Operation", i+1, len(steps), step)
    # Perform actual work here
```

### Error Reporting

```python
from tools import CursorTerminalResponder

responder = CursorTerminalResponder()

try:
    # Some operation
    result = risky_operation()
    responder.send_message("Operation succeeded!", "success")
except Exception as e:
    responder.send_error_report(
        f"Operation failed: {str(e)}", 
        {"operation": "risky_operation", "timestamp": datetime.now()}
    )
```

### Session Logging

```python
# Export session messages to file
responder = CursorTerminalResponder()
responder.export_session_log("session_log.txt")
```

## 🔧 Configuration

### Custom Message Formatting

```python
from tools import CursorTerminalResponder

responder = CursorTerminalResponder()

# Custom formatters
responder.formatters["custom"] = "🎯 {content}"
responder.send_message("Custom message", "custom")
```

### Output Stream Control

```python
import sys
from tools import CursorTerminalResponder

# Custom output stream
with open("output.log", "w") as f:
    responder = CursorTerminalResponder(output_stream=f)
    responder.send_message("This goes to file", "info")
```

## 📝 Best Practices

### 1. Use Appropriate Message Types
```python
# Good
send_terminal_response("Style switched successfully", "success")
send_terminal_response("Invalid style name", "error")

# Avoid
send_terminal_response("Style switched successfully", "error")  # Wrong type
```

### 2. Provide Progress Updates for Long Operations
```python
# Good - shows progress
for i, style in enumerate(styles):
    send_progress_update("Processing Styles", i+1, len(styles), style)
    process_style(style)

# Avoid - no feedback during long operation
for style in styles:
    process_style(style)  # User doesn't know what's happening
```

### 3. Handle Errors Gracefully
```python
# Good - informative error handling
try:
    result = switch_style("invalid")
except Exception as e:
    send_terminal_response(f"Error: {e}. Available styles: default, modern, dark", "error")

# Avoid - silent failures
try:
    result = switch_style("invalid")
except:
    pass  # User never knows what happened
```

### 4. Use Interactive Functions for Better UX
```python
# Good - automatic feedback
result = interactive_style_switch("dark")

# Okay but manual - requires more code
send_terminal_response("Switching style...", "progress")
result = switch_frontend_style("dark")
if result["success"]:
    send_terminal_response("Style switched!", "success")
```

## 🎨 Example Workflows

### Complete User Interaction
```python
def handle_user_request(request):
    agent = create_interactive_agent()
    
    if "dark mode" in request:
        agent.switch_style("dark")
        agent.generate_screenshots("dark")
        return "Switched to dark mode and generated screenshots"
    
    elif "showcase" in request:
        agent.show_styles()
        return "Displayed style showcase"
```

### Batch Operations
```python
def process_all_styles():
    agent = create_interactive_agent()
    styles = ["modern", "dark", "vibrant", "corporate", "retro"]
    
    for i, style in enumerate(styles):
        send_progress_update("Processing Styles", i+1, len(styles), style)
        agent.switch_style(style)
        agent.generate_screenshots(style)
    
    agent.reset_to_default()
    send_terminal_response("All styles processed!", "success")
```

## 🚨 Error Handling

The terminal integration includes comprehensive error handling:

- **Network errors** - Graceful fallbacks when terminal is unavailable
- **Format errors** - Automatic sanitization of message content
- **Stream errors** - Alternative output methods if primary stream fails
- **Agent errors** - Detailed error reports with context

## 🎯 Use Cases

### 1. Interactive Development
- Real-time feedback during frontend development
- Progress updates for long-running operations
- Error notifications with actionable suggestions

### 2. Automated Workflows
- Status reports for CI/CD pipelines
- Batch processing with progress tracking
- System monitoring with alert levels

### 3. User Assistance
- Guided tutorials with step-by-step feedback
- Help systems with interactive examples
- Troubleshooting with contextual information

## 📞 Support

For more examples, see:
- `tools/cursor_examples.py` - Complete usage examples
- `tools/example_usage.py` - General orchestration examples
- `tools/README.md` - Full documentation