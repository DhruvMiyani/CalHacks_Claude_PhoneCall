"""
Orchestration Tools for Timezone Converter Web App
==================================================

High-level tools that can be called by orchestration agents like Claude
to manage frontend styles and generate screenshots.
"""

import time
from typing import Dict, List, Optional, Tuple, Union, Any
import json
from pathlib import Path

from .style_manager import StyleManager, StyleInfo
from .screenshot_generator import ScreenshotGenerator, ScreenshotResult


def switch_frontend_style(style_name: str, base_path: str = ".") -> Dict[str, Any]:
    """
    Switch the frontend style of the timezone converter web app
    
    This is the main function that orchestration agents should call to change
    the visual appearance of the web application.
    
    Args:
        style_name: Name of the style to switch to. Available options:
                   - "default": Clean, simple design with green accents
                   - "modern": Purple gradient with glass morphism effects
                   - "dark": Futuristic dark theme with neon accents
                   - "vibrant": Colorful rainbow animations with playful elements
                   - "corporate": Professional business design with blue theme
                   - "retro": 80s terminal style with scanlines and green text
        base_path: Base directory path (default: current directory)
    
    Returns:
        Dictionary with keys:
        - success (bool): Whether the operation succeeded
        - message (str): Human-readable status message
        - current_style (str): Name of the currently active style
        - style_info (dict): Information about the active style
        - error (str, optional): Error message if operation failed
    
    Example:
        >>> result = switch_frontend_style("dark")
        >>> if result["success"]:
        ...     print(f"Switched to {result['style_info']['display_name']}")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        manager = StyleManager(base_path)
        success, message = manager.switch_style(style_name)
        
        if success:
            # Wait for file system to update
            time.sleep(1)
            
            current_style = manager.get_current_style()
            style_info = manager.get_style_info(style_name)
            
            return {
                "success": True,
                "message": message,
                "current_style": current_style or style_name,
                "style_info": {
                    "name": style_info.name,
                    "display_name": style_info.display_name,
                    "description": style_info.description,
                    "color_scheme": style_info.color_scheme,
                    "features": style_info.features
                } if style_info else None
            }
        else:
            return {
                "success": False,
                "message": message,
                "current_style": manager.get_current_style(),
                "style_info": None,
                "error": message
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "current_style": None,
            "style_info": None,
            "error": str(e)
        }


def generate_style_screenshot(style_name: str, include_demo: bool = True,
                            base_path: str = ".") -> Dict[str, Any]:
    """
    Generate screenshots of a specific frontend style
    
    This function switches to the specified style, generates screenshots,
    and returns information about the generated files.
    
    Args:
        style_name: Name of the style to screenshot
        include_demo: Whether to generate demo screenshots with filled form
        base_path: Base directory path (default: current directory)
    
    Returns:
        Dictionary with keys:
        - success (bool): Whether the operation succeeded
        - message (str): Human-readable status message
        - screenshots (dict): Information about generated screenshots
        - total_files (int): Number of files generated
        - error (str, optional): Error message if operation failed
    
    Example:
        >>> result = generate_style_screenshot("modern", include_demo=True)
        >>> if result["success"]:
        ...     print(f"Generated {result['total_files']} screenshots")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    try:
        manager = StyleManager(base_path)
        generator = ScreenshotGenerator(base_path)
        
        # Check dependencies
        deps_ok, missing_deps = generator.check_dependencies()
        if not deps_ok:
            return {
                "success": False,
                "message": f"Missing dependencies: {', '.join(missing_deps)}",
                "screenshots": {},
                "total_files": 0,
                "error": f"Missing dependencies: {', '.join(missing_deps)}"
            }
        
        # Get style info
        style_info = manager.get_style_info(style_name)
        if not style_info:
            return {
                "success": False,
                "message": f"Style '{style_name}' not found",
                "screenshots": {},
                "total_files": 0,
                "error": f"Style '{style_name}' not found"
            }
        
        # Backup current style
        original_style = manager.get_current_style()
        manager.backup_current_template()
        
        try:
            # Switch to target style
            success, switch_message = manager.switch_style(style_name, create_backup=False)
            if not success:
                return {
                    "success": False,
                    "message": switch_message,
                    "screenshots": {},
                    "total_files": 0,
                    "error": switch_message
                }
            
            # Wait for style to load
            time.sleep(2)
            
            # Generate screenshots
            screenshot_results = generator.generate_style_screenshots(
                style_name, style_info.template_path, include_demo
            )
            
            # Process results
            screenshots = {}
            total_files = 0
            all_successful = True
            
            for screenshot_type, result in screenshot_results.items():
                screenshots[screenshot_type] = {
                    "success": result.success,
                    "file_path": result.file_path,
                    "file_size": result.file_size,
                    "file_size_mb": round(result.file_size / (1024 * 1024), 2) if result.file_size else None,
                    "error": result.error_message
                }
                
                if result.success:
                    total_files += 1
                else:
                    all_successful = False
            
            return {
                "success": all_successful,
                "message": f"Generated {total_files} screenshots for {style_info.display_name}",
                "screenshots": screenshots,
                "total_files": total_files,
                "style_info": {
                    "name": style_info.name,
                    "display_name": style_info.display_name,
                    "description": style_info.description
                }
            }
            
        finally:
            # Restore original style
            if original_style and original_style != style_name:
                manager.switch_style(original_style, create_backup=False)
            else:
                manager.restore_template()
            
            # Cleanup temp files
            generator.cleanup_temp_files()
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "screenshots": {},
            "total_files": 0,
            "error": str(e)
        }


