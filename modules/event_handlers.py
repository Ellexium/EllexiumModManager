import os
import threading
from pathlib import Path


from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer



# --- Added utility functions from original file, that are needed in this file ---
def read_watcher_output(file_path):
    """
    Reads WatcherOutput.txt, now also getting lists of mod zip files and vanilla zip files.
    """
    check_mods, check_configs = False, False
    user_vehicles_files, config_pics_custom_files = {}, {}
    mods_files, repo_files, vanilla_files = {}, {}, {} # NEW: vanilla_files dictionary

    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            settings_section_started, user_vehicles_section_started = False, False
            config_pics_custom_section_started, mods_files_section_started = False, False
            repo_files_section_started, vanilla_files_section_started = False, False # NEW: vanilla_files_section_started


            for line in lines:
                line = line.strip()

                if line.startswith("CheckMods:"):
                    check_mods = (line.split(":", 1)[1].strip().lower() == "true")
                elif line.startswith("CheckConfigs:"):
                    check_configs = (line.split(":", 1)[1].strip().lower() == "true")
                elif line == "[Settings]":
                    settings_section_started = True; user_vehicles_section_started = False; config_pics_custom_section_started = False; mods_files_section_started = False; repo_files_section_started = False; vanilla_files_section_started = False
                elif line == "[UserVehiclesFiles]":
                    user_vehicles_section_started = True; settings_section_started = False; config_pics_custom_section_started = False; mods_files_section_started = False; repo_files_section_started = False; vanilla_files_section_started = False
                elif line == "[ConfigPicsCustomFiles]":
                    config_pics_custom_section_started = True; settings_section_started = False; user_vehicles_section_started = False; mods_files_section_started = False; repo_files_section_started = False; vanilla_files_section_started = False
                elif line == "[ModsFiles]":
                    mods_files_section_started = True; settings_section_started = False; user_vehicles_section_started = False; config_pics_custom_section_started = False; repo_files_section_started = False; vanilla_files_section_started = False
                elif line == "[RepoFiles]":
                    repo_files_section_started = True; settings_section_started = False; user_vehicles_section_started = False; config_pics_custom_section_started = False; mods_files_section_started = False; vanilla_files_section_started = False
                elif line == "[VanillaFiles]": # NEW: VanillaFiles Section Header
                    vanilla_files_section_started = True; settings_section_started = False; user_vehicles_section_started = False; config_pics_custom_section_started = False; mods_files_section_started = False; repo_files_section_started = False
                elif line.startswith("["):
                    settings_section_started = False; user_vehicles_section_started = False; config_pics_custom_section_started = False; mods_files_section_started = False; repo_files_section_started = False; vanilla_files_section_started = False


                if user_vehicles_section_started:
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        filepath, timestamp_str = parts[0].strip(), parts[1].strip()
                        try: user_vehicles_files[filepath] = float(timestamp_str)
                        except ValueError: print(f"Warning: Invalid timestamp format in UserVehiclesFiles line: {line}")
                elif config_pics_custom_section_started:
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        filepath, timestamp_str = parts[0].strip(), parts[1].strip()
                        try: config_pics_custom_files[filepath] = float(timestamp_str)
                        except ValueError: print(f"Warning: Invalid timestamp format in ConfigPicsCustomFiles line: {line}")
                elif mods_files_section_started:
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        filepath, timestamp_str = parts[0].strip(), parts[1].strip()
                        try: mods_files[filepath] = float(timestamp_str)
                        except ValueError: print(f"Warning: Invalid timestamp format in ModsFiles line: {line}")
                elif repo_files_section_started:
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        filepath, timestamp_str = parts[0].strip(), parts[1].strip()
                        try: repo_files[filepath] = float(timestamp_str)
                        except ValueError: print(f"Warning: Invalid timestamp format in RepoFiles line: {line}")
                elif vanilla_files_section_started: # NEW: VanillaFiles Section Parsing
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        filepath, timestamp_str = parts[0].strip(), parts[1].strip()
                        try: vanilla_files[filepath] = float(timestamp_str)
                        except ValueError: print(f"Warning: Invalid timestamp format in VanillaFiles line: {line}")


    except Exception as e:
        print(f"Error reading {file_path}: {e}. Using default settings and empty file lists.")

    return check_mods, check_configs, user_vehicles_files, config_pics_custom_files, mods_files, repo_files, vanilla_files # NEW: return vanilla_files

def scan_folders_for_mod_zips(folders_list):
    """
    Scans a list of folders for .zip files and returns a dictionary of {filepath: modification_timestamp}.
    """
    all_zip_files = {}
    extensions = ['.zip']
    for folder_path in folders_list: # Iterate through list of folders
        if not folder_path or not os.path.isdir(folder_path):
            continue # Skip invalid folders, but continue checking others
        for root, _, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    normalized_filepath = os.path.normpath(filepath).lower().replace('\\', '/') # Normalize path
                    try:
                        all_zip_files[normalized_filepath] = os.path.getmtime(filepath)
                    except OSError: # Handle cases where file might be inaccessible
                        print(f"Warning: Could not get modification time for {filepath}. Skipping.")
    return all_zip_files

