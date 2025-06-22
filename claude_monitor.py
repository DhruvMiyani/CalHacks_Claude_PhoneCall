#!/usr/bin/env python3

import asyncio
import json
import os
import glob
import time
from typing import List, Optional
from anthropic import Anthropic
import pyautogui
# from claude_code_sdk import query, ClaudeCodeOptions  # SDK not available yet

class ClaudeMonitor:
    def __init__(self):
        self.claude_api_key = self.load_config()
        self.client = Anthropic(api_key=self.claude_api_key)
        self.watch_directory = "/Users/jaidevshah/.claude/projects/-Users-jaidevshah-Desktop-sandwich-berkeley-hacks"
        self.monitor_interval = 45  # Simple 45 second monitoring
        self.running = False
        self.paused = False
        self.last_file_mtime = None
        self.last_processed_file = None
        self.stability_check_seconds = 30  # Wait 30s for stability at end of 45s cycle

    def load_config(self) -> str:
        """Load API key from config.json file."""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                api_key = config.get('anthropic_api_key')
                if not api_key or api_key == "your-anthropic-api-key-here":
                    raise ValueError("Please set your Anthropic API key in config.json")
                return api_key
        except FileNotFoundError:
            raise ValueError("config.json file not found. Please create it with your Anthropic API key.")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in config.json file.")

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
        # Pause monitoring during voice call
        print(f"🔴 PAUSING monitoring for voice call...")
        self.paused = True
        
        # This is a placeholder for the actual voice agent implementation
        print(f"Voice agent called with context: {context}")
        print(f"📞 Starting voice call...")
        # Simulate async voice call
        await asyncio.sleep(2)
        
        # Simulate user response from voice call
        user_voice_response = "User said: I want the most minimlistic style. Do it"
        print(f"🟢 Voice call completed.")
        print(f"📝 User response: {user_voice_response}")
        
        return user_voice_response

    async def call_claude_for_analysis(self, context_lines: List[str]):
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
                        "content": f"Context from recent conversation:\n{context_text}\n\n. There will be many logs but focus mostly on the last log as this is the most recent log. Use the previous logs to get an understanding of the conversation. In the last log, if there is an error or question that needs to be answered by the user or multiple plans proposed, then call the voice_agent tool."
                    }
                ]
            )
            
            return response
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return None

    async def summarize_user_instruction(self, context_lines: List[str], voice_response: str) -> Optional[str]:
        """Call Claude to summarize the user's instruction from the voice call."""
        context_text = "\n".join(context_lines)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                messages=[
                    {
                        "role": "user",
                        "content": f"Original context from code monitoring:\n{context_text}\n\nUser's response from voice call: {voice_response}\n\nExtract ONLY the user's actionable instruction from the voice response. Return ONLY the clean instruction text that should be typed at the cursor - no explanations, no formatting, no extra text. Just the raw instruction the user wants executed."
                    }
                ]
            )
            
            return response.content[0].text if response.content else None
        except Exception as e:
            print(f"Error summarizing user instruction: {e}")
            return None

    def type_response_at_cursor(self, message: str) -> bool:
        """Type the user instruction at the current cursor location using pyautogui."""
        try:
            # Add a small delay to ensure we don't interfere with other operations
            import time
            time.sleep(1.0)  # Longer delay to ensure user is ready
            
            # Type the user instruction directly without extra formatting
            pyautogui.write(message.replace('\n', ' '), interval=0.02)  # ~50 chars/s for natural typing
            
            # Press Enter after typing the user instruction
            pyautogui.press('enter')
            
            print(f"✅ Successfully typed user instruction at cursor location and pressed Enter")
            return True
                
        except Exception as e:
            print(f"❌ Error typing user instruction with pyautogui: {e}")
            return False

    async def send_response_to_cursor(self, message: str):
        """Send a message by typing it at the current cursor location."""
        print(f"\n=== TYPING USER INSTRUCTION AT CURSOR ===")
        print(f"Instruction: {message}")
        print(f"=== END INSTRUCTION ===\n")
        
        # Type the user instruction directly (no extra formatting)
        success = self.type_response_at_cursor(message)
        
        if not success:
            print(f"💡 Fallback - User instruction:")
            print(f"\n=== USER INSTRUCTION ===")
            print(message)
            print(f"=== END INSTRUCTION ===\n")

    async def process_latest_file(self):
        """Process the latest JSONL file and handle any errors/questions."""
        latest_file = self.find_latest_jsonl_file()
        if not latest_file:
            print("No JSONL files found in watch directory")
            return

        # Check if the file has changed since last processing
        current_mtime = os.path.getmtime(latest_file)
        
        # Skip if file unchanged
        if (self.last_processed_file == latest_file and 
            self.last_file_mtime == current_mtime):
            return

        print(f"📄 File {os.path.basename(latest_file)} changed - checking stability...")
        
        # Check stability - wait and see if file changes again
        await asyncio.sleep(self.stability_check_seconds)
        
        # Re-check file after stability wait
        latest_file_after_wait = self.find_latest_jsonl_file()
        mtime_after_wait = os.path.getmtime(latest_file_after_wait) if latest_file_after_wait else 0
        
        if (latest_file_after_wait != latest_file or mtime_after_wait != current_mtime):
            print(f"📄 File changed during stability check - skipping (will retry next cycle)")
            return
            
        print(f"✅ File stable - processing {os.path.basename(latest_file)}")
        
        # Update tracking
        self.last_processed_file = latest_file
        self.last_file_mtime = current_mtime

        last_lines = self.read_last_n_lines(latest_file, 15)
        if not last_lines:
            print("No lines found in latest file")
            return

        # Log the lines we're processing
        print(f"\n--- Processing file: {os.path.basename(latest_file)} (CHANGED) ---")
        print("Last 15 lines:")
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
        if hasattr(response, 'content') and response.content:
            for content_block in response.content:
                if content_block.type == "tool_use" and content_block.name == "voice_agent":
                    # Extract tool parameters
                    tool_input = content_block.input
                    reason = getattr(tool_input, "reason", "") if hasattr(tool_input, "reason") else ""
                    context = getattr(tool_input, "context", "") if hasattr(tool_input, "context") else ""
                
                    print(f"🔊 CLAUDE DETECTED ISSUE - Initiating voice call")
                    print(f"Reason: {reason}")
                    print(f"Context: {context[:100]}..." if len(context) > 100 else f"Context: {context}")
                    
                    # Call the voice agent
                    voice_response = await self.voice_agent(context)
                    
                    # Extract user instruction directly from voice response
                    print(f"🧠 Extracting user instruction from voice response...")
                    
                    # Simple extraction - get text after "User said:"
                    if "User said:" in voice_response:
                        user_instruction = voice_response.split("User said:", 1)[1].strip()
                        # Remove quotes if present
                        if user_instruction.startswith('"') and user_instruction.endswith('"'):
                            user_instruction = user_instruction[1:-1]
                        if user_instruction.startswith("'") and user_instruction.endswith("'"):
                            user_instruction = user_instruction[1:-1]
                    else:
                        # Fallback - use the whole voice response
                        user_instruction = voice_response.strip()
                    
                    if user_instruction:
                        print(f"📝 USER INSTRUCTION:")
                        print(user_instruction)
                        # Type the user's actual words at cursor location
                        await self.send_response_to_cursor(user_instruction)
                    else:
                        print(f"❌ Could not extract user instruction from voice response")
                    
                    # Resume monitoring after completing the full flow
                    print(f"🟢 Resuming monitoring...")
                    self.paused = False
                    
                    voice_call_made = True
                elif content_block.type == "text":
                    print(f"💭 CLAUDE RESPONSE: {content_block.text}")
        
        if not voice_call_made:
            print("✅ No issues detected - continuing monitoring")

    async def monitor_loop(self):
        """Main monitoring loop - check every 45 seconds."""
        self.running = True
        print(f"🚀 Starting Claude monitor - watching {self.watch_directory}")
        print(f"⏰ Checking every {self.monitor_interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        while self.running:
            try:
                if self.paused:
                    print(f"⏸️  Monitoring paused - waiting for voice call completion...")
                    await asyncio.sleep(1)  # Short sleep while paused
                    continue
                    
                await self.process_latest_file()
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