import os
import zipfile
import re
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from PIL import Image  # Import the Pillow library for image processing


# ========================
# Configuration Constants
# ========================

SCRIPT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Script's directory path
MODS_PATH = os.path.abspath(os.path.join(SCRIPT_PATH, "..", "..")) # Path to the Mods folder
MODS_REPO_PATH = os.path.join(MODS_PATH, "repo") # Path to the repo folder
CONFIG_PICS_FOLDER = os.path.abspath(os.path.join(SCRIPT_PATH, "..", "data/ConfigPics"))  # Output directory
LOG_FILE_PATH = os.path.join(SCRIPT_PATH, "extraction_logpics.txt")  # Log file path
ERROR_LOG_PATH = os.path.join(SCRIPT_PATH, "error_log_pics.txt")  # Error log path

print(f"configpicextractorNEWMODS.py\n\n")
print(f"SCRIPT_PATH: {SCRIPT_PATH}")
print(f"MODS_PATH: {MODS_PATH}")
print(f"MODS_REPO_PATH: {MODS_REPO_PATH}")
print(f"CONFIG_PICS_FOLDER: {CONFIG_PICS_FOLDER}")
print(f"LOG_FILE_PATH: {LOG_FILE_PATH}")
print(f"ERROR_LOG_PATH: {ERROR_LOG_PATH}")


# ========================
# Setup Output and Logs
# ========================

# Create ConfigPics folder if it doesn't exist
os.makedirs(CONFIG_PICS_FOLDER, exist_ok=True)

# ========================
# Step 1: Initialize or Clear Log Files and Log Message Lists
# ========================

# Initialize or clear log files (opened in write mode now, but writing happens later)
log_file_obj = open(LOG_FILE_PATH, 'w', encoding="utf-8", errors="replace") # Open for writing, will be closed at the end
error_log_obj = open(ERROR_LOG_PATH, 'w', encoding="utf-8", errors="replace") # Open for writing, will be closed at the end

# Initialize lists to store log messages
log_messages = []
error_messages = []

# Initialize counters for summary
extracted_count = 0
skipped_count = 0
error_count = 0

# Global dictionary to store original extensions
original_extensions = {}

# ========================
# Helper Functions
# ========================

def preload_existing_files(folder_path):
    """Preloads existing files and their jpg, png, jpeg variations into a set for efficient lookup."""
    existing_files_set = set()
    for filename in os.listdir(folder_path):
        base_filename = os.path.splitext(filename)[0]
        existing_files_set.add(base_filename + ".png")
        existing_files_set.add(base_filename + ".jpg")
        existing_files_set.add(base_filename + ".jpeg")
    return existing_files_set

# ========================
# Main Script Execution
# ========================

async def process_zip_file(zip_file, config_pictures, existing_config_pics, executor, mods_dir):
    """Processes a single ZIP file, extracting specified config pictures and resizing them."""
    global extracted_count, skipped_count, error_count, log_messages, error_messages, original_extensions

    #print(f"mods_dir: {mods_dir}")  # Debug: Print mods_dir
    #print(f"zip_file: {zip_file}")  # Debug: Print zip_file

    full_zip_path = os.path.join(mods_dir, zip_file)

    if not os.path.exists(full_zip_path):
        error_message = f"Error: Zip file not found: {zip_file} in {mods_dir} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        error_messages.append(error_message)
        error_count += 1
        return

    loop = asyncio.get_event_loop()
    zip_skipped = False # Flag to indicate if any file in the zip was skipped

    try:
        with zipfile.ZipFile(full_zip_path, 'r') as zfile:
            for config_picture_path in config_pictures:
                # If the entire zip is already skipped, no need to process further files
                if zip_skipped:
                    continue

                # Extract the vehicle name and config name from the configPicturePath
                match = re.match(r"^vehicles/([^/]+)/([^/]+\.(png|jpg|jpeg))$", config_picture_path)
                if not match:
                    error_message = f"Unexpected internal path format: {config_picture_path} in {zip_file} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    error_messages.append(error_message)
                    error_count += 1
                    continue

                vehicle_name = match.group(1)
                config_picture_file = match.group(2)
                file_extension = match.group(3)
                config_name = os.path.splitext(config_picture_file)[0]

                # Construct the output file name (initially PNG)
                output_picture_name = f"vehicles--{vehicle_name}_{zip_file}--{config_name}.png" # Force PNG output
                output_picture_path = os.path.join(CONFIG_PICS_FOLDER, output_picture_name)

                # Check if the output file already exists
                if output_picture_name in existing_config_pics:
                    log_message = f"WOULD HAVE SKIPPED - Skipped (already exists): {output_picture_name} from {zip_file} - Skipping entire zip file at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    log_messages.append(log_message)
                    skipped_count += len(config_pictures) # Increment skipped count by the number of config pictures in this zip
                    zip_skipped = False # Set the flag to skip the rest of the files in this zip - CHANGED TO FALSE TO PREVENT ZIP SKIPPING
                    continue # Skip to the next config_picture_path

                try:
                    if config_picture_path not in zfile.namelist():
                        error_message = f"Error: {config_picture_path} not found in {zip_file} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        error_messages.append(error_message)
                        error_count += 1
                        continue

                    # Extract the specific picture (in memory), resize, and save
                    with zfile.open(config_picture_path) as source, open(output_picture_path, 'wb') as target:
                        try:
                            img = Image.open(source)
                            resized_img = img.resize((200, 110)) # Resize the image to 200x110
                            resized_img.save(target, "PNG") # Save the resized image as PNG, explicitly specifying format
                            original_extensions[output_picture_name] = file_extension # Store original extension
                        except Exception as image_error:
                            error_message = f"Error resizing image {config_picture_path} from {zip_file} at {time.strftime('%Y-%m-%d %H:%M:%S')}: {image_error} - Original Extension: {file_extension}\n" # Added original extension to error log
                            error_messages.append(error_message)
                            error_count += 1
                            # If resizing fails, we still count it as an error but continue processing other files.
                            continue # Skip to the next config_picture_path in the zip

                    # Log the successful extraction and resizing
                    log_message = f"Extracted and resized: {output_picture_name} from {zip_file} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    log_messages.append(log_message)
                    extracted_count += 1
                    existing_config_pics.add(output_picture_name)

                except Exception as e:
                    error_message = f"Error: Failed to extract {config_picture_path} from {zip_file} at {time.strftime('%Y-%m-%d %H:%M:%S')}: {e}\n"
                    error_messages.append(error_message)
                    error_count += 1
            if zip_skipped: # Log that the entire zip was skipped after processing all files in it (or skipping early)
                log_message = f"Skipped entire zip file: {zip_file} because at least one config picture already existed. at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                log_messages.append(log_message)


    except zipfile.BadZipFile:
        error_message = f"Error: Bad zip file encountered: {zip_file} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        error_messages.append(error_message)
        error_count += 1
        return

