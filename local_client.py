#!/usr/bin/env python3
"""
Simplified Claude Orchestration IDE Monitor
Claude acts as orchestrator, analyzing Gemini responses and calling tools
"""

import os
import json
import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, Any
from PIL import Image
import mss
import google.generativeai as genai
from twilio.rest import Client
import anthropic

class IDEMonitor:
    def __init__(self):
        self.config = self.load_config()
        self.is_running = False
        self.stats = {
            "total_checks": 0,
            "errors_detected": 0,
            "conversations_initiated": 0,
            "last_check": None,
            "last_error": None,
            "last_action": None,
            "error_history": []
        }
        
        # Initialize clients
        if self.config.get('gemini_api_key'):
            genai.configure(api_key=self.config['gemini_api_key'])
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        if self.config.get('claude_api_key'):
            self.claude_client = anthropic.Anthropic(api_key=self.config['claude_api_key'])
        
        # Claude tools definition
        self.claude_tools = [
            {
                "name": "send_error_notification",
                "description": "Send a notification about a detected programming error via Twilio SMS",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "error_summary": {
                            "type": "string",
                            "description": "A concise summary of the error detected"
                        },
                        "error_type": {
                            "type": "string",
                            "description": "Type of error (e.g., compilation, runtime, syntax, build)"
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Urgency level of the error"
                        },
                        "suggested_action": {
                            "type": "string",
                            "description": "Suggested next steps to resolve the error"
                        }
                    },
                    "required": ["error_summary", "error_type", "urgency"]
                }
            },
            {
                "name": "initiate_conversation",
                "description": "Initiate a conversation/assistance session when Cursor chat or similar tool is asking for human input",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "context": {
                            "type": "string",
                            "description": "Context of what the AI assistant is asking help with"
                        },
                        "conversation_type": {
                            "type": "string",
                            "enum": ["cursor_chat", "copilot", "code_review", "debugging"],
                            "description": "Type of conversation being initiated"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Priority of the conversation request"
                        }
                    },
                    "required": ["context", "conversation_type"]
                }
            }
        ]
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        config_file = 'monitor_config.json'
        default_config = {
            "claude_api_key": "",
            "gemini_api_key": "",
            "twilio_account_sid": "",
            "twilio_auth_token": "",
            "twilio_from_phone": "",
            "twilio_to_phone": "",
            "monitor_interval": 30,
            "error_cooldown": 300
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return {**default_config, **config}
            except Exception as e:
                self.log(f"Error loading config: {e}", "ERROR")
        
        # Create default config file
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        self.log(f"Created default config file: {config_file}")
        return default_config
    
    def log(self, message: str, level: str = "INFO"):
        """Simple logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def take_screenshot(self) -> Optional[Image.Image]:
        """Take screenshot of primary monitor"""
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                return img
        except Exception as e:
            self.log(f"Error taking screenshot: {e}", "ERROR")
            return None
    
    def analyze_with_gemini(self, image: Image.Image) -> Optional[Dict[str, Any]]:
        """Analyze screenshot with Gemini API for errors and chat requests"""
        try:
            if not hasattr(self, 'gemini_model'):
                self.log("Gemini model not initialized", "ERROR")
                return None
            
            prompt = """
            Analyze this screenshot for TWO specific scenarios:
            
            1. PROGRAMMING ERRORS: Look for:
               - Terminal/command line errors (red text, error messages, stack traces)
               - IDE error indicators (red underlines, error panels, compilation errors)
               - Build failures, test failures, or deployment errors
               - Syntax errors, runtime exceptions, or warnings
            
            2. AI CHAT ASSISTANCE REQUESTS: Look for:
               - Cursor chat interface asking for human input or showing "waiting for response"
               - GitHub Copilot chat requests or suggestions
               - Any AI coding assistant requesting clarification or input
               - Code review requests or debugging assistance prompts
            
            Respond with JSON in this format:
            {
                "has_error": boolean,
                "error_details": {
                    "type": "compilation|runtime|syntax|build|test|deployment",
                    "description": "detailed description of the error",
                    "severity": "low|medium|high",
                    "location": "where the error appears (file, line, etc.)"
                },
                "has_chat_request": boolean,
                "chat_details": {
                    "type": "cursor_chat|copilot|code_review|debugging",
                    "context": "what the AI is asking help with",
                    "urgency": "low|medium|high"
                },
                "screenshot_analysis": "brief description of what's visible in the screenshot"
            }
            
            If neither errors nor chat requests are detected, set both has_error and has_chat_request to false.
            """
            
            response = self.gemini_model.generate_content([prompt, image])
            
            try:
                result = json.loads(response.text.strip())
                return result
            except json.JSONDecodeError:
                # Fallback analysis if JSON parsing fails
                text = response.text.lower()
                has_error = any(word in text for word in ['error', 'exception', 'failed', 'traceback', 'compilation'])
                has_chat = any(word in text for word in ['cursor', 'chat', 'input', 'assistance', 'copilot'])
                
                return {
                    "has_error": has_error,
                    "error_details": {
                        "type": "unknown",
                        "description": "Potential error detected in fallback analysis",
                        "severity": "medium"
                    },
                    "has_chat_request": has_chat,
                    "chat_details": {
                        "type": "unknown",
                        "context": "Potential chat request detected",
                        "urgency": "medium"
                    },
                    "screenshot_analysis": "Fallback analysis due to JSON parsing error"
                }
                
        except Exception as e:
            self.log(f"Error analyzing with Gemini: {e}", "ERROR")
            return None
    
    def claude_orchestrate(self, gemini_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Claude analyzes Gemini's response and decides what action to take"""
        try:
            if not hasattr(self, 'claude_client'):
                self.log("Claude client not initialized", "ERROR")
                return None
            
            # Prepare context for Claude
            context = f"""
            I am an orchestration agent monitoring an IDE for errors and AI chat requests.
            
            Here's the analysis from Gemini Vision about the current screenshot:
            {json.dumps(gemini_analysis, indent=2)}
            
            Recent error history (to avoid duplicate notifications):
            {json.dumps(self.stats["error_history"][-5:], indent=2)}
            
            Based on this analysis, I need to decide what action to take:
            1. If there's a programming error that needs attention, I should send a notification
            2. If there's an AI chat request waiting for human input, I should initiate a conversation
            3. If nothing significant is detected, I should take no action
            
            Consider:
            - Don't send duplicate notifications for the same error within the cooldown period
            - Prioritize high-severity errors and urgent chat requests
            - Provide clear, actionable summaries
            """
            
            message = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                tools=self.claude_tools,
                messages=[
                    {
                        "role": "user",
                        "content": context
                    }
                ]
            )
            
            # Check if Claude used tools
            if message.stop_reason == "tool_use":
                for content in message.content:
                    if content.type == "tool_use":
                        tool_name = content.name
                        tool_input = content.input
                        
                        self.log(f"Claude decided to use tool: {tool_name}")
                        
                        if tool_name == "send_error_notification":
                            return self.execute_error_notification(tool_input)
                        elif tool_name == "initiate_conversation":
                            return self.execute_conversation_initiation(tool_input)
            
            # If no tools were used, Claude decided no action is needed
            reasoning = message.content[0].text if message.content else "No action needed"
            self.log(f"Claude decision: {reasoning}")
            
            return {
                "action": "none",
                "reasoning": reasoning
            }
            
        except Exception as e:
            self.log(f"Error in Claude orchestration: {e}", "ERROR")
            return None
    
    def execute_error_notification(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the error notification tool"""
        try:
            # Check if we've seen this error recently
            error_signature = f"{tool_input.get('error_type')}:{tool_input.get('error_summary')}"
            current_time = time.time()
            
            # Check error history for duplicates
            for hist_error in self.stats["error_history"]:
                if (hist_error.get("signature") == error_signature and 
                    current_time - hist_error.get("timestamp", 0) < self.config["error_cooldown"]):
                    self.log(f"Error notification skipped - duplicate within cooldown: {error_signature}")
                    return {
                        "action": "none",
                        "reasoning": "Duplicate error within cooldown period"
                    }
            
            # Send Twilio notification
            success = self.send_twilio_message(tool_input, "error")
            
            if success:
                # Add to error history
                self.stats["error_history"].append({
                    "signature": error_signature,
                    "timestamp": current_time,
                    "details": tool_input
                })
                # Keep only last 20 errors
                if len(self.stats["error_history"]) > 20:
                    self.stats["error_history"] = self.stats["error_history"][-20:]
                
                self.stats["errors_detected"] += 1
                self.stats["last_error"] = tool_input.get('error_summary')
                self.stats["last_action"] = f"Sent error notification: {tool_input.get('error_type')}"
                
                return {
                    "action": "notify_error",
                    "reasoning": "Error notification sent successfully",
                    "error_summary": tool_input.get('error_summary'),
                    "urgency": tool_input.get('urgency', 'medium')
                }
            else:
                return {
                    "action": "none",
                    "reasoning": "Failed to send error notification"
                }
                
        except Exception as e:
            self.log(f"Error executing notification tool: {e}", "ERROR")
            return {
                "action": "none",
                "reasoning": f"Error executing notification: {e}"
            }
    
    def execute_conversation_initiation(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the conversation initiation tool"""
        try:
            # Send conversation initiation via Twilio
            success = self.send_twilio_message(tool_input, "conversation")
            
            if success:
                self.stats["conversations_initiated"] += 1
                self.stats["last_action"] = f"Initiated conversation: {tool_input.get('conversation_type')}"
                
                return {
                    "action": "initiate_conversation",
                    "reasoning": "Conversation initiation sent successfully",
                    "conversation_context": tool_input.get('context'),
                    "urgency": tool_input.get('priority', 'medium')
                }
            else:
                return {
                    "action": "none",
                    "reasoning": "Failed to initiate conversation"
                }
                
        except Exception as e:
            self.log(f"Error executing conversation tool: {e}", "ERROR")
            return {
                "action": "none",
                "reasoning": f"Error executing conversation: {e}"
            }
    
    def send_twilio_message(self, data: Dict[str, Any], message_type: str) -> bool:
        """Send message via Twilio"""
        try:
            if not all([self.config.get('twilio_account_sid'), self.config.get('twilio_auth_token'), 
                       self.config.get('twilio_from_phone'), self.config.get('twilio_to_phone')]):
                self.log("Twilio configuration incomplete", "WARNING")
                return False
            
            client = Client(self.config['twilio_account_sid'], self.config['twilio_auth_token'])
            
            if message_type == "error":
                urgency_emoji = {"low": "⚠️", "medium": "🚨", "high": "🔥"}
                emoji = urgency_emoji.get(data.get('urgency', 'medium'), "🚨")
                
                message_body = f"{emoji} IDE Error Detected!\n\n"
                message_body += f"Type: {data.get('error_type', 'Unknown')}\n"
                message_body += f"Urgency: {data.get('urgency', 'Medium')}\n"
                message_body += f"Summary: {data.get('error_summary', 'No summary')}\n"
                
                if data.get('suggested_action'):
                    message_body += f"Suggested Action: {data.get('suggested_action')}\n"
                
            elif message_type == "conversation":
                priority_emoji = {"low": "💬", "medium": "🤖", "high": "🔔"}
                emoji = priority_emoji.get(data.get('priority', 'medium'), "🤖")
                
                message_body = f"{emoji} AI Assistant Needs Input!\n\n"
                message_body += f"Type: {data.get('conversation_type', 'Unknown')}\n"
                message_body += f"Priority: {data.get('priority', 'Medium')}\n"
                message_body += f"Context: {data.get('context', 'No context')}\n"
            
            message_body += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            message = client.messages.create(
                body=message_body,
                from_=self.config['twilio_from_phone'],
                to=self.config['twilio_to_phone']
            )
            
            self.log(f"Message sent via Twilio (SID: {message.sid})", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Error sending Twilio message: {e}", "ERROR")
            return False
    
    async def monitor_loop(self):
        """Main monitoring loop orchestrated by Claude"""
        self.log("Starting Claude orchestration monitor loop")
        
        while self.is_running:
            try:
                self.log("Taking screenshot for analysis...")
                
                # Take screenshot
                screenshot = self.take_screenshot()
                if not screenshot:
                    await asyncio.sleep(self.config["monitor_interval"])
                    continue
                
                self.stats["total_checks"] += 1
                self.stats["last_check"] = datetime.now().isoformat()
                
                # Analyze with Gemini
                self.log("Sending screenshot to Gemini for analysis...")
                gemini_analysis = self.analyze_with_gemini(screenshot)
                if not gemini_analysis:
                    await asyncio.sleep(self.config["monitor_interval"])
                    continue
                
                self.log(f"Gemini analysis: errors={gemini_analysis.get('has_error')}, chat_requests={gemini_analysis.get('has_chat_request')}")
                
                # Let Claude orchestrate the response
                if gemini_analysis.get('has_error') or gemini_analysis.get('has_chat_request'):
                    self.log("Sending to Claude for orchestration...")
                    claude_decision = self.claude_orchestrate(gemini_analysis)
                    
                    if claude_decision:
                        self.log(f"Claude decision: {claude_decision.get('action')} - {claude_decision.get('reasoning')}")
                    else:
                        self.log("Claude orchestration failed", "WARNING")
                else:
                    self.log("No errors or chat requests detected - continuing monitoring")
                    
            except Exception as e:
                self.log(f"Error in monitor loop: {e}", "ERROR")
            
            await asyncio.sleep(self.config["monitor_interval"])
        
        self.log("Monitor loop stopped")
    
    def start_monitoring(self):
        """Start the monitoring process"""
        if self.is_running:
            self.log("Monitoring already running")
            return
        
        if not self.config.get('claude_api_key'):
            self.log("Claude API key not configured", "ERROR")
            return
        
        if not self.config.get('gemini_api_key'):
            self.log("Gemini API key not configured", "ERROR")
            return
        
        self.is_running = True
        self.log("Starting Claude orchestration monitoring...")
        
        # Run the async monitor loop
        asyncio.run(self.monitor_loop())
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.is_running = False
        self.log("Stopping monitoring...")
    
    def print_status(self):
        """Print current status"""
        print("\n" + "="*50)
        print("CLAUDE ORCHESTRATION MONITOR STATUS")
        print("="*50)
        print(f"Running: {'Yes' if self.is_running else 'No'}")
        print(f"Total Checks: {self.stats['total_checks']}")
        print(f"Errors Detected: {self.stats['errors_detected']}")
        print(f"Conversations Initiated: {self.stats['conversations_initiated']}")
        print(f"Last Check: {self.stats['last_check']}")
        print(f"Last Action: {self.stats['last_action']}")
        print("="*50)

def main():
    """Main function to run the monitor"""
    monitor = IDEMonitor()
    
    print("Claude Orchestration IDE Monitor")
    print("================================")
    print("Please configure your API keys in 'monitor_config.json'")
    print("Required: claude_api_key, gemini_api_key")
    print("Optional: Twilio credentials for notifications")
    print()
    
    while True:
        try:
            command = input("Enter command (start/stop/status/quit): ").strip().lower()
            
            if command == "start":
                if not monitor.is_running:
                    print("Starting monitoring... (Press Ctrl+C to stop)")
                    monitor.start_monitoring()
                else:
                    print("Already running!")
            
            elif command == "stop":
                monitor.stop_monitoring()
            
            elif command == "status":
                monitor.print_status()
            
            elif command == "quit":
                if monitor.is_running:
                    monitor.stop_monitoring()
                print("Goodbye!")
                break
            
            else:
                print("Available commands: start, stop, status, quit")
        
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            monitor.stop_monitoring()
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()