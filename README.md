# IDE Monitor System

This is a Python-based IDE monitoring system that uses Claude AI for orchestration and Gemini Vision for screenshot analysis.

## Setup

### Environment Variables

Before running the application, you need to set the ANTHROPIC_API_KEY environment variable:

```bash
export SANDWICH_ANTHROPIC_API_KEY=your-claude-api-key-here

```

### Configuration

The system also requires a `monitor_config.json` file with additional API keys and settings. See CLAUDE.md for detailed configuration instructions.

## Running

```bash
python local_client.py
```

For more detailed information about the architecture and usage, see CLAUDE.md.