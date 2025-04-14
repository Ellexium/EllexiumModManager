import os
import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from PIL import Image



# --- DEBUG PRINT SWITCH ---
DEBUG_MODE = False

def debug_print(*args, **kwargs):
    """
    Conditional print function. Prints only if DEBUG_MODE is True.
    """
    if DEBUG_MODE:
        print(*args, **kwargs)

# Utility function to show a message box (MUST BE DEFINED HERE, OTHERWISE UI WILL BREAK)
def show_message_internal(title, message):
    """Utility function to show a message box (internal)."""
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showerror(title, message)
    root.destroy()

def preload_existing_files_internal(folder_path: Path) -> set:
    """
    Preload existing files in the specified folder into a set for efficient lookup.

    Parameters:
    - folder_path: Path object representing the folder to preload.

    Returns:
    - A set containing the names of existing files in the folder.
    """
    return {file.name for file in folder_path.iterdir() if file.is_file()}


# ------------------------------------------------------------
# NEW: Integrated configpicextractor_CUSTOM functionality - DEBUGGING PRINTS ADDED - PATH CONVERSION FORCED
# ------------------------------------------------------------
def run_configpicextractor_custom_integrated(script_dir, user_folder, config_pics_custom_folder): # <--- NEW METHOD
    """
    Integrated functionality of configpicextractor_CUSTOM.py, now with extensive debugging prints and forced Path conversion.
    Converts images to PNG format and resizes them to 200x110, then renames to original extension.
    **MODIFIED to delete the content of the config_pics_folder before processing.**
    """
    debug_print("CONFIGPICTUREEXTRACTORDUBUG - START: run_configpicextractor_custom_integrated() - Integrated Method") # Debug: Function Start

    # --- FORCE Path CONVERSION for config_pics_folder RIGHT HERE ---
    config_pics_folder = Path(config_pics_custom_folder) # <--- FORCE CONVERSION - Apply to config_pics_folder (passed arg)
    # --- FORCE Path CONVERSION for config_pics_folder RIGHT HERE ---

    # ========================
    # Configuration Constants - MODIFIED for integration
    # ========================

    # No command-line argument check needed here anymore

    # Define the script directory (still needed)
    script_dir = Path(script_dir).resolve() # <--- USE passed script_dir

    # Define paths for output directories and log files - UNCHANGED (relative to script_dir)
    log_file_path = script_dir / "data/extraction_log_custom.txt"
    error_log_path = script_dir / "data/error_log_custom.txt"
    input_file = script_dir / "data/outputGOODcustom.txt"

    debug_print(f"CONFIG_PROCESSORS.PY - input file {input_file}")


    # ========================
    # Setup Output and Logs - UNCHANGED
    # ========================

    # Create ConfigPicsCustom folder if it doesn't exist
    try:
        config_pics_folder.mkdir(parents=True, exist_ok=True) # <--- config_pics_folder is now Path object (local variable)
        debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - ConfigPicsCustom folder created or already exists: {config_pics_folder}") # Debug
    except Exception as e:
        debug_print(f"ERROR: Failed to create directory: {config_pics_folder}. Exception: {e}") # Debug: Error creating dir
        # show_message_internal("Error", f"Failed to create directory: {config_pics_folder}\n{e}")
        return  # Changed from sys.exit to return in method

    '''
    # --- DELETE CONTENT OF THE FOLDER HERE ---
    try:
        debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - START: Deleting contents of folder: {config_pics_folder}") # Debug: Folder deletion start
        for item in os.listdir(config_pics_folder):
            item_path = config_pics_folder / item
            if item_path.is_file():
                os.remove(item_path)
                debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Deleted file: {item_path}") # Debug: File deleted
            elif item_path.is_dir():
                shutil.rmtree(item_path)
                debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Deleted directory: {item_path}") # Debug: Directory deleted
        debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - END: Contents of folder deleted successfully: {config_pics_folder}") # Debug: Folder deletion end
    except Exception as e:
        error_message_delete = f"ERROR: Failed to delete contents of directory: {config_pics_folder}. Exception: {e}"
        debug_print(error_message_delete) # Debug: Error deleting folder content
        error_log += error_message_delete + "\n" # Add error to error log, even if log file init might fail later
        # Continue processing even if deletion fails, but log the error. Consider if you want to halt on deletion failure.
    '''

    # Initialize or clear log files
    try:
        log_file_path.write_text("", encoding="utf-8")
        error_log_path.write_text("", encoding="utf-8")
        debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Log files initialized/cleared: {log_file_path}, {error_log_path}") # Debug: Log files init success
    except Exception as e:
        debug_print(f"ERROR: Failed to initialize log files. Exception: {e}") # <--- ADDED DEBUG PRINT - Log init error
        # show_message_internal("Error", f"Failed to initialize log files.\n{e}")
        return  # Changed from sys.exit to return in method


    # Initialize log variables
    extraction_log = ""
    # error_log is already potentially populated from folder deletion errors
    if 'error_log' not in locals(): # Check if error_log was already initialized above in case of deletion error.
        error_log = ""

    # Initialize counters for summary
    extracted_count = 0
    skipped_count = 0
    error_count = 0
    if 'error_message_delete' in locals(): # Increment error count if deletion error occurred
        error_count += 1

    # Initialize dictionary to store original extensions
    original_extensions_custom = {}

    # ========================
    # Main Script Execution - MODIFIED for integration
    # ========================

    # Check if input file exists
    if not input_file.exists():
        debug_print(f"ERROR: Input file 'outputGOODcustom.txt' does not exist: {input_file}") # <--- ADDED DEBUG PRINT - Input file missing
        # show_message_internal("Error", f"Input file does not exist: {input_file}")
        return  # Changed from sys.exit to return in method
    debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Input file 'outputGOODcustom.txt' exists: {input_file}") # Debug: Input file exists

    # Read and parse the input file
    try:
        content = input_file.read_text(encoding="utf-8")
        debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Input file 'outputGOODcustom.txt' read successfully.") # Debug: Input file read success
    except Exception as e:
        debug_print(f"ERROR: Failed to read input file 'outputGOODcustom.txt'. Exception: {e}") # <--- ADDED DEBUG PRINT - Input file read error
        # show_message_internal("Error", f"Failed to read file: {input_file}\n{e}")
        return  # Changed from sys.exit to return in method

    # Split the content into lines
    lines = content.replace('\r', '').split('\n')

    # Preload existing ConfigPicsCustom files - this will now be empty as we just deleted everything
    #existing_config_pics = set() # preload_existing_files_internal(config_pics_folder) # <--- CORRECTED CALL - Pass config_pics_folder (singular) - No longer needed as we clear the folder
    existing_config_pics = preload_existing_files_internal(config_pics_folder) 

    # Define regex patterns
    config_picture_pattern = re.compile(r'^(.*?)\s-\s"(.+?)"\s\(config picture\)$')
    extension_pattern = re.compile(r'\.(png|jpg|jpeg)$', re.IGNORECASE)
    config_name_pattern = re.compile(r'(?:.*/)?([^./\\]+)\.(png|jpg|jpeg)$', re.IGNORECASE)

    # Current timestamp for logging
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    debug_print("CONFIGPICTUREEXTRACTORDUBUG - START: Processing lines from outputGOODcustom.txt") # Debug: Line processing start

    # Parse each line to process custom config pictures
    for index, line in enumerate(lines, start=1):
        line = line.strip()
        # debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Processing line {index}: '{line}'") # Debug: Line being processed

        # Skip lines that do not contain "(config picture)"
        if "(config picture)" not in line:
            # debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} skipped - no '(config picture)' found.") # Debug: Skip no config picture
            continue
        # debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} contains '(config picture)', proceeding...") # Debug: Continue processing config picture line

        # Extract vehicleName and configPicturePath using regex
        match = config_picture_pattern.match(line)
        if not match:
            # Log malformed line
            error_log += f"Malformed line at {index}: {line} at {current_time}\n"
            error_count += 1
            debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} MALFORMED - regex match failed.") # Debug: Malformed line
            continue
        # debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} regex MATCH successful.") # Debug: Regex match success

        vehicle_name, config_picture_path = match.groups()
        # debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} extracted vehicle_name: '{vehicle_name}', config_picture_path: '{config_picture_path}'") # Debug: Extracted values

        # Validate configPicturePath has valid extension
        ext_match = extension_pattern.search(config_picture_path)
        if not ext_match:
            # Log invalid file extension
            error_log += f"Invalid file extension for config picture at line {index}: {config_picture_path} at {current_time}\n"
            error_count += 1
            debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} - Invalid file extension: '{config_picture_path}'.") # Debug: Invalid extension
            continue
        # debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} - Valid file extension found.") # Debug: Valid extension

        config_extension = ext_match.group(1)

        # Extract the config name without extension
        config_match = config_name_pattern.match(config_picture_path)
        if not config_match:
            # Log unexpected config picture format
            error_log += f"Unexpected config picture format: {config_picture_path} at {current_time}\n"
            error_count += 1
            debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} - Unexpected config picture format: '{config_picture_path}'.") # Debug: Unexpected format
            continue
        # debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} - Expected config picture format.") # Debug: Expected format

        config_name, config_ext = config_match.groups()

        # Construct the output file name (always PNG initially)
        output_picture_name = f"vehicles--{vehicle_name}_user--{config_name}.png" # Force PNG extension
        output_picture_path = config_pics_folder / output_picture_name # <--- Use LOCAL config_pics_custom_folder - now guaranteed Path object
        # debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} - Output picture path constructed: '{output_picture_path}'") # Debug: Output path constructed

        # Check if a file with a similar base name already exists; if so, skip
        output_base_name = os.path.splitext(output_picture_name)[0]
        skip_file = False
        for existing_file in existing_config_pics:
            existing_base_name = os.path.splitext(existing_file)[0]
            if output_base_name in existing_base_name: # Check if output base name is a substring of existing base name
                skip_file = True
                break # No need to check other existing files if a match is found

        if skip_file:
            # Log the skipped file
            extraction_log += f"Skipped (similar base name exists): {output_picture_name} at {current_time}\n"
            skipped_count += 1
            debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} - File skipped (similar base name exists): '{output_picture_name}'.") # Debug: File skipped
            continue


        # debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} - File does NOT exist, proceeding to process and copy.") # Debug: File does not exist - no longer accurate

        debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} - Proceeding to process and copy (no similar base name found).") # Debug: File does not exist - modified message

        # Process and save the image as PNG and resized
        source_path = Path(config_picture_path)
        destination_path = output_picture_path

        try:
            debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} - Attempting to process image from '{source_path}' to '{destination_path}'...") # Debug: Before image processing
            img = Image.open(source_path)
            resized_img = img.resize((200, 110))
            resized_img.save(destination_path, "PNG") # Save as PNG, overwrites destination_path extension if needed

            original_extensions_custom[output_picture_name] = config_extension # Store original extension

            # Update the set to include the newly copied file - No longer needed as we don't skip based on existing files.
            # existing_config_pics.add(output_picture_name)
            # Log the successful copy
            extraction_log += f"Copied and resized to PNG: {output_picture_name} from {config_picture_path} at {current_time}\n"
            extracted_count += 1
            debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} - Image processed and saved successfully.") # Debug: Image process success
        except Exception as e:
            # Log the error if FileCopy fails
            error_log += f"Error: Failed to process image {config_picture_path} to {output_picture_path}\n{e} at {current_time}\n"
            error_count += 1
            debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Line {index} - Error during image processing. Exception: {e}") # Debug: Image process error
            continue

    debug_print("CONFIGPICTUREEXTRACTORDUBUG - END: Processing lines from outputGOODcustom.txt") # Debug: Line processing end

    # Rename files to original extensions
    debug_print("CONFIGPICTUREEXTRACTORDUBUG - START: Renaming files to original extensions") # Debug: Renaming start
    for output_picture_name, original_extension in original_extensions_custom.items():
        png_filepath = config_pics_folder / output_picture_name
        base_filename = os.path.splitext(output_picture_name)[0]
        new_filename = base_filename + "." + original_extension
        new_filepath = config_pics_folder / new_filename
        try:
            os.rename(png_filepath, new_filepath)
            extraction_log += f"Renamed: {output_picture_name} to {new_filename} at {current_time}\n"
            debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Renamed: {output_picture_name} to {new_filename}") # Debug: Renamed success
        except Exception as rename_error:
            error_log += f"Error renaming {output_picture_name} to {new_filename} at {current_time}: {rename_error}\n"
            error_count += 1
            debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Error renaming {output_picture_name} to {new_filename}: {rename_error}") # Debug: Renamed error
    debug_print("CONFIGPICTUREEXTRACTORDUBUG - END: Renaming files to original extensions") # Debug: Renaming end


    # Write Logs
    try:
        log_file_path.write_text(extraction_log, encoding="utf-8")
        debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Log file 'extraction_log_custom.txt' written successfully.") # Debug: extraction_log write success
    except Exception as e:
        # show_message_internal("Error", f"Failed to write to log file: {log_file_path}\n{e}") # Use show_message_internal
        return  # Changed from sys.exit to return in method

    try:
        error_log_path.write_text(error_log, encoding="utf-8")
        debug_print(f"CONFIGPICTUREEXTRACTORDUBUG - Error log file 'error_log_custom.txt' written successfully.") # Debug: error_log write success
    except Exception as e:
        # show_message_internal("Error", f"Failed to write to error log file: {error_log_path}\n{e}") # Use show_message_internal
        return  # Changed from sys.exit to return in method

    # Prepare the summary message
    summary_message = (
        f"Custom config picture extraction and renaming complete.\n\n"
        f"Files Copied, Converted to PNG (200x110), and Renamed: {extracted_count}\n"
        f"Files Skipped: {skipped_count} (Skipped count is now always 0 as folder is cleared)\n" # Updated skipped count message
        f"Errors: {error_count}\n\n"
        f"Config pictures have been processed and renamed in: {config_pics_folder}" # <--- Use LOCAL config_pics_custom_folder in message
    )

    # Display the summary message
    # show_message_internal("Info", summary_message) # Use show_message_internal
    # sys.exit(0) - No sys.exit in method, just return
    debug_print("CONFIGPICTUREEXTRACTORDUBUG - END: run_configpicextractor_custom_integrated() - Config picture extraction process completed (integrated method).") # Confirmation print - NEW
    return summary_message # Return summary message for potential UI display