def generate_all_screenshots(include_demo: bool = True, base_path: str = ".") -> Dict[str, Any]:
    """
    Generate screenshots for all available frontend styles
    
    This function iterates through all available styles, generating screenshots
    for each one and returning comprehensive information about the results.
    
    Args:
        include_demo: Whether to generate demo screenshots with filled form
        base_path: Base directory path (default: current directory)
    
    Returns:
        Dictionary with keys:
        - success (bool): Whether the operation succeeded overall
        - message (str): Human-readable status message
        - results (dict): Results for each style
        - total_files (int): Total number of files generated
        - successful_styles (list): List of styles that succeeded
        - failed_styles (list): List of styles that failed
        - error (str, optional): Error message if operation failed
    
    Example:
        >>> result = generate_all_screenshots(include_demo=True)
        >>> print(f"Generated {result['total_files']} total screenshots")
        >>> print(f"Successful: {result['successful_styles']}")
        >>> print(f"Failed: {result['failed_styles']}")
    """
    try:
        manager = StyleManager(base_path)
        generator = ScreenshotGenerator(base_path)
        
        # Check dependencies
        deps_ok, missing_deps = generator.check_dependencies()
        if not deps_ok:
            return {
                "success": False,
                "message": f"Missing dependencies: {', '.join(missing_deps)}",
                "results": {},
                "total_files": 0,
                "successful_styles": [],
                "failed_styles": [],
                "error": f"Missing dependencies: {', '.join(missing_deps)}"
            }
        
        # Get all styles
        available_styles = manager.get_available_styles()
        
        # Backup current style
        original_style = manager.get_current_style()
        manager.backup_current_template()
        
        results = {}
        total_files = 0
        successful_styles = []
        failed_styles = []
        
        try:
            for style_name, style_info in available_styles.items():
                print(f"Processing {style_name} style...")
                
                # Switch to style
                success, switch_message = manager.switch_style(style_name, create_backup=False)
                if not success:
                    results[style_name] = {
                        "success": False,
                        "message": switch_message,
                        "screenshots": {},
                        "files_generated": 0
                    }
                    failed_styles.append(style_name)
                    continue
                
                # Wait for style to load
                time.sleep(2)
                
                # Generate screenshots
                screenshot_results = generator.generate_style_screenshots(
                    style_name, style_info.template_path, include_demo
                )
                
                # Process results for this style
                screenshots = {}
                files_generated = 0
                style_successful = True
                
                for screenshot_type, result in screenshot_results.items():
                    screenshots[screenshot_type] = {
                        "success": result.success,
                        "file_path": result.file_path,
                        "file_size": result.file_size,
                        "file_size_mb": round(result.file_size / (1024 * 1024), 2) if result.file_size else None,
                        "error": result.error_message
                    }
                    
                    if result.success:
                        files_generated += 1
                        total_files += 1
                    else:
                        style_successful = False
                
                results[style_name] = {
                    "success": style_successful,
                    "message": f"Generated {files_generated} screenshots",
                    "screenshots": screenshots,
                    "files_generated": files_generated,
                    "style_info": {
                        "display_name": style_info.display_name,
                        "description": style_info.description
                    }
                }
                
                if style_successful:
                    successful_styles.append(style_name)
                else:
                    failed_styles.append(style_name)
            
            overall_success = len(failed_styles) == 0
            
            return {
                "success": overall_success,
                "message": f"Generated {total_files} screenshots across {len(successful_styles)} styles",
                "results": results,
                "total_files": total_files,
                "successful_styles": successful_styles,
                "failed_styles": failed_styles
            }
            
        finally:
            # Restore original style
            if original_style:
                manager.switch_style(original_style, create_backup=False)
            else:
                manager.restore_template()
            
            # Cleanup temp files
            generator.cleanup_temp_files()
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "results": {},
            "total_files": 0,
            "successful_styles": [],
            "failed_styles": [],
            "error": str(e)
        }


def get_available_styles(base_path: str = ".") -> Dict[str, Any]:
    """
    Get information about all available frontend styles
    
    Args:
        base_path: Base directory path (default: current directory)
    
    Returns:
        Dictionary with keys:
        - styles (dict): Information about each available style
        - current_style (str): Name of the currently active style
        - total_styles (int): Number of available styles
        - validation (dict): Template file validation results
    
    Example:
        >>> styles_info = get_available_styles()
        >>> for name, info in styles_info["styles"].items():
        ...     print(f"{name}: {info['display_name']}")
    """
    try:
        manager = StyleManager(base_path)
        
        available_styles = manager.get_available_styles()
        current_style = manager.get_current_style()
        validation = manager.validate_styles()
        
        styles = {}
        for name, style_info in available_styles.items():
            styles[name] = {
                "display_name": style_info.display_name,
                "description": style_info.description,
                "color_scheme": style_info.color_scheme,
                "features": style_info.features,
                "template_exists": validation.get(name, False),
                "is_current": name == current_style
            }
        
        return {
            "styles": styles,
            "current_style": current_style,
            "total_styles": len(styles),
            "validation": validation
        }
        
    except Exception as e:
        return {
            "styles": {},
            "current_style": None,
            "total_styles": 0,
            "validation": {},
            "error": str(e)
        }


def reset_to_default_style(base_path: str = ".") -> Dict[str, Any]:
    """
    Reset the frontend to the default style
    
    Args:
        base_path: Base directory path (default: current directory)
    
    Returns:
        Dictionary with keys:
        - success (bool): Whether the operation succeeded
        - message (str): Human-readable status message
        - current_style (str): Name of the currently active style
        - error (str, optional): Error message if operation failed
    
    Example:
        >>> result = reset_to_default_style()
        >>> if result["success"]:
        ...     print("Reset to default style")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    return switch_frontend_style("default", base_path)