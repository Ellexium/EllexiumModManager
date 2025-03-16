import os
import tkinter as tk
from tkinter import messagebox

def on_floating_window_unmapped(app, event=None):
        """Called when the floating window becomes invisible (including minimize)."""
        print("Floating window Unmapped (Hidden/Minimized)") # Debug print
        if hasattr(app, 'show_switcher_button'):
            app.show_switcher_button.config(text="Show Switcher") # Update button text to "Show"
            

        
def destroy_floating_button_window(app):
    """Destroys the floating button window if it exists."""
    if hasattr(app, 'floating_window') and app.floating_window and app.floating_window.winfo_exists():
        app.floating_window.destroy()
        app.floating_window = None
        print("Floating Button Window destroyed.")
        # Optionally, update the "Show Switcher" button text to indicate it's now a "Show" button
        # Find the "Show Switcher" button (you might need to store a reference to it when creating it in setup_gui)
        # if hasattr(app, 'show_switcher_button'): # Example - you'd need to store the button as app.show_switcher_button
        #     app.show_switcher_button.config(text="Show Switcher") # Change text back to "Show Switcher"

def hide_floating_window(app):
    """Hides the floating button window instead of destroying it and resets 'Show Switcher' button text."""
    if hasattr(app, 'floating_window') and app.floating_window and app.floating_window.winfo_exists():
        app.floating_window.withdraw() # Hide the window
        print("Floating Button Window hidden.")
        # --- NEW: Update "Show Switcher" button text back to "Show Switcher" ---
        if hasattr(app, 'show_switcher_button'):
            app.show_switcher_button.config(text="Show Switcher") # Change text back to "Show Switcher"
        # --- NEW: Update "Show Switcher" button text back to "Show Switcher" ---

def show_floating_window(app):
    """Shows the floating button window if it exists."""
    if hasattr(app, 'floating_window') and app.floating_window:
        app.floating_window.deiconify() # Show the window
        print("Floating Button Window shown.")
        # Optionally, update the "Show Switcher" button text to indicate it's now a "Hide" button
        # if hasattr(app, 'show_switcher_button'): # Example - you'd need to store the button as app.show_switcher_button
        #     app.show_switcher_button.config(text="Hide Switcher") # Change text to "Hide Switcher"

def focus_config_viewer_from_floating_button(app):
    """Focuses the Config Viewer window when button in floating window is clicked."""
    app.master.deiconify()
    app.master.focus_force()
    app.on_details_window_close()
    print("Focus switched to Config Viewer (from floating button)")

def remember_floating_window_position(app, event):
        """Remembers the floating window's last position."""
        if hasattr(app, 'floating_window') and app.floating_window and app.floating_window.winfo_exists():
            x = app.floating_window.winfo_x()
            y = app.floating_window.winfo_y()
            app.floating_window_last_position = (x, y)
            # print(f"Floating window position remembered: {app.floating_window_last_position}") # Optional debug print            





def on_floating_window_mapped(app, event=None):
        """Called when the floating window becomes visible (including de-minimize)."""
        print("Floating window Mapped (Visible/De-Minimized)") # Debug print
        if hasattr(app, 'show_switcher_button'):
            app.show_switcher_button.config(text="Hide Switcher") # Update button text to "Hide"

def on_floating_window_unmapped(app, event=None):
        """Called when the floating window becomes invisible (including minimize)."""
        print("Floating window Unmapped (Hidden/Minimized)") # Debug print
        if hasattr(app, 'show_switcher_button'):
            app.show_switcher_button.config(text="Show Switcher") # Update button text to "Show"
            
def toggle_floating_window_visibility(app):
    """Toggles the visibility of the floating button window and updates 'Show Switcher' button text."""
    if not hasattr(app, 'floating_window') or not app.floating_window:
        create_floating_button_window(app) # Create if it doesn't exist
        if hasattr(app, 'show_switcher_button'):
            app.show_switcher_button.config(text="Hide Switcher") # Update button text to "Hide" when SHOWN
    elif app.floating_window.winfo_ismapped(): # Check if it's currently visible
        hide_floating_window(app) # Hide if visible
        if hasattr(app, 'show_switcher_button'):
            app.show_switcher_button.config(text="Show Switcher") # Update button text to "Show" when HIDDEN
    else:
        show_floating_window(app) # Show if hidden
        if hasattr(app, 'show_switcher_button'):
            app.show_switcher_button.config(text="Hide Switcher") # Update button text to "Hide" when SHOWN
            


       
       
       
       
       
