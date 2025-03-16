import os
import zipfile
import re
import time
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor

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


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")