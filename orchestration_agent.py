#!/usr/bin/env python3
"""
Generic Orchestration Agent
Reads any JSON configuration and provides flexible integration capabilities
"""

import json
import requests
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

class GenericOrchestrationAgent:
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.config = {}
        self.system_prompt = ""
        self.tools = []
        self.context = {}
        self.api_config = {}
        
        if config_path:
            self.load_config()
        
    def load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load any JSON configuration file"""
        if config_path:
            self.config_path = config_path
            
        if not self.config_path:
            print("No configuration file specified")
            return {}
            
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
                
            # Extract common fields if they exist
            self.system_prompt = self.config.get("systemPrompt", "")
            self.tools = self.config.get("tools", [])
            self.context = self.config.get("context", {})
            self.api_config = self.config.get("config", {})
            
            print(f"✅ Successfully loaded configuration from: {self.config_path}")
            return self.config
            
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON configuration: {e}")
            return {}
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the loaded configuration"""
        return {
            "config_path": self.config_path,
            "has_system_prompt": bool(self.system_prompt),
            "tools_count": len(self.tools),
            "context_keys": list(self.context.keys()),
            "config_keys": list(self.api_config.keys()),
            "total_config_size": len(str(self.config))
        }
    
    def get_system_prompt(self) -> str:
        """Extract and return the system prompt"""
        return self.system_prompt
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from configuration"""
        return self.tools
    
    def get_tool_by_name(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Find a specific tool by name"""
        for tool in self.tools:
            if tool.get("name") == tool_name:
                return tool
        return None
    
    def extract_config_value(self, key_path: str, default=None) -> Any:
        """Extract a value from config using dot notation (e.g. 'config.api_key')"""
        keys = key_path.split('.')
        current = self.config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def make_api_request(self, 
                        url: str, 
                        method: str = "POST", 
                        payload: Dict = None, 
                        headers: Dict = None,
                        api_key_path: str = None) -> Dict[str, Any]:
        """Make a generic API request with configuration support"""
        try:
            # Extract API key if path provided
            if api_key_path:
                api_key = self.extract_config_value(api_key_path)
                if api_key and headers:
                    headers["Authorization"] = f"Bearer {api_key}"
            
            # Default headers
            if not headers:
                headers = {"Content-Type": "application/json"}
            
            # Add timestamp to payload if it exists
            if payload:
                payload["timestamp"] = datetime.now().isoformat()
                payload["source"] = "generic_orchestration_agent"
            
            response = requests.request(
                method=method,
                url=url,
                json=payload if method in ["POST", "PUT", "PATCH"] else None,
                headers=headers,
                timeout=10
            )
            
            return {
                "success": response.status_code in [200, 201, 202],
                "status_code": response.status_code,
                "response": response.json() if response.content else {},
                "message": f"API call {'successful' if response.status_code < 400 else 'failed'}"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {e}",
                "message": "Network error occurred"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {e}",
                "message": "An unexpected error occurred"
            }
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool based on its configuration"""
        tool = self.get_tool_by_name(tool_name)
        
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "available_tools": [t.get("name") for t in self.tools]
            }
        
        # Validate required parameters
        tool_params = tool.get("parameters", {})
        required_params = tool_params.get("required", [])
        
        missing_params = [param for param in required_params if param not in parameters]
        if missing_params:
            return {
                "success": False,
                "error": f"Missing required parameters: {missing_params}",
                "required": required_params,
                "provided": list(parameters.keys())
            }
        
        # Tool execution result
        return {
            "success": True,
            "tool_name": tool_name,
            "parameters": parameters,
            "description": tool.get("description", ""),
            "executed_at": datetime.now().isoformat(),
            "message": f"Tool '{tool_name}' executed successfully"
        }
    
    def analyze_user_input(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze user input and suggest actions based on available tools"""
        context = context or {}
        user_lower = user_input.lower()
        
        # Find relevant tools based on input
        relevant_tools = []
        for tool in self.tools:
            tool_name = tool.get("name", "").lower()
            tool_desc = tool.get("description", "").lower()
            
            if (tool_name in user_lower or 
                any(word in tool_desc for word in user_lower.split())):
                relevant_tools.append(tool)
        
        return {
            "user_input": user_input,
            "relevant_tools": relevant_tools,
            "suggested_actions": [tool.get("name") for tool in relevant_tools],
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
    
    def process_user_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main method to process user requests"""
        analysis = self.analyze_user_input(user_input, context)
        
        # If tools were found, suggest their usage
        if analysis["relevant_tools"]:
            suggested_tool = analysis["relevant_tools"][0]
            return {
                "analysis": analysis,
                "recommendation": f"Consider using tool: {suggested_tool.get('name')}",
                "tool_description": suggested_tool.get("description"),
                "action": "tool_suggested"
            }
        
        # Fallback: general response
        return {
            "analysis": analysis,
            "message": "No specific tools found for this request",
            "available_tools": [tool.get("name") for tool in self.tools],
            "action": "general_response"
        }
    
    def export_config_template(self, output_path: str) -> bool:
        """Export a template configuration file"""
        template = {
            "name": "example-project",
            "description": "Example configuration for generic orchestration agent",
            "systemPrompt": "You are an intelligent orchestration agent that helps users with various tasks.",
            "tools": [
                {
                    "name": "example_tool",
                    "description": "An example tool that demonstrates the structure",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input_text": {
                                "type": "string",
                                "description": "Input text to process"
                            },
                            "action_type": {
                                "type": "string",
                                "enum": ["analyze", "transform", "validate"],
                                "description": "Type of action to perform"
                            }
                        },
                        "required": ["input_text"]
                    }
                }
            ],
            "context": {
                "project_type": "generic",
                "framework": "flexible",
                "integration_type": "api_based"
            },
            "config": {
                "api_key": "your_api_key_here",
                "base_url": "https://api.example.com",
                "timeout": 30,
                "retry_attempts": 3
            }
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(template, f, indent=2)
            print(f"✅ Template exported to: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to export template: {e}")
            return False

def main():
    """Demo of the generic orchestration agent"""
    agent = GenericOrchestrationAgent()
    
    print("🤖 Generic Orchestration Agent")
    print("=" * 50)
    
    # Option 1: Export template
    print("1. Export configuration template")
    template_path = "config_template.json"
    agent.export_config_template(template_path)
    
    # Option 2: Load existing config if available
    config_files = [
        ".claude/projects/timezone-webapp-prettified.json",
        "config_template.json"
    ]
    
    loaded_config = None
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"\n2. Loading configuration: {config_file}")
            agent.load_config(config_file)
            loaded_config = config_file
            break
    
    if loaded_config:
        # Show config summary
        summary = agent.get_config_summary()
        print("\n📊 Configuration Summary:")
        for key, value in summary.items():
            print(f"   {key}: {value}")
        
        # Show system prompt preview
        if agent.get_system_prompt():
            print(f"\n📝 System Prompt Preview:")
            print(f"   {agent.get_system_prompt()[:150]}...")
        
        # Show available tools
        tools = agent.get_tools()
        if tools:
            print(f"\n🛠️  Available Tools ({len(tools)}):")
            for tool in tools:
                print(f"   - {tool.get('name')}: {tool.get('description', 'No description')}")
        
        # Demo user interactions
        print("\n" + "=" * 50)
        print("🗣️  Demo User Interactions:")
        
        test_inputs = [
            "I need to switch styles",
            "Call the API",
            "Get recommendations",
            "Help me with configuration"
        ]
        
        for user_input in test_inputs:
            print(f"\n💬 User: {user_input}")
            result = agent.process_user_request(user_input)
            print(f"🤖 Agent: {result.get('recommendation', result.get('message', 'No response'))}")
    
    else:
        print("\n❌ No configuration files found. Use the exported template to get started.")

if __name__ == "__main__":
    main() 