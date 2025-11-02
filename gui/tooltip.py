"""
Tooltip widget implementation for displaying helpful hints.

This module provides an enhanced ToolTip class that can be used to add tooltips
to Tkinter widgets with various customization options.
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Union, Dict, Any


class ToolTip:
    """
    Create a tooltip for a given widget with various customization options.
    
    Args:
        widget: The widget this tooltip is associated with
        text: The text to display in the tooltip, or a dictionary containing
              tooltip configuration including 'text' and other options
        **kwargs: Additional configuration options that will override any
                 settings in the text parameter if it's a dictionary
    """
    def __init__(self, widget: tk.Widget, text: Union[str, Dict[str, Any]], **kwargs):
        self.widget = widget
        self.config = self._parse_config(text, **kwargs)
        self.tooltip = None
        
        # Bind events
        self.widget.bind("<Enter>", self.enter, add='+')
        self.widget.bind("<Leave>", self.leave, add='+')
        self.widget.bind("<ButtonPress>", self.leave, add='+')
    
    def _parse_config(self, text: Union[str, Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Parse the tooltip configuration from various input formats."""
        # Default configuration
        config = {
            'text': 'No description available.',
            'background': '#ffffe0',
            'foreground': 'black',
            'borderwidth': 1,
            'relief': 'solid',
            'padding': 5,
            'wraplength': 300,
            'justify': 'left',
            'delay': 500,  # ms before showing tooltip
            'follow_cursor': True,
            'offset_x': 10,
            'offset_y': 10
        }
        
        # Update with text if it's a dictionary
        if isinstance(text, dict):
            config.update(text)
        else:
            config['text'] = text
            
        # Update with any additional kwargs
        config.update(kwargs)
        
        return config
    
    def _get_monitor_dimensions(self, x: int, y: int) -> tuple[int, int, int, int]:
        """
        Get the dimensions of the monitor containing the given coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Tuple of (x, y, width, height) for the monitor containing the coordinates
        """
        try:
            # Try to get the screen that contains the given coordinates
            screen = self.widget.winfo_toplevel().tk.call('winfo', 'screen', f'.!toplevel')
            monitors = self.widget.tk.call('winfo', 'screen', 'monitors')
            
            # If we can't get monitor info, fall back to primary screen
            if not monitors or not isinstance(monitors, tuple):
                return (0, 0, 
                        self.widget.winfo_screenwidth(), 
                        self.widget.winfo_screenheight())
            
            # Find the monitor that contains our point
            for monitor in monitors:
                if (isinstance(monitor, dict) and 
                    monitor['x'] <= x < monitor['x'] + monitor['width'] and
                    monitor['y'] <= y < monitor['y'] + monitor['height']):
                    return (monitor['x'], monitor['y'], 
                            monitor['width'], monitor['height'])
            
            # If no monitor contains the point, return the primary screen
            return (0, 0, 
                    self.widget.winfo_screenwidth(), 
                    self.widget.winfo_screenheight())
                    
        except Exception:
            # Fallback to basic screen dimensions if anything goes wrong
            return (0, 0, 
                    self.widget.winfo_screenwidth(), 
                    self.widget.winfo_screenheight())
    
    def _get_tooltip_position(self, x: int, y: int, width: int, height: int) -> tuple[int, int]:
        """
        Calculate the tooltip position based on cursor and screen boundaries.
        
        Args:
            x: Current x-coordinate of the cursor
            y: Current y-coordinate of the cursor
            width: Width of the tooltip
            height: Height of the tooltip
            
        Returns:
            Tuple of (x, y) coordinates for the tooltip
        """
        # Get the monitor dimensions that contain the current position
        mon_x, mon_y, mon_width, mon_height = self._get_monitor_dimensions(x, y)
        
        # Calculate initial position
        if self.config['follow_cursor']:
            x_pos = x + self.config['offset_x']
            y_pos = y + self.config['offset_y']
        else:
            # Position relative to the widget
            x_pos = self.widget.winfo_rootx() + self.config['offset_x']
            y_pos = self.widget.winfo_rooty() + self.widget.winfo_height() + self.config['offset_y']
        
        # Adjust position if tooltip would go off-screen
        if x_pos + width > mon_x + mon_width:
            x_pos = max(mon_x, mon_x + mon_width - width - 5)
        if y_pos + height > mon_y + mon_height:
            # Try above the cursor if there's not enough space below
            if y - height - 10 > mon_y:
                y_pos = y - height - 10
            else:
                # If not enough space above either, just position at the bottom of the screen
                y_pos = mon_y + mon_height - height - 5
        
        # Ensure the tooltip stays within monitor bounds
        x_pos = max(mon_x, min(mon_x + mon_width - width - 5, x_pos))
        y_pos = max(mon_y, min(mon_y + mon_height - height - 5, y_pos))
        
        return int(x_pos), int(y_pos)
    
    def enter(self, event: Optional[tk.Event] = None) -> None:
        """Show the tooltip when mouse enters the widget after a delay."""
        if hasattr(self, 'after_id'):
            self.widget.after_cancel(self.after_id)
        self.after_id = self.widget.after(
            self.config['delay'],
            self._show_tooltip
        )
    
    def _show_tooltip(self) -> None:
        """Display the tooltip with the configured options."""
        # Don't show if the widget is no longer visible
        if not self.widget.winfo_ismapped():
            return
            
        # Get cursor position
        x = self.widget.winfo_pointerx()
        y = self.widget.winfo_pointery()
        
        # Create a toplevel window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        
        # Make the window stay on top
        self.tooltip.wm_attributes("-topmost", True)
        
        # Add the tooltip text
        label = ttk.Label(
            self.tooltip,
            text=self.config['text'],
            background=self.config['background'],
            foreground=self.config['foreground'],
            relief=self.config['relief'],
            borderwidth=self.config['borderwidth'],
            padding=self.config['padding'],
            wraplength=self.config['wraplength'],
            justify=self.config['justify'],
            font=('TkDefaultFont', 9)
        )
        label.pack()
        
        # Position the tooltip on screen
        self.tooltip.update_idletasks()
        width = self.tooltip.winfo_width()
        height = self.tooltip.winfo_height()
        
        # Get final position
        x_pos, y_pos = self._get_tooltip_position(x, y, width, height)
        self.tooltip.wm_geometry(f"+{x_pos}+{y_pos}")
        
        # Bind motion to update position if follow_cursor is True
        if self.config['follow_cursor']:
            self.widget.bind("<Motion>", self._update_position, add='+')
    
    def _update_position(self, event: tk.Event) -> None:
        """Update the tooltip position to follow the cursor."""
        if not self.tooltip:
            return
            
        self.tooltip.update_idletasks()
        width = self.tooltip.winfo_width()
        height = self.tooltip.winfo_height()
        
        x_pos, y_pos = self._get_tooltip_position(
            event.x_root, 
            event.y_root,
            width,
            height
        )
        
        self.tooltip.wm_geometry(f"+{x_pos}+{y_pos}")
    
    def leave(self, event: Optional[tk.Event] = None) -> None:
        """Destroy the tooltip when mouse leaves the widget."""
        if hasattr(self, 'after_id'):
            self.widget.after_cancel(self.after_id)
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
        self.widget.unbind("<Motion>")
    
    def update_text(self, new_text: str) -> None:
        """Update the tooltip text."""
        self.config['text'] = new_text
        if self.tooltip:
            for child in self.tooltip.winfo_children():
                if isinstance(child, ttk.Label):
                    child.config(text=new_text)
                    break


def create_tooltip(widget: tk.Widget, text: Union[str, Dict[str, Any]], **kwargs) -> ToolTip:
    """
    Convenience function to create a tooltip for a widget.
    
    Args:
        widget: The widget to attach the tooltip to
        text: The tooltip text or configuration dictionary
        **kwargs: Additional configuration options
        
    Returns:
        ToolTip: The created ToolTip instance
    """
    return ToolTip(widget, text, **kwargs)
