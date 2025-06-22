#!/usr/bin/env python3
"""
Enhanced Claude Orchestrator Agent
Based on the architecture: FastAPI backend, Gemini Vision, and enhanced tools
"""

import os
import json
import asyncio
import time
import subprocess
import pyautogui
import pyperclip
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List
from PIL import Image
import mss
import google.generativeai as genai
from twilio.rest import Client
import anthropic
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from threading import Thread
import queue

class ClaudeOrchestrator:
    def __init__(self):
        self.config = self.load_config()
        self.is_running = False
        self.conversation_history = []
        self.screenshot_queue = queue.Queue()
        self.websocket_connections = []
        
        self.stats = {
            "total_checks": 0,
            "errors_detected": 0,
            "conversations_initiated": 0,
            "tools_executed": 0,
            "vapi_messages_sent": 0,
            "last_check": None,
            "last_error": None,
            "last_action": None,
            "error_history": [],
            "conversation_history": []
        }
        
        # Initialize clients
        if self.config.get('gemini_api_key'):
            genai.configure(api_key=self.config['gemini_api_key'])
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        if self.config.get('claude_api_key'):
            self.claude_client = anthropic.Anthropic(api_key=self.config['claude_api_key'])
        
        # Enhanced Claude tools 
        self.claude_tools = [
            {
                "name": "send_error_notification",
                "description": "Send a notification about a detected programming error via Twilio SMS",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "error_summary": {"type": "string", "description": "A concise summary of the error detected"},
                        "error_type": {"type": "string", "description": "Type of error (e.g., compilation, runtime, syntax, build)"},
                        "urgency": {"type": "string", "enum": ["low", "medium", "high"], "description": "Urgency level of the error"},
                        "suggested_action": {"type": "string", "description": "Suggested next steps to resolve the error"}
                    },
                    "required": ["error_summary", "error_type", "urgency"]
                }
            },
            {
                "name": "copy_to_clipboard",
                "description": "Copy text content to clipboard using Cursor extension functionality",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Content to copy to clipboard"},
                        "content_type": {"type": "string", "enum": ["code", "error", "command", "text"], "description": "Type of content being copied"}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "execute_terminal_command",
                "description": "Execute a command in the Linux terminal/chat box",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Command to execute in terminal"},
                        "working_directory": {"type": "string", "description": "Working directory for command execution"},
                        "timeout": {"type": "integer", "description": "Timeout in seconds (default: 30)"}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "trigger_cursor_action",
                "description": "Trigger specific Cursor IDE actions like opening chat, running commands, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["open_chat", "run_code", "debug", "format", "search"], "description": "Action to trigger in Cursor"},
                        "context": {"type": "string", "description": "Additional context for the action"},
                        "file_path": {"type": "string", "description": "File path if action is file-specific"}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "initiate_conversation",
                "description": "Initiate a conversation/assistance session when Cursor chat or similar tool is asking for human input",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "context": {"type": "string", "description": "Context of what the AI assistant is asking help with"},
                        "conversation_type": {"type": "string", "enum": ["cursor_chat", "copilot", "code_review", "debugging"], "description": "Type of conversation being initiated"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority of the conversation request"}
                    },
                    "required": ["context", "conversation_type"]
                }
            },
            {
                "name": "update_conversation_history",
                "description": "Update the full conversation history with new context",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Message to add to conversation history"},
                        "role": {"type": "string", "enum": ["user", "assistant", "system"], "description": "Role of the message sender"},
                        "metadata": {"type": "object", "description": "Additional metadata about the message"}
                    },
                    "required": ["message", "role"]
                }
            },
            {
                "name": "send_to_vapi",
                "description": "Send conversational history and context to VAPI assistant for voice interaction",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Text message to send to VAPI assistant"},
                        "context_type": {"type": "string", "enum": ["error", "conversation", "status", "general"], "description": "Type of context being sent"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority level for VAPI processing"}
                    },
                    "required": ["message", "context_type"]
                }
            }
        ]
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        config_file = 'orchestrator_config.json'
        default_config = {
            "claude_api_key": "",
            "gemini_api_key": "",
            "twilio_account_sid": "",
            "twilio_auth_token": "",
            "twilio_from_phone": "",
            "twilio_to_phone": "",
            "vapi_public_api_key": "",
            "vapi_assistant_id": "",
            "monitor_interval": 30,
            "error_cooldown": 300,
            "fastapi_port": 8000,
            "fastapi_host": "localhost",
            "enable_websocket": True,
            "enable_vapi_integration": True,
            "screenshot_history_limit": 100,
            "conversation_history_limit": 1000
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
        """Enhanced logging with WebSocket broadcast"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        # Broadcast to WebSocket connections
        if self.websocket_connections:
            log_data = {
                "type": "log",
                "timestamp": timestamp,
                "level": level,
                "message": message
            }
            self.broadcast_to_websockets(log_data)
    
    async def broadcast_to_websockets(self, data: Dict[str, Any]):
        """Broadcast data to all WebSocket connections"""
        if not self.websocket_connections:
            return
        
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(data)
            except:
                disconnected.append(websocket)
        
        # Remove disconnected WebSockets
        for ws in disconnected:
            if ws in self.websocket_connections:
                self.websocket_connections.remove(ws)
    
    def take_screenshot(self) -> Optional[Image.Image]:
        """Take screenshot of primary monitor"""
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Add to screenshot queue for history
                timestamp = datetime.now().isoformat()
                self.screenshot_queue.put({
                    "timestamp": timestamp,
                    "image": img,
                    "size": screenshot.size
                })
                
                # Maintain screenshot history limit
                while self.screenshot_queue.qsize() > self.config["screenshot_history_limit"]:
                    self.screenshot_queue.get()
                
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
            Analyze this screenshot for multiple scenarios:
            
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
            
            3. CURSOR EXTENSION OPPORTUNITIES: Look for:
               - Code that could be copied to clipboard
               - Commands that should be executed
               - Files that need to be opened or modified
            
            4. TERMINAL/LINUX INTERACTION NEEDS: Look for:
               - Commands waiting to be executed
               - Terminal prompts needing input
               - System messages requiring attention
            
            Respond with JSON in this format:
            {
                "has_error": boolean,
                "error_details": {
                    "type": "compilation|runtime|syntax|build|test|deployment",
                    "description": "detailed description of the error",
                    "severity": "low|medium|high",
                    "location": "where the error appears (file, line, etc.)",
                    "suggested_fix": "potential solution or next step"
                },
                "has_chat_request": boolean,
                "chat_details": {
                    "type": "cursor_chat|copilot|code_review|debugging",
                    "context": "what the AI is asking help with",
                    "urgency": "low|medium|high"
                },
                "cursor_opportunities": {
                    "copy_content": "content that should be copied to clipboard",
                    "executable_commands": ["list of commands that could be executed"],
                    "file_actions": ["list of file operations needed"]
                },
                "terminal_needs": {
                    "pending_commands": ["commands waiting in terminal"],
                    "needs_input": boolean,
                    "system_messages": ["important system messages"]
                },
                "screenshot_analysis": "brief description of what's visible in the screenshot"
            }
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
                    "cursor_opportunities": {},
                    "terminal_needs": {},
                    "screenshot_analysis": "Fallback analysis due to JSON parsing error"
                }
                
        except Exception as e:
            self.log(f"Error analyzing with Gemini: {e}", "ERROR")
            return None
    
    def claude_orchestrate(self, gemini_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhanced Claude orchestration with more tools and context"""
        try:
            if not hasattr(self, 'claude_client'):
                self.log("Claude client not initialized", "ERROR")
                return None
            
            # Prepare enhanced context for Claude
            context = f"""
            I am an enhanced orchestration agent monitoring an IDE and development environment.
            
            Here's the current analysis from Gemini Vision:
            {json.dumps(gemini_analysis, indent=2)}
            
            Recent conversation history (last 10 entries):
            {json.dumps(self.conversation_history[-10:], indent=2)}
            
            Recent error history (to avoid duplicate notifications):
            {json.dumps(self.stats["error_history"][-5:], indent=2)}
            
            Current stats:
            - Total checks: {self.stats["total_checks"]}
            - Errors detected: {self.stats["errors_detected"]}
            - Conversations initiated: {self.stats["conversations_initiated"]}
            - Tools executed: {self.stats["tools_executed"]}
            
            Based on this analysis, I need to decide what actions to take. Available tools:
            1. send_error_notification - for programming errors needing attention
            2. copy_to_clipboard - for copying useful content via Cursor extension
            3. execute_terminal_command - for running Linux/terminal commands
            4. trigger_cursor_action - for triggering Cursor IDE actions
            5. initiate_conversation - for AI chat requests needing human input
            6. update_conversation_history - for maintaining conversation context
            7. send_to_vapi - for sending conversational history and context to VAPI assistant
            
            Consider:
            - Don't send duplicate notifications for the same error within cooldown period
            - Prioritize high-severity errors and urgent chat requests
            - Use copy/terminal tools proactively when opportunities are detected
            - Maintain conversation history for context
            - Provide clear, actionable responses
            """
            
            message = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2048,
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
                results = []
                for content in message.content:
                    if content.type == "tool_use":
                        tool_name = content.name
                        tool_input = content.input
                        
                        self.log(f"Claude decided to use tool: {tool_name}")
                        self.stats["tools_executed"] += 1
                        
                        if tool_name == "send_error_notification":
                            result = self.execute_error_notification(tool_input)
                        elif tool_name == "copy_to_clipboard":
                            result = self.execute_copy_to_clipboard(tool_input)
                        elif tool_name == "execute_terminal_command":
                            result = self.execute_terminal_command(tool_input)
                        elif tool_name == "trigger_cursor_action":
                            result = self.execute_cursor_action(tool_input)
                        elif tool_name == "initiate_conversation":
                            result = self.execute_conversation_initiation(tool_input)
                        elif tool_name == "update_conversation_history":
                            result = self.execute_update_conversation_history(tool_input)
                        elif tool_name == "send_to_vapi":
                            result = self.execute_send_to_vapi(tool_input)
                        else:
                            result = {"action": "unknown_tool", "reasoning": f"Unknown tool: {tool_name}"}
                        
                        results.append(result)
                
                return {
                    "action": "multiple_tools",
                    "results": results,
                    "reasoning": "Claude executed multiple tools based on analysis"
                }
            
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
    
    def execute_copy_to_clipboard(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute copy to clipboard functionality"""
        try:
            content = tool_input.get('content', '')
            content_type = tool_input.get('content_type', 'text')
            
            # Copy to clipboard
            pyperclip.copy(content)
            
            self.log(f"Copied {content_type} to clipboard: {content[:100]}...")
            
            return {
                "action": "copy_to_clipboard",
                "reasoning": f"Successfully copied {content_type} content to clipboard",
                "content_length": len(content),
                "content_type": content_type
            }
            
        except Exception as e:
            self.log(f"Error copying to clipboard: {e}", "ERROR")
            return {
                "action": "none",
                "reasoning": f"Failed to copy to clipboard: {e}"
            }
    
    def execute_terminal_command(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute terminal command"""
        try:
            command = tool_input.get('command', '')
            working_directory = tool_input.get('working_directory', os.getcwd())
            timeout = tool_input.get('timeout', 30)
            
            self.log(f"Executing terminal command: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_directory,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "action": "execute_terminal_command",
                "reasoning": f"Command executed: {command}",
                "command": command,
                "return_code": result.returncode,
                "stdout": result.stdout[:1000],  # Limit output
                "stderr": result.stderr[:1000],
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "action": "execute_terminal_command",
                "reasoning": f"Command timed out: {command}",
                "command": command,
                "success": False,
                "error": "Timeout"
            }
        except Exception as e:
            self.log(f"Error executing terminal command: {e}", "ERROR")
            return {
                "action": "none",
                "reasoning": f"Failed to execute command: {e}"
            }
    
    def execute_cursor_action(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Cursor IDE actions"""
        try:
            action = tool_input.get('action', '')
            context = tool_input.get('context', '')
            file_path = tool_input.get('file_path', '')
            
            self.log(f"Triggering Cursor action: {action}")
            
            # Define keyboard shortcuts for Cursor actions
            cursor_shortcuts = {
                "open_chat": ["cmd", "shift", "i"] if os.name == "posix" else ["ctrl", "shift", "i"],
                "run_code": ["cmd", "shift", "r"] if os.name == "posix" else ["ctrl", "shift", "r"],
                "debug": ["f5"],
                "format": ["cmd", "shift", "f"] if os.name == "posix" else ["ctrl", "shift", "f"],
                "search": ["cmd", "f"] if os.name == "posix" else ["ctrl", "f"]
            }
            
            if action in cursor_shortcuts:
                # Use pyautogui to trigger keyboard shortcuts
                pyautogui.hotkey(*cursor_shortcuts[action])
                
                return {
                    "action": "trigger_cursor_action",
                    "reasoning": f"Successfully triggered Cursor action: {action}",
                    "cursor_action": action,
                    "context": context,
                    "success": True
                }
            else:
                return {
                    "action": "trigger_cursor_action",
                    "reasoning": f"Unknown Cursor action: {action}",
                    "success": False
                }
                
        except Exception as e:
            self.log(f"Error triggering Cursor action: {e}", "ERROR")
            return {
                "action": "none",
                "reasoning": f"Failed to trigger Cursor action: {e}"
            }
    
    def execute_update_conversation_history(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Update conversation history"""
        try:
            message = tool_input.get('message', '')
            role = tool_input.get('role', 'assistant')
            metadata = tool_input.get('metadata', {})
            
            conversation_entry = {
                "timestamp": datetime.now().isoformat(),
                "role": role,
                "message": message,
                "metadata": metadata
            }
            
            self.conversation_history.append(conversation_entry)
            
            # Maintain conversation history limit
            if len(self.conversation_history) > self.config["conversation_history_limit"]:
                self.conversation_history = self.conversation_history[-self.config["conversation_history_limit"]:]
            
            self.stats["conversation_history"].append(conversation_entry)
            
            return {
                "action": "update_conversation_history",
                "reasoning": f"Added {role} message to conversation history",
                "message_length": len(message),
                "history_size": len(self.conversation_history)
            }
            
        except Exception as e:
            self.log(f"Error updating conversation history: {e}", "ERROR")
            return {
                "action": "none",
                "reasoning": f"Failed to update conversation history: {e}"
            }
    
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
    
    def execute_send_to_vapi(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the send to VAPI tool for conversational history"""
        try:
            if not self.config.get('enable_vapi_integration'):
                return {
                    "action": "none",
                    "reasoning": "VAPI integration is disabled"
                }
            
            if not all([self.config.get('vapi_public_api_key'), self.config.get('vapi_assistant_id')]):
                self.log("VAPI configuration incomplete", "WARNING")
                return {
                    "action": "none",
                    "reasoning": "VAPI configuration incomplete"
                }
            
            message = tool_input.get('message', '')
            context_type = tool_input.get('context_type', 'general')
            priority = tool_input.get('priority', 'medium')
            
            self.log(f"Sending {context_type} message to VAPI: {message[:100]}...")
            
            # Prepare VAPI payload
            vapi_payload = {
                "assistant": {
                    "assistantId": self.config['vapi_assistant_id']
                },
                "customer": {
                    "number": "+1234567890"  # You can configure this
                },
                "message": {
                    "type": "text",
                    "content": message,
                    "metadata": {
                        "context_type": context_type,
                        "priority": priority,
                        "timestamp": datetime.now().isoformat(),
                        "source": "claude_orchestrator"
                    }
                }
            }
            
            # VAPI API headers
            headers = {
                "Authorization": f"Bearer {self.config['vapi_public_api_key']}",
                "Content-Type": "application/json"
            }
            
            # Send to VAPI API
            vapi_response = requests.post(
                "https://api.vapi.ai/call",
                json=vapi_payload,
                headers=headers,
                timeout=10
            )
            
            if vapi_response.status_code in [200, 201]:
                self.stats["vapi_messages_sent"] += 1
                self.stats["last_action"] = f"Sent {context_type} message to VAPI"
                
                self.log(f"Message sent to VAPI successfully (Status: {vapi_response.status_code})", "SUCCESS")
                
                # Add to conversation history
                conversation_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "role": "system",
                    "message": f"Sent to VAPI: {message}",
                    "metadata": {
                        "context_type": context_type,
                        "priority": priority,
                        "vapi_response_status": vapi_response.status_code
                    }
                }
                self.conversation_history.append(conversation_entry)
                
                return {
                    "action": "send_to_vapi",
                    "reasoning": f"Successfully sent {context_type} message to VAPI assistant",
                    "message_length": len(message),
                    "context_type": context_type,
                    "priority": priority,
                    "vapi_messages_sent": self.stats["vapi_messages_sent"],
                    "vapi_response_status": vapi_response.status_code
                }
            else:
                error_msg = f"VAPI API returned status {vapi_response.status_code}: {vapi_response.text}"
                self.log(f"Failed to send message to VAPI: {error_msg}", "ERROR")
                return {
                    "action": "none",
                    "reasoning": f"Failed to send to VAPI: {error_msg}"
                }
                
        except requests.exceptions.Timeout:
            self.log("VAPI request timed out", "ERROR")
            return {
                "action": "none",
                "reasoning": "VAPI request timed out"
            }
        except requests.exceptions.RequestException as e:
            self.log(f"VAPI request failed: {e}", "ERROR")
            return {
                "action": "none",
                "reasoning": f"VAPI request failed: {e}"
            }
        except Exception as e:
            self.log(f"Error executing send to VAPI: {e}", "ERROR")
            return {
                "action": "none",
                "reasoning": f"Error executing send to VAPI: {e}"
            }

    def send_conversation_history_to_vapi(self) -> bool:
        """Send full conversation history to VAPI as text input"""
        try:
            if not self.config.get('enable_vapi_integration') or not self.conversation_history:
                return False
            
            # Prepare conversation history summary
            recent_history = self.conversation_history[-10:]  # Last 10 entries
            history_text = "Recent conversation history:\n\n"
            
            for entry in recent_history:
                timestamp = entry.get('timestamp', 'Unknown time')
                role = entry.get('role', 'unknown')
                message = entry.get('message', '')
                metadata = entry.get('metadata', {})
                
                history_text += f"[{timestamp}] {role.upper()}: {message}\n"
                if metadata:
                    history_text += f"  Context: {metadata}\n"
                history_text += "\n"
            
            # Add current stats
            history_text += f"\nCurrent Stats:\n"
            history_text += f"- Total checks: {self.stats['total_checks']}\n"
            history_text += f"- Errors detected: {self.stats['errors_detected']}\n"
            history_text += f"- Tools executed: {self.stats['tools_executed']}\n"
            history_text += f"- Last action: {self.stats['last_action']}\n"
            
            # Execute the VAPI tool
            vapi_tool_input = {
                "message": history_text,
                "context_type": "conversation",
                "priority": "medium"
            }
            
            result = self.execute_send_to_vapi(vapi_tool_input)
            return result.get("action") == "send_to_vapi"
            
        except Exception as e:
            self.log(f"Error sending conversation history to VAPI: {e}", "ERROR")
            return False
    
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
        """Enhanced monitoring loop orchestrated by Claude"""
        self.log("Starting enhanced Claude orchestration monitor loop")
        vapi_sync_counter = 0
        
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
                self.log("Sending screenshot to Gemini for enhanced analysis...")
                gemini_analysis = self.analyze_with_gemini(screenshot)
                if not gemini_analysis:
                    await asyncio.sleep(self.config["monitor_interval"])
                    continue
                
                self.log(f"Gemini analysis: errors={gemini_analysis.get('has_error')}, "
                        f"chat_requests={gemini_analysis.get('has_chat_request')}, "
                        f"cursor_opportunities={bool(gemini_analysis.get('cursor_opportunities'))}")
                
                # Let Claude orchestrate the response
                needs_action = (
                    gemini_analysis.get('has_error') or 
                    gemini_analysis.get('has_chat_request') or
                    gemini_analysis.get('cursor_opportunities') or
                    gemini_analysis.get('terminal_needs')
                )
                
                if needs_action:
                    self.log("Sending to Claude for enhanced orchestration...")
                    claude_decision = self.claude_orchestrate(gemini_analysis)
                    
                    if claude_decision:
                        self.log(f"Claude decision: {claude_decision.get('action')} - {claude_decision.get('reasoning')}")
                        
                        # Broadcast decision to WebSocket clients
                        await self.broadcast_to_websockets({
                            "type": "claude_decision",
                            "timestamp": datetime.now().isoformat(),
                            "analysis": gemini_analysis,
                            "decision": claude_decision
                        })
                    else:
                        self.log("Claude orchestration failed", "WARNING")
                else:
                    self.log("No errors, chat requests, or opportunities detected - continuing monitoring")
                
                # Periodically sync conversation history to VAPI (every 5 cycles)
                vapi_sync_counter += 1
                if vapi_sync_counter >= 5 and self.config.get('enable_vapi_integration'):
                    self.log("Syncing conversation history to VAPI...")
                    if self.send_conversation_history_to_vapi():
                        self.log("Conversation history sent to VAPI successfully", "SUCCESS")
                    vapi_sync_counter = 0
                    
            except Exception as e:
                self.log(f"Error in monitor loop: {e}", "ERROR")
            
            await asyncio.sleep(self.config["monitor_interval"])
        
        self.log("Enhanced monitor loop stopped")
    
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
        self.log("Starting enhanced Claude orchestration monitoring...")
        
        # Run the async monitor loop
        asyncio.run(self.monitor_loop())
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.is_running = False
        self.log("Stopping monitoring...")
    
    def print_status(self):
        """Print current status"""
        print("\n" + "="*60)
        print("ENHANCED CLAUDE ORCHESTRATION MONITOR STATUS")
        print("="*60)
        print(f"Running: {'Yes' if self.is_running else 'No'}")
        print(f"Total Checks: {self.stats['total_checks']}")
        print(f"Errors Detected: {self.stats['errors_detected']}")
        print(f"Conversations Initiated: {self.stats['conversations_initiated']}")
        print(f"Tools Executed: {self.stats['tools_executed']}")
        print(f"VAPI Messages Sent: {self.stats['vapi_messages_sent']}")
        print(f"WebSocket Connections: {len(self.websocket_connections)}")
        print(f"Conversation History Size: {len(self.conversation_history)}")
        print(f"VAPI Integration: {'Enabled' if self.config.get('enable_vapi_integration') else 'Disabled'}")
        print(f"Last Check: {self.stats['last_check']}")
        print(f"Last Action: {self.stats['last_action']}")
        print("="*60)

# FastAPI Backend Integration
app = FastAPI(title="Claude Orchestrator API", description="Enhanced Claude orchestrator with FastAPI backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = ClaudeOrchestrator()

@app.get("/")
async def root():
    return {"message": "Enhanced Claude Orchestrator API", "status": "running"}

@app.get("/status")
async def get_status():
    return {
        "is_running": orchestrator.is_running,
        "stats": orchestrator.stats,
        "config": {k: v for k, v in orchestrator.config.items() if 'api_key' not in k and 'token' not in k}
    }

@app.post("/start")
async def start_monitoring():
    if orchestrator.is_running:
        return {"status": "already_running"}
    
    # Start monitoring in background thread
    def run_monitor():
        orchestrator.start_monitoring()
    
    thread = Thread(target=run_monitor)
    thread.daemon = True
    thread.start()
    
    return {"status": "started"}

@app.post("/stop")
async def stop_monitoring():
    orchestrator.stop_monitoring()
    return {"status": "stopped"}

@app.get("/conversation_history")
async def get_conversation_history():
    return {
        "history": orchestrator.conversation_history,
        "total_entries": len(orchestrator.conversation_history)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    orchestrator.websocket_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_json()
            # Handle WebSocket commands if needed
            if data.get("command") == "get_status":
                await websocket.send_json({
                    "type": "status",
                    "data": orchestrator.stats
                })
    except WebSocketDisconnect:
        if websocket in orchestrator.websocket_connections:
            orchestrator.websocket_connections.remove(websocket)

def run_fastapi_server():
    """Run FastAPI server"""
    uvicorn.run(
        app, 
        host=orchestrator.config["fastapi_host"], 
        port=orchestrator.config["fastapi_port"],
        log_level="info"
    )

def main():
    """Enhanced main function with FastAPI integration"""
    print("Enhanced Claude Orchestrator with FastAPI Backend")
    print("=" * 50)
    print("Please configure your API keys in 'orchestrator_config.json'")
    print("Required: claude_api_key, gemini_api_key")
    print("Optional: Twilio credentials for notifications")
    print(f"FastAPI server will run on: http://{orchestrator.config['fastapi_host']}:{orchestrator.config['fastapi_port']}")
    print()
    
    # Start FastAPI server in background thread
    if orchestrator.config.get("enable_websocket", True):
        fastapi_thread = Thread(target=run_fastapi_server)
        fastapi_thread.daemon = True
        fastapi_thread.start()
        print(f"FastAPI server started on port {orchestrator.config['fastapi_port']}")
    
    while True:
        try:
            command = input("Enter command (start/stop/status/quit): ").strip().lower()
            
            if command == "start":
                if not orchestrator.is_running:
                    print("Starting enhanced monitoring... (Press Ctrl+C to stop)")
                    
                    # Start monitoring in background thread
                    def run_monitor():
                        orchestrator.start_monitoring()
                    
                    monitor_thread = Thread(target=run_monitor)
                    monitor_thread.daemon = True
                    monitor_thread.start()
                    
                    print("Monitoring started in background. Use 'status' to check progress.")
                else:
                    print("Already running!")
            
            elif command == "stop":
                orchestrator.stop_monitoring()
            
            elif command == "status":
                orchestrator.print_status()
            
            elif command == "quit":
                if orchestrator.is_running:
                    orchestrator.stop_monitoring()
                print("Goodbye!")
                break
            
            else:
                print("Available commands: start, stop, status, quit")
        
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            orchestrator.stop_monitoring()
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main() 