def scan_folder_for_watched_files(folder_path):
    """
    Recursively scans a folder, normalizes file paths to lowercase and forward slashes,
    and returns a dictionary of {normalized_filepath: modification_timestamp}.
    """
    file_list = {}
    if not folder_path or not os.path.isdir(folder_path):
        return file_list # Return empty dict for invalid folder

    extensions = ['.pc', '.png', '.jpg', '.jpeg']
    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                filepath = os.path.join(root, file)
                normalized_filepath = os.path.normpath(filepath).lower().replace('\\', '/') # Normalize path
                try:
                    file_list[normalized_filepath] = os.path.getmtime(filepath)
                except OSError: # Handle cases where file might be inaccessible
                    print(f"Warning: Could not get modification time for {filepath}. Skipping.")
    return file_list
# ------------------------------------------------------------
# ModZipEventHandler Class - MODIFIED to update NewMods.txt and use local paths
# ------------------------------------------------------------
class ModZipEventHandler(FileSystemEventHandler):
    def __init__(self, app, debounce_delay=3.0):
        super().__init__()
        self.app = app  # Still keep app reference for calling app methods and settings_file_path
        self.debounce_delay = debounce_delay  # seconds
        self.debounce_timer = None
        self.lock = threading.Lock()

        # --- NEW: Define repo_folder and mods_folder DIRECTLY in ModZipEventHandler ---
        self.script_dir = Path(self.app.script_dir)  # Get script_dir from app instance
        self.repo_folder = self.script_dir.parent / "repo"  # Calculate repo_folder (Path object)
        self.mods_folder = self.script_dir.parent  # Calculate mods_folder (parent of script_dir) (Path object)

    def schedule_mod_scan_refresh(self):
        with self.lock:
            if self.debounce_timer:
                self.debounce_timer.cancel()  # Cancel any ongoing timer
            # Start a new debounce timer
            self.debounce_timer = threading.Timer(self.debounce_delay, self.trigger_mod_scan)
            self.debounce_timer.start()

    def trigger_mod_scan(self):
        print("\n--- ModZipEventHandler.trigger_mod_scan() CALLED ---")  # Debug - Entry Point

        # --- NEW: Identify newly added ZIP files BEFORE running mod scan ---
        newly_detected_zip_files = self.identify_newly_added_zips()
        print(f"DEBUG: ModZipEventHandler - Newly detected ZIP files: {newly_detected_zip_files}")  # Debug

        # Schedule the mod scan and refresh in the main thread
        self.app.master.after(0, self.app.clear_main_grid_cache)  # Clear main grid cache before refresh
        self.app.master.after(0, self.app.trigger_full_data_refresh_and_ui_update)  # Run mod scan scripts (AHK)
        self.app.master.after(0, self.app.refresh_data_from_files)  # Refresh data from files
        self.app.master.after(0, self.app.perform_search)  # Re-apply search/filters

        # --- NEW: Update NewMods.txt with newly detected ZIP files ---
        self.app.master.after(0, lambda: self.app.update_new_mods_txt_with_new_zips(newly_detected_zip_files))  # Call NewMods.txt update

        #self.app.master.after(0, self.show_mods_changed_messagebox)  # NEW: Call "Mods Changed" messagebox display function # not necessary, the main file shows a scanning window with info
        print("--- ModZipEventHandler.trigger_mod_scan() EXIT ---\n")  # Debug - Exit Point

    def identify_newly_added_zips(self):
        """
        Identifies newly added ZIP files by comparing current mod/repo folders with last known lists in WatcherOutput.txt.
        Now using LOCALLY defined repo_folder and mods_folder - no longer relying on self.app attributes.
        """
        # Read last known mod ZIP file lists from WatcherOutput.txt
        _, _, _, _, last_mods_files, last_repo_files, _ = read_watcher_output(self.app.settings_file_path)  # Use app.settings_file_path
        last_known_zip_files = set(last_mods_files.keys()) | set(last_repo_files.keys())

        # Scan for currently existing mod ZIP files - using LOCAL repo_folder and mods_folder
        current_mods_files = scan_folders_for_mod_zips([str(self.mods_folder)])  # Use LOCAL self.mods_folder - converted to string
        current_repo_files = scan_folders_for_mod_zips([str(self.repo_folder)])  # Use LOCAL self.repo_folder - converted to string
        current_zip_files = set(current_mods_files.keys()) | set(current_repo_files.keys())

        newly_detected_zip_files = []
        # Check for newly added ZIP files in mods folder
        for filepath, timestamp in current_mods_files.items(): # Iterate over items (filepath, timestamp)
            normalized_filepath = filepath.lower().replace('\\', '/')
            if normalized_filepath not in last_mods_files:  # If current file NOT in last known list, it's NEW
                newly_detected_zip_files.append(os.path.basename(filepath))  # Add base filename to list

        # Check for newly added ZIP files in repo folder
        for filepath, timestamp in current_repo_files.items(): # Iterate over items (filepath, timestamp)
            normalized_filepath = filepath.lower().replace('\\', '/')
            if normalized_filepath not in last_repo_files:  # If current file NOT in last known list, it's NEW
                newly_detected_zip_files.append(os.path.basename(filepath))  # Add base filename to list

        return newly_detected_zip_files

    def center_window(self, window):
        """Centers a tkinter window on the screen."""
        window.update_idletasks()  # Update window geometry to get correct width/height
        width = window.winfo_width()
        height = window.winfo_height()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f'+{x}+{y}')

    def show_temp_messagebox(self, message, parent, duration_ms=1500):
        """
        Displays a temporary messagebox that disappears after a specified duration.

        Args:
            message (str): The message to display.
            parent (tk.Tk or tk.Toplevel): The parent window.
            duration_ms (int): The duration in milliseconds before the messagebox disappears.
        """
        import tkinter as tk
        temp_window = tk.Toplevel(parent)
        temp_window.overrideredirect(True)  # Remove window decorations (optional, cleaner look for temp messages)

        message_label = tk.Label(temp_window, text=message, padx=20, pady=10) # Add padding for better visual
        message_label.pack()

        self.center_window(temp_window) # Center the temporary window

        temp_window.after(duration_ms, temp_window.destroy) # Schedule destruction after duration

    def show_mods_changed_messagebox(self):
        """
        Displays a temporary messagebox informing the user that mods have been added or removed
        and the main grid has been updated. This messagebox disappears after 1.5 seconds.
        """
        message = "Mod(s) Added or Removed!\nThe main grid has been updated to reflect the changes."
        self.show_temp_messagebox(message, self.app.master) # Use the temporary messagebox function

    def on_created(self, event):
        if not event.is_directory:
            if event.src_path.lower().endswith(".zip"):
                self.schedule_mod_scan_refresh()

    def on_deleted(self, event):
        if not event.is_directory:
            if event.src_path.lower().endswith(".zip"):
                self.schedule_mod_scan_refresh()

    def on_moved(self, event):
        if not event.is_directory:
            if event.dest_path.lower().endswith(".zip"):  # Use dest_path for moved files
                self.schedule_mod_scan_refresh()
        
