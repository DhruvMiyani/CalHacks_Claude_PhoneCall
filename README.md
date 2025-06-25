# Sandwich — Phone call Driven Development Workflow

This is a Python-based IDE monitoring system that uses Claude AI for orchestration.

# Devpost:
[Devpost Link 👉 ](https://devpost.com/software/sandwich-voice-driven-development-workflow?ref_content=user-portfolio&ref_feature=in_progress)


<img src="https://github.com/user-attachments/assets/ec91eac5-6c2d-4691-b8b6-55cb4f586a1d" alt="IMG_4517" width="500"/>




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
claude_monitor.py
```

For more detailed information about the architecture and usage, see CLAUDE.md.
