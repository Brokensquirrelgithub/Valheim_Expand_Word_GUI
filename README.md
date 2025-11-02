# Valheim Expand World Editor

A graphical user interface for editing Valheim's Expand World mod configuration files. This tool provides an intuitive way to manage and edit various game configurations including Clutter, Environments, Spawns, and more.

## Features

- **Easy Configuration Editing**: Edit Expand World YAML files through a user-friendly interface
- **Multiple Categories**: Supports editing Clutter, Environments, Spawns, Locations, and Vegetation
- **Real-time Filtering**: Filter entries by biome and search terms
- **Table and Entry Views**: Toggle between a spreadsheet-like view and detailed entry view
- **Validation**: Built-in validation for different parameter types (integers, floats, booleans, etc.)
- **Modern UI**: Clean, themable interface with tooltips and visual feedback

## Installation

1. Ensure you have Python 3.8 or higher installed
2. Clone this repository or download the source code
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

```bash
python expand_world_editor.py
```

2. Use the File menu to open an Expand World configuration folder (typically located in `BepInEx/config/expand_world`)
3. Select a category from the tabs at the top
4. Use the search and filter options to find specific entries
5. Make your changes - they are automatically saved when you switch tabs or use the save options

## Keyboard Shortcuts

- `Ctrl+O`: Open folder
- `Ctrl+S`: Save current file
- `Ctrl+Shift+S`: Save all files
- `Ctrl+F`: Focus search box
- `F5`: Refresh view
- `Ctrl+Tab`: Next tab
- `Ctrl+Shift+Tab`: Previous tab

## Project Structure

- `expand_world_editor.py`: Main application file
- `gui/`: Contains GUI components
  - `tooltip.py`: Custom tooltip implementation
- `data/`: Configuration and data handling
  - `config.py`: Configuration management
  - `file_handling.py`: File I/O operations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Created for the Valheim modding community
- Uses [ttkthemes](https://github.com/RedFantom/ttkthemes) for modern theming support
- Icons from [Material Design Icons](https://materialdesignicons.com/)

## Support

For support, please [open an issue](https://github.com/yourusername/valheim-expand-world-editor/issues) on GitHub.
