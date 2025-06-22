"""
Style Manager Tool for Frontend Style Switching
===============================================

This module provides functionality for switching between different frontend styles
in the timezone converter web application.
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time


@dataclass
class StyleInfo:
    """Information about a frontend style"""
    name: str
    display_name: str
    description: str
    template_path: str
    color_scheme: str
    features: List[str]


class StyleManager:
    """Manages frontend styles for the timezone converter application"""
    
    def __init__(self, base_path: str = "."):
        """
        Initialize StyleManager
        
        Args:
            base_path: Base directory path (default: current directory)
        """
        self.base_path = Path(base_path)
        self.templates_dir = self.base_path / "templates"
        self.styles_dir = self.templates_dir / "styles"
        self.main_template = self.templates_dir / "index.html"
        self.backup_template = self.templates_dir / "index_backup.html"
        
        # Define available styles
        self.styles = {
            "default": StyleInfo(
                name="default",
                display_name="Default/Original",
                description="Clean, simple design with green accents and traditional form layout",
                template_path=str(self.styles_dir / "original_default.html"),
                color_scheme="Green and white",
                features=["Simple layout", "Green accents", "Traditional forms"]
            ),
            "modern": StyleInfo(
                name="modern",
                display_name="Modern/Minimalist",
                description="Purple gradient background with glass morphism effects and modern typography",
                template_path=str(self.styles_dir / "modern.html"),
                color_scheme="Purple to blue gradient",
                features=["Glass morphism", "Gradient backgrounds", "Modern typography", "Smooth animations"]
            ),
            "dark": StyleInfo(
                name="dark",
                display_name="Dark Mode",
                description="Futuristic dark theme with neon accents and glowing effects",
                template_path=str(self.styles_dir / "dark.html"),
                color_scheme="Dark with purple, pink, cyan accents",
                features=["Dark background", "Neon effects", "Glowing borders", "Sci-fi aesthetic"]
            ),
            "vibrant": StyleInfo(
                name="vibrant",
                display_name="Colorful/Vibrant",
                description="Animated rainbow gradients with playful elements and emoji animations",
                template_path=str(self.styles_dir / "vibrant.html"),
                color_scheme="Rainbow gradients",
                features=["Animated gradients", "Floating emojis", "Playful typography", "Colorful design"]
            ),
            "corporate": StyleInfo(
                name="corporate",
                display_name="Professional/Corporate",
                description="Clean business design with professional blue theme and structured layout",
                template_path=str(self.styles_dir / "corporate.html"),
                color_scheme="Professional blue and white",
                features=["Business design", "Structured layout", "Professional typography", "Clean interface"]
            ),
            "retro": StyleInfo(
                name="retro",
                display_name="Retro/Vintage",
                description="80s computer terminal aesthetic with scanlines and green monospace text",
                template_path=str(self.styles_dir / "retro.html"),
                color_scheme="Green text on black background",
                features=["Terminal aesthetic", "Scanline effects", "Monospace font", "80s style"]
            )
        }
    
    def get_available_styles(self) -> Dict[str, StyleInfo]:
        """
        Get all available styles
        
        Returns:
            Dictionary of style name to StyleInfo objects
        """
        return self.styles.copy()
    
    def get_current_style(self) -> Optional[str]:
        """
        Detect the current active style by analyzing the main template
        
        Returns:
            Name of current style or None if cannot determine
        """
        if not self.main_template.exists():
            return None
        
        try:
            with open(self.main_template, 'r') as f:
                content = f.read()
            
            # Check for style-specific markers
            if "TimeSync" in content:
                return "modern"
            elif "🌙 TimeZone" in content:
                return "dark"
            elif "🌈 WorldClock" in content:
                return "vibrant"
            elif "Global Time Converter" in content and "Enterprise" in content:
                return "corporate"
            elif "TIMEMACHINE" in content:
                return "retro"
            else:
                return "default"
                
        except Exception:
            return None
    
    def backup_current_template(self) -> bool:
        """
        Backup the current template
        
        Returns:
            True if backup successful, False otherwise
        """
        try:
            if self.main_template.exists():
                shutil.copy(self.main_template, self.backup_template)
                return True
            return False
        except Exception:
            return False
    
    def restore_template(self) -> bool:
        """
        Restore template from backup
        
        Returns:
            True if restore successful, False otherwise
        """
        try:
            if self.backup_template.exists():
                shutil.move(self.backup_template, self.main_template)
                return True
            return False
        except Exception:
            return False
    
    def switch_style(self, style_name: str, create_backup: bool = True) -> Tuple[bool, str]:
        """
        Switch to a specific style
        
        Args:
            style_name: Name of the style to switch to
            create_backup: Whether to create a backup of current template
            
        Returns:
            Tuple of (success, message)
        """
        if style_name not in self.styles:
            return False, f"Style '{style_name}' not found. Available: {list(self.styles.keys())}"
        
        style_info = self.styles[style_name]
        source_path = Path(style_info.template_path)
        
        if not source_path.exists():
            return False, f"Template file not found: {source_path}"
        
        try:
            # Create backup if requested
            if create_backup:
                self.backup_current_template()
            
            # Copy the new style template
            shutil.copy(source_path, self.main_template)
            
            # Wait a moment for file system
            time.sleep(0.5)
            
            return True, f"Successfully switched to '{style_info.display_name}' style"
            
        except Exception as e:
            return False, f"Error switching style: {str(e)}"
    
    def reset_to_default(self) -> Tuple[bool, str]:
        """
        Reset to the default style
        
        Returns:
            Tuple of (success, message)
        """
        return self.switch_style("default", create_backup=False)
    
    def validate_styles(self) -> Dict[str, bool]:
        """
        Validate that all style templates exist
        
        Returns:
            Dictionary of style name to existence status
        """
        validation = {}
        for style_name, style_info in self.styles.items():
            template_path = Path(style_info.template_path)
            validation[style_name] = template_path.exists()
        return validation
    
    def get_style_info(self, style_name: str) -> Optional[StyleInfo]:
        """
        Get information about a specific style
        
        Args:
            style_name: Name of the style
            
        Returns:
            StyleInfo object or None if not found
        """
        return self.styles.get(style_name)
    
    def export_style_catalog(self, output_path: str) -> bool:
        """
        Export style catalog to JSON file
        
        Args:
            output_path: Path to save the catalog
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            catalog = {}
            for name, info in self.styles.items():
                catalog[name] = {
                    "display_name": info.display_name,
                    "description": info.description,
                    "color_scheme": info.color_scheme,
                    "features": info.features,
                    "template_exists": Path(info.template_path).exists()
                }
            
            with open(output_path, 'w') as f:
                json.dump(catalog, f, indent=2)
            
            return True
        except Exception:
            return False