async def main():
    """Main function to control the script's execution flow."""
    global extracted_count, skipped_count, error_count, log_messages, error_messages, log_file_obj, error_log_obj, original_extensions

    # Step 3: Read and Parse Input File
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

        # Extract ZIP file name and config picture path using RegEx
        match = re.match(r"^(.*?) \(package\).*\"(.*?)\" \(config picture\)$", line)
        if not match:
            error_message = f"Malformed line at {index}: {line} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            error_messages.append(error_message)
            error_count += 1
            continue

        zip_file = match.group(1)
        config_picture_path = match.group(2)

        # Validate configPicturePath has a valid extension
        if not re.search(r"\.(png|jpg|jpeg)$", config_picture_path, re.IGNORECASE):
            error_message = f"Invalid file extension for config picture at line {index}: {config_picture_path} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            error_messages.append(error_message)
            error_count += 1
            continue

        # Group config picture paths by ZIP file
        if zip_file not in zip_files:
            zip_files[zip_file] = []
        if config_picture_path not in zip_files[zip_file]:
            zip_files[zip_file].append(config_picture_path)

    # Step 4: Preload Existing ConfigPics
    existing_config_pics = preload_existing_files(CONFIG_PICS_FOLDER)

    # Step 5: Process Each ZIP File Asynchronously
    with ThreadPoolExecutor(max_workers=5) as executor:  # Limit the number of threads
        tasks = []
        mods_dirs = [MODS_PATH, MODS_REPO_PATH]

        # Read BeamNG vehicles directory from file
        beamng_vehicles_dir_file = os.path.join(SCRIPT_PATH, "beamng_VANILLA_vehicles_folder.txt")

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
            for zip_file, config_pictures in zip_files.items():
                tasks.append(process_zip_file(zip_file, config_pictures, existing_config_pics, executor, mods_dir))
        await asyncio.gather(*tasks)

    # Step 6: Rename files back to original extension
    for output_picture_name, original_extension in original_extensions.items():
        png_filepath = os.path.join(CONFIG_PICS_FOLDER, output_picture_name)
        base_filename = os.path.splitext(output_picture_name)[0]
        new_filename = base_filename + "." + original_extension
        new_filepath = os.path.join(CONFIG_PICS_FOLDER, new_filename)
        try:
            os.rename(png_filepath, new_filepath)
            log_message = f"Renamed: {output_picture_name} to {new_filename} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            log_messages.append(log_message)
        except Exception as rename_error:
            error_message = f"Error renaming {output_picture_name} to {new_filename} at {time.strftime('%Y-%m-%d %H:%M:%S')}: {rename_error}\n"
            error_messages.append(error_message)

    # Step 7 & 8: Write Logs and Display Summary
    # Write all accumulated log messages to log files in one go
    log_file_obj.writelines(log_messages)
    error_log_obj.writelines(error_messages)

    print(f"Extraction and Renaming complete.\n\nFiles Extracted: {extracted_count}\nFiles Skipped: {skipped_count}\nErrors: {error_count}\n\nConfig pictures have been extracted, resized, and renamed in: {CONFIG_PICS_FOLDER}")

    end_time = time.time()
    execution_time_message = f"Execution time: {end_time - start_time:.2f} seconds\n"
    log_messages.append(execution_time_message) # Also add execution time to log messages
    log_file_obj.write(execution_time_message) # Write execution time to log file separately to ensure it's included even if log_messages is empty for some reason

    # Close log file objects
    log_file_obj.close()
    error_log_obj.close()


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())