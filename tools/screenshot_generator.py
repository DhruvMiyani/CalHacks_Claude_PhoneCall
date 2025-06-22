"""
Screenshot Generator Tool for Web Application Documentation
==========================================================

This module provides functionality for generating screenshots of different
frontend styles for documentation and comparison purposes.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import json


@dataclass
class ScreenshotConfig:
    """Configuration for screenshot generation"""
    width: int = 1200
    height: int = 800
    demo_height: int = 1000
    format: str = "png"
    quality: int = 90


@dataclass
class ScreenshotResult:
    """Result of screenshot generation"""
    success: bool
    file_path: Optional[str]
    file_size: Optional[int]
    error_message: Optional[str] = None


class ScreenshotGenerator:
    """Generates screenshots of web application styles"""
    
    def __init__(self, base_path: str = ".", screenshot_dir: str = "screenshots"):
        """
        Initialize ScreenshotGenerator
        
        Args:
            base_path: Base directory path (default: current directory)
            screenshot_dir: Directory to save screenshots (default: "screenshots")
        """
        self.base_path = Path(base_path)
        self.screenshot_dir = self.base_path / screenshot_dir
        self.config = ScreenshotConfig()
        
        # Create screenshots directory
        self.screenshot_dir.mkdir(exist_ok=True)
        
        # Try to import html2image
        try:
            import html2image
            self.hti = html2image.Html2Image()
            self.html2image_available = True
        except ImportError:
            self.hti = None
            self.html2image_available = False
    
    def check_dependencies(self) -> Tuple[bool, List[str]]:
        """
        Check if required dependencies are available
        
        Returns:
            Tuple of (all_available, missing_dependencies)
        """
        missing = []
        
        if not self.html2image_available:
            missing.append("html2image")
        
        # Check if localhost is accessible
        try:
            import requests
            response = requests.get("http://127.0.0.1:5000", timeout=5)
            if response.status_code != 200:
                missing.append("localhost:5000 (Flask app not running)")
        except Exception:
            missing.append("localhost:5000 (Flask app not accessible)")
        
        return len(missing) == 0, missing
    
    def configure_screenshot(self, width: int = None, height: int = None, 
                           format: str = None, quality: int = None) -> None:
        """
        Configure screenshot settings
        
        Args:
            width: Screenshot width in pixels
            height: Screenshot height in pixels
            format: Image format (png, jpg, etc.)
            quality: Image quality (1-100)
        """
        if width is not None:
            self.config.width = width
        if height is not None:
            self.config.height = height
        if format is not None:
            self.config.format = format
        if quality is not None:
            self.config.quality = quality
        
        # Update html2image settings if available
        if self.html2image_available:
            self.hti.size = (self.config.width, self.config.height)
    
    def generate_url_screenshot(self, url: str, filename: str, 
                               use_demo_height: bool = False) -> ScreenshotResult:
        """
        Generate screenshot from URL
        
        Args:
            url: URL to capture
            filename: Output filename (without extension)
            use_demo_height: Whether to use taller height for demo screenshots
            
        Returns:
            ScreenshotResult object
        """
        if not self.html2image_available:
            return ScreenshotResult(
                success=False,
                file_path=None,
                file_size=None,
                error_message="html2image library not available"
            )
        
        try:
            # Set appropriate height
            height = self.config.demo_height if use_demo_height else self.config.height
            
            # Generate screenshot
            self.hti.screenshot(
                url=url,
                save_as=f"{filename}.{self.config.format}",
                size=(self.config.width, height)
            )
            
            # Move to screenshots directory
            source_path = Path(f"{filename}.{self.config.format}")
            target_path = self.screenshot_dir / f"{filename}.{self.config.format}"
            
            if source_path.exists():
                shutil.move(str(source_path), str(target_path))
                file_size = target_path.stat().st_size
                
                return ScreenshotResult(
                    success=True,
                    file_path=str(target_path),
                    file_size=file_size
                )
            else:
                return ScreenshotResult(
                    success=False,
                    file_path=None,
                    file_size=None,
                    error_message="Screenshot file not generated"
                )
                
        except Exception as e:
            return ScreenshotResult(
                success=False,
                file_path=None,
                file_size=None,
                error_message=f"Error generating screenshot: {str(e)}"
            )
    
    def generate_html_screenshot(self, html_file: str, filename: str,
                                use_demo_height: bool = False) -> ScreenshotResult:
        """
        Generate screenshot from HTML file
        
        Args:
            html_file: Path to HTML file
            filename: Output filename (without extension)
            use_demo_height: Whether to use taller height for demo screenshots
            
        Returns:
            ScreenshotResult object
        """
        if not self.html2image_available:
            return ScreenshotResult(
                success=False,
                file_path=None,
                file_size=None,
                error_message="html2image library not available"
            )
        
        try:
            # Set appropriate height
            height = self.config.demo_height if use_demo_height else self.config.height
            
            # Generate screenshot
            self.hti.screenshot(
                html_file=html_file,
                save_as=f"{filename}.{self.config.format}",
                size=(self.config.width, height)
            )
            
            # Move to screenshots directory
            source_path = Path(f"{filename}.{self.config.format}")
            target_path = self.screenshot_dir / f"{filename}.{self.config.format}"
            
            if source_path.exists():
                shutil.move(str(source_path), str(target_path))
                file_size = target_path.stat().st_size
                
                return ScreenshotResult(
                    success=True,
                    file_path=str(target_path),
                    file_size=file_size
                )
            else:
                return ScreenshotResult(
                    success=False,
                    file_path=None,
                    file_size=None,
                    error_message="Screenshot file not generated"
                )
                
        except Exception as e:
            return ScreenshotResult(
                success=False,
                file_path=None,
                file_size=None,
                error_message=f"Error generating screenshot: {str(e)}"
            )
    
    def create_demo_html(self, template_path: str, style_name: str) -> str:
        """
        Create demo HTML with pre-filled form and results
        
        Args:
            template_path: Path to the template file
            style_name: Name of the style
            
        Returns:
            Path to the created demo HTML file
        """
        try:
            # Read template
            with open(template_path, 'r') as f:
                html_content = f.read()
            
            # Add demo data script
            demo_script = '''
    <script>
        window.addEventListener('load', function() {
            // Fill the form
            document.getElementById('cityA').value = 'New York';
            document.getElementById('cityB').value = 'London';
            
            // Show results after a delay
            setTimeout(function() {
                showResult({
                    city_a: "New York",
                    city_b: "London", 
                    time_a: "2025-06-21 16:45:38 EDT",
                    time_b: "2025-06-21 21:45:38 BST",
                    timezone_a: "America/New_York",
                    timezone_b: "Europe/London"
                });
            }, 1000);
        });
    </script>
    '''
            
            # Insert demo script before closing body tag
            html_content = html_content.replace('</body>', demo_script + '</body>')
            
            # Write demo HTML
            demo_path = self.screenshot_dir / f"demo_{style_name}.html"
            with open(demo_path, 'w') as f:
                f.write(html_content)
            
            return str(demo_path)
            
        except Exception as e:
            raise Exception(f"Error creating demo HTML: {str(e)}")
    
    def generate_style_screenshots(self, style_name: str, template_path: str,
                                 include_demo: bool = True) -> Dict[str, ScreenshotResult]:
        """
        Generate screenshots for a specific style
        
        Args:
            style_name: Name of the style
            template_path: Path to the template file
            include_demo: Whether to generate demo screenshot with filled form
            
        Returns:
            Dictionary of screenshot type to ScreenshotResult
        """
        results = {}
        
        # Generate basic screenshot from localhost
        basic_result = self.generate_url_screenshot(
            url="http://127.0.0.1:5000",
            filename=style_name
        )
        results['basic'] = basic_result
        
        # Generate demo screenshot if requested
        if include_demo:
            try:
                demo_html_path = self.create_demo_html(template_path, style_name)
                demo_result = self.generate_html_screenshot(
                    html_file=demo_html_path,
                    filename=f"{style_name}_demo",
                    use_demo_height=True
                )
                results['demo'] = demo_result
            except Exception as e:
                results['demo'] = ScreenshotResult(
                    success=False,
                    file_path=None,
                    file_size=None,
                    error_message=f"Error creating demo: {str(e)}"
                )
        
        return results
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary HTML files"""
        try:
            for file_path in self.screenshot_dir.glob("demo_*.html"):
                file_path.unlink()
        except Exception:
            pass
    
    def get_screenshot_info(self) -> Dict:
        """
        Get information about existing screenshots
        
        Returns:
            Dictionary with screenshot information
        """
        info = {
            "directory": str(self.screenshot_dir),
            "total_files": 0,
            "total_size": 0,
            "files": {}
        }
        
        try:
            for file_path in self.screenshot_dir.glob("*.png"):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    info["files"][file_path.name] = {
                        "size": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2)
                    }
                    info["total_files"] += 1
                    info["total_size"] += file_size
            
            info["total_size_mb"] = round(info["total_size"] / (1024 * 1024), 2)
            
        except Exception:
            pass
        
        return info