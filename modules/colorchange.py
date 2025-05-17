import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
import json
import os
import random # Import the random module
from pathlib import Path
import re # Import the regular expression module
import time





class CustomSlider(tk.Frame):
    def __init__(self, master=None, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=None, font_size_add=0, **kwargs):
        super().__init__(master, **kwargs)
        self.from_value = from_
        self.to_value = to
        self.resolution = resolution
        self.orient = orient
        self.command = command
        self._value = tk.DoubleVar(self, value=from_)
        self._enabled = tk.BooleanVar(self, value=True) # Track enabled state

        self.font_size_add = font_size_add

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

        self.percentage_label = tk.Label(self, text="0%", width=4, font=("Segoe UI", 12+self.font_size_add, "bold"), fg="lightgrey", bg="#333333") # Styled label

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
            try:
                # Use try-except for safety if tk not fully initialized
                self.tk.call('tk', 'scaling', 1.25)
            except tk.TclError as e:
                print(f"Could not set Tk scaling: {e}")

        self.title("Pick Color") # Changed title
        self.configure(bg="#333333") # Set background for the main window

        self.font_size_add = self._load_font_size_setting()

        # --- Animation Parameters (INITIALIZED HERE) ---
        self.widget_original_colors = {} # Stores original colors for widgets
        self.animation_states = {}      # Tracks ongoing animations
        self.global_highlight_color = "orange" # Default hover color for backgrounds/highlights
        self.transition_duration_sec = 0.15   # Animation speed

        # Main frame to contain everything and handle centering
        self.main_frame = tk.Frame(self, bg="#333333")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=0) # Padding around main frame
        self.main_frame.columnconfigure(0, weight=1) # Allow column 0 (labels) to expand
        self.main_frame.columnconfigure(1, weight=1) # Allow column 1 (sliders) to expand

        # Title Label
        self.app_title_label = tk.Label(self.main_frame, text="Color Configuration", font=("Segoe UI", 13+self.font_size_add, "bold"), fg="white", bg="#333333")
        self.app_title_label.grid(row=0, column=0, columnspan=2, pady=10)


        # Font for all widgets
        font = ("Segoe UI", 12+self.font_size_add)

        # Button default and hover colors (Used for initial setup and binding)
        button_default_bg = "#555555"
        button_default_fg = "white"
        # hover_bg will default to self.global_highlight_color ("orange")
        button_hover_fg = "white" # Can be customized if needed

        # --- Create Buttons (with active colors for click feedback) ---
        self.randomize_button = tk.Button(self.main_frame, text="Randomize", command=self.randomize_settings, font=font, bg=button_default_bg, fg=button_default_fg, relief=tk.FLAT, highlightthickness=0, activebackground="white", activeforeground="black")
        self.randomize_button.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

        self.replace_current_button = tk.Button(self.main_frame, text="Replace Current", command=self.replace_current_vehicle_lua, font=font, bg=button_default_bg, fg=button_default_fg, relief=tk.FLAT, highlightthickness=0, activebackground="white", activeforeground="black")
        self.replace_current_button.grid(row=5, column=0, columnspan=2, pady=5, sticky="ew")

        self.spawn_new_button = tk.Button(self.main_frame, text="Spawn New", command=self.spawn_new_vehicle_lua, font=font, bg=button_default_bg, fg=button_default_fg, relief=tk.FLAT, highlightthickness=0, activebackground="white", activeforeground="black")
        self.spawn_new_button.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")

        # New: Close Button
        self.close_button = tk.Button(self.main_frame, text="Close", command=self.close_window, font=font, bg=button_default_bg, fg=button_default_fg, relief=tk.FLAT, highlightthickness=0, activebackground="white", activeforeground="black")
        # If you want to show the close button, uncomment the grid line below
        # self.close_button.grid(row=7, column=0, columnspan=2, pady=10, sticky="ew")



        # --- ADD NEW ANIMATED BINDINGS (AFTER BUTTON CREATION) ---
        self._bind_animated_hover(self.randomize_button, button_default_bg, button_default_fg, hover_fg=button_hover_fg, check_state=False) # Button state doesn't change currently
        self._bind_animated_hover(self.replace_current_button, button_default_bg, button_default_fg, hover_fg=button_hover_fg, check_state=False)
        self._bind_animated_hover(self.spawn_new_button, button_default_bg, button_default_fg, hover_fg=button_hover_fg, check_state=False)
        self._bind_animated_hover(self.close_button, button_default_bg, button_default_fg, hover_fg=button_hover_fg, check_state=False) # If using close button

        # Sliders Frame
        self.sliders_frame = tk.Frame(self.main_frame, bg="#333333")
        self.sliders_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10)
        self.sliders_frame.columnconfigure(0, weight=1) # Labels column
        self.sliders_frame.columnconfigure(1, weight=1) # Sliders column

        # Labels Frame
        self.labels_column_frame = tk.Frame(self.sliders_frame, bg="#333333")
        self.labels_column_frame.grid(row=0, column=0, sticky="new")

        # Sliders Frame
        self.sliders_column_frame = tk.Frame(self.sliders_frame, bg="#333333")
        self.sliders_column_frame.grid(row=0, column=1, sticky="new")

        # Base Color Label
        self.base_color_label = tk.Label(self.labels_column_frame, text="Base Color:", font=font, fg="white", bg="#333333")
        self.base_color_label.grid(row=0, column=0, sticky="ne", padx=5, pady=7)

        # --- Color Swatch ---
        self.default_swatch_highlightcolor = "#808080" # Store default highlight color
        swatch_hover_highlightcolor = self.global_highlight_color # Use global orange for hover

        self.color_swatch_canvas = tk.Canvas(self.sliders_column_frame, width=190, height=21, bg="white", highlightthickness=2, relief='solid', bd=1, highlightbackground=self.default_swatch_highlightcolor) # Use variable
        self.color_swatch_canvas.grid(row=0, column=1, sticky="nw", padx=5, pady=8)

        # Keep the click binding for the swatch
        self.color_swatch_canvas.bind("<Button-1>", lambda event: self._open_color_picker_from_swatch()) # Opens color picker

        # --- REMOVED OLD SWATCH BINDINGS (<Enter>/<Leave>) ---

        # --- ADD NEW ANIMATED BINDING FOR SWATCH HIGHLIGHT ---
        self._bind_animated_hover(
            widget=self.color_swatch_canvas,
            original_bg=self.default_swatch_highlightcolor, # The color to animate
            original_fg=self.color_swatch_canvas.cget("bg"), # Dummy FG - not used by canvas highlight
            hover_bg=swatch_hover_highlightcolor,         # Target color for animation
            hover_fg=None,                                # Dummy FG
            property_to_animate="highlightbackground",    # <<< Animate this property
            check_state=True                              # Swatch can be disabled
        )

        # --- Sliders for paint properties ---
        self.clearcoat_label = tk.Label(self.labels_column_frame, text="Clearcoat:", font=font, fg="white", bg="#333333")
        self.clearcoat_slider = CustomSlider(self.sliders_column_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=self.update_clearcoat, font_size_add=self.font_size_add, bg="#333333")
        self.clearcoat_label.grid(row=1, column=0, sticky='ne', padx=5, pady=7)
        self.clearcoat_slider.grid(row=1, column=1, sticky='ew', padx=5, pady=7)

        self.clearcoatRoughness_label = tk.Label(self.labels_column_frame, text="Clearcoat Roughness:", font=font, fg="white", bg="#333333")
        self.clearcoatRoughness_slider = CustomSlider(self.sliders_column_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=self.update_clearcoatRoughness, font_size_add=self.font_size_add, bg="#333333")
        self.clearcoatRoughness_label.grid(row=2, column=0, sticky='ne', padx=5, pady=7)
        self.clearcoatRoughness_slider.grid(row=2, column=1, sticky='ew', padx=5, pady=7)

        self.metallic_label = tk.Label(self.labels_column_frame, text="Metallic:", font=font, fg="white", bg="#333333")
        self.metallic_slider = CustomSlider(self.sliders_column_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=self.update_metallic, font_size_add=self.font_size_add, bg="#333333")
        self.metallic_label.grid(row=3, column=0, sticky='ne', padx=5, pady=7)
        self.metallic_slider.grid(row=3, column=1, sticky='ew', padx=5, pady=7)

        self.roughness_label = tk.Label(self.labels_column_frame, text="Roughness:", font=font, fg="white", bg="#333333")
        self.roughness_slider = CustomSlider(self.sliders_column_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=self.update_roughness, font_size_add=self.font_size_add, bg="#333333")
        self.roughness_label.grid(row=4, column=0, sticky='ne', padx=5, pady=7)
        self.roughness_slider.grid(row=4, column=1, sticky='ew', padx=5, pady=7)

        # --- Save Button ---
        save_button_default_bg = "#555555" # Specific color for save button when disabled/enabled
        save_button_default_fg = "white"
        save_button_disabled_fg = "#AAAAAA" # Lighter grey when disabled
        save_button_hover_fg = "white"

        self.save_button = tk.Button(self.main_frame, text="Save File", command=self.save_file, state=tk.DISABLED, font=font, bg=save_button_default_bg, fg=save_button_disabled_fg, relief=tk.FLAT, highlightthickness=0, activebackground=self.global_highlight_color, activeforeground=save_button_hover_fg) # Start with disabled fg
        # self.save_button.grid(...) # Grid if needed

        # --- ADD NEW ANIMATED BINDING FOR SAVE BUTTON ---
        # We use save_button_default_fg as the 'original_fg' for the binder,
        # because the actual fg will be updated by enable/disable_controls.
        # The binder needs a consistent 'normal state' foreground to revert to.
        # The check_state=True ensures hover only works when NORMAL.
        self._bind_animated_hover(
            widget=self.save_button,
            original_bg=save_button_default_bg, # Normal background
            original_fg=save_button_default_fg, # Normal foreground (used by binder logic)
            hover_fg=save_button_hover_fg,    # Hover foreground
            check_state=True                 # IMPORTANT: Save button state changes
        )
        # Note: We will manage the actual foreground color (white/grey) in enable/disable_controls

        self.file_label = tk.Label(self.main_frame, text="File: No file loaded", font=font, fg="white", bg="#333333")
        # self.file_label.grid(...) # Grid if needed

        # --- Instance Variables ---
        self.data = None
        self.filepath = None

        # --- Initial State ---
        self.disable_controls() # Disable controls first
        self.update_color_swatch("#FFFFFF") # Initialize swatch to white (before controls are disabled)

        # --- Icon Loading Code ---
        try:
             # Correct path calculation assuming script is in a subfolder
             script_dir_path = Path(__file__).parent
             self.script_dir = script_dir_path.parent # Go up one level
             icon_path = self.script_dir / "data/icon.png"

             if icon_path.exists():
                icon_image = tk.PhotoImage(file=str(icon_path))
                self.iconphoto(False, icon_image)
             else:
                 print(f"Icon file not found: {icon_path}")
        except NameError:
             # __file__ might not be defined (e.g., in interactive session)
             print("Warning: Could not determine script directory to load icon.")
        except tk.TclError as e: # Catch potential TclError for image loading issues
            print(f"Error loading icon: {e}")
            print(f"Make sure icon file is a valid PNG.")
        except Exception as e: # Catch other potential errors
            print(f"An unexpected error occurred during icon loading: {e}")


        # --- Protocol Handler for Window Close Button ---
        self.protocol("WM_DELETE_WINDOW", self.close_window) # Ensure proper cleanup on X button

        # --- Load File ---
        self.auto_load_file() # Call auto_load_file at the end of initialization


