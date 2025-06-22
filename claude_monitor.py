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
        # Load all configuration from config file
        self.config = self.load_config()
        
        # Initialize Claude client
        claude_api_key = self.config.get('sandwich_claude_api_key') or os.getenv('SANDWICH_ANTHROPIC_API_KEY')
        if not claude_api_key:
            raise ValueError("Claude API key must be set in monitor_config.json or ANTHROPIC_API_KEY environment variable")
        self.client = Anthropic(api_key=claude_api_key)
        
        self.watch_directory = self.get_claude_project_directory()
        self.monitor_interval = self.config.get('monitor_interval', 15)
        self.running = False
        self.paused = False
        self.last_file_mtime = None
        self.last_processed_file = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        config_file = 'monitor_config.json'
        default_config = {
            "claude_api_key": "",
            "vapi_api_key": "",
            "vapi_phone_number_id": "",
            "vapi_target_phone": "",
            "twilio_account_sid": "",
            "twilio_auth_token": "",
            "twilio_from_phone": "",
            "twilio_to_phone": "",
            "monitor_interval": 15,
            "watch_directory": ""  # Auto-detect if empty
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return {**default_config, **config}
            except Exception as e:
                print(f"Error loading config: {e}")
        
        # Create default config file
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"Created default config file: {config_file}")
        return default_config

    def get_claude_project_directory(self) -> str:
        """Automatically detect the Claude project directory"""
        # Check if explicitly configured
        if self.config.get('watch_directory'):
            configured_dir = self.config['watch_directory']
            if os.path.exists(configured_dir):
                print(f"📁 Using configured directory: {configured_dir}")
                return configured_dir
            else:
                print(f"⚠️ Configured directory doesn't exist: {configured_dir}")
        
        # Auto-detect Claude project directory
        current_user = os.path.expanduser("~")
        claude_projects_dir = os.path.join(current_user, ".claude", "projects")
        
        if not os.path.exists(claude_projects_dir):
            fallback_dir = os.getcwd()
            print(f"❌ Claude projects directory not found: {claude_projects_dir}")
            print(f"📁 Falling back to current directory: {fallback_dir}")
            return fallback_dir
        
        # Get current working directory to match against project names
        current_dir = os.getcwd()
        current_dir_encoded = current_dir.replace("/", "-").replace(" ", "-")
        
        # Look for matching project directories
        project_dirs = []
        for item in os.listdir(claude_projects_dir):
            project_path = os.path.join(claude_projects_dir, item)
            if os.path.isdir(project_path):
                project_dirs.append((item, project_path, os.path.getmtime(project_path)))
        
        if not project_dirs:
            fallback_dir = os.getcwd()
            print(f"❌ No Claude project directories found in: {claude_projects_dir}")
            print(f"📁 Falling back to current directory: {fallback_dir}")
            return fallback_dir
        
        # Show available projects for debugging
        print(f"📂 Found {len(project_dirs)} Claude projects:")
        for name, path, mtime in sorted(project_dirs, key=lambda x: x[2], reverse=True)[:3]:
            from datetime import datetime
            time_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            print(f"   • {name} (modified: {time_str})")
        
        # First, try to find a project that matches current directory
        for project_name, project_path, mtime in project_dirs:
            # Check if project name contains parts of current directory
            if any(part in project_name.lower() for part in current_dir.lower().split('/') if len(part) > 3):
                print(f"📁 Found matching project: {project_name}")
                print(f"📍 Watching: {project_path}")
                return project_path
        
        # If no match, use the most recently modified project
        most_recent = max(project_dirs, key=lambda x: x[2])
        project_name, project_path, mtime = most_recent
        print(f"📁 Using most recent Claude project: {project_name}")
        print(f"📍 Watching: {project_path}")
        return project_path

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
        """Make VAPI voice call for clarification"""
        try:
            import requests
            import time
            from datetime import datetime
            
            if not all([self.config.get('vapi_api_key'), self.config.get('vapi_phone_number_id'), self.config.get('vapi_target_phone')]):
                return "VAPI configuration incomplete - check monitor_config.json"
            
            # Create clarification question from context
            question = f"I need clarification on this coding issue: {context[:200]}{'...' if len(context) > 200 else ''}. What's your decision or solution?"
            
            # VAPI assistant configuration
            assistant = {
                'firstMessage': f"Hello, this is your coding assistant calling. {question}",
                'model': {
                    'provider': 'openai',
                    'model': 'gpt-4o',
                    'temperature': 0.7,
                    'messages': [
                        {
                            'role': 'system',
                            'content': (
                                "You are a professional coding assistant gathering clarification. "
                                "Ask the clarification question clearly. When the user responds, "
                                "summarize their decision briefly and say you'll relay it back, then end the call. "
                                "Keep all responses under 25 words. Be direct and professional."
                            )
                        }
                    ],
                    'tools': [{'type': 'endCall'}]
                },
                'voice': {
                    'provider': '11labs',
                    'voiceId': 'pNInz6obpgDQGcFmaJgB'  # Adam voice
                },
                'transcriber': {
                    'provider': 'deepgram',
                    'model': 'nova-2',
                    'language': 'en-US'
                },
                'firstMessageMode': 'assistant-speaks-first',
                'silenceTimeoutSeconds': 10,
                'maxDurationSeconds': 120
            }
            
            # Call payload
            call_payload = {
                'assistant': assistant,
                'customer': {
                    'number': self.config['vapi_target_phone']
                },
                'phoneNumberId': self.config['vapi_phone_number_id']
            }
            
            # Make the VAPI call
            headers = {
                'Authorization': f'Bearer {self.config["vapi_api_key"]}',
                'Content-Type': 'application/json'
            }
            
            print(f"🚀 Initiating VAPI call...")
            response = requests.post('https://api.vapi.ai/call', headers=headers, json=call_payload)
            
            if response.status_code == 201:
                call_data = response.json()
                call_id = call_data.get('id')
                print(f"✅ VAPI call initiated! Call ID: {call_id}")
                print("📞 Answer your phone...")
                
                # Wait for call to complete and get results
                print("⏳ Waiting for call to complete...")
                
                while True:
                    await asyncio.sleep(5)  # Check every 5 seconds
                    
                    # Get call details
                    call_response = requests.get(f'https://api.vapi.ai/call/{call_id}', headers=headers)
                    
                    if call_response.status_code == 200:
                        call_info = call_response.json()
                        status = call_info.get('status')
                        
                        print(f"📊 Call status: {status}")
                        
                        if status == 'ended':
                            # Call finished - get the transcript
                            print("\n🏁 CALL COMPLETED!")
                            
                            # Get conversation messages
                            artifact = call_info.get('artifact', {})
                            messages = artifact.get('messages', [])
                            
                            user_responses = []
                            for msg in messages:
                                if msg.get('role') == 'user':
                                    user_msg = msg.get('message', '')
                                    if user_msg:
                                        user_responses.append(user_msg)
                                        print(f"👤 You said: \"{user_msg}\"")
                            
                            if user_responses:
                                decision = " | ".join(user_responses)
                                
                                # Save the decision
                                clarification_file = f"clarification_{call_id}.txt"
                                with open(clarification_file, 'w') as f:
                                    f.write(f"Clarification Decision\n")
                                    f.write(f"=====================\n")
                                    f.write(f"Context: {context}\n")
                                    f.write(f"Raw Response: {decision}\n")
                                    f.write(f"Call ID: {call_id}\n")
                                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                                
                                print(f"🎯 USER DECISION: \"{decision}\"")
                                print(f"💾 Saved to: {clarification_file}")
                                
                                return f"User decision: {decision}"
                            else:
                                return "No clear response captured from voice call"
                        
                        elif status == 'failed':
                            return f"VAPI call failed: {call_info.get('error', 'Unknown error')}"
                    else:
                        return f"Error checking call status: {call_response.status_code}"
            else:
                return f"Failed to initiate VAPI call: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error in voice agent: {e}"

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

    def inject_text_to_active_terminal(self, text: str) -> bool:
        """Inject text into the currently active terminal application."""
        import platform
        
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return self._inject_text_macos(text)
        elif system == "Linux":
            return self._inject_text_linux(text)
        elif system == "Windows":
            return self._inject_text_windows(text)
        else:
            print(f"❌ Unsupported platform: {system}")
            return False
    
    def _inject_text_macos(self, text: str) -> bool:
        """Inject text on macOS using AppleScript."""
        try:
            # Escape special characters for AppleScript
            escaped_text = text.replace('"', '\\"').replace('\\', '\\\\')
            
            # AppleScript to type text in the frontmost application
            applescript = f'''
            tell application "System Events"
                keystroke "{escaped_text}"
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"✅ Successfully injected text to active terminal (macOS)")
                return True
            else:
                print(f"❌ AppleScript error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout injecting text to terminal")
            return False
        except Exception as e:
            print(f"❌ Error injecting text (macOS): {e}")
            return False
    
    def _inject_text_linux(self, text: str) -> bool:
        """Inject text on Linux using xdotool."""
        try:
            # Check if xdotool is available
            subprocess.run(['which', 'xdotool'], check=True, capture_output=True)
            
            # Use xdotool to type text
            result = subprocess.run(
                ['xdotool', 'type', text],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"✅ Successfully injected text to active terminal (Linux)")
                return True
            else:
                print(f"❌ xdotool error: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError:
            print(f"❌ xdotool not found. Install with: sudo apt-get install xdotool")
            return False
        except Exception as e:
            print(f"❌ Error injecting text (Linux): {e}")
            return False
    
    def _inject_text_windows(self, text: str) -> bool:
        """Inject text on Windows using PowerShell."""
        try:
            # Use PowerShell to send keystrokes
            powershell_script = f'''
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.SendKeys]::SendWait("{text}")
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', powershell_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"✅ Successfully injected text to active terminal (Windows)")
                return True
            else:
                print(f"❌ PowerShell error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error injecting text (Windows): {e}")
            return False

    async def send_to_claude_code_terminal(self, message: str):
        """Send a message back to the Claude Code terminal by injecting text."""
        print(f"\n=== INJECTING TO ACTIVE TERMINAL ===")
        print(f"Message: {message}")
        print(f"=== END MESSAGE ===\n")
        
        # Format the message for injection
        formatted_message = f"\n\n🤖 Monitor Alert: {message}\n"
        
        # Try to inject text into active terminal
        success = self.inject_text_to_active_terminal(formatted_message)
        
        if not success:
            print(f"💡 Falling back to console output:")
            print(f"\n=== CLAUDE MONITOR RESPONSE ===")
            print(message)
            print(f"=== END RESPONSE ===\n")
        
        # Resume monitoring after sending terminal instruction
        if self.paused:
            print(f"🟢 Resuming monitoring after terminal instruction...")
            self.paused = False

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
                    await self.send_to_claude_code_terminal(summary)
                
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
                if self.paused:
                    print(f"⏸️  Monitoring paused - waiting for voice call completion...")
                    await asyncio.sleep(1)  # Short sleep while paused
                    continue
                    
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