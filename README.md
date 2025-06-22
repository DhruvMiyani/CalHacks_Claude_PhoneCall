# Enhanced Claude Orchestrator Agent

An intelligent orchestration system that monitors your development environment, automatically detects errors and opportunities, and takes action through Claude AI with enhanced tools for Cursor IDE integration, terminal commands, and clipboard operations.

## Architecture Overview

Based on your system diagram, this orchestrator integrates:

- **Local Backend (FastAPI)**: REST API and WebSocket server
- **Screenshot Monitoring**: Captures desktop every 30 seconds
- **Gemini Vision Analysis**: Analyzes screenshots for errors and opportunities
- **Claude Orchestrator**: Makes intelligent decisions and executes tools
- **Enhanced Tools**: 
  - Copy to clipboard (Cursor extension functionality)
  - Terminal command execution
  - Cursor IDE action triggers
  - Error notifications via Twilio
  - Conversation history management
- **Real-time Updates**: WebSocket broadcasting for live monitoring

## Features

### 🔍 Intelligent Monitoring
- **Screenshot Analysis**: Automatic desktop monitoring every 30 seconds
- **Error Detection**: Identifies compilation errors, runtime exceptions, build failures
- **AI Chat Detection**: Recognizes when Cursor/Copilot needs human input
- **Opportunity Recognition**: Finds code that should be copied or commands to execute

### 🤖 Claude Orchestration
- **Smart Decision Making**: Claude analyzes Gemini's findings and chooses appropriate actions
- **Tool Execution**: Automatically executes relevant tools based on context
- **History Awareness**: Maintains conversation history for better context
- **Duplicate Prevention**: Avoids sending duplicate notifications

### 🛠️ Enhanced Tools
- **Copy to Clipboard**: Seamlessly copy code, errors, or commands
- **Terminal Execution**: Run Linux/terminal commands automatically
- **Cursor Actions**: Trigger IDE actions (open chat, format, debug, etc.)
- **Smart Notifications**: Twilio SMS alerts for critical issues
- **Conversation Management**: Full conversation history tracking

### 🌐 FastAPI Backend
- **REST API**: Control monitoring via HTTP endpoints
- **WebSocket Support**: Real-time updates and live monitoring
- **Status Dashboard**: Monitor system health and statistics
- **Remote Control**: Start/stop monitoring remotely

## Installation

1. **Clone and Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   Create `orchestrator_config.json` with your credentials:
   ```json
   {
     "claude_api_key": "your_claude_api_key_here",
     "gemini_api_key": "your_gemini_api_key_here",
     "twilio_account_sid": "your_twilio_sid",
     "twilio_auth_token": "your_twilio_token",
     "twilio_from_phone": "+1234567890",
     "twilio_to_phone": "+0987654321",
     "monitor_interval": 30,
     "error_cooldown": 300,
     "fastapi_port": 8000,
     "fastapi_host": "localhost",
     "enable_websocket": true,
     "screenshot_history_limit": 100,
     "conversation_history_limit": 1000
   }
   ```

3. **Required API Keys**:
   - **Claude API**: Get from [Anthropic Console](https://console.anthropic.com/)
   - **Gemini API**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - **Twilio** (Optional): Get from [Twilio Console](https://console.twilio.com/)

## Usage

### Command Line Interface

```bash
python claude_orchestrator.py
```

Available commands:
- `start`: Begin monitoring
- `stop`: Stop monitoring  
- `status`: Show current statistics
- `quit`: Exit the program

### FastAPI Web Interface

The orchestrator automatically starts a FastAPI server on `http://localhost:8000`:

- **GET** `/` - API status
- **GET** `/status` - Monitoring statistics  
- **POST** `/start` - Start monitoring
- **POST** `/stop` - Stop monitoring
- **GET** `/conversation_history` - View conversation log
- **WebSocket** `/ws` - Real-time updates

### WebSocket Integration

Connect to `ws://localhost:8000/ws` for real-time monitoring:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Orchestrator update:', data);
};
```

## Tool Capabilities

### 1. Error Notifications
- Detects programming errors in real-time
- Sends SMS notifications via Twilio
- Prevents duplicate alerts with cooldown periods
- Categorizes errors by type and urgency

### 2. Clipboard Operations
- Automatically copies useful code snippets
- Copies error messages for easy sharing
- Copies terminal commands for execution
- Integrates with Cursor extension functionality

### 3. Terminal Commands  
- Executes Linux/terminal commands automatically
- Configurable timeout and working directory
- Captures stdout/stderr for analysis
- Safe execution with proper error handling

### 4. Cursor IDE Integration
- Triggers Cursor actions via keyboard shortcuts
- Opens chat interface when needed
- Formats code automatically
- Starts debugging sessions
- Performs searches and navigation

### 5. Conversation History
- Maintains full conversation context
- Tracks all interactions and decisions
- Provides context for better AI responses
- Configurable history limits

## Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `monitor_interval` | Screenshot interval (seconds) | 30 |
| `error_cooldown` | Duplicate error prevention (seconds) | 300 |
| `fastapi_port` | Web server port | 8000 |
| `fastapi_host` | Web server host | localhost |
| `screenshot_history_limit` | Max screenshots to keep | 100 |
| `conversation_history_limit` | Max conversation entries | 1000 |

## Security Considerations

- API keys are stored locally in configuration file
- No sensitive data is transmitted to external services except APIs
- WebSocket connections are local by default
- Terminal command execution is sandboxed with timeouts

## Troubleshooting

### Common Issues

1. **Screenshot Permission**: 
   - macOS: Grant screen recording permission in System Preferences
   - Linux: Ensure X11 forwarding is enabled

2. **Keyboard Shortcuts**:
   - Verify Cursor IDE shortcuts match the configuration
   - Adjust shortcuts in `execute_cursor_action()` if needed

3. **API Rate Limits**:
   - Monitor API usage in logs
   - Adjust `monitor_interval` if hitting limits

4. **WebSocket Connections**:
   - Check firewall settings
   - Verify port availability

### Logs and Debugging

The orchestrator provides detailed logging:
- Real-time console output
- WebSocket broadcasting of all events
- Error tracking with full stack traces
- Performance statistics and timing

## Extending the System

### Adding New Tools

1. Define tool schema in `claude_tools`
2. Implement execution function
3. Add tool handling in `claude_orchestrate()`
4. Test with sample scenarios

### Custom Integrations

The FastAPI backend makes it easy to integrate with other systems:
- Add custom endpoints for specific workflows
- Integrate with CI/CD pipelines
- Connect to project management tools
- Add custom notification channels

## Contributing

This orchestrator is designed to be extensible and customizable for your specific development workflow. Feel free to modify the tools, add new integrations, or enhance the monitoring capabilities based on your needs.

## License

This project is designed for personal development workflow enhancement. Please respect API terms of service for Claude, Gemini, and Twilio. 