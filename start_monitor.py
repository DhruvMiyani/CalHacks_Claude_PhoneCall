#!/usr/bin/env python3

import asyncio
from claude_monitor import ClaudeMonitor

if __name__ == "__main__":
    print("Starting Claude Monitor...")
    print("Monitoring /Users/jaidevshah/.claude/projects/-Users-jaidevshah-Desktop-sandwich-berkeley-hacks")
    print("Press Ctrl+C to stop\n")
    
    monitor = ClaudeMonitor()
    try:
        asyncio.run(monitor.monitor_loop())
    except KeyboardInterrupt:
        print("\nMonitor stopped by user")