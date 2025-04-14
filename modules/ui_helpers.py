import os
import tkinter as tk
from tkinter import messagebox

import win32gui
import win32con
import win32api

import win32process
import pywintypes
import psutil
import time

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



 

#ATTEMPT 2
#'''   
def focus_config_viewer_from_floating_button(app): # 'app' is 'self' if called from within the class
    """
    Finds the application's main window based on its title and process name
    (python.exe or pythonw.exe) and brings it to the foreground.

    Args:
        app: The application instance (presumably 'self').

    Returns:
        True if the window was found and focus was attempted, False otherwise.
    """
    app.skip_perform_search = True
    print("skip_perform_search set to TRUE, perform search should NOT GET EXECUTED")


    print(f"DEBUG: Focus request successful. Activating KeyRelease ignore period for {app.ignore_keyrelease_after_focus_msec}ms.")

    if app._ignore_keyrelease_timer_id:
        app.master.after_cancel(app._ignore_keyrelease_timer_id)
        print("DEBUG: Cancelled previous ignore timer.")
        # Ensure entry is re-enabled if a previous timer was cancelled prematurely
        try:
            if app.search_entry.cget('state') == tk.DISABLED:
                    print("DEBUG: Re-enabling search entry due to timer cancellation.")
                    app.search_entry.config(state=tk.NORMAL)
        except AttributeError:
                print("WARN: search_entry might not exist yet during early timer cancel.")


    # --- Disable the search entry ---
    try:
        print("DEBUG: Disabling search entry.")
        app.search_entry.config(state=tk.DISABLED)
    except AttributeError:
        print("ERROR: app.search_entry does not exist when trying to disable.")
        # Handle error appropriately, maybe return or log more severely

    # Start the timer to clear the flag AND re-enable the entry
    app._ignore_keyrelease_timer_id = app.master.after(
        app.ignore_keyrelease_after_focus_msec,
        app._clear_ignore_state # Rename callback for clarity
    )




    config_viewer_handle = None # Renamed for clarity
    window_title = app.main_window_title # Get the exact title from the app instance
    process_name_check_w = 'pythonw.exe'
    process_name_check_regular = 'python.exe'
    target_process_names = {process_name_check_w, process_name_check_regular} # Use a set for efficient lookup
    
    try:
        app.master.attributes("-topmost", True)
        
        
        def window_enum_handler(hwnd, _): # Second argument (wildcard) is not used
            nonlocal config_viewer_handle

            # 1. Check Visibility
            if not win32gui.IsWindowVisible(hwnd):
                return True # Skip invisible windows

            # 2. Get Process ID using pywin32
            try:
                # GetWindowThreadProcessId returns tuple: (threadId, processId)
                _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                if process_id == 0: # Check for invalid process ID
                     return True # Skip if PID is invalid
            except pywintypes.error as e:
                # Handle potential errors getting PID (e.g., invalid handle)
                # print(f"Debug: Error getting PID for HWND {hwnd}: {e}") # Optional debug print
                return True # Skip this window
            except Exception as e_pid:
                # print(f"Debug: Unexpected error getting PID for HWND {hwnd}: {e_pid}") # Optional debug print
                return True # Skip this window

            # 3. Get Process Name using psutil
            process_name = None
            try:
                current_process = psutil.Process(process_id)
                process_name = current_process.name()
            except psutil.NoSuchProcess:
                # Process might have terminated between getting PID and getting name
                return True # Skip this window
            except (psutil.AccessDenied, OSError) as e_psutil:
                # Handle errors accessing process info (permissions etc.)
                # print(f"Debug: Error getting process info for PID {process_id}: {e_psutil}") # Optional debug print
                return True # Skip this window
            except Exception as e_process_get:
                # Catch any other unexpected psutil error
                # print(f"Debug: Unexpected error getting process name for PID {process_id}: {e_process_get}") # Optional debug print
                return True # Skip this window

            # 4. Check Process Name
            # Ensure the process name is one of the expected python executables
            if process_name not in target_process_names:
                # print(f"Debug: Skipping HWND {hwnd}, process '{process_name}' != expected") # Optional
                return True # Not the right process type, continue enumeration

            # 5. Check Window Title (Exact Match) - Only if process name matched
            try:
                current_window_title = win32gui.GetWindowText(hwnd)
            except pywintypes.error as e:
                 # Handle potential errors getting title (rare for visible windows)
                 # print(f"Debug: Error getting title for HWND {hwnd}: {e}") # Optional
                 return True # Skip this window

            # Perform an exact match against the title stored in the app instance
            if current_window_title == window_title:
                # Found the matching window!
                config_viewer_handle = hwnd
                # print(f"Debug: Found matching window! HWND: {hwnd}, Title: '{current_window_title}', Process: '{process_name}'") # Optional
                return False # Stop enumeration

            # print(f"Debug: Skipping HWND {hwnd}, title '{current_window_title}' != '{window_title}'") # Optional
            return True # Continue enumeration if title doesn't match

        # --- EnumWindows Call with Retry Logic ---
        attempts = 3  # Increased attempts slightly for robustness
        for attempt in range(attempts):
            try:
                win32gui.EnumWindows(window_enum_handler, None)
                # If EnumWindows completes without error OR the handler returned False, break
                if config_viewer_handle is not None: # Check if found within the handler
                     break
                # If EnumWindows finished but didn't find it, still break (no need to retry)
                if attempt == attempts -1 and config_viewer_handle is None:
                     print(f"Warning: EnumWindows completed but did not find window '{window_title}' from process '{process_name_check_regular}' or '{process_name_check_w}'.")
                break # Exit loop if EnumWindows ran successfully (found or not found)
            except pywintypes.error as e:
                # Specific error code 1400 (Invalid window handle) can sometimes occur during enumeration
                # Error code 2 (File not Found - sometimes related to system state)
                # Error code 8 (Not enough storage - rare)
                # We retry primarily for transient issues like error code 2
                if e.winerror in [2] and attempt < attempts - 1:
                    print(f"Warning: EnumWindows failed on attempt {attempt + 1} with error {e.winerror}: {e}. Retrying in 0.1s...")
                    time.sleep(0.1)
                else:
                    print(f"Error: EnumWindows failed definitively after {attempt + 1} attempts with error {e.winerror}: {e}. Cannot find window.")
                    config_viewer_handle = None # Ensure handle is None if EnumWindows failed badly
                    break # Stop trying
            except Exception as e_enum:
                 print(f"Error: An unexpected error occurred during EnumWindows: {e_enum}")
                 config_viewer_handle = None
                 break # Stop trying


        # --- Window Focusing Logic (Bottom Part) ---
        if config_viewer_handle:
            try:
                is_minimized = win32gui.IsIconic(config_viewer_handle)

                if is_minimized:
                    print(f"Window '{window_title}' is minimized. Restoring...")
                    # SW_RESTORE activates and displays the window. If minimized/maximized,
                    # it restores to original size/position.
                    win32gui.ShowWindow(config_viewer_handle, win32con.SW_RESTORE)
                    time.sleep(0.05) # Short pause after restore, sometimes helps SetForegroundWindow

                # Attempt to bring the window to the foreground.
                # This is needed even if restored, to ensure it gets focus over other windows.
                try:
                    win32gui.SetForegroundWindow(config_viewer_handle)
                    print(f"Successfully focused window: '{window_title}' (HWND: {config_viewer_handle})")
                except pywintypes.error as e_fg:
                    # SetForegroundWindow can fail (often error 0 or 5) if another app
                    # is preventing it or if the calling process doesn't have foreground rights.
                    print(f"Warning: Could not set foreground window (Error: {e_fg.winerror} - {e_fg}). Attempting SW_SHOW.")
                    # Fallback: Ensure the window is at least shown and activated,
                    # even if not guaranteed to be the top foreground window.
                    # SW_SHOW activates the window and displays it in its current size/position.
                    if not is_minimized: # Only use SW_SHOW if it wasn't originally minimized (SW_RESTORE already handled that)
                        try:
                             win32gui.ShowWindow(config_viewer_handle, win32con.SW_SHOW)
                        except pywintypes.error as e_show:
                             print(f"Error: Fallback ShowWindow failed: {e_show}")


                # This line's purpose depends on your application's logic.
                # It might close the floating button's own window, etc.
                # Keep it if it's required for your workflow after focusing the main window.
                print("Debug: Calling app.on_details_window_close() after focusing main window...") # Optional Debug Print
                app.on_details_window_close() # Call your function regardless of focus success if window handle was found

                return True # Indicate that the window was found and focus was attempted

            except pywintypes.error as e_main_op:
                print(f"Error operating on found window handle {config_viewer_handle}: {e_main_op}")
                return False # Indicate failure operating on the handle
            except Exception as e_general:
                 print(f"Error during window focusing logic: {e_general}")
                 return False

        else:
            # This executes if EnumWindows completed but config_viewer_handle is still None
            # or if EnumWindows failed critically.
            print(f"Window '{window_title}' associated with '{process_name_check_regular}' or '{process_name_check_w}' not found.")
            return False
        


    finally:
        # Keep topmost for longer
        app.master.after(500, lambda: reset_topmost(app))
        print("Scheduling -topmost attribute reset (longer delay)...")






def reset_topmost(app): # 'app' is 'self' if called from within the class
    """Helper function to reset the topmost attribute."""
    try:
        if app.master.winfo_exists(): # Check if window still exists
             app.master.attributes("-topmost", False)
             print("-topmost attribute reset.")
             # We don't touch the focus flags here. They are managed by events
             # and the update_main_focus_flag function.
             app.focus_config_viewer_from_floating_button_layer_2()

    except tk.TclError as e:
         print(f"Error resetting topmost (window likely destroyed): {e}")
    except Exception as e:
        print(f"Unexpected error resetting topmost: {e}")




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

    
    
    
