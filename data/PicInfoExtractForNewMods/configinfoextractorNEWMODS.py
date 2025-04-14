import os
import zipfile
import re
import time
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor

import tkinter as tk


#changing the encoding

# ========================
# Configuration Constants
# ========================

MODS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # Path to the Mods folder
MODS_REPO_PATH = os.path.join(MODS_PATH, "repo") # Path to the repo folder
SCRIPT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Script's directory path
CONFIG_INFO_FOLDER = os.path.abspath(os.path.join(SCRIPT_PATH, "..", "data/ConfigInfo"))  # Output directory
LOG_FILE_PATH = os.path.join(SCRIPT_PATH, "extraction_logINFO.txt")  # Log file path
ERROR_LOG_PATH = os.path.join(SCRIPT_PATH, "error_log_info.txt")  # Error log path

print(f"configinfoextractorNEWMODS.py\n\n")
print(f"SCRIPT_PATH: {SCRIPT_PATH}")
print(f"MODS_PATH: {MODS_PATH}")
print(f"MODS_REPO_PATH: {MODS_REPO_PATH}")
print(f"CONFIG_INFO_FOLDER: {CONFIG_INFO_FOLDER}")
print(f"LOG_FILE_PATH: {LOG_FILE_PATH}")
print(f"ERROR_LOG_PATH: {ERROR_LOG_PATH}")


# ========================
# Show the scanning window
# ========================


scan_window_position_file = os.path.abspath(os.path.join(SCRIPT_PATH, "..", "data/scanning_window_position.txt")) 


scanning_window = tk.Toplevel() # Assuming you have a root window created elsewhere

scanning_window.attributes('-topmost', True)
scanning_window.tk.call('tk', 'scaling', 1.25)
scanning_window.resizable(False, False)

# Define scanning window size - default values
window_width = 600
window_height = 70

# --- Load position from file or use default ---
pos_x = None
pos_y = None
position_loaded = False

# Use the pathlib path directly
if os.path.exists(scan_window_position_file):
    try:
        with open(scan_window_position_file, 'r') as f:
            content = f.read().strip() # Read and remove leading/trailing whitespace
            if content: # Check if the file is not empty
                parts = content.split(',')
                if len(parts) == 2:
                    # Try converting parts to integers
                    loaded_x = int(parts[0].strip())
                    loaded_y = int(parts[1].strip())
                    pos_x = loaded_x
                    pos_y = loaded_y
                    position_loaded = True
                    print(f"Loaded position from file: ({pos_x}, {pos_y})") # Optional logging
                else:
                    print(f"Warning: Invalid format in {scan_window_position_file}. Expected 'x,y'. Using default position.")
            else:
                 print(f"Warning: Position file {scan_window_position_file} is empty. Using default position.")
    except ValueError:
        print(f"Warning: Non-numeric coordinates found in {scan_window_position_file}. Using default position.")
    except Exception as e:
        # Catch other potential errors during file reading
        print(f"Error reading position file {scan_window_position_file}: {e}. Using default position.")
else:
    print(f"Position file not found: {scan_window_position_file}. Using default position.") # Optional logging