# ------------------------------------------------------------
# NEW: Integrated MOD_COMMAND_LINE_CONFIG_GEN_CUSTOM.py functionality - DEBUGGING ADDED (EXTREME) - PATHLIB IMPORTED
# ------------------------------------------------------------
def run_mod_command_line_config_gen_custom_integrated(script_dir, user_folder, config_pics_folder): # <--- NEW METHOD
    """
    Integrated functionality of MOD_COMMAND_LINE_CONFIG_GEN_CUSTOM.py, now as a method - DEBUGGING ADDED (EXTREME) - PATHLIB IMPORTED.
    """
    import pathlib  # Ensure pathlib is imported here, though it's already at the top level

    debug_print("\n--- run_mod_command_line_config_gen_custom_integrated() ENTRY - EXTREME DEBUGGING - PATHLIB IMPORTED ---") # Debug Entry - EXTREME DEBUGGING - PATHLIB IMPORTED
    debug_print(f"  [DEBUG-START] script_dir (type): {type(script_dir)}, value: {script_dir}") # Debug - Print script_dir with type
    debug_print(f"  [DEBUG-START] config_pics_folder (type): {type(config_pics_folder)}, value: {config_pics_folder}") # Debug - Print config_pics_folder with type
    debug_print(f"  [DEBUG-START] user_folder (type): {type(user_folder)}, value: {user_folder}") # Debug - Print user_folder with type

    # --- Configuration and Paths (MODIFIED for integration) ---
    script_dir = pathlib.Path(script_dir).resolve() # Use script_dir
    debug_print("  [DEBUG-PATH] script_dir (after resolve, type): {type(script_dir)}, value: {script_dir}") # Debug - Print script_dir AFTER resolve

    debug_print("  [DEBUG-PATH] About to assign config_pics_folder...") # Debug - Before config_pics_folder assignment
    config_pics_folder = pathlib.Path(config_pics_folder).resolve() # <-- **CHECK THIS LINE - POTENTIAL ERROR SOURCE** ### PATHLIB FIX
    debug_print("  [DEBUG-PATH] config_pics_folder ASSIGNED (type): {type(config_pics_folder)}, value: {config_pics_folder}") # Debug - Print config_pics_folder AFTER assignment

    user_folder = pathlib.Path(user_folder).resolve() # Use user_folder
    debug_print("  [DEBUG-PATH] user_folder (after resolve, type): {type(user_folder)}, value: {user_folder}") # Debug - Print user_folder AFTER resolve

    output_file = script_dir / "data/outputGOODcustom.txt" # Output in script dir
    debug_print("  [DEBUG-PATH] output_file (type): {type(output_file)}, value: {output_file}") # Debug - Print output_file path

    # --- Processing Function (MODIFIED to use internal show_message and paths) ---


    def process_vehicle_folder_internal(folder_path: pathlib.Path, folder_name: str, output_file: pathlib.Path):
        """
        Process each vehicle folder (internal version) - DEBUGGING ADDED.
        MODIFIED to handle missing config pictures - use "MISSINGCONFIGPICTURE" placeholder.
        """
        debug_print(f"\n  --- process_vehicle_folder_internal() ENTRY ---") # Debug Entry - process_vehicle_folder_internal
        # debug_print(f"    folder_path: {folder_path}, folder_name: {folder_name}") # Debug - Args to process_vehicle_folder_internal

        debug_print("    Globbing for *.pc files...") # Debug - Before globbing
        # Iterate through all .pc files in the folder
        for pc_file in folder_path.glob("*.pc"):
            original_pc_file_path = pc_file
            pc_filename = pc_file.stem  # Filename without extension

            # Replace '.' with ' ' in the filename
            modified_pc_filename = pc_filename.replace('.', ' ')
            new_pc_file_path = folder_path / f"{modified_pc_filename}.pc"

            # debug_print(f"    Processing pc_file: {pc_file}, pc_filename: {pc_filename}") # Debug - Processing pc_file
            # debug_print(f"      Renaming {original_pc_file_path} to {new_pc_file_path}...") # Debug - Rename PC file

            try:
                # Rename the original .pc file
                shutil.move(str(original_pc_file_path), str(new_pc_file_path))
                debug_print(f"      Renamed successfully: {new_pc_file_path}") # Debug - Rename PC success
            except Exception as e:
                error_msg = f"      Failed to rename {original_pc_file_path} to {new_pc_file_path}.\n{e}"
                show_message_internal("Error", error_msg)
                debug_print(error_msg) # Debug - Rename PC error
                continue  # Skip to the next file

            # Construct the spawn command
            spawn_command = f'core_vehicles.spawnNewVehicle("{folder_name}", {{config = \'vehicles/{folder_name}/{modified_pc_filename}.pc\'}})'

            # Define the image extensions
            extensions = ["jpg", "jpeg", "png"]

            debug_print("      Processing images...") # Debug - Image processing start
            # Process and rename images based on the .pc file
            image_info = None # Initialize image_info outside the loop
            found_image = False # Flag to track if image was found
            for ext in extensions:
                original_image_path = folder_path / f"{pc_filename}.{ext}"
                new_image_filename = f"{modified_pc_filename}.{ext}"
                new_image_path = folder_path / new_image_filename

                if original_image_path.exists():
                    found_image = True # Set flag to True if image is found
                    debug_print(f"        Renaming image {original_image_path} to {new_image_path}...") # Debug - Rename image
                    try:
                        shutil.move(str(original_image_path), str(new_image_path))
                        debug_print(f"        Renamed image successfully: {new_image_path}") # Debug - Rename image success
                    except Exception as e:
                        error_msg = f"        Failed to rename {original_image_path} to {new_image_path}.\n{e}"
                        show_message_internal("Error", error_msg)
                        debug_print(error_msg) # Debug - Rename image error
                        continue  # Skip to the next extension

                    # Normalize backslashes to forward slashes
                    normalized_image_path = new_image_path.as_posix()

                    # Create the image information line - NOW CREATED HERE IF IMAGE FOUND
                    image_info = f'{folder_name} - "{normalized_image_path}" (config picture)'
                    break # Exit extension loop after finding one image

            if not found_image: # If no image was found in any extension
                debug_print(f"        No config picture found for {pc_filename}. Using 'MISSINGCONFIGPICTURE' placeholder.") # Debug - No image found
                image_info = f'{folder_name} - "MISSINGCONFIGPICTURE" (config picture)' # Use placeholder

            if image_info: # ONLY write if image_info is set (either with path or placeholder)
                # debug_print(f"        Writing image info to output file: {image_info}") # Debug - Write image info
                # Append the image information line to the output file
                try:
                    with output_file.open("a", encoding="utf-8", errors="replace") as f:
                        f.write(f"{image_info}\n")
                    debug_print(f"        Image info written successfully.") # Debug - Image info written
                except Exception as e:
                    error_msg = f"        Failed to write image info to {output_file}.\n{e}"
                    show_message_internal("Error", error_msg)
                    debug_print(error_msg) # Debug - Image info write error
                    return # Changed from sys.exit to return in method
            else:
                debug_print("        Warning: image_info was not set. Skipping write for this config picture.") # Debug - Warning - image_info not set


            # Create the additional package line
            config_path = f"vehicles/{folder_name}/{modified_pc_filename}"
            package_line = f'{folder_name} (package) - "{folder_name}" (internal folder name) - "{config_path}"'

            debug_print(f"      Writing package line to output file: {package_line}") # Debug - Write package line
            # Append the package line to the output file
            try:
                with output_file.open("a", encoding="utf-8", errors="replace") as f:
                    f.write(f"{package_line}\n")
                    debug_print(f"      Package line written successfully.") # Debug - Package line written
            except Exception as e:
                error_msg = f"      Failed to write package line to {output_file}.\n{e}"
                show_message_internal("Error", error_msg)
                debug_print(error_msg) # Debug - Package line write error
                return # Changed from sys.exit to return in method

            debug_print(f"      Writing spawn command to output file: {spawn_command}") # Debug - Write spawn command
            # Append the spawn command line to the output file with two newlines
            try:
                with output_file.open("a", encoding="utf-8", errors="replace") as f:
                    f.write(f"{spawn_command}\n\n")
                debug_print(f"      Spawn command written successfully.") # Debug - Spawn command written
            except Exception as e:
                error_msg = f"      Failed to write spawn command to {output_file}.\n{e}"
                show_message_internal("Error", error_msg)
                debug_print(error_msg) # Debug - Spawn command write error
                return # Changed from sys.exit to return in method
        debug_print(f"  --- process_vehicle_folder_internal() EXIT ---\n") # Debug Exit - process_vehicle_folder_internal


    # --- Main Script Logic (MODIFIED for integration) ---

    debug_print("  [DEBUG-MAIN] Checking if config_pics_folder is valid...") # Debug - Check config_pics_folder validity
    if not config_pics_folder: # Robust check for config_pics_folder
        error_msg = "  Error: config_pics_folder is not initialized in run_mod_command_line_config_gen_custom_integrated(). Aborting."
        show_message_internal("Error", error_msg) # Use internal show_message
        debug_print(error_msg) # Debug - config_pics_folder invalid
        return # Exit if config_pics_folder is invalid
    debug_print("  [DEBUG-MAIN] config_pics_folder is valid.") # Debug - config_pics_folder valid

    # Check if user_folder is valid (already checked in ConfigViewerApp init)
    debug_print("  Checking if user_folder is valid...") # Debug - User folder check start
    if not user_folder.exists() or not user_folder.is_dir():
        error_msg = "  User folder not provided or invalid. (Integrated Script)"
        #show_message_internal("Error", error_msg) # Use internal show_message
        #debug_print(error_msg) # Debug - User folder invalid
        return # Changed from sys.exit to return in method
    debug_print("  user_folder is valid.") # Debug - User folder valid

    # Delete the existing output file if it exists
    debug_print(f"  Checking if output_file exists: {output_file}") # Debug - Output file check
    if output_file.exists():
        debug_print(f"  output_file exists, attempting to delete: {output_file}") # Debug - Output file exists
        try:
            output_file.unlink()
            debug_print(f"  output_file deleted successfully: {output_file}") # Debug - Output file deleted
        except Exception as e:
            error_msg = f"  Failed to delete existing output file {output_file}.\n{e}"
            show_message_internal("Error", error_msg) # Use internal show_message
            debug_print(error_msg) # Debug - Output file delete error
            return # Changed from sys.exit to return in method
    else:
        debug_print(f"  output_file does not exist, no deletion needed.") # Debug - Output file does not exist

    debug_print("  Iterating through user_folder subdirectories...") # Debug - Folder iteration start
    # Iterate through each subdirectory in the user folder
    for folder in user_folder.iterdir():
        if folder.is_dir():
            folder_path = folder
            folder_name = folder.name
            debug_print(f"    Processing folder: {folder_name}, path: {folder_path}") # Debug - Processing folder
            process_vehicle_folder_internal(folder_path, folder_name, output_file) # Call INTERNAL processing function
    debug_print("  Finished iterating through user_folder subdirectories.") # Debug - Folder iteration end

    # show_message_internal("Info", f"Custom Config Generation completed. Output written to {output_file}") # Use internal show_message
    debug_print("  MOD_COMMAND_LINE_CONFIG_GEN_CUSTOM.py process completed (integrated method).") # Confirmation print - NEW
    debug_print("--- run_mod_command_line_config_gen_custom_integrated() EXIT - EXTREME DEBUGGING - PATHLIB IMPORTED ---\n") # Debug Exit - EXTREME DEBUGGING - PATHLIB IMPORTED