#------------------------------
#---------testing area---------
#------------------------------

def load_floating_window_position(app):
    """Loads the floating window position and other settings from settings file."""
    print("\n--- load_floating_window_position() DEBUG ENTRY ---") # Debug entry
    default_show_switcher_on_startup = False # Default value if not found in file
    app.show_switcher_on_startup = default_show_switcher_on_startup # Initialize with default
    print(f"DEBUG: Initial app.show_switcher_on_startup: {app.show_switcher_on_startup}") # Debug initial value

    try:
        if os.path.exists(app.settings_file_path):
            print(f"DEBUG: Settings file exists: {app.settings_file_path}") # Debug - file exists
            with open(app.settings_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SwitcherPosition:"):
                        try:
                            pos_str = line[len("SwitcherPosition:"):].strip()
                            x_str, y_str = pos_str.strip("()").split(",")
                            x = int(x_str.strip())
                            y = int(y_str.strip())
                            app.floating_window_last_position = (x, y)
                            print(f"Loaded floating window position from file: {app.floating_window_last_position}") # Debug
                        except ValueError:
                            print("Warning: Invalid SwitcherPosition format in settings file.")
                            break # Stop processing after invalid line
                    elif line.startswith("ShowSwitcherOnStartup:"): # NEW: Load Show Switcher On Startup setting
                        value_str = line[len("ShowSwitcherOnStartup:"):].strip().lower()
                        print(f"DEBUG: ShowSwitcherOnStartup line found, value_str: '{value_str}'") # Debug - value_str
                        if value_str == "on":
                            app.show_switcher_on_startup = True
                        elif value_str == "off":
                            app.show_switcher_on_startup = False
                        else:
                            print(f"Warning: Invalid ShowSwitcherOnStartup value: '{value_str}'. Using default.")
                    else:
                        pass # Handle other settings if needed
        else:
            print(f"DEBUG: Settings file DOES NOT exist: {app.settings_file_path}") # Debug - file does not exist

    except Exception as e:
        print(f"Error loading floating window position and settings: {e}")

    print(f"DEBUG: Final app.show_switcher_on_startup value: {app.show_switcher_on_startup}") # Debug - final value

    if app.show_switcher_on_startup: # NEW: Show switcher on startup if setting is on
        print("DEBUG: Show Switcher On Startup setting is ON. About to create and show switcher window.") # Debug - before create/show
        app.create_floating_button_window()
        app.show_floating_window()
        print("DEBUG: create_floating_button_window() and show_floating_window() called.") # Debug - after create/show
    else:
        print("DEBUG: Show Switcher On Startup setting is OFF. Not showing switcher window on startup.") # Debug - not showing
    print("--- load_floating_window_position() DEBUG EXIT ---\n") # Debug exit
        
        
        
def save_floating_window_position(app):
    """Saves the floating window position and other settings to settings file."""
    if app.floating_window_last_position:
        try:
            with open(app.settings_file_path, "w") as f:
                f.write(f"SwitcherPosition: {app.floating_window_last_position}\n")
                f.write(f"ShowSwitcherOnStartup: {'on' if app.show_switcher_on_startup else 'off'}\n") # NEW: Save Show Switcher On Startup setting
                print(f"Saved floating window position: {app.floating_window_last_position} to file.") # Debug
                print(f"Saved ShowSwitcherOnStartup setting: {app.show_switcher_on_startup} to file.") # Debug - NEW
        except Exception as e:
            print(f"Error saving floating window position and settings: {e}")
            
            
            
#------------------------------
#---------testing area---------
#------------------------------



def create_floating_button_window(app):
    """Creates the always-on-top floating button window with custom styling and draggable area."""
    if hasattr(app, 'floating_window') and app.floating_window and app.floating_window.winfo_exists():
        app.floating_window.focus_set()
        return

    app.floating_window = tk.Toplevel(app.master, bg="#333333") # Set background color to dark grey
    app.floating_window.title("Focus Switcher")
    app.floating_window.overrideredirect(True) # Remove window decorations
    app.floating_window.attributes("-topmost", True)
    app.floating_window.attributes('-alpha', 0.8 * 0.75) # 25% more transparent
    app.floating_window.bind("<ButtonPress-2>", app.send_j)
    app.floating_window.bind("<ButtonPress-3>", app.send_escape)


#Left Click	"<Button-1>"
#Right Click	"<Button-3>"
#Middle Click	"<Button-2>"
#Double Left Click	"<Double-Button-1>"
#Double Right Click	"<Double-Button-3>"
#Double Middle Click	"<Double-Button-2>"


    window_width = 200
    window_height = 30
    padding_size = 13 # Custom padding size

    # --- NEW: Draggable Padding Frame ---
    draggable_frame = tk.Frame(app.floating_window, bg="#333333", width=window_width + 2 * padding_size, height=window_height + 2 * padding_size) # Dark grey background, fleur cursor for drag
    draggable_frame.pack(fill="both", expand=True)

    # --- Draggable Functionality ---
    def start_drag(event):
        app.floating_window.drag_start_x = event.x_root - app.floating_window.winfo_rootx()
        app.floating_window.drag_start_y = event.y_root - app.floating_window.winfo_rooty()

    def on_drag(event):
        x = event.x_root - app.floating_window.drag_start_x
        y = event.y_root - app.floating_window.drag_start_y
        app.floating_window.geometry(f"+{x}+{y}")

    draggable_frame.bind("<ButtonPress-1>", start_drag)
    draggable_frame.bind("<B1-Motion>", on_drag)


    # --- Draggable Functionality ---




    # --- NEW: Use loaded position if available, otherwise center ---
    if app.floating_window_last_position:
        x, y = app.floating_window_last_position
        print(f"Using loaded floating window position: {(x,y)}") # Debug
    else:
        screen_width = app.master.winfo_screenwidth()
        screen_height = app.master.winfo_screenheight()
        x = (screen_width / 2) - ((window_width + 2 * padding_size) / 2) # Center with padding
        y = (screen_height / 2) - ((window_height + 2 * padding_size) / 2) # Center with padding
        print("Centering floating window as no saved position found.") # Debug

    app.floating_window.geometry(f"{window_width + 2 * padding_size}x{window_height + 2 * padding_size}+{int(x)}+{int(y)}") # Geometry with padding
    # --- NEW: Use loaded position if available, otherwise center ---

    app.floating_window.bind("<Map>", lambda event: on_floating_window_mapped(app, event))
    app.floating_window.bind("<Unmap>", lambda event: on_floating_window_unmapped(app, event))

    app.floating_window.pack_propagate(False)

    # Frame to hold the two buttons - for centered layout - Place inside draggable_frame
    button_frame = tk.Frame(draggable_frame, bg="#333333", width=window_width) # Dark grey background for buttons, fixed width
    button_frame.pack(pady=(padding_size, padding_size), padx=padding_size, fill="both", expand=True) # Padding around buttons
    button_frame.pack_propagate(False)

    # Button Style Arguments
    button_style_args = {
        "bg": "#555555", # Dark grey background
        "fg": "white",
        "font": ("Segoe UI", 10, "bold"), # White bold text
        "relief": tk.FLAT, # Flat buttons, no border
        "bd": 0,
        "highlightthickness": 0,
        "activebackground": "orange", # Orange hover
        "activeforeground": "white",
        "padx": 10,
        "pady": 2
    }

    # "BeamNG" Button
    beamng_button = tk.Button(
        button_frame,
        text="BeamNG",
        command=lambda: app.focus_beamng_window(),
        **button_style_args
    )
    beamng_button.pack(side="left", fill="x", expand=True, padx=(0, 2))
    beamng_button.bind("<Enter>", lambda event: beamng_button.config(bg="orange")) # Hover orange
    beamng_button.bind("<Leave>", lambda event: beamng_button.config(bg="#555555"))# Hover leave dark grey

    # "Selector" Button (Config Viewer)
    cv_button = tk.Button(
        button_frame,
        text="Selector",
        command=lambda: app.focus_config_viewer_from_floating_button(),
        **button_style_args
    )
    cv_button.pack(side="left", fill="x", expand=True, padx=(2, 0))
    cv_button.bind("<Enter>", lambda event: cv_button.config(bg="orange")) # Hover orange
    cv_button.bind("<Leave>", lambda event: cv_button.config(bg="#555555")) # Hover leave dark grey


    # Make sure floating window is not resizable
    app.floating_window.resizable(False, False)

    # Store initial position
    app.floating_window_last_position = (int(x), int(y))
    app.floating_window.bind("<Configure>", lambda event: remember_floating_window_position(app, event))

    app.floating_window.protocol("WM_DELETE_WINDOW", lambda: hide_floating_window(app))

    print("Floating Button Window created (Custom Style, Draggable Padding, Centered Buttons).")

    
    
    