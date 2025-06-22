# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Python-based IDE monitoring system that uses Claude AI for orchestration and Gemini Vision for screenshot analysis. The system monitors IDE screens for programming errors and AI chat requests, then uses Claude to decide on appropriate actions like sending notifications or initiating conversations.

## Architecture

The project consists of a single main Python file:

- `local_client.py` - The core IDEMonitor class that orchestrates the entire monitoring workflow

### Key Components

1. **IDEMonitor Class** - Main orchestration engine (`local_client.py:19`)
   - Manages configuration, API clients, and monitoring state
   - Coordinates between Gemini Vision analysis and Claude decision-making

2. **Multi-AI Workflow**:
   - Takes screenshots using `mss` library
   - Sends to Gemini Vision API for initial analysis of errors/chat requests
   - Uses Claude with function calling to orchestrate responses
   - Executes actions like Twilio SMS notifications

3. **Claude Function Tools** (`local_client.py:42-94`):
   - `send_error_notification` - For programming error alerts
   - `initiate_conversation` - For AI chat assistance requests

4. **Configuration System** (`local_client.py:96-123`):
   - Uses `monitor_config.json` for API keys and settings
   - Auto-creates default config if missing

## Dependencies

The system requires these Python packages:
- `anthropic` - Claude API client
- `google-generativeai` - Gemini API client  
- `twilio` - SMS notifications
- `mss` - Screenshot capture
- `PIL` (Pillow) - Image processing

## Running the Application

The system is designed to run as an interactive CLI:

```bash
python local_client.py
```

Commands available in the CLI:
- `start` - Begin monitoring
- `stop` - Stop monitoring  
- `status` - Show current statistics
- `quit` - Exit application

## Configuration

Before running, you need to set up API keys in `monitor_config.json`:

```json
{
  "claude_api_key": "your-claude-key",
  "gemini_api_key": "your-gemini-key", 
  "twilio_account_sid": "optional-twilio-sid",
  "twilio_auth_token": "optional-twilio-token",
  "twilio_from_phone": "optional-from-number",
  "twilio_to_phone": "optional-to-number",
  "monitor_interval": 30,
  "error_cooldown": 300
}
```

## Key Methods

- `monitor_loop()` (`local_client.py:412`) - Main async monitoring loop
- `analyze_with_gemini()` (`local_client.py:142`) - Screenshot analysis 
- `claude_orchestrate()` (`local_client.py:216`) - Claude decision-making
- `take_screenshot()` (`local_client.py:130`) - Screen capture functionality

## Error Handling

The system includes sophisticated error deduplication logic (`local_client.py:287-298`) to prevent spam notifications for the same issues within a cooldown period.