# --- Fallback to centering if position wasn't loaded ---
if not position_loaded:
    # Ensure window manager has processed geometry requests before getting screen size
    scanning_window.update_idletasks()
    screen_width = scanning_window.winfo_screenwidth()
    screen_height = scanning_window.winfo_screenheight()
    pos_x = (screen_width // 2) - (window_width // 2)
    pos_y = (screen_height // 2) - (window_height // 2)
    print(f"Using default centered position: ({pos_x}, {pos_y})") # Optional logging

# --- Configure and place the window ---

# Set background color of the window
scanning_window.configure(bg="#333333")  # Set background color

scanning_window.overrideredirect(True)  # Remove window border
scanning_window.config(highlightthickness=5, highlightbackground="#555555") # Add border here

# Set the geometry of the scanning window using the determined position
if pos_x is not None and pos_y is not None: # Check if pos_x/pos_y were set
    scanning_window.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
else:
    # Handle the unlikely case where neither loading nor centering worked (shouldn't happen with this logic)
    print("Error: Window position could not be determined. Placing at default.")
    scanning_window.geometry(f"{window_width}x{window_height}") # Place without position offset

lbl = tk.Label(
    scanning_window,
    text="Copying mod and vehicle information to data folder...",
    font=("Segoe UI", 12, "bold"),
    fg="#ffffff",
    bg="#333333"
)
lbl.pack(expand=True, padx=20, pady=20)

scanning_window.update()




# ========================
# Setup Output and Logs
# ========================

# Create ConfigInfo folder if it doesn't exist
os.makedirs(CONFIG_INFO_FOLDER, exist_ok=True)

# Initialize or clear log files and open them once
log_file = open(LOG_FILE_PATH, 'w', encoding="utf-8", errors="replace")
error_log = open(ERROR_LOG_PATH, 'w', encoding="utf-8", errors="replace")

# Initialize counters for summary
extracted_count = 0
skipped_count = 0
error_count = 0

# ========================
# Helper Functions
# ========================

def preload_existing_files(folder_path):
    """Preloads existing files into a set for efficient lookup."""
    return set(os.listdir(folder_path))

# ========================
# Main Script Execution
# ========================

async def process_zip_file(zip_file, internal_paths, existing_config_infos, skipped_files, executor, mods_dir):
    """Processes a single ZIP file, extracting specified info.json files."""
    global extracted_count, skipped_count, error_count

    full_zip_path = os.path.join(mods_dir, zip_file) # Use mods_dir instead of MODS_PATH
    if not os.path.exists(full_zip_path):
        error_log.write(
            f"Error: Zip file not found: {zip_file} in {mods_dir} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        error_count += 1
        return

    loop = asyncio.get_event_loop()

    try:
        with zipfile.ZipFile(full_zip_path, "r") as zfile:
           for internal_path in internal_paths:
                # Extract the vehicle path from the internal path
                match = re.match(r"^vehicles/(.*?)/info\.json$", internal_path)
                if not match:
                    error_log.write(
                        f"Unexpected internal path format: {internal_path} in {zip_file} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    )
                    error_count += 1
                    continue
                vehicle_path = match.group(1)

                # Get directory path from the current file path
                folder_to_scan = os.path.dirname(internal_path)
                # Extract all json files in the given directory
                all_files_in_dir = [f for f in zfile.namelist() if f.startswith(folder_to_scan) and f.endswith(".json")]

                # Process each of these files
                for internal_file in all_files_in_dir:
                    # Extract file name (e.g., info_td6_hse_prefacelift.json)
                   file_base_name = os.path.basename(internal_file)
                   file_base_name_no_ext = os.path.splitext(file_base_name)[0]

                    # Construct the output file name
                   if internal_file == internal_path:
                        output_info_name = f"vehicles--{vehicle_path}_{zip_file}--info.json" # Original name, same as before
                   else:
                        output_info_name = f"vehicles--INDIVIDUAL--{vehicle_path}_{zip_file}--info_{file_base_name_no_ext}.json" # New naming convention for *other* files

                   output_info_path = os.path.join(CONFIG_INFO_FOLDER, output_info_name)


                   if output_info_name in skipped_files:
                        log_file.write(
                            f"Skipped (pre-check): {output_info_name} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        )
                        skipped_count += 1
                        continue


                   try:
                        # Extract the info.json file
                        with zfile.open(internal_file) as source, open(
                                output_info_path, "wb"
                                ) as target:
                             shutil.copyfileobj(source, target)

                        # Log the successful extraction
                        log_file.write(
                             f"Extracted: {output_info_name} from {zip_file} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        )
                        extracted_count += 1
                        existing_config_infos.add(output_info_name)

                   except Exception as e:
                       error_log.write(
                            f"Error: Failed to extract {internal_file} from {zip_file} at {time.strftime('%Y-%m-%d %H:%M:%S')}: {e}\n"
                            )
                       error_count += 1

    except zipfile.BadZipFile:
        error_log.write(f"Error: Bad zip file encountered: {zip_file} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        error_count += 1
        return

async def main():
    """Main function to control the script's execution flow."""
    global extracted_count, skipped_count, error_count

    # ========================
    # Step 4: Read and Parse Input File
    # ========================
    parent_dir = os.path.dirname(SCRIPT_PATH)
    input_file = os.path.join(parent_dir, "data/outputGOOD.txt")

    try:
        with open(input_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found: {input_file}")
        return

    lines = content.splitlines()
    zip_files = {}

    for index, line in enumerate(lines):
        line = line.strip()

        # Skip lines that do not contain both "(package)" and "vehicles/"
        if "(package)" not in line or "vehicles/" not in line:
            continue

        # Extract ZIP file name and vehicle path using RegEx
        match = re.match(r"^(.*?) \(package\).*vehicles/(.*?)/", line)
        if not match:
            error_log.write(
                f"Malformed line at {index}: {line} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            error_count += 1
            continue

        zip_file = match.group(1)
        vehicle_path = match.group(2)

        # Define the internal path for info.json
        internal_path = f"vehicles/{vehicle_path}/info.json"

        # Group internal paths by ZIP file
        if zip_file not in zip_files:
            zip_files[zip_file] = []
        if internal_path not in zip_files[zip_file]:
            zip_files[zip_file].append(internal_path)

    # ========================
    # Step 5: Preload Existing ConfigInfo Files
    # ========================
    existing_config_infos = preload_existing_files(CONFIG_INFO_FOLDER)

    # ========================
    # Step 5.5: Pre-calculate skipped files
    # ========================
    skipped_files = set()
    for zip_file, internal_paths in zip_files.items():
        for internal_path in internal_paths:
            match = re.match(r"^vehicles/(.*?)/info\.json$", internal_path)
            if not match:
                continue # Should not happen, but for robustness
            vehicle_path = match.group(1)

            mods_dirs = [MODS_PATH, MODS_REPO_PATH]
            beamng_vehicles_dir_file = os.path.join(SCRIPT_PATH, "data/beamng_VANILLA_vehicles_folder.txt")
            try:
                with open(beamng_vehicles_dir_file, "r", encoding="utf-8", errors="replace") as f:
                    vanilla_vehicles_path = f.readline().strip()
                    if vanilla_vehicles_path and os.path.exists(vanilla_vehicles_path):
                        mods_dirs.append(vanilla_vehicles_path)
            except FileNotFoundError:
                pass

            for mods_dir in mods_dirs: # Check in all mods directories
                full_zip_path = os.path.join(mods_dir, zip_file)
                if not os.path.exists(full_zip_path):
                    continue # Zip file not found in this dir, check next

                try:
                    with zipfile.ZipFile(full_zip_path, "r") as zfile:
                        folder_to_scan = os.path.dirname(internal_path)
                        all_files_in_dir = [f for f in zfile.namelist() if f.startswith(folder_to_scan) and f.endswith(".json")]

                        for internal_file in all_files_in_dir:
                            file_base_name = os.path.basename(internal_file)
                            file_base_name_no_ext = os.path.splitext(file_base_name)[0]

                            if internal_file == internal_path:
                                output_info_name = f"vehicles--{vehicle_path}_{zip_file}--info.json"
                            else:
                                output_info_name = f"vehicles--INDIVIDUAL--{vehicle_path}_{zip_file}--info_{file_base_name_no_ext}.json"

                            if output_info_name.startswith("vehicles--INDIVIDUAL") and "info_info" not in output_info_name:
                                skipped_files.add(output_info_name)
                                continue
                            if output_info_name in existing_config_infos:
                                skipped_files.add(output_info_name)
                                continue
                except zipfile.BadZipFile:
                    continue # Handle bad zip silently in pre-check, errors are already logged during processing


    # ========================
    # Step 6: Process Each ZIP File
    # ========================
    with ThreadPoolExecutor(max_workers=15) as executor:  # Limit the number of threads
        tasks = []
        mods_dirs = [MODS_PATH, MODS_REPO_PATH]

         # Read BeamNG vehicles directory from file (in MODFINDER directory)
        beamng_vehicles_dir_file = os.path.join(SCRIPT_PATH, "beamng_VANILLA_vehicles_folder.txt") # File is one level up
        try:
            with open(beamng_vehicles_dir_file, "r", encoding="utf-8", errors="replace") as f:
                vanilla_vehicles_path = f.readline().strip()
                if vanilla_vehicles_path and os.path.exists(vanilla_vehicles_path): # Check if path is valid and exists
                    mods_dirs.append(vanilla_vehicles_path)
                elif vanilla_vehicles_path:
                    print(f"Warning: BeamNG vehicles directory '{vanilla_vehicles_path}' from '{beamng_vehicles_dir_file}' does not exist or is invalid.")
        except FileNotFoundError:
            print(f"Warning: {beamng_vehicles_dir_file} not found. BeamNG vehicles directory will not be checked.")


        for mods_dir in mods_dirs:
            print(f"Checking directory: {mods_dir}") # Debug print
            zip_files_in_dir = {}
            for zip_file_name, internal_paths in zip_files.items():
                full_zip_path = os.path.join(mods_dir, zip_file_name)
                if os.path.exists(full_zip_path):
                    if mods_dir not in zip_files_in_dir:
                        zip_files_in_dir[mods_dir] = {}
                    zip_files_in_dir[mods_dir][zip_file_name] = internal_paths

            for current_mods_dir, zip_file_data in zip_files_in_dir.items():
                for zip_file_name, internal_paths in zip_file_data.items():
                    tasks.append(
                        process_zip_file(
                            zip_file_name, internal_paths, existing_config_infos, skipped_files, executor, current_mods_dir
                        )
                    )
        await asyncio.gather(*tasks)

    # ========================
    # Step 7 & 8: Write Logs and Display Summary
    # ========================
    print(
        f"Extraction complete.\n\nFiles Extracted: {extracted_count}\nFiles Skipped: {skipped_count}\nErrors: {error_count}\n\nInfo.json files have been extracted to: {CONFIG_INFO_FOLDER}"
    )

    log_file.close()
    error_log.close()

    if scanning_window: # Check if the window variable exists
            try:
                scanning_window.destroy() # Close the Tkinter window
            except tk.TclError as e:
                # Handle cases where the window might already be destroyed
                # or in an invalid state (less likely here, but good practice)
                print(f"Info: Could not destroy scanning window (might already be closed): {e}")


if __name__ == "__main__":
    start_time = time.time()
    try:
        # Run the main asynchronous function
        asyncio.run(main())

    finally:
        # This block executes after asyncio.run(main()) finishes,
        # regardless of whether main() completed successfully or raised an error.
        print("Main execution finished. Attempting to close scanning window.") # Optional debug print

        try:

            if scanning_window:
                scanning_window.destroy() # Close the Tkinter window
        except NameError:
            # Handle case where 'scanning_window' might not have been defined
            print("Info: 'scanning_window' variable not found.")
        except tk.TclError as e:
            # Handle cases where the window might already be destroyed or invalid
            print(f"Info: Could not destroy scanning window (might already be closed/invalid): {e}")

    # Calculate and print time *after* the main work and cleanup attempt
    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")
