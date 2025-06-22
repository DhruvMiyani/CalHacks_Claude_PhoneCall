#!/usr/bin/env python3

import asyncio
import json
import os
import glob
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from anthropic import Anthropic

class ClaudeMonitor:
    def __init__(self):
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.claude_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable must be set")
        self.client = Anthropic(api_key=self.claude_api_key)
        self.watch_directory = "/Users/jaidevshah/.claude/projects/-Users-jaidevshah-Desktop-sandwich-berkeley-hacks"
        self.monitor_interval = 15
        self.running = False
        self.last_file_mtime = None
        self.last_processed_file = None

    def find_latest_jsonl_file(self) -> Optional[str]:
        """Find the most recently created .jsonl file in the watch directory."""
        pattern = os.path.join(self.watch_directory, "*.jsonl")
        jsonl_files = glob.glob(pattern)
        
        if not jsonl_files:
            return None
        
        # Get the most recently modified file
        latest_file = max(jsonl_files, key=os.path.getmtime)
        return latest_file

    def read_last_n_lines(self, file_path: str, n: int = 5) -> List[str]:
        """Read the last n lines from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return [line.strip() for line in lines[-n:] if line.strip()]
        except (IOError, UnicodeDecodeError) as e:
            print(f"Error reading file {file_path}: {e}")
            return []

    async def voice_agent(self, context: str) -> str:
        """Placeholder for voice agent function - assumes this is implemented elsewhere."""
        # This is a placeholder for the actual voice agent implementation
        print(f"Voice agent called with context: {context}")
        # Simulate async voice call
        await asyncio.sleep(2)
        return "Voice call completed. User provided clarification on the error."

    async def call_claude_for_analysis(self, context_lines: List[str]) -> Optional[Dict[str, Any]]:
        """Call Claude API to analyze context and potentially trigger voice agent."""
        if not context_lines:
            return None

        context_text = "\n".join(context_lines)
        
        tools = [
            {
                "name": "voice_agent",
                "description": "Initiate a voice call with the user to clarify errors or answer questions or give a decision when multiple plans are proposed",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "The reason for initiating the voice call (error or question or multiple plans are proposed )"
                        },
                        "context": {
                            "type": "string", 
                            "description": "The relevant context from the conversation"
                        }
                    },
                    "required": ["reason", "context"]
                }
            }
        ]

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                tools=tools,
                messages=[
                    {
                        "role": "user",
                        "content": f"Context from recent conversation:\n{context_text}\n\nIf there is an error or question that needs to be answered by the user or multiple plans proposed, then call the voice_agent tool."
                    }
                ]
            )
            
            return response
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return None

    async def summarize_response(self, context_lines: List[str], voice_response: str) -> Optional[str]:
        """Call Claude to summarize the voice agent response."""
        context_text = "\n".join(context_lines)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                messages=[
                    {
                        "role": "user",
                        "content": f"Original context:\n{context_text}\n\nVoice call response: {voice_response}\n\nPlease provide a concise summary of this interaction and any key information that should be communicated back to the terminal."
                    }
                ]
            )
            
            return response.content[0].text if response.content else None
        except Exception as e:
            print(f"Error summarizing response: {e}")
            return None

    def send_to_claude_code_terminal(self, message: str):
        """Send a message back to the Claude Code terminal by printing it."""
        print(f"\n=== CLAUDE MONITOR RESPONSE ===")
        print(message)
        print(f"=== END RESPONSE ===\n")

    async def process_latest_file(self):
        """Process the latest JSONL file and handle any errors/questions."""
        latest_file = self.find_latest_jsonl_file()
        if not latest_file:
            print("No JSONL files found in watch directory")
            return

        # Check if the file has changed since last processing
        current_mtime = os.path.getmtime(latest_file)
        
        if (self.last_processed_file == latest_file and 
            self.last_file_mtime == current_mtime):
            print(f"📄 File {os.path.basename(latest_file)} unchanged - skipping Claude API call")
            return

        # Update tracking variables
        self.last_processed_file = latest_file
        self.last_file_mtime = current_mtime

        last_lines = self.read_last_n_lines(latest_file, 5)
        if not last_lines:
            print("No lines found in latest file")
            return

        # Log the lines we're processing
        print(f"\n--- Processing file: {os.path.basename(latest_file)} (CHANGED) ---")
        print("Last 5 lines:")
        for i, line in enumerate(last_lines, 1):
            # Truncate long lines for readability
            display_line = line[:200] + "..." if len(line) > 200 else line
            print(f"{i}: {display_line}")
        print("--- End of lines ---\n")

        # Call Claude for analysis
        response = await self.call_claude_for_analysis(last_lines)
        if not response:
            print("No response from Claude API")
            return

        # Check if Claude wants to use the voice_agent tool
        voice_call_made = False
        for content_block in response.content:
            if content_block.type == "tool_use" and content_block.name == "voice_agent":
                # Extract tool parameters
                tool_input = content_block.input
                reason = tool_input.get("reason", "")
                context = tool_input.get("context", "")
                
                print(f"🔊 CLAUDE DETECTED ISSUE - Initiating voice call")
                print(f"Reason: {reason}")
                print(f"Context: {context[:100]}..." if len(context) > 100 else f"Context: {context}")
                
                # Call the voice agent
                voice_response = await self.voice_agent(context)
                
                # Summarize the response
                summary = await self.summarize_response(last_lines, voice_response)
                
                if summary:
                    print(f"📝 CLAUDE SUMMARY:")
                    print(summary)
                    # Send summary back to Claude Code terminal
                    self.send_to_claude_code_terminal(summary)
                
                voice_call_made = True
            elif content_block.type == "text":
                print(f"💭 CLAUDE RESPONSE: {content_block.text}")
        
        if not voice_call_made:
            print("✅ No issues detected - continuing monitoring")

    async def monitor_loop(self):
        """Main monitoring loop that runs every 15 seconds."""
        self.running = True
        print(f"🚀 Starting Claude monitor - watching {self.watch_directory}")
        print(f"⏰ Checking every {self.monitor_interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        while self.running:
            try:
                print(f"🔍 [{asyncio.get_event_loop().time():.1f}] Checking for latest JSONL file...")
                await self.process_latest_file()
                print(f"⏳ Waiting {self.monitor_interval} seconds until next check...\n")
                await asyncio.sleep(self.monitor_interval)
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitor_interval)

    def stop(self):
        """Stop the monitoring loop."""
        self.running = False

async def main():
    monitor = ClaudeMonitor()
    await monitor.monitor_loop()

if __name__ == "__main__":
    asyncio.run(main())