def process_lines(self, lines, full_data, is_custom):
    """
    Processes lines (regular or custom) and updates the provided full_data dictionary.
    Does NOT handle caching or final 'data' dictionary creation.
    """
    # NOTE: We DO NOT clear full_data here - it accumulates across calls.

    current_zip_file = None
    missing_custom_pic_path = os.path.join(self.script_dir, "data/MissingCustomConfigPic.png")
    missing_zip_pic_path = os.path.join(self.script_dir, "data/MissingZipConfigPic.png")
    last_picture_path = None

    # Ensure missing pictures exist (add checks if needed)

    print(f"\n--- process_lines() PROCESSING {'CUSTOM' if is_custom else 'REGULAR'} LINES ---")

    for line in lines:
        line = line.strip()
        folder_name = None

        # --- Start of original processing logic ---
        if is_custom:
            if "(config picture)" in line:
                try:
                    folder_name_extract, rest = line.split(" - ", 1)
                    folder_name = folder_name_extract.strip().lower()
                    full_path = rest.split("\" (config picture)")[0].strip("\"")
                    file_name_with_ext = os.path.basename(full_path)
                    file_name = os.path.splitext(file_name_with_ext)[0]
                    prefix = f"vehicles--{folder_name}_user--"
                    if file_name.lower().startswith(prefix.lower()):
                        file_name = file_name[len(prefix):]
                except ValueError:
                    print(f"  process_lines - Skipping line due to ValueError (custom config picture): {line}")
                    continue

                if folder_name is None:
                        print(f"  process_lines - Skipping line, folder_name is None (custom config picture): {line}")
                        continue

                picture_path = self.find_image_path(folder_name, file_name)
                if not picture_path or not os.path.exists(picture_path):
                    picture_path = missing_custom_pic_path
                last_picture_path = picture_path

            elif "core_vehicles.spawnNewVehicle" in line:
                match = re.search(
                    r'core_vehicles\.spawnNewVehicle\("(.+?)", \{config = \'vehicles/(.+?)/(.+?)\.pc\'\}\)', line)
                if match:
                    folder_name_raw, _, file_name = match.groups()
                    folder_name = folder_name_raw.lower()
                else:
                    match_nil = re.search(
                        r'core_vehicles\.spawnNewVehicle\("(.+?)",\s*\{(?:config\s*=\s*(?:nil|\'\'))?\}\)', line
                    )
                    if match_nil:
                        folder_name_raw = match_nil.group(1)
                        folder_name = folder_name_raw.lower()
                        file_name = "nil_config"
                    else:
                        print(f"  process_lines - Skipping line, regex failed (custom spawn): {line}")
                        continue

                if folder_name is None:
                    print(f"  process_lines - Skipping line, folder_name is None (custom spawn): {line}")
                    continue

                current_zip_file = "user_custom_configs"
                info_data = {}
                use_match = re.search(r'\(USE\s+(vehicles--[^)]+\.json)\)$', line)
                info_path = None

                if use_match:
                    use_info_json = use_match.group(1)
                    info_path = os.path.join(self.config_info_folder, use_info_json)
                    if os.path.exists(info_path):
                        info_data = self.extract_fallback_info(info_path)
                    else:
                        print(f"  process_lines - USE info file not found: {info_path}")
                        info_data = self.find_fallback_info(
                        os.path.basename(last_picture_path) if last_picture_path else ""
                        )
                else:
                    if last_picture_path and last_picture_path != missing_custom_pic_path:
                         img_basename = os.path.basename(last_picture_path)
                         img_name_no_ext = os.path.splitext(img_basename)[0]
                         # Construct individual info file name based on custom pic naming
                         # Example: vehicles--FOLDER_user--CONFIG.ext -> vehicles--FOLDER_user--CONFIG_info.json
                         individual_info_file = f"{img_name_no_ext}_info.json" # Check this format
                         info_path = os.path.join(self.config_info_folder, individual_info_file)

                    if info_path and os.path.exists(info_path):
                         info_data = self.extract_fallback_info(info_path)
                    else:
                         info_data = self.find_fallback_info(
                             os.path.basename(last_picture_path) if last_picture_path else ""
                         )


                current_picture_path_to_use = last_picture_path if last_picture_path else missing_custom_pic_path
                if not os.path.exists(current_picture_path_to_use):
                    current_picture_path_to_use = missing_custom_pic_path


                if folder_name not in full_data:
                    full_data[folder_name] = []

                if not isinstance(info_data, dict):
                     print(f"ERROR: process_lines - info_data is not a dict for custom line: {line}. Resetting.")
                     info_data = {"Name": "Data Error", "Value": 0}
                if 'Value' not in info_data or not isinstance(info_data.get('Value'), (int, float)):
                     info_data['Value'] = 0

                full_data[folder_name].append(
                    [current_picture_path_to_use, line, current_zip_file, info_data, folder_name]
                )
                last_picture_path = None

            else:
                continue # Skip other custom lines
        else: # Not is_custom (Regular Processing)
            if "(package)" in line:
                current_zip_file = line.split(" (package)")[0].strip()
                last_picture_path = None
                continue
            if "core_vehicles.spawnNewVehicle" not in line:
                continue
            if not current_zip_file:
                # print(f"  process_lines - Skipping line, no current_zip_file: {line}") # Can be noisy
                continue

            try:
                parts = line.split("core_vehicles.spawnNewVehicle(")[1]
                nil_match = re.search(r'"(.+?)",\s*\{(?:config\s*=\s*(?:nil|\'\'))?\}\)', parts)
                if nil_match:
                    folder_name_raw = nil_match.group(1)
                    folder_name = folder_name_raw.lower()
                    file_name = "nil_config"
                    candidate_base = f"vehicles--{folder_name}_{current_zip_file}--{file_name}" # Need base for info
                else:
                    config_match = re.search(r", \{config = 'vehicles/(.+?)/(.+?)\.pc'\}\)", parts)
                    if not config_match:
                         # Try finding just the folder name if config part is missing/different
                         folder_match = re.search(r'"([^"]+)"', parts)
                         if folder_match:
                             folder_name_raw = folder_match.group(1)
                             folder_name = folder_name_raw.lower()
                             file_name = "unknown_config" # Placeholder if config missing
                             candidate_base = f"vehicles--{folder_name}_{current_zip_file}--{file_name}"
                             print(f"  process_lines - Warning: Config path missing/malformed, using folder only for: {line}")
                         else:
                              print(f"  process_lines - Skipping line, cannot extract folder/config (non-custom): {line}")
                              continue
                    else:
                         # Standard case with config path
                         folder_name_raw, file_name = config_match.groups()
                         folder_name = folder_name_raw.lower()
                         candidate_base = f"vehicles--{folder_name}_{current_zip_file}--{file_name}"

            except Exception as e:
                 print(f"  process_lines - Skipping line due to unexpected error during split (non-custom): {line} - Error: {e}")
                 continue

            if folder_name is None:
                    print(f"  process_lines - Skipping line, folder_name is None (non-custom): {line}")
                    continue

            extensions = ['jpg', 'jpeg', 'png']
            picture_path = None
            for ext in extensions:
                candidate = f"{candidate_base}.{ext}"
                check_path = os.path.join(self.config_pics_folder, candidate)
                if os.path.exists(check_path):
                    picture_path = check_path
                    break

            if not picture_path:
                picture_path = missing_zip_pic_path
            current_picture_path = picture_path

            info_data = {}
            use_info_json_match = re.search(r'\(USE\s+(vehicles--[^)]+\.json)\)$', line)
            info_path = None

            if use_info_json_match:
                info_file = use_info_json_match.group(1)
                info_path = os.path.join(self.config_info_folder, info_file)
            else:
                # Construct standard individual info filename
                info_file = f"{candidate_base}_info.json"
                info_path = os.path.join(self.config_info_folder, info_file)


            if info_path and os.path.exists(info_path):
                info_data = self.extract_fallback_info(info_path)
            else:
                 # Fallback to zip-level info
                 old_info_file = f"vehicles--{folder_name}_{current_zip_file}--info.json"
                 old_info_path = os.path.join(self.config_info_folder, old_info_file)
                 if os.path.exists(old_info_path):
                      info_data = self.extract_fallback_info(old_info_path)
                 else:
                      info_data = self.find_fallback_info(os.path.basename(picture_path))


            if folder_name not in full_data:
                full_data[folder_name] = []

            line_clean = re.sub(r'\s*\(USE\s+vehicles--[^)]+\.json\)$', '', line).strip()

            current_picture_path_to_use = current_picture_path
            if not os.path.exists(current_picture_path_to_use):
                current_picture_path_to_use = missing_zip_pic_path

            if not isinstance(info_data, dict):
                 print(f"ERROR: process_lines - info_data is not a dict for regular line: {line_clean}. Resetting.")
                 info_data = {"Name": "Data Error", "Value": 0}
            if 'Value' not in info_data or not isinstance(info_data.get('Value'), (int, float)):
                info_data['Value'] = 0

            full_data[folder_name].append(
                [current_picture_path_to_use, line_clean, current_zip_file, info_data, folder_name]
            )
        # --- End of original processing logic ---

    print(f"--- process_lines() FINISHED PROCESSING {'CUSTOM' if is_custom else 'REGULAR'} LINES ---")
    # No post-processing here, just return the updated dictionary
    return full_data