# ------------------------------------------------------------
# Watchdog Event Handler with Debouncefor custom configs
# ------------------------------------------------------------
class CustomFileEventHandler(FileSystemEventHandler):
    def __init__(self, app, debounce_delay=3.0):
        super().__init__()
        self.app = app
        self.debounce_delay = debounce_delay  # seconds
        self.debounce_timer = None
        self.lock = threading.Lock()

    def schedule_refresh(self):
        with self.lock:
            if self.debounce_timer:
                self.debounce_timer.cancel()  # Cancel any ongoing timer
            # Start a new debounce timer
            self.debounce_timer = threading.Timer(self.debounce_delay, self.trigger_scan)
            self.debounce_timer.start()

    def trigger_scan(self):
        print("\n--- FileSystemEventHandler.trigger_scan() CALLED ---") # Debug - Entry Point
        print("Setting self.app.auto_reopen_details_after_change = True") # Debug - Setting Flag
        # self.app.auto_reopen_details_after_change = True # <----- SET THE FLAG HERE
        
        # Schedule the scan and refresh in the main thread
        #self.app.master.after(0, self.app.clear_main_grid_cache) # Clear cache - for testing
        self.app.master.after(0, self.app.trigger_custom_config_scan_and_refresh)
        # self.app.master.after(0, self.app.refresh_details_window)
        print("--- FileSystemEventHandler.trigger_scan() EXIT ---\n") # Debug - Exit Point
        
    def on_created(self, event):
        if not event.is_directory:
            ext = os.path.splitext(event.src_path)[1].lower()
            if ext in [".png", ".jpg", ".jpeg", ".pc"]:
                self.schedule_refresh()

    def on_deleted(self, event):
        if not event.is_directory:
            ext = os.path.splitext(event.src_path)[1].lower()
            if ext in [".png", ".jpg", ".jpeg", ".pc"]:
                # Remove corresponding custom image from ConfigPicsCustom if it exists
                self.app.remove_corresponding_custom_image(event.src_path)
                self.schedule_refresh()

    def on_moved(self, event):
        if not event.is_directory:
            ext = os.path.splitext(event.dest_path)[1].lower()
            if ext in [".png", ".jpg", ".jpeg", ".pc"]:
                self.schedule_refresh()