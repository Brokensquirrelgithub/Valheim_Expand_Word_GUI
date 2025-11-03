import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont
from gui.tooltip import ToolTip
import yaml
import os
import json
import time
import re
import webbrowser
import traceback
import sys
from typing import Dict, List, Any, Optional, Union


# Configuration file path
CONFIG_FILE = os.path.expanduser("~/.valheim_editor_config.json")

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {}

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

class ExpandWorldEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Valheim Expand World Editor")
        self.root.geometry("1400x900")
        
        # Initialize scroll state
        self._scroll_lock = False
        self._scroll_job = None
        self._scroll_region_job = None
        
        # Store loaded files
        self.files = {
            "Clutter": {"path": None, "data": []},
            "Environments": {"path": None, "data": []},
            "Spawns": {"path": None, "data": []},
            "Locations": {"path": None, "data": []},
            "Vegetation": {"path": None, "data": []}
        }
        
        # Try to load the last used profile
        config = load_config()
        self.last_profile = config.get('last_profile')
        
        self.current_category = "Clutter"
        self.current_biome = None
        self.view_mode = "entry"  # 'table' or 'entry'
        
        # Parameter definitions for different categories
        self.param_defs = {
            "Clutter": {
                "prefab": {"type": "str", "required": True, "default": ""},
                "enabled": {"type": "bool", "required": False, "default": True},
                "amount": {"type": "int", "required": False, "default": 80},
                "biome": {"type": "list", "required": False, "default": ""},
                "instanced": {"type": "bool", "required": False, "default": False},
                "onUncleared": {"type": "bool", "required": False, "default": True},
                "onCleared": {"type": "bool", "required": False, "default": False},
                "scaleMin": {"type": "float", "required": False, "default": 1.0},
                "scaleMax": {"type": "float", "required": False, "default": 1.0},
                "minTilt": {"type": "float", "required": False, "default": 0.0},
                "maxTilt": {"type": "float", "required": False, "default": 10.0},
                "minAltitude": {"type": "float", "required": False, "default": -1000.0},
                "maxAltitude": {"type": "float", "required": False, "default": 1000.0},
                "minVegetation": {"type": "int", "required": False, "default": 0},
                "maxVegetation": {"type": "int", "required": False, "default": 0},
                "snapToWater": {"type": "bool", "required": False, "default": False},
                "terrainTilt": {"type": "bool", "required": False, "default": False},
                "randomOffset": {"type": "float", "required": False, "default": 0.0},
                "minOceanDepth": {"type": "float", "required": False, "default": 0.0},
                "maxOceanDepth": {"type": "float", "required": False, "default": 0.0},
                "inForest": {"type": "bool", "required": False, "default": False},
                "forestTresholdMin": {"type": "float", "required": False, "default": 0.0},
                "forestTresholdMax": {"type": "float", "required": False, "default": 0.0},
                "fractalScale": {"type": "float", "required": False, "default": 0.0},
                "fractalOffset": {"type": "float", "required": False, "default": 0.0},
                "fractalThresholdMin": {"type": "float", "required": False, "default": 0.0},
                "fractalThresholdMax": {"type": "float", "required": False, "default": 1.0}
            },
            "Spawns": {
                "prefab": {"type": "str", "required": True, "default": "", "tooltip": "Name of the object to spawn. Any object is valid, not just creatures."},
                "name": {"type": "str", "required": False, "default": "", "tooltip": "Identifier for this entry, only needed for mod compatibility."},
                "enabled": {"type": "bool", "required": False, "default": True, "tooltip": "Quick way to disable this entry if needed."},
                "biome": {"type": "list", "required": False, "default": "", "tooltip": "List of possible biomes. Separate multiple biomes with commas."},
                "biomeArea": {"type": "list", "required": False, "default": "", "tooltip": "List of possible biome areas (edge = zones with multiple biomes, median = zones with only a single biome, 4 = unused)."},
                "spawnChance": {"type": "float", "required": False, "default": 100.0, "tooltip": "Chance to spawn when attempted (in %)."},
                "maxSpawned": {"type": "int", "required": False, "default": 1, "tooltip": "Limit for this entry. Also how many spawn attempts are stacked over time."},
                "spawnInterval": {"type": "int", "required": False, "default": 100, "tooltip": "How often the spawning is attempted (in seconds)."},
                "minLevel": {"type": "int", "required": False, "default": 1, "tooltip": "Minimum creature level."},
                "maxLevel": {"type": "int", "required": False, "default": 1, "tooltip": "Maximum creature level."},
                "minAltitude": {"type": "float", "required": False, "default": -1000.0, "tooltip": "Minimum terrain altitude in meters."},
                "maxAltitude": {"type": "float", "required": False, "default": 1000.0, "tooltip": "Maximum terrain altitude in meters."},
                "minDistance": {"type": "float", "required": False, "default": 0.0, "tooltip": "Minimum distance from the world center in meters (0 = disabled)."},
                "maxDistance": {"type": "float", "required": False, "default": 0.0, "tooltip": "Maximum distance from the world center in meters (0 = disabled)."},
                "spawnAtDay": {"type": "bool", "required": False, "default": True, "tooltip": "Enabled during the day time."},
                "spawnAtNight": {"type": "bool", "required": False, "default": True, "tooltip": "Enabled during the night time."},
                "requiredGlobalKey": {"type": "str", "required": False, "default": "", "tooltip": "Which global keys must be set to enable this entry. Use format 'key value' to require a minimum value."},
                "requiredEnvironments": {"type": "list", "required": False, "default": "", "tooltip": "List of valid environments/weathers for this spawn."},
                "spawnDistance": {"type": "float", "required": False, "default": 10.0, "tooltip": "Distance to suppress similar spawns in meters."},
                "spawnRadiusMin": {"type": "float", "required": False, "default": 40.0, "tooltip": "Minimum distance from every player in meters."},
                "spawnRadiusMax": {"type": "float", "required": False, "default": 80.0, "tooltip": "Maximum distance from any player in meters."},
                "groupSizeMin": {"type": "int", "required": False, "default": 1, "tooltip": "Minimum amount spawned at the same time."},
                "groupSizeMax": {"type": "int", "required": False, "default": 1, "tooltip": "Maximum amount spawned at the same time."},
                "groupRadius": {"type": "float", "required": False, "default": 3.0, "tooltip": "Radius when spawning multiple objects in meters."},
                "minTilt": {"type": "float", "required": False, "default": 0.0, "tooltip": "Minimum terrain angle in degrees."},
                "maxTilt": {"type": "float", "required": False, "default": 35.0, "tooltip": "Maximum terrain angle in degrees."},
                "inForest": {"type": "bool", "required": False, "default": True, "tooltip": "Enabled in forests."},
                "outsideForest": {"type": "bool", "required": False, "default": True, "tooltip": "Enabled outside forests."},
                "canSpawnCloseToPlayers": {"type": "bool", "required": False, "default": False, "tooltip": "If set to true, spawnRadiusMin is ignored."},
                "insidePlayerBase": {"type": "bool", "required": False, "default": False, "tooltip": "If set to true, player base protection is ignored."},
                "inLava": {"type": "bool", "required": False, "default": False, "tooltip": "If set to true, can spawn in lava."},
                "outsideLava": {"type": "bool", "required": False, "default": True, "tooltip": "If set to false, can only spawn in lava."},
                "minOceanDepth": {"type": "float", "required": False, "default": 0.0, "tooltip": "Minimum ocean depth in meters."},
                "maxOceanDepth": {"type": "float", "required": False, "default": 0.0, "tooltip": "Maximum ocean depth in meters."},
                "huntPlayer": {"type": "bool", "required": False, "default": False, "tooltip": "Spawned creatures are more aggressive."},
                "groundOffset": {"type": "float", "required": False, "default": 0.5, "tooltip": "Spawns above the ground in meters."},
                "groundOffsetRandom": {"type": "float", "required": False, "default": 0.0, "tooltip": "Maximum random offset from the ground in meters."},
                "levelUpMinCenterDistance": {"type": "float", "required": False, "default": 0.0, "tooltip": "Distance from the world center to enable higher creature levels."},
                "overrideLevelupChance": {"type": "float", "required": False, "default": -1.0, "tooltip": "Chance per level up (from the default 10%)."},
                "faction": {"type": "str", "required": False, "default": "", "tooltip": "Name of the faction. Requires using Expand World Factions."}
            },
            "Environments": {
                "name": {
                    "type": "str", 
                    "required": True, 
                    "default": "",
                    "tooltip": "Unique identifier for this environment, used in other files to reference it."
                },
                "particles": {
                    "type": "str", 
                    "required": True, 
                    "default": "",
                    "tooltip": "Identifier of a default environment to set particles. Required for new environments."
                },
                "isDefault": {
                    "type": "bool", 
                    "required": False, 
                    "default": False,
                    "tooltip": "The first default environment is loaded at game start. Only set if removing from Clear environment."
                },
                "isWet": {
                    "type": "bool", 
                    "required": False, 
                    "default": False,
                    "tooltip": "If true, is considered to be raining in this environment."
                },
                "isFreezing": {
                    "type": "bool", 
                    "required": False, 
                    "default": False,
                    "tooltip": "If true, causes the freezing debuff during the day."
                },
                "isFreezingAtNight": {
                    "type": "bool", 
                    "required": False, 
                    "default": False,
                    "tooltip": "If true, causes the freezing debuff at night."
                },
                "isCold": {
                    "type": "bool", 
                    "required": False, 
                    "default": False,
                    "tooltip": "If true, causes the cold debuff during the day."
                },
                "isColdAtNight": {
                    "type": "bool", 
                    "required": False, 
                    "default": False,
                    "tooltip": "If true, causes the cold debuff at night."
                },
                "alwaysDark": {
                    "type": "bool", 
                    "required": False, 
                    "default": False,
                    "tooltip": "If true, causes constant darkness regardless of time of day."
                },
                "windMin": {
                    "type": "float", 
                    "required": False, 
                    "default": 0.0,
                    "tooltip": "Minimum wind strength (0.0 to 1.0)."
                },
                "windMax": {
                    "type": "float", 
                    "required": False, 
                    "default": 1.0,
                    "tooltip": "Maximum wind strength (0.0 to 1.0)."
                },
                "rainCloudAlpha": {
                    "type": "float", 
                    "required": False, 
                    "default": 0.0,
                    "tooltip": "Controls the opacity of rain clouds (0.0 to 1.0)."
                },
                "ambientVol": {
                    "type": "float", 
                    "required": False, 
                    "default": 0.3,
                    "tooltip": "Volume level for ambient sounds (0.0 to 1.0)."
                },
                "ambientList": {
                    "type": "list", 
                    "required": False, 
                    "default": "",
                    "tooltip": "List of ambient sound effects to play in this environment."
                },
                "musicMorning": {
                    "type": "str", 
                    "required": False, 
                    "default": "",
                    "tooltip": "Music override for morning. Overrides biome music. Use 'ew_musics' command to see available tracks."
                },
                "musicDay": {
                    "type": "str", 
                    "required": False, 
                    "default": "",
                    "tooltip": "Music override for daytime. Overrides biome music. Use 'ew_musics' command to see available tracks."
                },
                "musicEvening": {
                    "type": "str", 
                    "required": False, 
                    "default": "",
                    "tooltip": "Music override for evening. Overrides biome music. Use 'ew_musics' command to see available tracks."
                },
                "musicNight": {
                    "type": "str", 
                    "required": False, 
                    "default": "",
                    "tooltip": "Music override for night. Overrides biome music. Use 'ew_musics' command to see available tracks."
                },
                # Color parameters with tooltips
                "ambColorDay": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
                    "tooltip": "Ambient light color during daytime (RGB 0-1)."
                },
                "ambColorNight": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0},
                    "tooltip": "Ambient light color during night (RGB 0-1)."
                },
                "sunColorMorning": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
                    "tooltip": "Sun color during morning (RGB 0-1)."
                },
                "sunColorDay": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
                    "tooltip": "Sun color during day (RGB 0-1)."
                },
                "sunColorEvening": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
                    "tooltip": "Sun color during evening (RGB 0-1)."
                },
                "sunColorNight": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
                    "tooltip": "Sun color during night (RGB 0-1)."
                },
                "fogColorMorning": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0},
                    "tooltip": "Fog color during morning (RGB 0-1)."
                },
                "fogColorDay": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0},
                    "tooltip": "Fog color during day (RGB 0-1)."
                },
                "fogColorEvening": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0},
                    "tooltip": "Fog color during evening (RGB 0-1)."
                },
                "fogColorNight": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0},
                    "tooltip": "Fog color during night (RGB 0-1)."
                },
                "fogColorSunMorning": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0},
                    "tooltip": "Sun-affected fog color during morning (RGB 0-1)."
                },
                "fogColorSunDay": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0},
                    "tooltip": "Sun-affected fog color during day (RGB 0-1)."
                },
                "fogColorSunEvening": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0},
                    "tooltip": "Sun-affected fog color during evening (RGB 0-1)."
                },
                "fogColorSunNight": {
                    "type": "color", 
                    "required": False, 
                    "default": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0},
                    "tooltip": "Sun-affected fog color during night (RGB 0-1)."
                },
                # Other parameters with tooltips
                "fogDensityMorning": {
                    "type": "float", 
                    "required": False, 
                    "default": 0.01,
                    "tooltip": "Fog density during morning. Higher values create thicker fog."
                },
                "fogDensityDay": {
                    "type": "float", 
                    "required": False, 
                    "default": 0.01,
                    "tooltip": "Fog density during day. Higher values create thicker fog."
                },
                "fogDensityEvening": {
                    "type": "float", 
                    "required": False, 
                    "default": 0.01,
                    "tooltip": "Fog density during evening. Higher values create thicker fog."
                },
                "fogDensityNight": {
                    "type": "float", 
                    "required": False, 
                    "default": 0.01,
                    "tooltip": "Fog density during night. Higher values create thicker fog."
                },
                "lightIntensityDay": {
                    "type": "float", 
                    "required": False, 
                    "default": 1.2,
                    "tooltip": "Intensity of directional light during day."
                },
                "lightIntensityNight": {
                    "type": "float", 
                    "required": False, 
                    "default": 0.0,
                    "tooltip": "Intensity of directional light during night."
                },
                "sunAngle": {
                    "type": "float", 
                    "required": False, 
                    "default": 60.0,
                    "tooltip": "Angle of the sun in the sky (in degrees)."
                },
                "statusEffects": {
                    "type": "list", 
                    "required": False, 
                    "default": [],
                    "tooltip": "List of status effects active in this environment. Note: Normal biome effects still apply."
                }
            }
        }
        
        # Create main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Menu bar
        self.create_menu()
        
        # Main content area
        self.create_editor_interface()
        
    def open_profile_folder(self):
        """Open the expand_world folder containing the YAML files"""
        # First check if we have any loaded files with paths
        current_path = None
        for category, data in self.files.items():
            if data.get('path') and os.path.exists(data['path']):
                current_path = data['path']
                break
        
        # If no current files are loaded, try the last profile
        if not current_path and self.last_profile:
            current_path = self.last_profile
        
        if not current_path:
            messagebox.showinfo("Info", "No profile or files are currently open.")
            return
        
        # Get the directory containing the YAML files (BepInEx/config/expand_world)
        expand_world_dir = os.path.dirname(current_path)
        
        if os.path.exists(expand_world_dir):
            try:
                # Try Windows first
                if os.name == 'nt':
                    os.startfile(expand_world_dir)
                else:
                    # Try other platforms
                    import subprocess
                    if sys.platform == 'darwin':  # macOS
                        subprocess.call(['open', expand_world_dir])
                    else:  # Linux and others
                        subprocess.call(['xdg-open', expand_world_dir])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open expand_world folder: {e}")
        else:
            messagebox.showerror("Error", f"expand_world folder not found: {expand_world_dir}")
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Folder...", command=self.open_folder)
        file_menu.add_command(label="Open File...", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save Current", command=self.save_current_file)
        file_menu.add_command(label="Save All", command=self.save_all_files)
        file_menu.add_separator()
        file_menu.add_command(label="Open Profile Folder", command=self.open_profile_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        self.view_mode_var = tk.StringVar(value="table")
        view_menu.add_radiobutton(label="Table View", variable=self.view_mode_var, 
                                value="table", command=self.toggle_view_mode)
        view_menu.add_radiobutton(label="Entry Mode", variable=self.view_mode_var,
                                value="entry", command=self.toggle_view_mode)
        menubar.add_cascade(label="View", menu=view_menu)
        
    def toggle_view_mode(self):
        """Toggle between table and entry view modes"""
        new_mode = self.view_mode_var.get()
        
        # Only allow entry mode for categories that support it (Clutter and Environments)
        if new_mode == "entry" and self.current_category not in ["Clutter", "Environments"]:
            messagebox.showinfo("Info", "Entry mode is only available for Clutter and Environments")
            self.view_mode_var.set("table")  # Reset the radio button
            return
            
        self.view_mode = new_mode
        
        # Force a complete refresh of the display
        if self.view_mode == "table":
            self.create_table_view()
            self.update_biome_list()
            self.update_items_tree()
        else:  # entry mode
            self.create_entry_view()
    
    def create_editor_interface(self):
        # Top panel - Category tabs
        top_panel = ttk.Frame(self.main_frame)
        top_panel.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_panel, text="Category:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.category_notebook = ttk.Notebook(top_panel)
        self.category_notebook.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.category_notebook.bind('<<NotebookTabChanged>>', self.on_category_change)
        
        # Create tabs for each category
        self.category_frames = {}
        for category in ["Clutter", "Environments", "Spawns", "Locations", "Vegetation"]:
            frame = ttk.Frame(self.category_notebook)
            self.category_notebook.add(frame, text=category)
            self.category_frames[category] = frame
        
        # Main content area
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create table view components (initially hidden)
        self.create_table_view()
        
        # Create entry mode components (initially hidden)
        self.entry_frame = ttk.Frame(self.content_frame)
        
        # Bind double-click to edit
        self.tree.bind('<Double-1>', self.on_item_double_click)
    
    def create_table_view(self):
        """Create the table view components"""
        # Clear any existing widgets in content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Left panel - Biome filter
        left_panel = ttk.LabelFrame(self.content_frame, text="Filter by Biome", padding=5)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        self.biome_listbox = tk.Listbox(left_panel, width=25, height=30)
        self.biome_listbox.pack(fill=tk.BOTH, expand=True)
        self.biome_listbox.bind('<<ListboxSelect>>', self.on_biome_filter)
        
        # Add "All" option
        self.biome_listbox.insert(tk.END, "-- All Biomes --")
        
        # Update biome list with counts
        self.update_biome_list()
        
        # Right panel - Items list
        right_panel = ttk.Frame(self.content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Items treeview
        tree_frame = ttk.Frame(right_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with scrollbars
        self.tree = ttk.Treeview(tree_frame, show='tree headings', selectmode='browse')
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
    
    def create_entry_view(self):
        """Create the entry mode view for clutter configuration with section-based lazy loading"""
        print("\n=== Creating Entry View ===")
        print(f"Current category: {self.current_category}")
        print(f"Current biome filter: {self.current_biome}")
        
        # Clear existing widgets and references
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Store data reference
        self.all_data = self.files[self.current_category]["data"]
        self.filtered_data = []
        self.visible_entries = set()
        self.entry_frames = {}
        self.entry_height = 200  # Approximate height of each entry in pixels
        self.entry_padding = 10  # Padding between entries
        self._last_scroll_height = 0
        self._scroll_job = None
        
        # Create main container with grid layout
        self.main_frame = ttk.Frame(self.content_frame)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a frame for the biome filter (left panel)
        self.filter_frame = ttk.LabelFrame(self.main_frame, text="Filter by Biome", padding=5)
        self.filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # Create a frame for the content (right panel)
        self.content_panel = ttk.Frame(self.main_frame)
        self.content_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create a canvas with scrollbar for the content
        self.canvas = tk.Canvas(self.content_panel, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self.content_panel, orient="vertical", command=self.canvas.yview)
        
        # Create a frame inside the canvas for the scrollable content
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure the canvas scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create a window in the canvas to hold the scrollable frame
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Pack the canvas and scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create columns for the entries
        self.columns_frame = ttk.Frame(self.scrollable_frame)
        self.columns_frame.pack(fill=tk.BOTH, expand=True)
        
        self.left_column = ttk.Frame(self.columns_frame)
        self.left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.right_column = ttk.Frame(self.columns_frame)
        self.right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create a frame for buttons at the bottom
        self.button_frame = ttk.Frame(self.scrollable_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        # Add new entry button
        self.add_btn = ttk.Button(
            self.button_frame,
            text=f"+ Add New {self.current_category} Entry",
            command=self.add_clutter_entry
        )
        self.add_btn.pack(pady=5)
        
        # Save button
        self.save_btn = ttk.Button(
            self.button_frame,
            text="Save Changes",
            command=self.save_clutter_entries
        )
        self.save_btn.pack(pady=5)
        
        # Initialize biome filter
        self.init_biome_filter()
        
        # Filter and display data
        self.filter_data()
        
        # Configure scroll region and bindings after UI is set up
        self.setup_scroll_behavior()
        
        # Initial rendering of visible entries
        self.update_visible_entries()
    
    def init_biome_filter(self):
        """Initialize the biome filter controls"""
        # Create a search box for biomes
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_biome)
        
        search_frame = ttk.Frame(self.filter_frame)
        search_frame.pack(fill=tk.X, padx=2, pady=2)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Create a frame for the listbox and scrollbar
        list_frame = ttk.Frame(self.filter_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create a scrollbar for the listbox
        list_scrollbar = ttk.Scrollbar(list_frame)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create the listbox for biomes
        self.biome_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=list_scrollbar.set,
            selectmode=tk.SINGLE,
            exportselection=0
        )
        self.biome_listbox.pack(fill=tk.BOTH, expand=True)
        list_scrollbar.config(command=self.biome_listbox.yview)
        
        # Add "All Biomes" option
        self.biome_listbox.insert(tk.END, "-- All Biomes --")
        self.biome_listbox.selection_set(0)  # Select "All Biomes" by default
        
        # Bind selection event
        
        # Update biome list
        self.update_biome_list()
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling with debounce"""
        if self._scroll_lock:
            return "break"
            
        try:
            self._scroll_lock = True
            
            # Get current scroll position
            first_visible, last_visible = self.canvas.yview()
            
            # Calculate if we're at the top or bottom
            at_top = first_visible <= 0.0
            at_bottom = last_visible >= 0.99
            
            # Only process the scroll if we're not at the boundary in the scroll direction
            if (event.delta < 0 and not at_bottom) or (event.delta > 0 and not at_top):
                # Scroll the canvas
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                
                # Update visible entries immediately
                self.update_visible_entries()
                
                # Cancel any pending updates
                if hasattr(self, '_scroll_job'):
                    try:
                        self.canvas.after_cancel(self._scroll_job)
                    except (ValueError, tk.TclError):
                        pass
                
                # Schedule a final update
                self._scroll_job = self.canvas.after(150, self._delayed_scroll_update)
            
            return "break"
            
        finally:
            self._scroll_lock = False
    
    def _schedule_delayed_update(self):
        """Schedule a delayed update after scrolling"""
        if hasattr(self, '_scroll_job') and self._scroll_job is not None:
            try:
                self.canvas.after_cancel(self._scroll_job)
            except (ValueError, tk.TclError):
                # Ignore if the timer doesn't exist anymore
                pass
        
        # Only schedule if we have a valid canvas
        if hasattr(self, 'canvas') and self.canvas.winfo_exists():
            self._scroll_job = self.canvas.after(150, self._delayed_scroll_update)
    
    def _on_mousewheel_scroll(self, direction):
        """Handle mouse wheel scrolling for Linux"""
        if self._scroll_lock:
            return "break"
            
        try:
            self._scroll_lock = True
            
            # Get current scroll position
            first_visible, last_visible = self.canvas.yview()
            
            # Calculate if we're at the top or bottom
            at_top = first_visible <= 0.0
            at_bottom = last_visible >= 0.99
            
            # Only process the scroll if we're not at the boundary in the scroll direction
            if (direction > 0 and not at_bottom) or (direction < 0 and not at_top):
                # Scroll the canvas
                self.canvas.yview_scroll(-1 * direction, "units")
                
                # Update visible entries immediately
                self.update_visible_entries()
                
                # Cancel any pending updates
                if hasattr(self, '_scroll_job'):
                    try:
                        self.canvas.after_cancel(self._scroll_job)
                    except (ValueError, tk.TclError):
                        pass
                
                # Schedule a final update
                self._scroll_job = self.canvas.after(150, self._delayed_scroll_update)
            
            return "break"
            
        finally:
            self._scroll_lock = False
    
    def _delayed_scroll_update(self):
        """Final update after scrolling has settled"""
        # Clear the job ID
        if hasattr(self, '_scroll_job'):
            self._scroll_job = None
        
        # Only proceed if we have a valid canvas
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists() or self._scroll_lock:
            return
            
        try:
            self._scroll_lock = True
            
            # Get current scroll position
            first, last = self.canvas.yview()
            
            # If we're near the bottom, make sure we're exactly at the bottom
            if last >= 0.99:
                self.canvas.yview_moveto(1.0)
            
            # Update the display with a full refresh
            self.update_visible_entries()
            
            # Schedule a scroll region update
            if not hasattr(self, '_scroll_region_job'):
                self._scroll_region_job = self.canvas.after(50, self._update_scroll_region_delayed)
            
        except Exception as e:
            # Prevent any errors from breaking the scroll handling
            print(f"Error in scroll update: {e}")
            
        finally:
            self._scroll_lock = False
        
    def update_scroll_region(self):
        """Update the scroll region to include all content"""
        # Update the scroll region to encompass the inner frame
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)
    
    def on_canvas_configure(self, event):
        """Handle canvas resize events"""
        # Update the canvas's width to match the scrollable frame
        if event:
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_frame, width=canvas_width)
        
        # Update the scroll region to ensure all content is scrollable
        self.update_scroll_region()
    
    def setup_scroll_behavior(self):
        """Configure scroll behavior and event bindings"""
        # Configure grid weights for proper resizing
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Configure canvas scrolling
        self.scrollable_frame.bind('<Configure>', lambda e: self.update_scroll_region())
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Bind mousewheel events for Windows and MacOS
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Bind mousewheel events for Linux
        self.canvas.bind_all("<Button-4>", lambda e: self._on_mousewheel_scroll(-1))
        self.canvas.bind_all("<Button-5>", lambda e: self._on_mousewheel_scroll(1))
        
        # Initial configuration
        self.update_scroll_region()
        
        # Make sure canvas gets focus on mouse enter/leave
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())
        self.canvas.bind("<Leave>", lambda e: self.canvas.master.focus_set())
        
        # Initialize scroll job tracking
        self._scroll_job = None
        
        # Initial update of visible entries
        self.update_visible_entries()
        
        # Ensure scroll region is properly set after a short delay
        self.canvas.after(100, self._ensure_scroll_region)
    
    def _ensure_scroll_region(self):
        """Ensure scroll region is properly set after UI is fully initialized"""
        if hasattr(self, 'canvas') and self.canvas.winfo_exists():
            self.update_scroll_region()
            self.canvas.update_idletasks()
        
    def filter_data(self):
        """Filter data based on selected biome and search term"""
        self.filtered_data = []
        
        # Get search term
        search_term = self.search_var.get().lower()
        
        # Filter data by selected biome and search term
        for item in self.all_data:
            if not isinstance(item, dict):
                continue
                
            # Filter by biome if one is selected
            if self.current_biome and self.current_biome != "-- All Biomes --":
                if "biome" not in item or not item["biome"]:
                    continue
                    
                # Get all biomes for this entry
                entry_biomes = set()
                if isinstance(item["biome"], list):
                    entry_biomes.update(str(b).strip().lower() for b in item["biome"] if b is not None)
                else:
                    biome_str = str(item["biome"]).strip()
                    if biome_str:
                        entry_biomes.update(b.strip().lower() for b in biome_str.split(",") if b.strip())
                
                # Check if current biome is in this entry's biomes
                if not any(biome == self.current_biome.lower() for biome in entry_biomes):
                    continue
            
            # Filter by search term if one is provided
            if search_term:
                # Check if any value in the item matches the search term
                match_found = False
                for key, value in item.items():
                    if search_term in str(value).lower():
                        match_found = True
                        break
                
                if not match_found:
                    # Also check if the search term matches any parameter name
                    if search_term not in str(item.keys()).lower():
                        continue
            
            self.filtered_data.append(item)
        
        print(f"Filtered to {len(self.filtered_data)} entries")
    
    def on_search_biome(self, *args):
        """Handle search box changes"""
        self.filter_data()
        self.update_visible_entries()
    
    def on_biome_filter(self, event):
        """Handle biome filter selection"""
        if not self.biome_listbox.curselection():
            return
            
        selected = self.biome_listbox.get(self.biome_listbox.curselection())
        if selected == "-- All Biomes --":
            self.current_biome = None
        else:
            self.current_biome = selected
        
        # Re-filter data and update display
        self.filter_data()
        self.update_visible_entries()
    
    def update_visible_entries(self, event=None):
        """Update which entries are currently visible in the viewport"""
        if not hasattr(self, 'canvas') or not hasattr(self, 'filtered_data'):
            return
            
        try:
            # Load all entries - no lazy loading for now
            first_visible = 0
            last_visible = len(self.filtered_data)
            
            # Track which entries should be visible in this update
            should_be_visible = set(range(first_visible, last_visible))
            
            # Remove entries that are no longer visible
            to_remove = []
            for i in self.visible_entries:
                if i not in should_be_visible:
                    self.destroy_entry_widget(i)
                    to_remove.append(i)
            
            # Update the visible_entries set
            self.visible_entries.difference_update(to_remove)
            
            # Add newly visible entries in chunks for better performance
            for i in range(first_visible, last_visible, 5):  # Load 5 entries at a time
                chunk_end = min(i + 5, last_visible)
                for j in range(i, chunk_end):
                    if j < len(self.filtered_data) and j not in self.visible_entries:
                        self.create_entry_widget(j)
                        self.visible_entries.add(j)
                # Allow the UI to update between chunks
                self.canvas.update_idletasks()
            
            # Update scroll region if needed
            if not hasattr(self, '_last_scroll_height') or self._last_scroll_height != len(self.filtered_data):
                # Calculate the actual content height by checking the scrollable frame
                self.canvas.update_idletasks()
                
                # Get the bounding box of all content in the canvas
                bbox = self.canvas.bbox("all")
                if bbox:
                    # bbox returns (x1, y1, x2, y2)
                    total_height = bbox[3] + 50  # Add padding at the bottom
                else:
                    # Fallback: estimate based on number of entries
                    entry_height = 50  # Collapsed entry height
                    entries_per_column = (len(self.filtered_data) + 1) // 2
                    total_height = (entries_per_column * entry_height) + 100
                
                # Set the scroll region to the full height
                self.canvas.config(scrollregion=(0, 0, self.canvas.winfo_width(), total_height))
                self._last_scroll_height = len(self.filtered_data)
                
        except Exception as e:
            print(f"Error updating visible entries: {e}")
            import traceback
            traceback.print_exc()
            # If there's an error, try again after a short delay
            if hasattr(self, 'canvas') and self.canvas.winfo_exists():
                self.canvas.after(100, self.update_visible_entries)
    
    def toggle_entry_expand(self, index, expand_btn, content_frame):
        """Toggle the expanded/collapsed state of an entry"""
        if not hasattr(self, 'entry_states'):
            self.entry_states = {}
            
        # Toggle the state
        is_expanded = self.entry_states.get(index, False)
        self.entry_states[index] = not is_expanded
        
        # Update the button text and show/hide content
        if is_expanded:
            expand_btn.config(text="+")
            content_frame.grid_remove()
        else:
            expand_btn.config(text="-")
            content_frame.grid()
        
        # Update the scroll region after the widget is shown/hidden
        self.canvas.update_idletasks()
        self.update_scroll_region()
    
    def create_entry_widget(self, index):
        """Create a widget for a single entry"""
        if index >= len(self.filtered_data):
            return
        
        try:
            item = self.filtered_data[index]
            
            # Choose which column to place this entry in (alternating)
            column = self.left_column if index % 2 == 0 else self.right_column
            
            # Create a frame for the entry
            entry_frame = ttk.Frame(column, padding=2)
            entry_frame.pack(fill=tk.X, pady=2, expand=True)
            
            # Store reference to the frame
            if not hasattr(self, 'entry_frames'):
                self.entry_frames = {}
            self.entry_frames[index] = entry_frame
            
            # Configure grid for entry frame
            entry_frame.columnconfigure(1, weight=1)
            
            # Header frame for the entry
            header_frame = ttk.Frame(entry_frame)
            header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
            header_frame.columnconfigure(1, weight=1)
            
            # Expand/collapse button
            expand_btn = ttk.Button(
                header_frame,
                text="+",  # Start collapsed (+)
                width=2,
                command=lambda i=index, btn=None, frm=None: self.toggle_entry_expand(i, btn, frm)
            )
            expand_btn.grid(row=0, column=0, padx=2, sticky="w")
            
            # Entry title
            title = item.get('prefab', item.get('name', f"{self.current_category} Entry {index + 1}"))
            title_label = ttk.Label(
                header_frame,
                text=title,
                font=('TkDefaultFont', 9, 'bold')
            )
            title_label.grid(row=0, column=1, sticky="w")
            
            # Delete button
            del_btn = ttk.Button(
                header_frame,
                text="X",
                width=2,
                command=lambda i=index: self.delete_clutter_entry(i)
            )
            del_btn.grid(row=0, column=2, padx=2, sticky="e")
            
            # Content frame (initially hidden)
            content_frame = ttk.LabelFrame(entry_frame, padding=5)
            content_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
            
            # Set initial state to collapsed
            if not hasattr(self, 'entry_states'):
                self.entry_states = {}
            self.entry_states[index] = False
            content_frame.grid_remove()
            
            # Update the expand button command with the content frame reference
            expand_btn.config(command=lambda i=index, btn=expand_btn, frm=content_frame: 
                             self.toggle_entry_expand(i, btn, frm))
            
            # Main parameter frame
            main_param_frame = ttk.Frame(content_frame)
            main_param_frame.pack(fill=tk.X, expand=True)
            
            # Frame for the add parameter button
            add_param_frame = ttk.Frame(content_frame)
            add_param_frame.pack(fill=tk.X, pady=(5, 0))
            
            # Store frames for this entry
            if not hasattr(self, 'entry_widgets'):
                self.entry_widgets = {}
            if not hasattr(self, 'param_frames'):
                self.param_frames = {}
                
            self.entry_widgets[index] = {}
            self.param_frames[index] = {
                'main': main_param_frame,
                'add_param': add_param_frame,
                'frame': entry_frame
            }
            
            # Add initial required parameters and parameters that exist in the item
            if self.current_category in self.param_defs:
                for param, param_info in self.param_defs[self.current_category].items():
                    if param_info.get('required', False) or param in item:
                        self._add_parameter_widget(index, param, item)
            
            # Add parameter button
            self._update_add_param_button(index)
            
        except Exception as e:
            print(f"Error creating entry widget for index {index}: {e}")
            import traceback
            traceback.print_exc()
    
    def destroy_entry_widget(self, index):
        """Destroy the widget for a single entry"""
        if hasattr(self, 'entry_frames') and index in self.entry_frames:
            self.entry_frames[index].destroy()
            del self.entry_frames[index]
        
        if hasattr(self, 'entry_widgets') and index in self.entry_widgets:
            del self.entry_widgets[index]
        
        if hasattr(self, 'param_frames') and index in self.param_frames:
            del self.param_frames[index]
    
    def update_biome_list(self):
        """Update the list of available biomes"""
        if not hasattr(self, 'biome_listbox'):
            return
            
        # Keep track of biomes we've already added
        biomes = set()
        
        # Get all biomes from the data
        for item in self.all_data:
            if not isinstance(item, dict) or "biome" not in item:
                continue
                
            if isinstance(item["biome"], list):
                biomes.update(str(b).strip() for b in item["biome"] if b is not None)
            else:
                biome_str = str(item["biome"]).strip()
                if biome_str:
                    biomes.update(b.strip() for b in biome_str.split(",") if b.strip())
        
        # Clear existing items (except "All Biomes")
        self.biome_listbox.delete(1, tk.END)
        
        # Add biomes to the listbox
        for biome in sorted(biomes):
            if biome:  # Skip empty strings
                self.biome_listbox.insert(tk.END, biome)
        
        print(f"Found {len(biomes)} unique biomes")
    
    def _add_parameter_widget(self, entry_idx, param, item_data):
        """Add a parameter widget to the specified entry"""
        if param in self.entry_widgets[entry_idx]:
            return  # Already added
            
        param_info = self.param_defs[self.current_category][param]
        main_frame = self.param_frames[entry_idx]['main']
        
        # Create a frame for this parameter
        frame = ttk.Frame(main_frame)
        frame.param_name = param  # Store the parameter name on the frame
        frame.pack(fill=tk.X, padx=2, pady=1)
        
        # Parameter tooltips
        tooltips = {
            "prefab": "Name of the clutter object.",
            "enabled": "(Default: true) Quick way to disable this entry.",
            "amount": "(Default: 80) Amount of clutter.",
            "biome": "List of possible biomes. Separate multiple biomes with commas.",
            "instanced": "(Default: false) Way of rendering or something. Might cause errors if changed.",
            "onUncleared": "(Default: true) Only on uncleared terrain.",
            "onCleared": "(Default: false) Only on cleared terrain.",
            "scaleMin": "(Default: 1.0) Minimum scale for instanced clutter.",
            "scaleMax": "(Default: 1.0) Maximum scale for instanced clutter.",
            "minTilt": "(Default: 0.0) Minimum terrain angle in degrees.",
            "maxTilt": "(Default: 10.0) Maximum terrain angle in degrees.",
            "minAltitude": "(Default: -1000.0) Minimum terrain altitude in meters.",
            "maxAltitude": "(Default: 1000.0) Maximum terrain altitude in meters.",
            "minVegetation": "(Default: 0) Minimum vegetation mask.",
            "maxVegetation": "(Default: 0) Maximum vegetation mask.",
            "snapToWater": "(Default: false) Place at water level instead of terrain.",
            "terrainTilt": "(Default: false) Rotate with the terrain angle.",
            "randomOffset": "(Default: 0.0) Random vertical offset in meters.",
            "minOceanDepth": "(Default: 0.0) Minimum water depth in meters.",
            "maxOceanDepth": "(Default: 0.0) Maximum water depth in meters.",
            "inForest": "(Default: false) Only in forests.",
            "forestTresholdMin": "(Default: 0.0) Minimum forest value (if only in forests).",
            "forestTresholdMax": "(Default: 0.0) Maximum forest value (if only in forests).",
            "fractalScale": "(Default: 0.0) Scale when calculating the fractal value.",
            "fractalOffset": "(Default: 0.0) Offset when calculating the fractal value.",
            "fractalThresholdMin": "(Default: 0.0) Minimum fractal value.",
            "fractalThresholdMax": "(Default: 1.0) Maximum fractal value."
        }

        # Create label with tooltip
        label = ttk.Label(frame, text=f"{param}:", width=20, anchor='e')
        label.pack(side=tk.LEFT, padx=5)
        ToolTip(label, param_info.get("tooltip", "No description available."))
        
        # Create appropriate input widget based on parameter type
        if param_info["type"] == "color":
            # Handle color parameters with a color swatch and picker
            value = item_data.get(param, param_info["default"])
            if not isinstance(value, dict):
                value = {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}  # Default to white if invalid
                
            # Create a frame for the color widget
            color_frame = ttk.Frame(frame)
            color_frame.pack(fill=tk.X, expand=True, side=tk.LEFT)
            
            # Create a canvas to show the color swatch
            swatch_canvas = tk.Canvas(color_frame, width=24, height=24, bd=1, relief="solid")
            swatch_canvas.pack(side=tk.LEFT, padx=5, pady=2)
            
            # Convert float RGB (0-1) to 0-255 for display
            r = int(value.get('r', 0) * 255)
            g = int(value.get('g', 0) * 255)
            b = int(value.get('b', 0) * 255)
            hex_color = f'#{r:02x}{g:02x}{b:02x}'
            
            # Draw the color swatch
            swatch_canvas.create_rectangle(0, 0, 24, 24, fill=hex_color, outline="black")
            
            # Create a frame for the RGB values
            rgb_frame = ttk.Frame(color_frame)
            rgb_frame.pack(side=tk.LEFT, padx=5)
            
            # Function to update the RGB display
            def update_rgb_display(r_val, g_val, b_val):
                # Clear previous labels
                for widget in rgb_frame.winfo_children():
                    widget.destroy()
                
                # Convert to 0-1 range with 2 decimal places
                r_disp = r_val / 255.0
                g_disp = g_val / 255.0
                b_disp = b_val / 255.0
                
                # Create labels for each color component with slightly darker colors
                r_label = ttk.Label(rgb_frame, text=f"R: {r_disp:.2f}", foreground="#cc5555")  # Darker red
                g_label = ttk.Label(rgb_frame, text=f" G: {g_disp:.2f}", foreground="#55aa55")  # Darker green
                b_label = ttk.Label(rgb_frame, text=f" B: {b_disp:.2f}", foreground="#5555cc")  # Darker blue
                
                # Pack the labels
                r_label.pack(side=tk.LEFT)
                g_label.pack(side=tk.LEFT)
                b_label.pack(side=tk.LEFT)
                
                return r_val, g_val, b_val
            
            # Initial RGB display
            r, g, b = update_rgb_display(r, g, b)
            
            # Create a button to open color picker
            def choose_color():
                from tkinter import colorchooser
                # Get current color values
                current_color = (r, g, b)
                # Open color chooser dialog
                color = colorchooser.askcolor(
                    initialcolor=current_color,
                    title=f"Choose {param} color"
                )
                if color[0]:  # User didn't cancel
                    # Get new RGB values
                    new_r = int(color[0][0])
                    new_g = int(color[0][1])
                    new_b = int(color[0][2])
                    
                    # Update the RGB display
                    update_rgb_display(new_r, new_g, new_b)
                    
                    # Update the swatch
                    hex_color = color[1]
                    swatch_canvas.delete("all")
                    swatch_canvas.create_rectangle(0, 0, 24, 24, fill=hex_color, outline="black")
                    
                    # Convert 0-255 RGB to 0-1 and store in the value dict
                    r_val = new_r / 255.0
                    g_val = new_g / 255.0
                    b_val = new_b / 255.0
                    
                    # Update the stored value
                    value = {"r": r_val, "g": g_val, "b": b_val, "a": 1.0}
                    self.entry_widgets[entry_idx][param] = (value, "color")
            
            # Add choose color button
            choose_btn = ttk.Button(color_frame, text="Choose Color", command=choose_color)
            choose_btn.pack(side=tk.LEFT, padx=5)
            
            # Store the color value
            self.entry_widgets[entry_idx][param] = (value, "color")
            
        elif param_info["type"] == "bool":
            var = tk.BooleanVar(value=item_data.get(param, param_info["default"]))
            widget = ttk.Checkbutton(frame, variable=var, text="")
            self.entry_widgets[entry_idx][param] = (var, "bool")
            ToolTip(widget, tooltips.get(param, ""))
        elif param_info["type"] == "list":
            # Handle biome lists properly
            value = item_data.get(param, param_info["default"])
            if isinstance(value, list):
                display_value = ", ".join(str(v).strip() for v in value if str(v).strip())
            else:
                display_value = str(value) if value else ""
            var = tk.StringVar(value=display_value)
            widget = ttk.Entry(frame, textvariable=var)
            self.entry_widgets[entry_idx][param] = (var, "list")
            ToolTip(widget, tooltips.get(param, ""))
        elif param_info["type"] == "int":
            var = tk.StringVar(value=str(item_data.get(param, param_info["default"])))
            widget = ttk.Entry(frame, textvariable=var, validate='key')
            widget.configure(validatecommand=(widget.register(self._validate_numeric), '%P'))
            self.entry_widgets[entry_idx][param] = (var, "int")
        elif param_info["type"] == "float":
            var = tk.StringVar(value=str(item_data.get(param, param_info["default"])))
            widget = ttk.Entry(frame, textvariable=var, validate='key')
            widget.configure(validatecommand=(widget.register(self._validate_float), '%P'))
            self.entry_widgets[entry_idx][param] = (var, "float")
        else:  # str
            var = tk.StringVar(value=str(item_data.get(param, param_info["default"])))
            widget = ttk.Entry(frame, textvariable=var)
            self.entry_widgets[entry_idx][param] = (var, "str")
        
        if param_info["type"] != "color":  # Color widgets are already packed
            widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Add remove button for non-required parameters
        if not param_info.get('required', False) and param_info["type"] != "color":  # Don't add remove button for colors
            remove_btn = ttk.Button(frame, text="−", width=2,
                                 command=lambda p=param, i=entry_idx: self._remove_parameter(i, p))
            remove_btn.pack(side=tk.RIGHT, padx=2)
    
    def _update_add_param_button(self, entry_idx):
        """Update the add parameter button for the specified entry"""
        # Clear existing button
        for widget in self.param_frames[entry_idx]['add_param'].winfo_children():
            widget.destroy()
        
        # Get current parameters for this entry
        current_params = set(self.entry_widgets[entry_idx].keys())
        
        # Find available parameters that aren't already added and aren't required
        available_params = []
        if self.current_category in self.param_defs:
            for param, param_info in self.param_defs[self.current_category].items():
                if param not in current_params and not param_info.get('required', False):
                    available_params.append(param)
        
        if available_params:
            # Create menu button for adding parameters
            menu_btn = ttk.Menubutton(
                self.param_frames[entry_idx]['add_param'],
                text="+ Add Parameter",
                width=15
            )
            menu_btn.pack(side=tk.LEFT, padx=5, pady=5)
            
            # Create dropdown menu
            menu = tk.Menu(menu_btn, tearoff=0)
            menu_btn["menu"] = menu
            
            # Add menu items for each available parameter
            for param in sorted(available_params):
                menu.add_command(
                    label=param,
                    command=lambda p=param: self._add_parameter_widget(entry_idx, p, {})
                )
        else:
            # If no more parameters to add, show a disabled button
            btn = ttk.Button(
                self.param_frames[entry_idx]['add_param'],
                text="No more parameters",
                state=tk.DISABLED,
                width=15
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)
    
    def _remove_parameter(self, entry_idx, param):
        """Remove a parameter from the specified entry"""
        if entry_idx not in self.entry_widgets or param not in self.entry_widgets[entry_idx]:
            return
            
        # Get the parameter frame from param_frames
        if entry_idx not in self.param_frames:
            return
            
        main_frame = self.param_frames[entry_idx]['main']
        
        # Find and destroy the widget for this parameter
        for child in main_frame.winfo_children():
            if hasattr(child, 'param_name') and child.param_name == param:
                # Get scroll position before removal
                canvas = main_frame.master.master  # Navigate up to the canvas
                if hasattr(canvas, 'yview'):  # Make sure it's the canvas
                    scroll_y = canvas.yview()[0]
                else:
                    scroll_y = 0
                
                # Destroy the parameter frame and all its children
                child.destroy()
                
                # Update data structures
                if (entry_idx < len(self.files["Clutter"]["data"]) and 
                    isinstance(self.files["Clutter"]["data"][entry_idx], dict)):
                    if param in self.files["Clutter"]["data"][entry_idx]:
                        del self.files["Clutter"]["data"][entry_idx][param]
                
                # Remove from entry_widgets
                if param in self.entry_widgets[entry_idx]:
                    del self.entry_widgets[entry_idx][param]
                
                # Update the add parameter button
                self._update_add_param_button(entry_idx)
                
                # Restore scroll position after a short delay if we have a valid canvas
                if hasattr(canvas, 'yview_moveto'):
                    def restore_scroll():
                        canvas.yview_moveto(scroll_y)
                    canvas.after(10, restore_scroll)
                
                break
    
    def _validate_numeric(self, value):
        """Validate that the input is a valid integer"""
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    def _validate_float(self, value):
        """Validate that the input is a valid float"""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def save_clutter_entries(self):
        """Save all entries for the current category"""
        try:
            if self.current_category not in self.files:
                messagebox.showerror("Error", f"Invalid category: {self.current_category}")
                return
                
            # Get the current file path or prompt to save as
            file_path = self.files[self.current_category]["path"]
            if not file_path:
                # If no file is open, prompt to save as
                return self.save_current_file()
                
            # Save the data to the file
            with open(file_path, 'w') as f:
                yaml.dump(self.files[self.current_category]["data"], f, default_flow_style=False, sort_keys=False)
                
            messagebox.showinfo("Success", f"{self.current_category} entries saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save {self.current_category} entries: {str(e)}")
            
    def delete_clutter_entry(self, index):
        """Delete an entry from the current category"""
        try:
            if not hasattr(self, 'filtered_data') or index >= len(self.filtered_data):
                return
                
            # Get the item to be deleted
            item_to_delete = self.filtered_data[index]
            
            # Remove from filtered data
            del self.filtered_data[index]
            
            # Remove from original data if it exists there
            if self.current_category in self.files and 'data' in self.files[self.current_category]:
                if item_to_delete in self.files[self.current_category]['data']:
                    self.files[self.current_category]['data'].remove(item_to_delete)
            
            # Update the display
            self.update_visible_entries()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete entry: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def add_clutter_entry(self):
        """Add a new empty entry for the current category"""
        try:
            if self.current_category not in self.files:
                messagebox.showerror("Error", f"Invalid category: {self.current_category}")
                return
                
            new_entry = {}
            # Only add required parameters initially
            if self.current_category in self.param_defs:
                for param, param_info in self.param_defs[self.current_category].items():
                    if param_info.get('required', False):
                        if param == "prefab" or param == "name":
                            new_entry[param] = ""
                        else:
                            new_entry[param] = param_info["default"]
            
            # Add the new entry to the current category's data
            self.files[self.current_category]["data"].append(new_entry)
            
            # Store current scroll position
            scroll_y = 0
            if hasattr(self, 'canvas'):
                scroll_y = self.canvas.yview()[0]
            
            # Refresh the entry view
            self.create_entry_view()
            
            # Restore scroll position after a short delay to allow UI to update
            if hasattr(self, 'canvas') and hasattr(self, 'canvas') and self.canvas.winfo_exists():
                def restore_scroll():
                    self.canvas.yview_moveto(1.0)  # Scroll to bottom
                self.canvas.after(10, restore_scroll)
            
            messagebox.showinfo("Success", f"New {self.current_category} entry added successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while adding entry: {str(e)}")
    
    def update_display(self):
        """Update the display based on current view mode"""
        if self.view_mode == "table":
            self.create_table_view()
            # Update biome list and items tree
            self.update_biome_list()
            self.update_items_tree()
        else:  # entry mode
            if self.current_category in ["Clutter", "Spawns"]:
                self.create_entry_view()
            else:
                messagebox.showinfo("Info", "Entry mode is only available for Clutter and Spawns categories")
                self.view_mode_var.set("table")
                self.view_mode = "table"
                self.update_display()
    
    def open_folder(self, initial_dir=None):
        """Open a profile folder and load all expand world YAML files from BepInEx/config/expand_world"""
        # Load config to get last used profile
        config = load_config()
        
        # Set initial directory based on config or default
        profiles_dir = os.path.expanduser("~\\AppData\\Roaming\\r2modmanPlus-local\\Valheim\\profiles")
        initial_dir = initial_dir or config.get('last_profile', profiles_dir)
        
        # Let user select the profile folder
        profile_path = filedialog.askdirectory(
            title="Select Profile Folder (e.g., 'WS5 Treasure WIP')",
            initialdir=initial_dir
        )
        
        if profile_path:
            # Save the selected profile to config
            config['last_profile'] = profile_path
            save_config(config)
            
            # Construct the path to the expand_world config directory
            expand_world_path = os.path.join(profile_path, "BepInEx", "config", "expand_world")
            
            # Check if the expand_world directory exists
            if not os.path.exists(expand_world_path):
                messagebox.showerror("Error", f"Could not find expand_world config directory at:\n{expand_world_path}")
                return
                
            # Try to load each file
            file_mapping = {
                "Clutter": "expand_clutter.yaml",
                "Environments": "expand_environments.yaml",
                "Spawns": "expand_spawns.yaml",
                "Locations": "expand_locations.yaml",
                "Vegetation": "expand_vegetation.yaml"
            }
            
            files_loaded = 0
            for category, filename in file_mapping.items():
                file_path = os.path.join(expand_world_path, filename)
                if os.path.exists(file_path):
                    self.load_file(file_path, category)
                    files_loaded += 1
            
            if files_loaded > 0:
                self.update_display()
                # Update window title to show current profile
                profile_name = os.path.basename(profile_path)
                self.root.title(f"Valheim Expand World Editor - {profile_name}")
                
                # Save the successful load to config
                config['last_profile'] = profile_path
                save_config(config)
            else:
                messagebox.showwarning("No Files Found", f"No expand world config files found in:\n{expand_world_path}")
    
    def open_file(self):
        """Open a single YAML file"""
        file_path = filedialog.askopenfilename(
            title="Open YAML File",
            filetypes=(("YAML files", "*.yaml;*.yml"), ("All files", "*.*")),
            initialdir=r"C:\Users\Broke\AppData\Roaming\r2modmanPlus-local\Valheim\profiles"
        )
        
        if file_path:
            # Determine category from filename
            filename = os.path.basename(file_path).lower()
            category = None
            
            if "clutter" in filename:
                category = "Clutter"
            elif "environment" in filename:
                category = "Environments"
            elif "spawn" in filename:
                category = "Spawns"
            elif "location" in filename:
                category = "Locations"
            elif "vegetation" in filename:
                category = "Vegetation"
            
            if category:
                self.load_file(file_path, category)
                self.update_display()
            else:
                messagebox.showwarning("Unknown File", "Could not determine file type from filename")
    
    def load_file(self, file_path, category):
        """Load a YAML file into the specified category"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file) or []
            
            self.files[category]["path"] = file_path
            self.files[category]["data"] = data if isinstance(data, list) else []
            
            self.root.title(f"Valheim Expand World Editor - {os.path.dirname(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load {file_path}: {str(e)}")
    
    def save_current_file(self):
        """Save the currently active category file"""
        category = self.current_category
        if not self.files[category]["path"]:
            messagebox.showwarning("No File", f"No {category} file loaded")
            return
        
        try:
            with open(self.files[category]["path"], 'w', encoding='utf-8') as file:
                yaml.dump(self.files[category]["data"], file, default_flow_style=False, sort_keys=False)
            messagebox.showinfo("Success", f"{category} file saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def save_all_files(self):
        """Save all loaded files"""
        saved_count = 0
        for category, file_info in self.files.items():
            if file_info["path"]:
                try:
                    with open(file_info["path"], 'w', encoding='utf-8') as file:
                        yaml.dump(file_info["data"], file, default_flow_style=False, sort_keys=False)
                    saved_count += 1
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save {category}: {str(e)}")
        
        if saved_count > 0:
            messagebox.showinfo("Success", f"Saved {saved_count} file(s) successfully!")
    
    def on_category_change(self, event=None):
        """Handle category tab change"""
        selected_tab = self.category_notebook.index(self.category_notebook.select())
        categories = list(self.category_frames.keys())
        new_category = categories[selected_tab]
        
        # Only allow entry mode for categories that support it (Clutter, Spawns, and Environments)
        if self.view_mode == "entry" and new_category not in ["Clutter", "Spawns", "Environments"]:
            messagebox.showinfo("Info", "Entry mode is only available for Clutter, Spawns, and Environments")
            # Switch back to table view
            self.view_mode = "table"
            self.view_mode_var.set("table")
            
        self.current_category = new_category
        
        # Force update the display with the new category
        if self.view_mode == "table":
            self.create_table_view()
            self.update_biome_list()
            self.update_items_tree()
        elif self.view_mode == "entry":
            self.create_entry_view()
        else:  # entry mode
            if self.current_category in ["Clutter", "Spawns"]:
                self.create_entry_view()
            else:
                # This shouldn't happen due to the check above, but just in case
                self.view_mode = "table"
                self.view_mode_var.set("table")
                self.update_display()
    
    def update_display(self):
        """Update the display based on current view mode"""
        if self.view_mode == "table":
            self.create_table_view()
            # Update biome list and items tree
            self.update_biome_list()
            self.update_items_tree()
        else:  # entry mode
            if self.current_category == "Clutter":
                self.create_entry_view()
            else:
                # If somehow we're in entry mode but not in Clutter, switch to table view
                self.view_mode = "table"
                self.view_mode_var.set("table")
                self.update_display()
    
    def on_biome_filter(self, event):
        """Handle biome filter selection"""
        if not hasattr(self, 'biome_listbox'):
            return
            
        selection = self.biome_listbox.curselection()
        if not selection:
            return
            
        selected = self.biome_listbox.get(selection[0])
        
        # Extract the base biome name by removing the count in parentheses if present
        if selected.startswith("-- All Biomes --"):
            self.current_biome = None
            selected_biome = None
        else:
            # Remove the count at the end (e.g., "Meadows (5)" -> "Meadows")
            self.current_biome = selected.split(" (")[0].strip()
            selected_biome = self.current_biome
        
        # Update the display based on current view mode
        if self.view_mode == "table":
            self.update_items_tree()
        elif self.current_category == "Clutter":  # entry mode
            self.create_entry_view()
        
        # After updating the view, restore the selection
        self.root.after(100, lambda: self._restore_biome_selection(selected_biome))
        
        print(f"Selected biome: {self.current_biome or 'All Biomes'}")
        print("=== End Biome Filter ===\n")
    
    def _restore_biome_selection(self, selected_biome):
        """Restore the biome selection after view updates"""
        if not hasattr(self, 'biome_listbox'):
            return
            
        # Update the selection in the listbox
        for i in range(self.biome_listbox.size()):
            item_text = self.biome_listbox.get(i)
            if selected_biome is None and item_text.startswith("-- All Biomes --"):
                self.biome_listbox.selection_clear(0, tk.END)
                self.biome_listbox.selection_set(i)
                self.biome_listbox.see(i)
                self.biome_listbox.activate(i)
                break
            elif selected_biome is not None and item_text.startswith(f"{selected_biome} ("):
                self.biome_listbox.selection_clear(0, tk.END)
                self.biome_listbox.selection_set(i)
                self.biome_listbox.see(i)
                self.biome_listbox.activate(i)
                break
    
    def update_biome_list(self):
        """Update the list of biomes with entry counts"""
        if not hasattr(self, 'biome_listbox') or not self.files[self.current_category]["data"]:
            return
            
        # Store the currently selected biome to restore it later
        current_selection = None
        if hasattr(self, 'current_biome') and self.current_biome:
            current_selection = self.current_biome
        
        # Count occurrences of each biome
        biome_counts = {}
        total_entries = 0
        
        for item in self.files[self.current_category]["data"]:
            if not isinstance(item, dict):
                continue
                
            total_entries += 1
            
            if "biome" in item and item["biome"]:
                biomes = set()  # Use a set to avoid duplicates within the same entry
                
                if isinstance(item["biome"], list):
                    # Handle list of biomes
                    for b in item["biome"]:
                        if b:  # Skip empty values
                            # Normalize the biome name (strip and title case)
                            normalized = str(b).strip()
                            if normalized:  # Only add non-empty strings
                                biomes.add(normalized)
                else:
                    # Handle string of comma-separated biomes
                    biome_str = str(item["biome"]).strip()
                    if biome_str:
                        # Split by comma, strip whitespace, and add to set
                        biomes.update(b.strip() for b in biome_str.split(",") if b.strip())
                
                # Count each unique biome for this entry
                for biome in biomes:
                    biome_counts[biome] = biome_counts.get(biome, 0) + 1
        
        # Clear and update biome listbox
        self.biome_listbox.delete(0, tk.END)
        
        # Add "All Biomes" with total count
        all_biomes_text = f"-- All Biomes -- ({total_entries} entries)"
        self.biome_listbox.insert(tk.END, all_biomes_text)
        
        # Add each biome with its count, excluding debug biome "128"
        biome_items = []
        for biome in sorted(biome_counts.keys()):
            # Skip the debug biome "128"
            if biome == "128":
                continue
                
            count = biome_counts[biome]
            item_text = f"{biome} ({count})"
            self.biome_listbox.insert(tk.END, item_text)
            biome_items.append((biome, item_text))
        
        # Restore the previous selection if it still exists
        if current_selection:
            found = False
            for i, (biome, item_text) in enumerate([(None, all_biomes_text)] + biome_items, 1):
                if biome == current_selection:
                    self.biome_listbox.selection_clear(0, tk.END)
                    self.biome_listbox.selection_set(i)
                    self.biome_listbox.see(i)
                    self.biome_listbox.activate(i)
                    found = True
                    break
            
            if not found:
                # If the previous selection is no longer valid, select "All Biomes"
                self.current_biome = None
                self.biome_listbox.selection_clear(0, tk.END)
                self.biome_listbox.selection_set(0)
                self.biome_listbox.see(0)
                self.biome_listbox.activate(0)
        else:
            # Select "All Biomes" by default
            self.current_biome = None
            self.biome_listbox.selection_clear(0, tk.END)
            self.biome_listbox.selection_set(0)
            self.biome_listbox.see(0)
            self.biome_listbox.activate(0)
    
    def _filter_entry_view(self):
        """Filter entry view based on selected biome"""
        print("\n=== Filtering Entry View ===")
        print(f"Current biome filter: {self.current_biome}")
        print(f"Number of entries before filter: {len(self.param_frames) if hasattr(self, 'param_frames') else 'N/A'}")
        
        # This method is no longer used as we now recreate the entire view
        # when filtering to ensure consistency
        print("Skipping filter (using full view recreation)")
        
        print("=== End Filtering ===\n")
    
    def _auto_size_columns(self, tree):
        """Auto-size all columns based on content"""
        # Get the appropriate data based on current filter
        if not hasattr(self, 'current_biome') or not self.current_biome:
            # No biome filter, use all data
            data = self.files.get(self.current_category, {}).get("data", [])
        else:
            # Use filtered data based on biome
            data = [
                item for item in self.files.get(self.current_category, {}).get("data", [])
                if isinstance(item, dict) and "biome" in item and 
                   (isinstance(item["biome"], str) and self.current_biome.lower() in item["biome"].lower() or
                    isinstance(item["biome"], list) and any(
                        self.current_biome.lower() == b.lower() for b in item["biome"] 
                        if isinstance(b, str)
                    )
                )
            ]
        
        # First pass: set column widths based on header text
        for col in tree["columns"]:
            tree.column(col, width=tkfont.Font().measure(col) + 20)
        
        # Second pass: adjust for content width
        for item in tree.get_children():
            values = tree.item(item, 'values')
            if not values:  # Skip if no values
                continue
                
            # Get the corresponding data item
            try:
                idx = int(values[0]) - 1  # Get index from first column (1-based)
                if 0 <= idx < len(data):
                    item_data = data[idx]
                    for col_idx, col in enumerate(tree["columns"][1:], 1):  # Skip index column
                        if col in item_data and item_data[col] is not None:
                            width = tkfont.Font().measure(str(item_data[col])) + 20
                            if tree.column(col, 'width') < width:
                                tree.column(col, width=min(400, width))  # Cap width at 400px
            except (ValueError, IndexError, TypeError) as e:
                print(f"Error sizing columns: {e}")
    
    def update_items_tree(self):
        """Update the items treeview with current category data"""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get data
        data = self.files[self.current_category]["data"]
        
        if not data:
            return
        
        # Filter by biome if selected
        filtered_data = data
        if self.current_biome:
            filtered_data = [
                item for item in data 
                if isinstance(item, dict) and "biome" in item and self.current_biome in str(item["biome"])
            ]
        
        # Initialize columns with default value
        columns = ["#"]
        
        # Configure columns based on first item
        if filtered_data and isinstance(filtered_data[0], dict):
            try:
                # Get all unique keys from all items
                all_keys = set()
                for item in filtered_data:
                    if isinstance(item, dict):
                        all_keys.update(item.keys())
                
                columns = ["#"] + sorted(all_keys)
                self.tree["columns"] = columns
                
                # Clear existing columns
                for col in self.tree["columns"]:
                    self.tree.heading(col, text="")
                    self.tree.column(col, width=0, stretch=False)
                
                # Configure column headings
                self.tree.heading("#0", text="Index")
                self.tree.column("#0", width=50, stretch=False)
                
                for col in columns[1:]:  # Skip "#"
                    self.tree.heading(col, text=col)
                    self.tree.column(col, width=120, stretch=False)  # Initial width, will be auto-sized
                
                # Add items
                for idx, item in enumerate(filtered_data):
                    if isinstance(item, dict):
                        values = [idx + 1]
                        for col in columns[1:]:  # Skip "#"
                            val = item.get(col, "")
                            # Handle color values
                            if isinstance(val, dict) and all(k in val for k in ['r', 'g', 'b']):
                                r = val['r']
                                g = val['g']
                                b = val['b']
                                val = f"R: {r:.2f} G: {g:.2f} B: {b:.2f}"
                            values.append(str(val) if val is not None else "")
                        self.tree.insert("", tk.END, text=str(idx), values=values)
                
                # Auto-size columns after all items are added
                self._auto_size_columns(self.tree)
                
            except Exception as e:
                print(f"Error updating tree view: {e}")
                messagebox.showerror("Error", f"Failed to update tree view: {str(e)}")
    
    def on_item_double_click(self, event):
        """Handle double-click on item to edit"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = self.tree.item(selection[0])["text"]
        messagebox.showinfo("Edit", f"Editing item {item_id} - Feature coming soon!")

def main():
    root = tk.Tk()
    
    try:
        style = ttk.Style()
        style.theme_use('clam')  # Use a modern theme
        
        # Configure styles before creating the app
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        app = ExpandWorldEditor(root)
        
        # Try to load the last used profile
        def try_load_last_profile():
            try:
                if app.last_profile and os.path.exists(app.last_profile):
                    expand_world_path = os.path.join(app.last_profile, "BepInEx", "config", "expand_world")
                    if os.path.exists(expand_world_path):
                        app.open_folder(app.last_profile)
            except Exception as e:
                print(f"Error loading last profile: {e}")
                # Don't show error to user on startup
        
        # Use after() to ensure the UI is fully initialized
        root.after(500, try_load_last_profile)
        
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application failed to start: {str(e)}")
        raise

if __name__ == "__main__":
    main()