# ------------------------------------------------------------
# NEW: Integrated modify_output_good functionality
# ------------------------------------------------------------
def run_modify_output_good_integrated(self):
    """
    Integrated functionality of modify_output_good.py, now as a method.
    """
    output_file_path = os.path.join(self.script_dir, 'data/outputGOODcustom.txt')
    config_info_dir_path = os.path.join(self.script_dir, 'data/configInfo')

    # --- Function: modify_output_good (Integrated) ---
    def modify_output_good_internal(output_file, config_info_dir):
        """
        This function processes the outputGOODcustom.txt file, checks for corresponding info.json files
        in the configInfo directory, and modifies spawnNewVehicle lines if necessary.

        Parameters:
        - output_file (str): Path to the outputGOODcustom.txt file.
        - config_info_dir (str): Path to the configInfo directory containing info.json files.
        """

        cache_file_path = self.script_dir / "data" / "config_processing_cache.json"
        if cache_file_path.exists():
            try:
                cache_file_path.unlink()
                print(f"DEBUG: Deleted cache file due to mod scan: {cache_file_path}")
            except OSError as e:
                print(f"Warning: Failed to delete cache file {cache_file_path}: {e}")


        # Verify the existence of the output file
        if not os.path.isfile(output_file):
            debug_print(f"Error: The file '{output_file}' does not exist.")
            return

        # Verify the existence of the configInfo directory
        if not os.path.isdir(config_info_dir):
            debug_print(f"Error: The directory '{config_info_dir}' does not exist.")
            return

        # Gather all existing info.json filenames in configInfo
        existing_info_files = set(
            f for f in os.listdir(config_info_dir) if f.endswith('--info.json')
        )

        # Read all lines from the output file
        with open(output_file, 'r', encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        modified_lines = []  # To store the updated lines
        entry = []            # To accumulate lines related to a single vehicle entry

        for line in lines:
            entry.append(line)

            # Check if the current line is a spawnNewVehicle line
            if 'core_vehicles.spawnNewVehicle' in line:
                # Extract package name and internal folder name from the accumulated entry
                package_name = None
                internal_folder = None
                for e_line in entry:
                    # Regex to extract package name and internal folder name
                    match = re.match(
                        r'(\S+)\s+\(package\)\s+-\s+"([^"]+)"\s+\(internal folder name\)', e_line
                    )
                    if match:
                        package_name = match.group(1)
                        internal_folder = match.group(2)
                        break  # Assuming the first matching line contains the needed info

                if not package_name or not internal_folder:
                    debug_print("Warning: Could not find package name or internal folder name in an entry.")
                    modified_lines.extend(entry)
                    entry = []
                    continue  # Skip to the next entry

                # Form the expected info.json filename
                expected_info = f'vehicles--{internal_folder}_{package_name}--info.json'

                if expected_info not in existing_info_files:
                    # Search for alternative info.json files for the same internal folder
                    alternative_infos = [
                        f for f in existing_info_files
                        if f.startswith(f'vehicles--{internal_folder}_') and f != expected_info
                    ]

                    if alternative_infos:
                        # Select the first available alternative
                        alternative_info = alternative_infos[0]

                        # Modify the spawnNewVehicle line by appending the USE statement
                        new_entry = []
                        for e_line in entry:
                            if 'core_vehicles.spawnNewVehicle' in e_line:
                                # Append the USE information before the newline character
                                e_line = e_line.rstrip('\n') + f' (USE {alternative_info})\n'
                            new_entry.append(e_line)

                        modified_lines.extend(new_entry)
                    else:
                        # No alternative info.json found; keep the original spawn line unchanged
                        debug_print(f"Warning: No alternative info.json found for '{internal_folder}' in package '{package_name}'.")
                        modified_lines.extend(entry)
                else:
                    # The expected info.json exists; no modification needed
                    modified_lines.extend(entry)

                # Reset the entry for the next vehicle
                entry = []

        # Handle any remaining lines that do not end with spawnNewVehicle
        if entry:
            modified_lines.extend(entry)

        # Rename the original outputGOODcustom.txt to outputGOODcustom (Original).txt
        original_output = 'outputGOODcustom (Original).txt'
        original_output_path = os.path.join(os.path.dirname(output_file), original_output) # Ensure path is correct
        if os.path.exists(original_output_path):
            os.remove(original_output_path)  # Remove if already exists to avoid errors
        shutil.move(output_file, original_output_path)

        # Write the modified lines to a new outputGOODcustom.txt
        with open(output_file, 'w', encoding="utf-8", errors="replace") as f:
            f.writelines(modified_lines)

        debug_print(f"Processing complete. The original file has been renamed to '{original_output}', and the updated file is '{output_file}'. (Integrated)")

    # --- Call the internal modify_output_good function ---
    modify_output_good_internal(output_file_path, config_info_dir_path)
    debug_print("modify_output_good process completed (integrated method).") # Confirmation print - NEW


    cumulative_script_path = os.path.join(self.script_dir, 'CumulativeMainInfoProcessor.py')
    try:
        #subprocess.run(['python', cumulative_script_path], check=True, cwd=self.script_dir)
        debug_print("this is where CumulativeMainInfoProcessor.py would have been executed.")
    except subprocess.CalledProcessError as e:
        #debug_print(f"Error running CumulativeMainInfoProcessor.py: {e}")
        pass
    except FileNotFoundError:
        #debug_print(f"Error: CumulativeMainInfoProcessor.py not found at: {cumulative_script_path}")
        pass
        
        
        
        
        
        
        
        
###############################