# START OF ANIMATED HOVER CODE


    def _hex_to_rgb(self, hex_color):
        """Converts a hex color string to an RGB tuple (0-255). Handles Tkinter color names too."""
        try:
            # Attempt to get RGB directly using winfo_rgb (handles names like 'white', 'orange')
            # Requires the widget the color is associated with, or the root window
            # Using self (the Toplevel window) should be safe here.
            rgb_short = self.winfo_rgb(hex_color)
            # winfo_rgb returns 16-bit values, scale them down to 8-bit (0-255)
            return tuple(c // 256 for c in rgb_short)
        except tk.TclError:
            # If winfo_rgb fails (e.g., invalid name or hex format), try manual hex parsing
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                try:
                    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                except ValueError:
                    pass # Invalid hex
            # Fallback for errors or invalid formats
            print(f"Warning: Could not convert color '{hex_color}' to RGB. Using black (0, 0, 0).")
            return (0, 0, 0)

    def _rgb_to_hex(self, rgb_color):
        """Converts an RGB tuple (0-255) to a hex color string."""
        try:
            r, g, b = map(int, rgb_color)
            r = max(0, min(255, r)); g = max(0, min(255, g)); b = max(0, min(255, b))
            return f'#{r:02x}{g:02x}{b:02x}'
        except (ValueError, TypeError):
             print(f"Warning: Invalid RGB color for conversion: {rgb_color}. Using #000000.")
             return "#000000"

    def _interpolate_color(self, color1_hex, color2_hex, factor):
        """Linearly interpolates between two hex colors."""
        rgb1 = self._hex_to_rgb(color1_hex)
        rgb2 = self._hex_to_rgb(color2_hex)
        factor = max(0.0, min(1.0, factor))
        interpolated_rgb = [int(rgb1[i] + (rgb2[i] - rgb1[i]) * factor) for i in range(3)]
        return self._rgb_to_hex(tuple(interpolated_rgb))

    def _run_animation_step(self, widget, property_to_animate):
        """Performs one step of the animation for the given widget and property."""
        if widget not in self.animation_states:
            return

        state = self.animation_states[widget]
        anim_id_key = f"{property_to_animate}_anim_id"
        start_color_key = f"{property_to_animate}_start_color"
        target_color_key = f"{property_to_animate}_target_color"
        start_time_key = f"{property_to_animate}_start_time"

        # Clear the stored ID now that this step is running
        state[anim_id_key] = None

        start_color = state.get(start_color_key)
        target_color = state.get(target_color_key)
        start_time = state.get(start_time_key, 0)

        if start_color is None or target_color is None:
             return # No active animation target for this property

        elapsed = time.time() - start_time
        progress = min(1.0, elapsed / self.transition_duration_sec)

        current_color = self._interpolate_color(start_color, target_color, progress)

        try:
            if widget.winfo_exists():
                # Apply the animation step using a dictionary for config
                widget.config(**{property_to_animate: current_color})

                if progress < 1.0:
                    # Schedule the next step
                    delay_ms = 15
                    anim_id = widget.after(delay_ms, lambda w=widget, prop=property_to_animate: self._run_animation_step(w, prop))
                    state[anim_id_key] = anim_id # Store the new ID for this property
                else:
                    # Animation finished
                    widget.config(**{property_to_animate: target_color}) # Ensure final color
                    # Mark this property's animation as inactive
                    state[target_color_key] = None
                    state[start_color_key] = None
                    # Optionally check if *any* animations are running for this widget before deleting state entry

        except tk.TclError:
            # Widget might have been destroyed, clean up state
            if widget in self.animation_states:
                 # Attempt to cancel any pending animations for this widget
                 for key in list(state.keys()):
                     if key.endswith("_anim_id") and state[key]:
                         try: widget.after_cancel(state[key])
                         except tk.TclError: pass
                 del self.animation_states[widget]
            # print(f"Warning: Widget {widget} destroyed during animation.") # Optional debug
        except Exception as e:
             print(f"Error during animation step for {widget}, property {property_to_animate}: {e}")
             if widget in self.animation_states:
                 # Attempt cleanup on error
                 if state.get(anim_id_key):
                     try: widget.after_cancel(state[anim_id_key])
                     except tk.TclError: pass
                 # Consider if removing the whole widget state is appropriate on *any* error
                 # For now, just cancel the specific animation ID if present
                 state[anim_id_key] = None # Mark as cancelled


    def _start_animation(self, widget, new_target_color, property_to_animate="bg"):
        """Starts or redirects the animation for a specific property of a widget."""
        # Ensure state dictionary exists for this widget
        if widget not in self.animation_states:
            self.animation_states[widget] = {} # General state for the widget
        state = self.animation_states[widget]

        # Define keys specific to the property being animated
        anim_id_key = f"{property_to_animate}_anim_id"
        start_color_key = f"{property_to_animate}_start_color"
        target_color_key = f"{property_to_animate}_target_color"
        start_time_key = f"{property_to_animate}_start_time"

        current_target = state.get(target_color_key)

        # If already animating towards the desired color for this property, do nothing
        if current_target == new_target_color:
            return

        # Cancel any pending animation step *for this specific property*
        anim_id = state.get(anim_id_key)
        if anim_id:
            try:
                widget.after_cancel(anim_id)
            except tk.TclError: pass # Widget might be gone
            state[anim_id_key] = None

        try:
            if not widget.winfo_exists():
                 # Clean up state if widget is already destroyed
                 if widget in self.animation_states: del self.animation_states[widget]
                 return

            # Get the *actual current* color of the property being animated
            # Use try-except for cget as it can fail if property doesn't exist
            try:
                current_color = widget.cget(property_to_animate)
            except tk.TclError:
                print(f"Warning: Could not get property '{property_to_animate}' for widget {widget}. Using target color as start.")
                current_color = new_target_color # Fallback

            # Set new animation parameters in the state dictionary for this property
            state[start_color_key] = current_color
            state[target_color_key] = new_target_color
            state[start_time_key] = time.time()

            # Start the animation loop immediately for this property
            self._run_animation_step(widget, property_to_animate)

        except tk.TclError:
             # print(f"Warning: Widget {widget} likely destroyed just before starting animation for {property_to_animate}.") # Optional debug
             # Clean up if TclError occurs (e.g., widget destroyed between checks)
             if widget in self.animation_states:
                 del self.animation_states[widget] # Remove all state for this widget
        except Exception as e:
             print(f"Error starting animation for {widget}, property {property_to_animate}: {e}")
             # Attempt cleanup on other errors
             if widget in self.animation_states:
                 if state.get(anim_id_key):
                     try: widget.after_cancel(state[anim_id_key])
                     except tk.TclError: pass
                 # Decide if the whole widget state should be removed or just this property's animation keys
                 state[anim_id_key] = None
                 state[target_color_key] = None
                 state[start_color_key] = None


    def _bind_animated_hover(self, widget, original_bg, original_fg,
                             hover_bg=None, hover_fg=None,
                             property_to_animate="bg", check_state=False):
        """
        Binds Enter, Leave, FocusOut, and Destroy events for smooth hover animation
        on a specified color property.

        Args:
            widget: The tkinter widget to bind events to.
            original_bg: The normal color value for the animated property (e.g., "#555555").
            original_fg: The normal foreground color (e.g., "white"). Used for fg config.
            hover_bg: The target color for the animated property on hover.
                      Defaults to self.global_highlight_color if None.
            hover_fg: The foreground color on hover. Defaults to original_fg if None.
            property_to_animate: The widget config option to animate (e.g., "bg", "highlightbackground").
            check_state: If True, handlers will check widget['state'] before changing appearance.
        """
        if hover_fg is None:
            hover_fg = original_fg
        if hover_bg is None:
             # Use the globally defined highlight color if a specific one isn't provided
             hover_bg = self.global_highlight_color

        # --- Store Original Colors ---
        if widget not in self.widget_original_colors:
             self.widget_original_colors[widget] = {}
        # Store original values for *both* the animated property and foreground
        self.widget_original_colors[widget][property_to_animate] = original_bg
        self.widget_original_colors[widget]['fg'] = original_fg # Store original fg separately

        # --- Define Event Handlers ---
        def _on_hover_enter(event, w=widget, target_prop_color=hover_bg, target_fg_color=hover_fg, prop=property_to_animate):
            try:
                if not w.winfo_exists(): return
                if not check_state or w['state'] == tk.NORMAL:
                    # Set foreground immediately (if applicable and different)
                    if 'fg' in w.config() and w.cget('fg') != target_fg_color:
                         w.config(fg=target_fg_color)
                    # Start the animation for the specified property
                    self._start_animation(w, target_prop_color, property_to_animate=prop)
            except tk.TclError: pass

        def _on_hover_leave(event, w=widget, target_prop_color=original_bg, target_fg_color=original_fg, prop=property_to_animate):
            try:
                if not w.winfo_exists(): return

                # Improved check: Ensure mouse is actually outside widget bounds
                x, y = event.x_root, event.y_root
                widget_x, widget_y = w.winfo_rootx(), w.winfo_rooty()
                widget_w, widget_h = w.winfo_width(), w.winfo_height()

                #if not (widget_x <= x < widget_x + widget_w and widget_y <= y < widget_y + widget_h):
                
                if not check_state or w['state'] == tk.NORMAL:
                        # Set foreground immediately (if applicable and different)
                        if 'fg' in w.config() and w.cget('fg') != target_fg_color:
                            w.config(fg=target_fg_color)
                        # Start animation back to original for the specified property
                        self._start_animation(w, target_prop_color, property_to_animate=prop)
            except tk.TclError: pass # Widget info might not be available
            except Exception as e: # Catch potential errors getting geometry if window disappears
                print(f"Error during hover leave check for {w}: {e}")


        def _on_focus_out(event, w=widget, target_prop_color=original_bg, target_fg_color=original_fg, prop=property_to_animate):
             try:
                if not w.winfo_exists(): return

                # Check mouse position relative to widget at the time of focus loss
                root = w.winfo_toplevel()
                mouse_x, mouse_y = root.winfo_pointerxy() # Get mouse coords relative to screen
                widget_x, widget_y = w.winfo_rootx(), w.winfo_rooty()
                widget_w, widget_h = w.winfo_width(), w.winfo_height()

                is_mouse_outside = not (widget_x <= mouse_x < widget_x + widget_w and
                                        widget_y <= mouse_y < widget_y + widget_h)

                # Determine if reset is needed based on state and mouse position
                should_reset = False
                if check_state and w['state'] != tk.NORMAL:
                    should_reset = True # Always reset if disabled (and state checking is on)
                elif not check_state or w['state'] == tk.NORMAL:
                    if is_mouse_outside:
                        should_reset = True # Reset if enabled and mouse is outside

                if should_reset:
                     # Set foreground immediately (if applicable and different)
                     if 'fg' in w.config() and w.cget('fg') != target_fg_color:
                         w.config(fg=target_fg_color)
                     # Start animation back to original for the specified property
                     self._start_animation(w, target_prop_color, property_to_animate=prop)

             except tk.TclError: pass # Widget info might not be available
             except Exception as e:
                 print(f"Error during focus out check for {w}: {e}")


        def _on_destroy(event, w=widget):
            # Cleanup animation state and original color storage
            if w in self.animation_states:
                state = self.animation_states[w]
                # Cancel all potential animations for this widget
                for key in list(state.keys()):
                     if key.endswith("_anim_id") and state[key]:
                         try: w.after_cancel(state[key])
                         except tk.TclError: pass
                del self.animation_states[w]
            if w in self.widget_original_colors:
                del self.widget_original_colors[w]

        # --- Perform Binding ---
        widget.bind("<Enter>", _on_hover_enter, add='+')
        widget.bind("<Leave>", _on_hover_leave, add='+')
        widget.bind("<FocusOut>", _on_focus_out, add='+') # Handle losing focus
        widget.bind("<Destroy>", _on_destroy, add='+') # Handle widget destruction

# END OF ANIMATED HOVER CODE (REVISED)

# END OF ANIMATED HOVER CODE


    def _load_font_size_setting(self):
        """Reads FontSizeAdd from data/MMSelectorSettings.txt."""
        default_size = 0 # Default value if file/setting is missing or invalid
        try:
            # Determine the correct path relative to the script's parent directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir) # Assumes script is in a subdir
            settings_file_path = os.path.join(parent_dir, "data", "MMSelectorSettings.txt")

            if not os.path.exists(settings_file_path):
                print(f"Warning: Settings file not found at {settings_file_path}. Using default font size addon ({default_size}).")
                return default_size

            with open(settings_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("FontSizeAdd:"):
                        try:
                            # Extract the value after the colon
                            value_str = line.split(':', 1)[1].strip()
                            return int(value_str) # Convert to integer and return
                        except (IndexError, ValueError):
                            print(f"Warning: Invalid format for FontSizeAdd in {settings_file_path}. Using default ({default_size}).")
                            return default_size # Return default if value is not integer

            # If loop finishes without finding the key
            print(f"Warning: 'FontSizeAdd:' key not found in {settings_file_path}. Using default font size addon ({default_size}).")
            return default_size

        except Exception as e: # Catch potential file reading errors etc.
            print(f"Error reading settings file {settings_file_path}: {e}. Using default font size addon ({default_size}).")
            return default_size
        


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


                # --- FIX IS HERE: Convert values to float before setting sliders ---
                def get_paint_value_as_float(key, default_value):
                    raw_value = paint.get(key, default_value)
                    try:
                        return float(raw_value)
                    except (ValueError, TypeError):
                        print(f"Warning: Could not convert paint value '{raw_value}' for key '{key}' to float. Using default {default_value}.")
                        return float(default_value) # Ensure default is also float

                self.clearcoat_slider.set(get_paint_value_as_float('clearcoat', 1.0))
                self.clearcoatRoughness_slider.set(get_paint_value_as_float('clearcoatRoughness', 0.03))
                self.metallic_slider.set(get_paint_value_as_float('metallic', 1.0))
                self.roughness_slider.set(get_paint_value_as_float('roughness', 0.65))
                # --- END FIX ---


        else:
            self.update_color_swatch("#FFFFFF") # Default white swatch if no data loaded
            self.reset_slider_values() # Reset sliders if no data loaded

        # Enable/Disable swatch based on data presence (unchanged)
        if not hasattr(self, 'data') or self.data is None:
            self.color_swatch_canvas.config(state=tk.DISABLED)
        else:
            self.color_swatch_canvas.config(state=tk.NORMAL)


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
