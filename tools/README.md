# 🛠️ Orchestration Tools for Timezone Converter

This directory contains Python tools that can be called by orchestration agents (like Claude AI) to manage frontend styles and generate screenshots for the timezone converter web application.

## 📦 Available Tools

### 🎨 High-Level Orchestration Functions

These are the main functions that orchestration agents should use:

#### `switch_frontend_style(style_name, base_path=".")`
Switches the frontend style of the web application.

**Parameters:**
- `style_name` (str): Style to switch to - "default", "modern", "dark", "vibrant", "corporate", "retro"
- `base_path` (str): Base directory path (optional)

**Returns:** Dictionary with success status, message, current style info

**Example:**
```python
from tools import switch_frontend_style

result = switch_frontend_style("dark")
if result["success"]:
    print(f"Switched to {result['style_info']['display_name']}")
else:
    print(f"Error: {result['error']}")
```

#### `generate_style_screenshot(style_name, include_demo=True, base_path=".")`
Generates screenshots for a specific style.

**Parameters:**
- `style_name` (str): Style to screenshot
- `include_demo` (bool): Whether to generate demo screenshots with filled form
- `base_path` (str): Base directory path (optional)

**Returns:** Dictionary with screenshot information and file paths

#### `generate_all_screenshots(include_demo=True, base_path=".")`
Generates screenshots for all available styles.

**Returns:** Dictionary with comprehensive results for all styles

#### `get_available_styles(base_path=".")`
Gets information about all available frontend styles.

**Returns:** Dictionary with style information and validation status

#### `reset_to_default_style(base_path=".")`
Resets the frontend to the default style.

**Returns:** Dictionary with operation status

## 📋 Available Styles

| Style Name | Display Name | Description |
|------------|--------------|-------------|
| `default` | Default/Original | Clean, simple design with green accents |
| `modern` | Modern/Minimalist | Purple gradient with glass morphism effects |
| `dark` | Dark Mode | Futuristic dark theme with neon accents |
| `vibrant` | Colorful/Vibrant | Rainbow gradients with playful animations |
| `corporate` | Professional/Corporate | Business design with blue theme |
| `retro` | Retro/Vintage | 80s terminal style with scanlines |

## 🚀 Quick Start

### Basic Usage

```python
# Import the tools
from tools import (
    switch_frontend_style,
    generate_style_screenshot,
    get_available_styles
)

# Get available styles
styles = get_available_styles()
print(f"Available styles: {list(styles['styles'].keys())}")

# Switch to dark mode
result = switch_frontend_style("dark")
print(f"Style switch: {result['message']}")

# Generate screenshots for the current style
screenshot_result = generate_style_screenshot("dark", include_demo=True)
print(f"Screenshots: {screenshot_result['total_files']} files generated")
```

### Orchestration Agent Usage

```python
# For Claude AI or other orchestration agents
def handle_style_request(user_request):
    """Example orchestration function"""
    
    # Parse user intent
    if "dark mode" in user_request.lower():
        result = switch_frontend_style("dark")
    elif "screenshot" in user_request.lower():
        result = generate_all_screenshots(include_demo=True)
    elif "available styles" in user_request.lower():
        result = get_available_styles()
    else:
        result = {"success": False, "error": "Unknown request"}
    
    return result
```

## 🔧 Dependencies

### Required Python Packages
```bash
pip install html2image requests
```

### System Requirements
- Flask application running on `http://127.0.0.1:5000`
- Chrome/Chromium browser (for html2image)
- Write permissions in the project directory

## 📁 Directory Structure

```
tools/
├── __init__.py                 # Package initialization
├── style_manager.py           # StyleManager class for style switching
├── screenshot_generator.py    # ScreenshotGenerator class for screenshots
├── orchestration_tools.py     # High-level orchestration functions
└── README.md                  # This documentation file
```

## 🔄 Internal Classes

### StyleManager
Handles template switching and style management.

**Key Methods:**
- `switch_style(style_name)` - Switch to a style
- `get_current_style()` - Detect current active style
- `get_available_styles()` - Get all style information
- `backup_current_template()` - Backup current template
- `restore_template()` - Restore from backup

### ScreenshotGenerator
Handles screenshot generation and HTML manipulation.

**Key Methods:**
- `generate_url_screenshot(url, filename)` - Screenshot from URL
- `generate_html_screenshot(html_file, filename)` - Screenshot from HTML file
- `create_demo_html(template_path, style_name)` - Create demo HTML with filled form
- `generate_style_screenshots(style_name, template_path)` - Generate all screenshots for a style

## 🛡️ Error Handling

All functions return dictionaries with:
- `success` (bool): Whether operation succeeded
- `message` (str): Human-readable status message
- `error` (str, optional): Error details if operation failed

## 📸 Screenshot Output

Screenshots are saved in the `screenshots/` directory:
- `{style_name}.png` - Empty form screenshot
- `{style_name}_demo.png` - Screenshot with filled form and results
- `demo_{style_name}.html` - Temporary HTML file for demo screenshots

## 🔄 Workflow

1. **Style Switching**: `StyleManager` backs up current template, copies new style template to `templates/index.html`
2. **Screenshot Generation**: `ScreenshotGenerator` uses html2image to capture web page
3. **Restoration**: Original template is restored after operations complete
4. **Cleanup**: Temporary files are cleaned up automatically

## 🚨 Important Notes

- **Flask App**: The Flask application must be running on `http://127.0.0.1:5000`
- **File Backup**: Original templates are automatically backed up before switching
- **Thread Safety**: Tools are not thread-safe; use one operation at a time
- **Dependencies**: html2image requires Chrome/Chromium browser to be installed

## 📞 Support

These tools are designed for orchestration agents. For manual usage, see the example scripts in the project root directory.