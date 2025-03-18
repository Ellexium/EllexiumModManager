import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
import json
import os
import random # Import the random module
from pathlib import Path
import re # Import the regular expression module


class CustomSlider(tk.Frame):
    def __init__(self, master=None, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.from_value = from_
        self.to_value = to
        self.resolution = resolution
        self.orient = orient
        self.command = command
        self._value = tk.DoubleVar(self, value=from_)
        self._enabled = tk.BooleanVar(self, value=True) # Track enabled state

        self.canvas_width = 200
        self.canvas_height = 25
        self.thumb_width = 10
        self.default_thumb_color = "#777777" # Store default thumb color
        self.thumb_color = self.default_thumb_color
        self.track_color = "#666666"
        self.active_track_color = "#999999"
        self.disabled_track_color = "#555555" # Color when disabled
        self.disabled_thumb_color = "#888888" # Color when disabled
        self.hover_thumb_color = "orange" # Color when hovering

        self.canvas = tk.Canvas(self, width=self.canvas_width, height=self.canvas_height, highlightthickness=0, background=self.master.cget('bg')) # inherit background
        self.canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Enter>", self._on_enter) # Bind hover enter event
        self.canvas.bind("<Leave>", self._on_leave) # Bind hover leave event

        self.percentage_label = tk.Label(self, text="0%", width=4, font=("Segoe UI", 12, "bold"), fg="lightgrey", bg="#333333") # Styled label

        self.percentage_label.pack(side=tk.RIGHT, padx=5)

        self.draw_slider()
        self._update_percentage_label() # Initial percentage update


    def draw_slider(self):
        self.canvas.delete("all")
        track_y_center = self.canvas_height / 2
        track_height = 5
        track_x1 = self.thumb_width / 2
        track_x2 = self.canvas_width - self.thumb_width / 2

        # Determine colors based on enabled state
        if self._enabled.get():
            track_color = self.track_color
            active_track_color = self.active_track_color
            thumb_color = self.thumb_color # Use self.thumb_color which can change on hover
        else:
            track_color = self.disabled_track_color
            active_track_color = self.disabled_track_color # Or keep track color same when disabled
            thumb_color = self.disabled_thumb_color


        # Track
        self.canvas.create_rectangle(track_x1, track_y_center - track_height/2, track_x2, track_y_center + track_height/2,
                                     fill=track_color, outline="")

        # Active Track (up to thumb)
        thumb_center_x = self._value_to_x(self._value.get())
        self.canvas.create_rectangle(track_x1, track_y_center - track_height/2, thumb_center_x, track_y_center + track_height/2,
                                     fill=active_track_color, outline="")


        # Thumb
        self.canvas.create_rectangle(thumb_center_x - self.thumb_width/2, 0, thumb_center_x + self.thumb_width/2, self.canvas_height,
                                     fill=thumb_color, outline="")

    def _x_to_value(self, x):
        """Convert canvas x-coordinate to slider value."""
        track_length = self.canvas_width - self.thumb_width
        if track_length <= 0:
            return self.from_value  # Avoid division by zero
        position_ratio = max(0.0, min(1.0, (x - self.thumb_width / 2) / track_length)) # Clamp between 0 and 1
        value_range = self.to_value - self.from_value
        value = self.from_value + position_ratio * value_range
        return round(value / self.resolution) * self.resolution # Apply resolution

    def _value_to_x(self, value):
        """Convert slider value to canvas x-coordinate."""
        track_length = self.canvas_width - self.thumb_width
        if self.to_value == self.from_value:
            return self.thumb_width / 2 # Avoid division by zero if range is zero
        value_ratio = (value - self.from_value) / (self.to_value - self.from_value)
        return self.thumb_width / 2 + value_ratio * track_length

    def _on_click(self, event):
        if self._enabled.get(): # Only respond to clicks if enabled
            self._update_value_from_event(event)

    def _on_drag(self, event):
        if self._enabled.get(): # Only respond to drags if enabled
            self._update_value_from_event(event)

    def _on_release(self, event):
        pass # Optional action on release

    def _update_value_from_event(self, event):
        new_value = self._x_to_value(event.x)
        self.set(new_value)

    def set(self, value):
        value = max(self.from_value, min(self.to_value, value)) # Clamp value
        self._value.set(value)
        self.draw_slider()
        self._update_percentage_label() # Update percentage label when value changes
        if self.command:
            self.command(value)

    def get(self):
        return self._value.get()

    def config(self, **kwargs):
        """Override config to handle state."""
        if 'state' in kwargs:
            state = kwargs['state']
            if state == tk.DISABLED:
                self.disable()
            elif state == tk.NORMAL:
                self.enable()
            del kwargs['state'] # Remove state so tk.Frame.config doesn't get it

        super().config(**kwargs) # Call tk.Frame.config for other options

    def configure(self, **kwargs): # configure is an alias for config
        self.config(**kwargs)


    def enable(self):
        """Enable the slider."""
        self._enabled.set(True)
        self.draw_slider() # Redraw in enabled state

    def disable(self):
        """Disable the slider."""
        self._enabled.set(False)
        self.draw_slider() # Redraw in disabled state

    def _on_enter(self, event):
        """Handle mouse hover enter event."""
        self.thumb_color = self.hover_thumb_color # Change thumb color to orange
        self.draw_slider()

    def _on_leave(self, event):
        """Handle mouse hover leave event."""
        self.thumb_color = self.default_thumb_color # Revert thumb color to default
        self.draw_slider()


    def _update_percentage_label(self):
        """Updates the percentage label next to the slider."""
        percentage = ((self._value.get() - self.from_value) / (self.to_value - self.from_value)) * 100
        self.percentage_label.config(text=f"{percentage:.0f}%")


# Global variable to keep track of the current ColorPickerApp instance
current_color_picker_app = None

def create_color_picker_window(master=None, on_replace_or_spawn_callback=None): # Added callback argument
    """
    Creates and displays the Color Picker window, optionally centered on the master window.
    If a window already exists, it closes the old one and opens a new one.

    Args:
        master (tk.Tk or tk.Toplevel, optional): The parent window.
                                                If None, it runs as a standalone app.
                                                Defaults to None.
        on_replace_or_spawn_callback (function, optional): Callback function to be called
                                                        on replace or spawn actions.

    Returns:
        ColorPickerApp: The instance of the ColorPickerApp window.
    """
    global current_color_picker_app

    print(f"DEBUG: Working directory in create_color_picker_window: {os.getcwd()}") # Print current working directory

    # Check if a color picker window already exists
    if current_color_picker_app:
        current_color_picker_app.destroy() # Close the existing window
        current_color_picker_app = None     # Reset the global variable

    if master:
        app = ColorPickerApp(master=master, on_replace_or_spawn_callback=on_replace_or_spawn_callback) # Pass callback to ColorPickerApp init
        app.transient(master) # Make it a transient window

        # Center the window on the master
        master.update_idletasks() # Ensure master window size is updated
        app_width = app.winfo_reqwidth()
        app_height = app.winfo_reqheight()
        master_width = master.winfo_width()
        master_height = master.winfo_height()
        pos_x = master.winfo_x() + (master_width - app_width) // 2
        pos_y = master.winfo_y() + (master_height - app_height) // 2
        app.geometry(f"+{pos_x}+{pos_y}")


    else:
        app = ColorPickerApp() # Run as standalone

        # Center the window on the screen
        screen_width = app.winfo_screenwidth()
        screen_height = app.winfo_screenheight()
        app_width = app.winfo_reqwidth()
        app_height = app.winfo_reqheight()
        pos_x = (screen_width - app_width) // 2
        pos_y = (screen_height - app_height) // 2
        app.geometry(f"+{pos_x}+{pos_y}")
        app.resizable(False, False)

    current_color_picker_app = app # Update the global variable with the new instance
    return app


class ColorPickerApp(tk.Toplevel): # Changed from tk.Tk to tk.Toplevel
    def __init__(self, master=None, on_replace_or_spawn_callback=None): # Added callback argument
        super().__init__(master) # Initialize as Toplevel, taking master as argument
        self.on_replace_or_spawn_callback = on_replace_or_spawn_callback # Store the callback

        # Set scaling factor - only if running standalone, otherwise inherit from master
        if master is None:
            self.tk.call('tk', 'scaling', 1.25)

        self.title("Pick Color") # Changed title
        self.configure(bg="#333333") # Set background for the main window

        # Main frame to contain everything and handle centering
        self.main_frame = tk.Frame(self, bg="#333333")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=0) # Padding around main frame
        self.main_frame.columnconfigure(0, weight=1) # Allow column 0 (labels) to expand
        self.main_frame.columnconfigure(1, weight=1) # Allow column 1 (sliders) to expand

        # Title Label
        self.app_title_label = tk.Label(self.main_frame, text="Color Configuration", font=("Segoe UI", 13, "bold"), fg="white", bg="#333333")
        self.app_title_label.grid(row=0, column=0, columnspan=2, pady=10)


        # Font for all widgets
        font = ("Segoe UI", 12)

        # Button default and hover colors
        button_default_bg = "#555555"
        button_default_fg = "white"
        button_hover_bg = "orange"
        button_hover_fg = "white"

        self.randomize_button = tk.Button(self.main_frame, text="Randomize", command=self.randomize_settings, font=font, bg=button_default_bg, fg=button_default_fg, relief=tk.FLAT, highlightthickness=0) # Renamed button and command
        self.randomize_button.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew") # Span 2 columns in main_frame

        self.replace_current_button = tk.Button(self.main_frame, text="Replace Current", command=self.replace_current_vehicle_lua, font=font, bg=button_default_bg, fg=button_default_fg, relief=tk.FLAT, highlightthickness=0) # New Replace Current button
        self.replace_current_button.grid(row=5, column=0, columnspan=2, pady=5, sticky="ew") # Column 0, moved below sliders and span 2 cols now

        self.spawn_new_button = tk.Button(self.main_frame, text="Spawn New", command=self.spawn_new_vehicle_lua, font=font, bg=button_default_bg, fg=button_default_fg, relief=tk.FLAT, highlightthickness=0) # New Spawn New button
        self.spawn_new_button.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew") # Column 0, moved below replace and span 2 cols now

        # New: Close Button - remains the same
        self.close_button = tk.Button(self.main_frame, text="Close", command=self.close_window, font=font, bg=button_default_bg, fg=button_default_fg, relief=tk.FLAT, highlightthickness=0) # New Close button
        #self.close_button.grid(row=7, column=0, columnspan=2, pady=10, sticky="ew") # Placed below other buttons, span 2 cols

        # Hover effect functions for buttons - remain the same
        def on_enter_button(event):
            event.widget.config(bg=button_hover_bg, fg=button_hover_fg)

        def on_leave_button(event):
            event.widget.config(bg=button_default_bg, fg=button_default_fg)

        self.randomize_button.bind("<Enter>", on_enter_button)
        self.randomize_button.bind("<Leave>", on_leave_button)
        self.replace_current_button.bind("<Enter>", on_enter_button)
        self.replace_current_button.bind("<Leave>", on_leave_button)
        self.spawn_new_button.bind("<Enter>", on_enter_button)
        self.spawn_new_button.bind("<Leave>", on_leave_button)
        self.close_button.bind("<Enter>", on_enter_button)
        self.close_button.bind("<Leave>", on_leave_button)


        # Sliders Frame to hold all sliders and labels in columns - remain the same
        self.sliders_frame = tk.Frame(self.main_frame, bg="#333333")
        self.sliders_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10) # Span 2 columns, expand

        # Column configure for sliders_frame - important for layout! - remain the same
        self.sliders_frame.columnconfigure(0, weight=1) # Weight for labels column
        self.sliders_frame.columnconfigure(1, weight=1) # Weight for sliders column


        # Labels Frame - New Frame for Labels Column - remain the same
        self.labels_column_frame = tk.Frame(self.sliders_frame, bg="#333333")
        self.labels_column_frame.grid(row=0, column=0, sticky="new") # Column 0 for labels, sticky North, East, West

        # Sliders Frame - New Frame for Sliders Column - remain the same
        self.sliders_column_frame = tk.Frame(self.sliders_frame, bg="#333333")
        self.sliders_column_frame.grid(row=0, column=1, sticky="new") # Column 1 for sliders, sticky North, East, West

        # Base Color Label - Moved to labels column frame - remain the same
        self.base_color_label = tk.Label(self.labels_column_frame, text="Base Color:", font=font, fg="white", bg="#333333")
        self.base_color_label.grid(row=0, column=0, sticky="ne", padx=5, pady=7) # Placed at the top of labels column, pady increased

        # Color Swatch - Moved to sliders column frame, next to base color label - remain the same
        self.color_swatch_canvas = tk.Canvas(self.sliders_column_frame, width=190, height=21, bg="white", highlightthickness=2, relief='solid', bd=1, highlightbackground="#808080") # Initial white swatch
        self.color_swatch_canvas.grid(row=0, column=1, sticky="nw", padx=5, pady=8) # Placed at the top of sliders column, next to label, pady increased
        self.color_swatch_canvas.bind("<Button-1>", lambda event: self._open_color_picker_from_swatch()) # Clicking swatch opens color picker - using new method
        self.color_swatch_canvas.bind("<Enter>", self._on_swatch_enter) # Bind hover enter event for swatch
        self.color_swatch_canvas.bind("<Leave>", self._on_swatch_leave) # Bind hover leave event for swatch
        self.default_swatch_highlightcolor = "#808080" # Store default highlight color

        # Sliders for paint properties - using grid inside respective column frames - remain the same
        self.clearcoat_label = tk.Label(self.labels_column_frame, text="Clearcoat:", font=font, fg="white", bg="#333333")
        self.clearcoat_slider = CustomSlider(self.sliders_column_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=self.update_clearcoat, bg="#333333")
        self.clearcoat_label.grid(row=1, column=0, sticky='ne', padx=5, pady=7) # Row 1 in labels column, pady increased
        self.clearcoat_slider.grid(row=1, column=1, sticky='ew', padx=5, pady=7) # Row 1 in sliders column, pady increased


        self.clearcoatRoughness_label = tk.Label(self.labels_column_frame, text="Clearcoat Roughness:", font=font, fg="white", bg="#333333")
        self.clearcoatRoughness_slider = CustomSlider(self.sliders_column_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=self.update_clearcoatRoughness, bg="#333333")
        self.clearcoatRoughness_label.grid(row=2, column=0, sticky='ne', padx=5, pady=7) # Row 2 in labels column, pady increased
        self.clearcoatRoughness_slider.grid(row=2, column=1, sticky='ew', padx=5, pady=7) # Row 2 in sliders column, pady increased


        self.metallic_label = tk.Label(self.labels_column_frame, text="Metallic:", font=font, fg="white", bg="#333333")
        self.metallic_slider = CustomSlider(self.sliders_column_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=self.update_metallic, bg="#333333")
        self.metallic_label.grid(row=3, column=0, sticky='ne', padx=5, pady=7) # Row 3 in labels column, pady increased
        self.metallic_slider.grid(row=3, column=1, sticky='ew', padx=5, pady=7) # Row 3 in sliders column, pady increased


        self.roughness_label = tk.Label(self.labels_column_frame, text="Roughness:", font=font, fg="white", bg="#333333")
        self.roughness_slider = CustomSlider(self.sliders_column_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=self.update_roughness, bg="#333333")
        self.roughness_label.grid(row=4, column=0, sticky='ne', padx=5, pady=7) # Row 4 in labels column, pady increased
        self.roughness_slider.grid(row=4, column=1, sticky='ew', padx=5, pady=7) # Row 4 in sliders column, pady increased


        self.save_button = tk.Button(self.main_frame, text="Save File", command=self.save_file, state=tk.DISABLED, font=font, bg="#555555", fg="white", relief=tk.FLAT, highlightthickness=0) # Initially disabled save button
        # self.save_button.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew") # Span 2 columns in main_frame # Removed from layout

        self.file_label = tk.Label(self.main_frame, text="File: No file loaded", font=font, fg="white", bg="#333333")
        # self.file_label.grid(row=7, column=0, columnspan=2, pady=5, sticky="ew") # Span 2 columns in main_frame # Removed from layout


        self.data = None
        self.filepath = None

        # Initial disable, moved here so CustomSliders are created before disabling.
        self.disable_controls()
        self.update_color_swatch("#FFFFFF") # Initialize swatch to white

        # --- Icon Loading Code ---
        self.script_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Define script_dir for ColorPickerApp
        icon_path = self.script_dir / "data/icon.png"

        if os.path.exists(icon_path):
            try:
                icon_image = tk.PhotoImage(file=icon_path)
                self.iconphoto(False, icon_image) # Use self (ColorPickerApp window) instead of detail_win
            except tk.TclError as e: # Catch potential TclError for image loading issues
                print(f"Error loading icon: {e}")
                print(f"Make sure icon file is a valid PNG and located at: {icon_path}")
        else:
            print(f"Icon file not found: {icon_path}")


        self.auto_load_file() # Call auto_load_file at startup


    def auto_load_file(self):
        """Automatically loads 'customcarcol.pc' from the 'data' directory."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        filepath_pc = os.path.join(parent_dir, "data", "customcarcol.pc")  # Direct path to customcarcol.pc

        if os.path.exists(filepath_pc):
            try:
                self.open_file(filepath=filepath_pc)  # Directly open customcarcol.pc
            except Exception as e:
                messagebox.showerror("Error", f"Error loading '{filepath_pc}': {e}")
        else:
            messagebox.showerror("Error", f"'customcarcol.pc' not found in 'data' directory:\n{filepath_pc}")
            print(f"'customcarcol.pc' not found at: {filepath_pc}. Autoload skipped.") # Optional print for console feedback


    def ask_open_file(self): # Renamed from open_file to ask_open_file
        """Opens a file dialog to choose a JSON file."""
        filepath = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            self.open_file(filepath=filepath) # Call open_file with the selected filepath


    def open_file(self, filepath): # Modified to accept filepath argument
        """Opens a JSON file, attempts to rebuild JSON on error, removes trailing commas, and loads its data."""
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json_string = f.read()

            try:
                data = json.loads(json_string) # Try to parse directly
            except json.JSONDecodeError as original_e:
                print("Initial JSON parsing failed. Attempting to rebuild JSON...")
                try:
                    rebuilt_json_string = self.rebuild_json_from_string(json_string)
                    if rebuilt_json_string:
                        data = json.loads(rebuilt_json_string) # Load the rebuilt JSON
                        print("JSON rebuilt and loaded successfully (after error correction). Please verify data.")
                    else:
                        raise original_e # Rebuilding failed, re-raise original error
                except Exception as rebuild_e: # Catch errors during rebuild process itself
                    messagebox.showerror("Error", f"Failed to load file and JSON rebuilding also failed. Please check JSON syntax manually.\nOriginal error: {original_e}\nRebuild error: {rebuild_e}")
                    self.handle_load_error()
                    return # Exit function on rebuild failure

            cleaned_json_string = self.remove_trailing_commas(json.dumps(data)) # Clean trailing commas from rebuilt JSON (just in case)
            data = json.loads(cleaned_json_string) # Parse again after trailing comma removal (though should be valid now)


            if 'paints' not in data:
                data['paints'] = []

            self.data = data
            self.filepath = filepath
            filename = os.path.basename(filepath)
            self.file_label.config(text=f"File: {filename}")
            self.update_color_display()
            self.enable_controls()
            #messagebox.showinfo("Success", "File loaded successfully!")

        except json.JSONDecodeError as e: # Catch general JSONDecodeErrors (if rebuild still fails to produce valid JSON)
            messagebox.showerror("Error", f"Failed to load file due to JSON format error even after attempting to rebuild. Please check JSON syntax manually.\nError: {e}")
            self.handle_load_error()
        except Exception as e: # Catch other potential errors (file reading, etc.)
            messagebox.showerror("Error", f"An unexpected error occurred while loading file: {e}")
            self.handle_load_error()


    def rebuild_json_from_string(self, json_string):
        """Attempts to rebuild a valid JSON string by extracting key-value pairs, including 'model'."""
        vars_data = {}
        parts_data = {}
        format_value = 2 # Default format, you might need to extract this more dynamically if it varies
        model_name = None # Initialize model_name to None

        try:
            lines = json_string.splitlines()
            current_section = None # Keep track of whether we are in "vars" or "parts"

            key_value_regex = re.compile(r'"([^"]+)":\s*"([^"]*)"') # Regex for key-value extraction (string values only for now)
            model_regex = re.compile(r'"model":\s*"([^"]*)"') # Regex to specifically extract "model"

            for line in lines:
                line = line.strip()

                # Check for "model" line first
                model_match = model_regex.search(line)
                if model_match:
                    model_name = model_match.group(1) # Extract model name

                if line.startswith('"vars":{'):
                    current_section = "vars"
                elif line.startswith('"parts":{'):
                    current_section = "parts"
                elif line.startswith('},') or line.startswith('}'): # End of a section (or '}' at the very end - more robust)
                    current_section = None # Important to reset for lines after sections
                elif current_section == "vars" or current_section == "parts":
                    match = key_value_regex.search(line)
                    if match:
                        key = match.group(1)
                        value = match.group(2)
                        if current_section == "vars":
                            vars_data[key] = value
                        elif current_section == "parts":
                            parts_data[key] = value

            rebuilt_data = {
                "vars": vars_data,
                "parts": parts_data,
                "format": format_value # Or extract format dynamically if needed
            }
            if model_name: # Add model to rebuilt_data only if found
                rebuilt_data["model"] = model_name

            return json.dumps(rebuilt_data, indent=2) # Serialize back to JSON with indentation for readability (optional)

        except Exception as e: # Catch any errors during rebuilding
            print(f"Error during JSON rebuilding: {e}")
            return None # Indicate rebuilding failure


    def remove_trailing_commas(self, json_string):
        """Removes trailing commas from a JSON string to make it valid."""
        trailing_comma_regex = re.compile(r',\s*(?=[}\]])')
        cleaned_string = trailing_comma_regex.sub('', json_string)
        return cleaned_string

    def handle_load_error(self):
        """Common actions to perform when file loading fails."""
        self.disable_controls()
        self.data = None
        self.filepath = None
        self.file_label.config(text="File: No file loaded")
        #self.color_display_label.config(text="Error loading file.")

    def hex_to_rgb(self, hex_color):
        """Converts hex color string to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _open_color_picker_from_swatch(self):
        """Opens the color picker with the current swatch color as initial color."""
        current_hex_color = self.color_swatch_canvas.cget("bg")
        initial_rgb = self.hex_to_rgb(current_hex_color)
        self.choose_color(initial_color=initial_rgb) # Call choose_color with initial color


    def randomize_settings(self): # Renamed from choose_color to randomize_settings
        """Randomizes slider values and base color."""
        if not hasattr(self, 'data') or self.data is None:
            messagebox.showerror("Error", "No file loaded. Please open a JSON file first.")
            return

        # Randomize slider values
        self.clearcoat_slider.set(random.uniform(0.0, 1.0))
        self.clearcoatRoughness_slider.set(random.uniform(0.0, 1.0))
        self.metallic_slider.set(random.uniform(0.0, 1.0))
        self.roughness_slider.set(random.uniform(0.0, 1.0))

        # Generate random RGB color (normalized 0.0-1.0)
        random_rgb_normalized = [random.random() for _ in range(3)]
        random_alpha = 1.0 # Keep alpha at 1.0 for now, can randomize if needed
        random_rgba_normalized = random_rgb_normalized + [random_alpha]
        random_rgb_255 = [int(c * 255) for c in random_rgb_normalized]
        random_hex_color = '#%02x%02x%02x' % tuple(random_rgb_255) # Get hex color

        # Update data with randomized values (including baseColor)
        if not self.data['paints']:
            self.data['paints'].append({}) # Ensure paints list isn't empty if it was
        if not self.data['paints'][0]:
            self.data['paints'][0] = {} # Ensure paint entry isn't empty if it was

        self.data['paints'][0]['baseColor'] = random_rgba_normalized
        self.data['paints'][0]['clearcoat'] = float(self.clearcoat_slider.get())
        self.data['paints'][0]['clearcoatRoughness'] = self.clearcoatRoughness_slider.get()
        self.data['paints'][0]['metallic'] = float(self.metallic_slider.get())
        self.data['paints'][0]['roughness'] = self.roughness_slider.get()


        self.update_color_display()
        self.update_color_swatch(random_hex_color) # Update swatch with random color
        if self.filepath: # Save only if a file is loaded
            self.save_file() # Autosave after randomization

    def spawn_new_vehicle_lua(self):
        """Creates Spawn_Queue_Transient.lua to spawn a new vehicle with current color config."""
        self.create_lua_file("spawnNewVehicle")
        if self.on_replace_or_spawn_callback: # Check if callback is set
            self.on_replace_or_spawn_callback() # Call the callback function

    def replace_current_vehicle_lua(self):
        """Creates Spawn_Queue_Transient.lua to replace the current vehicle with current color config."""
        self.create_lua_file("replaceVehicle")
        if self.on_replace_or_spawn_callback: # Check if callback is set
            self.on_replace_or_spawn_callback() # Call the callback function


    def create_lua_file(self, function_name):
        """Creates or updates Spawn_Queue_Transient.lua with specified function and model."""
        model_name = None

        if self.data and 'model' in self.data:
            model_name = self.data.get('model') # Get model name from loaded JSON
        else:
            # If model is not in self.data, try to read from model_information.txt
            script_dir = os.path.dirname(os.path.abspath(__file__)) # Script directory (as you have it)
            parent_dir = os.path.dirname(script_dir)  # Go one level up to the parent directory
            data_dir = os.path.join(parent_dir, "data") # Data folder path
            model_info_filepath = os.path.join(data_dir, "model_information.txt")

            if os.path.exists(model_info_filepath):
                try:
                    with open(model_info_filepath, 'r', encoding='utf-8') as f:
                        model_name = f.readline().strip() # Read the first line as model name
                except Exception as e:
                    messagebox.showerror("Error", f"Error reading model_information.txt: {e}")
                    return
            else:
                messagebox.showerror("Error", "Model information is missing from loaded file and model_information.txt not found.")
                return

        if not model_name:
            messagebox.showerror("Error", "Could not determine vehicle model.")
            return

        script_dir = os.path.dirname(os.path.abspath(__file__)) # Script directory (as you have it)
        parent_dir = os.path.dirname(script_dir)  # Go one level up to the parent directory

        data_dir = os.path.join(parent_dir, "data") # Data folder path
        os.makedirs(data_dir, exist_ok=True) # Ensure data folder exists
        lua_filepath = os.path.join(data_dir, "Spawn_Queue_Transient.lua") # Path to lua file

        lua_content = f'core_vehicles.{function_name}("{model_name}", {{config = \'mods/EllexiumModManager/data/customcarcol.pc\'}})'

        try:
            with open(lua_filepath, 'w', encoding='utf-8') as f:
                f.write("local file = io.open(\"mods/EllexiumModManager/data/commandconfirmation.txt\", \"w\")\n")
                f.write(lua_content)
            #messagebox.showinfo("Success", f"'{lua_filepath}' created/updated successfully!\n\nContents:\n{lua_content}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create/update '{lua_filepath}': {e}")


    def choose_color(self, initial_color=None):
        """Opens the color chooser dialog and updates or creates the baseColor and paint properties."""
        if not hasattr(self, 'data') or self.data is None:
            messagebox.showerror("Error", "No file loaded. Please open a JSON file first.")
            return

        color_code = colorchooser.askcolor(title="Choose Base Color", initialcolor=initial_color, parent=self) # Pass initial color
        if color_code[0]:
            rgb = color_code[0]
            normalized_rgb = [c / 255.0 for c in rgb]
            hex_color = '#%02x%02x%02x' % tuple(int(c) for c in rgb) # Get hex color

            if not self.data['paints']:
                default_paint = {
                    "baseColor": normalized_rgb + [1.0],
                    "clearcoat": float(self.clearcoat_slider.get()), # Get values from sliders as floats
                    "clearcoatRoughness": float(self.clearcoatRoughness_slider.get()),
                    "metallic": float(self.metallic_slider.get()), # Get values from floats
                    "roughness": float(self.roughness_slider.get())
                }
                self.data['paints'].append(default_paint)
            else:
                if 'baseColor' in self.data['paints'][0] and isinstance(self.data['paints'][0]['baseColor'], list) and len(self.data['paints'][0]['baseColor']) >= 3:
                     alpha_or_intensity = self.data['paints'][0]['baseColor'][3] if len(self.data['paints'][0]['baseColor']) > 3 else 1.0
                     self.data['paints'][0]['baseColor'] = normalized_rgb + [alpha_or_intensity]
                else:
                    default_paint = {
                        "baseColor": normalized_rgb + [1.0],
                        "clearcoat": float(self.clearcoat_slider.get()), # Get values from floats
                        "clearcoatRoughness": float(self.clearcoatRoughness_slider.get()),
                        "metallic": float(self.metallic_slider.get()), # Get values from floats
                        "roughness": float(self.roughness_slider.get())
                    }
                    self.data['paints'][0] = default_paint

                # Update other paint properties from sliders
                self.data['paints'][0]['clearcoat'] = float(self.clearcoat_slider.get()) # Save as float
                self.data['paints'][0]['clearcoatRoughness'] = float(self.clearcoatRoughness_slider.get())
                self.data['paints'][0]['metallic'] = float(self.metallic_slider.get()) # Save as float
                self.data['paints'][0]['roughness'] = float(self.roughness_slider.get())


            self.update_color_display()
            self.update_color_swatch(hex_color) # Update swatch after choosing color
            if self.filepath: # Save only if a file is loaded
                self.save_file() # Autosave after color change


    def save_file(self):
        """Saves the modified JSON data back to the opened file, removing space after colons."""
        if not hasattr(self, 'data') or self.data is None or not hasattr(self, 'filepath') or self.filepath is None:
            print("No file loaded or no changes to save.") # Changed to print for non-blocking autosave
            return

        try:
            # 1. Generate the JSON string with indent (for readability in file, if desired)
            json_string = json.dumps(self.data, indent=2)

            # 2. Remove the space after colons using string replacement
            json_string_no_space = json_string.replace(": ", ":")

            # 3. Write the modified JSON string to the file
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(json_string_no_space) # Write the space-less string

            print(f"File saved to: {self.filepath} (spaces after colons removed)") # Updated print message
        except Exception as e:
            print(f"Failed to save file: {e}") # Changed to print for non-blocking autosave

    def _on_swatch_enter(self, event):
        """Handles mouse hover enter event for color swatch."""
        self.color_swatch_canvas.config(highlightbackground="orange", highlightthickness=2) # Change highlight color to orange

    def _on_swatch_leave(self, event):
        """Handles mouse hover leave event for color swatch."""
        self.color_swatch_canvas.config(highlightbackground=self.default_swatch_highlightcolor,  highlightthickness=2) # Revert to default highlight color


    def update_color_display(self):
        """Updates the display of the current base colors and initializes sliders."""
        if hasattr(self, 'data') and self.data and 'paints' in self.data and isinstance(self.data['paints'], list):
            if not self.data['paints']:
                self.update_color_swatch("#cccccc") # Default white swatch if no paint entries
                self.reset_slider_values() # Reset sliders if no paint entries
            else:
                paint = self.data['paints'][0] # Assuming we are always working with the first paint for now
                if 'baseColor' in paint and isinstance(paint['baseColor'], list) and len(paint['baseColor']) >= 3:
                    rgb_normalized = paint['baseColor'][:3]
                    rgb_255 = [int(c * 255) for c in rgb_normalized]
                    hex_color = '#%02x%02x%02x' % tuple(rgb_255)
                    self.update_color_swatch(hex_color) # Update color swatch
                else:
                    self.update_color_swatch("#FFFFFF") # Default white swatch for invalid color


                # Initialize sliders with values from JSON or defaults if missing
                self.clearcoat_slider.set(paint.get('clearcoat', paint.get('clearcoat', 1.0))) # Default to 1.0 as float
                self.clearcoatRoughness_slider.set(paint.get('clearcoatRoughness', paint.get('clearcoatRoughness', 0.03)))
                self.metallic_slider.set(paint.get('metallic', paint.get('metallic', 1.0))) # Default to 1.0 as float
                self.roughness_slider.set(paint.get('roughness', paint.get('roughness', 0.65)))


            # self.color_display_label.config(text=color_text if color_text else "No base colors found in loaded file.") # No longer needed - text display removed
        else:
            self.update_color_swatch("#FFFFFF") # Default white swatch if no data loaded
            # self.color_display_label.config(text="No base colors to display. Load a file first.") # No longer needed - text display removed
            self.reset_slider_values() # Reset sliders if no data loaded
        if not hasattr(self, 'data') or self.data is None:
            self.color_swatch_canvas.config(state=tk.DISABLED) # Disable swatch if no file loaded
        else:
            self.color_swatch_canvas.config(state=tk.NORMAL) # Enable swatch if file loaded


    def update_color_swatch(self, color_hex):
        """Updates the color displayed in the swatch canvas."""
        self.color_swatch_canvas.config(bg=color_hex)


    def update_clearcoat(self, value):
        """Updates clearcoat value in data."""
        if not self.data or 'paints' not in self.data: # Check for data and paints section
            self.data = {'paints': [{}]} # Create data and paints if missing
        if not self.data['paints']: # Ensure paints list is not empty
             self.data['paints'].append({}) # Add an empty paint entry if list is empty

        if 'baseColor' not in self.data['paints'][0]: # Ensure baseColor exists
            self.data['paints'][0]['baseColor'] = [1.0, 1.0, 1.0, 1.0] # Default white RGBA if missing

        self.data['paints'][0]['clearcoat'] = float(value) # Now safe to access paints[0]

        if self.filepath: # Autosave after slider change
            self.save_file()

    def update_clearcoatRoughness(self, value):
        """Updates clearcoatRoughness value in data."""
        if not self.data or 'paints' not in self.data: # Check for data and paints section
            self.data = {'paints': [{}]} # Create data and paints if missing
        if not self.data['paints']: # Ensure paints list is not empty
             self.data['paints'].append({}) # Add an empty paint entry if list is empty

        if 'baseColor' not in self.data['paints'][0]: # Ensure baseColor exists
            self.data['paints'][0]['baseColor'] = [1.0, 1.0, 1.0, 1.0] # Default white RGBA if missing

        self.data['paints'][0]['clearcoatRoughness'] = float(value)
        if self.filepath: # Autosave after slider change
            self.save_file()

    def update_metallic(self, value):
        """Updates metallic value in data."""
        if not self.data or 'paints' not in self.data: # Check for data and paints section
            self.data = {'paints': [{}]} # Create data and paints if missing
        if not self.data['paints']: # Ensure paints list is not empty
             self.data['paints'].append({}) # Add an empty paint entry if list is empty

        if 'baseColor' not in self.data['paints'][0]: # Ensure baseColor exists
            self.data['paints'][0]['baseColor'] = [1.0, 1.0, 1.0, 1.0] # Default white RGBA if missing

        self.data['paints'][0]['metallic'] = float(value) # Now save as float
        if self.filepath: # Autosave after slider change
            self.save_file()

    def update_roughness(self, value):
        """Updates roughness value in data."""
        if not self.data or 'paints' not in self.data: # Check for data and paints section
            self.data = {'paints': [{}]} # Create data and paints if missing
        if not self.data['paints']: # Ensure paints list is not empty
             self.data['paints'].append({}) # Add an empty paint entry if list is empty

        if 'baseColor' not in self.data['paints'][0]: # Ensure baseColor exists
            self.data['paints'][0]['baseColor'] = [1.0, 1.0, 1.0, 1.0] # Default white RGBA if missing

        self.data['paints'][0]['roughness'] = float(value)
        if self.filepath: # Autosave after slider change
            self.save_file()

    def enable_controls(self):
        """Enables sliders and save button."""
        self.clearcoat_slider.config(state=tk.NORMAL)
        self.clearcoatRoughness_slider.config(state=tk.NORMAL)
        self.metallic_slider.config(state=tk.NORMAL)
        self.roughness_slider.config(state=tk.NORMAL)
        self.save_button.config(state=tk.NORMAL)
        self.color_swatch_canvas.config(state=tk.NORMAL) # Enable color swatch

    def disable_controls(self):
        """Disables sliders and save button."""
        self.clearcoat_slider.config(state=tk.DISABLED)
        self.clearcoatRoughness_slider.config(state=tk.DISABLED)
        self.metallic_slider.config(state=tk.DISABLED)
        self.roughness_slider.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.color_swatch_canvas.config(state=tk.DISABLED) # Disable color swatch

    def reset_slider_values(self):
        """Resets sliders to default values."""
        self.clearcoat_slider.set(0.5)
        self.clearcoatRoughness_slider.set(0.5)
        self.metallic_slider.set(0.5)
        self.roughness_slider.set(0.5)

    def close_window(self):
        """Custom function to close the window, similar to the close button."""
        global current_color_picker_app
        current_color_picker_app = None # Clear the global reference when closing
        self.destroy() # This destroys the Toplevel window


if __name__ == "__main__":
    root = tk.Tk() # Create a main window for standalone testing
    root.withdraw() # Hide the main window as we only need the color picker

    def example_callback(): # Example callback function
        print("Callback function from ColorPickerApp was called!")

    app = create_color_picker_window(on_replace_or_spawn_callback=example_callback) # Create and open, passing callback
    root.after(3000, lambda: create_color_picker_window(on_replace_or_spawn_callback=example_callback)) # Example: Re-open after 3 seconds, passing callback
    root.mainloop()
