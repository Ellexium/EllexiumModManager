import os
import sys
import subprocess
import re
import time
import importlib.util

import asyncio # Import asyncio



def run_hidden_on_windows(command_list):
    """
    Run a command in a hidden console window on Windows. On other OS, runs normally.
    Equivalent to AHK's 'RunWait ... , Hide'.
    """
    if os.name == 'nt':
        # Creation of a STARTUPINFO object to hide the console window
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        subprocess.run(command_list, check=True, startupinfo=startupinfo)
    else:
        # Non-Windows: just run normally
        subprocess.run(command_list, check=True)

def is_file_in_use(filepath):
    """
    Check if a file is being used by another process.
    Returns True if the file is in use, False otherwise.
    """
    if not os.path.exists(filepath):
        return False  # File does not exist, hence not in use

    if os.name == 'nt':
        # On Windows, try to open the file in exclusive mode
        import msvcrt
        try:
            with open(filepath, 'r+', encoding="utf-8", errors="replace") as f:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            return False
        except IOError:
            return True
    else:
        # On Unix-like systems, it's more complex. If opening for append fails, assume it's in use.
        try:
            with open(filepath, 'a'):
                return False
        except IOError:
            return True

def get_bad_names_set(script_dir):
    """
    Loads the set of 'bad names' (typically vanilla vehicle folders/zip names).

    Tries to read from a folder specified in data/beamng_VANILLA_vehicles_folder.txt.
    Falls back to a hardcoded list if the file/folder is missing or invalid.

    Args:
        script_dir: The base directory path of the main script.

    Returns:
        A set containing lowercase 'bad names' (without .zip extension).
    """
    bad_names_list = []
    vanilla_vehicles_folder_file = os.path.join(script_dir, "data", "beamng_VANILLA_vehicles_folder.txt")

    if os.path.exists(vanilla_vehicles_folder_file):
        try:
            with open(vanilla_vehicles_folder_file, "r", encoding="utf-8", errors="replace") as f:
                vanilla_vehicles_path = f.readline().strip()
            # Check if the path read is actually a directory
            if os.path.isdir(vanilla_vehicles_path):
                print(f"INFO: Loading bad names dynamically from folder: {vanilla_vehicles_path}")
                for filename in os.listdir(vanilla_vehicles_path):
                    # Ensure it's a file and ends with .zip (case-insensitive)
                    full_file_path = os.path.join(vanilla_vehicles_path, filename)
                    if os.path.isfile(full_file_path) and filename.lower().endswith(".zip"):
                        # Add the base name (without extension), lowercased
                        bad_names_list.append(filename[:-4].lower())
                if not bad_names_list:
                     print(f"Warning: No '.zip' files found in '{vanilla_vehicles_path}'. Will use defaults if path wasn't invalid.")

            else:
                # Path from file exists but is not a directory
                print(f"Warning: Path '{vanilla_vehicles_path}' from '{vanilla_vehicles_folder_file}' is not a valid directory. Using defaults.")
                bad_names_list = [] # Force default usage
        except Exception as e:
            # Error reading the file or listing directory contents
            print(f"Warning: Error reading or processing '{vanilla_vehicles_folder_file}' or path '{vanilla_vehicles_path}': {e}. Using defaults.")
            bad_names_list = [] # Force default usage
    else:
        # The file specifying the vanilla folder path doesn't exist
        print(f"INFO: '{vanilla_vehicles_folder_file}' not found. Using default bad names.")
        bad_names_list = [] # Ensure defaults are used

    # Fallback to hardcoded defaults if dynamic loading failed or wasn't attempted
    if not bad_names_list:
        print("INFO: Using hardcoded default bad names.")
        badNamesRaw_default = """
atv
autobello
ball
barrels
barrier
barrier_plastic
barstow
bastion
blockwall
bluebuck
bolide
bollard
boxutility
boxutility_large
burnside
bx
cannon
caravan
cardboard_box
cargotrailer
chair
christmas_tree
citybus
common
cones
containerTrailer
couch
covet
delineator
dolly
dryvan
engine_props
etk800
etkc
etki
flail
flatbed
flipramp
frameless_dump
fridge
fullsize
gate
haybale
hopper
inflated_mat
kickplate
lansdale
large_angletester
large_bridge
large_cannon
large_crusher
large_hamster_wheel
large_roller
large_spinner
large_tilt
large_tire
legran
log_trailer
logs
mattress
md_series
metal_box
metal_ramp
midsize
midtruck
miramar
moonhawk
nine
pessima
piano
pickup
pigeon
porta_potty
racetruck
roadsigns
roamer
rockbouncer
rocks
rollover
sawhorse
sbr
scintilla
shipping_container
simple_traffic
steel_coil
streetlight
sunburst
suspensionbridge
tanker
testroller
tiltdeck
tirestacks
tirewall
trafficbarrel
tsfb
tub
tube
tv
unicycle
us_semi
utv
van
vivace
wall
weightpad
wendover
wigeon
woodcrate
woodplanks
"""
        bad_names_list = [line.strip().lower() for line in badNamesRaw_default.strip().splitlines() if line.strip()]

    # Convert the final list to a set for efficient lookup
    badSet = set(bad_names_list)
    # print(f"DEBUG: Generated badSet with {len(badSet)} items.") # Optional debug
    return badSet



# --- MODIFY modify_output_good ---
def modify_output_good(
    script_dir, # Still need script_dir to pass to get_bad_names_set
    output_file='data/outputGOOD.txt',
    config_info_dir='data/configInfo'
    # REMOVED badSet from parameters
):
    """
    Processes outputGOOD.txt, checks for info.json files, and modifies lines.
    If an entry lacks its specific info.json but an alternative exists,
    it appends a (USE ...) clause and adopts the casing of the internal folder
    name from the entry that provided the alternative info.json.
    Otherwise, it applies lowercasing based on the badSet logic.
    """
    # Resolve full paths
    output_path = os.path.join(script_dir, output_file)
    config_dir_path = os.path.join(script_dir, config_info_dir)

    # Basic file/dir existence checks
    if not os.path.isfile(output_path):
        print(f"Error: The file '{output_path}' does not exist.")
        return
    if not os.path.isdir(config_dir_path):
        print(f"Error: The directory '{config_dir_path}' does not exist.")
        return

    # Load the bad names set WITHIN this function now
    badSet = get_bad_names_set(script_dir) # <<< CALL THE NEW FUNCTION HERE

    # Gather existing info files
    existing_info_files = set(
        f for f in os.listdir(config_dir_path) if f.endswith('--info.json')
    )

    # --- Pass 1: Determine Canonical Casing ---
    canonical_casing_map = {}
    temp_entry = []
    temp_lines_for_pass1 = []
    try:
        with open(output_path, 'r', encoding='utf-8', errors='replace') as f:
            temp_lines_for_pass1 = f.readlines()
    except Exception as e:
        print(f"Error reading {output_path} for pass 1: {e}")
        return

    # Build canonical map (logic remains the same)
    for line in temp_lines_for_pass1:
        temp_entry.append(line)
        if 'core_vehicles.spawnNewVehicle' in line:
            package_name = None
            internal_folder = None
            for e_line in temp_entry:
                match = re.match(
                    r'(\S+)\s+\(package\)\s+-\s+"([^"]+)"\s+\(internal folder name\)',
                    e_line
                )
                if match:
                    package_name = match.group(1)
                    internal_folder = match.group(2)
                    break
            if package_name and internal_folder:
                lower_folder = internal_folder.lower()
                # Use lower for convention check, but use exact package name from line
                expected_info_convention = f'vehicles--{lower_folder}_{package_name}--info.json'
                # Check against actual files using lower_folder prefix for robustness?
                # Let's stick to the convention used elsewhere for consistency for now.
                if expected_info_convention in existing_info_files and lower_folder not in canonical_casing_map:
                    canonical_casing_map[lower_folder] = internal_folder
            temp_entry = []

    # --- Pass 2: Process and Modify ---
    modified_lines = []
    entry = []
    lines = temp_lines_for_pass1 # Reuse lines

    # Processing loop (logic remains the same, uses badSet loaded above)
    for line in lines:
        entry.append(line)
        if 'core_vehicles.spawnNewVehicle' in line:
            # ... (extraction of package_name, internal_folder, etc. remains same) ...
            current_spawn_line = line
            package_name = None
            internal_folder = None
            config_picture_line = None
            descriptive_line_index = -1

            for i, e_line in enumerate(entry):
                 match = re.match(
                     r'(\S+)\s+\(package\)\s+-\s+"([^"]+)"\s+\(internal folder name\)',
                     e_line
                 )
                 if match:
                     package_name = match.group(1)
                     internal_folder = match.group(2)
                     config_picture_line = e_line # Store the line itself
                     descriptive_line_index = i
                     break

            if not package_name or not internal_folder:
                modified_lines.extend(entry)
                entry = []
                continue

            lower_folder = internal_folder.lower()
            expected_info = f'vehicles--{lower_folder}_{package_name}--info.json'

            final_display_case = internal_folder
            final_spawn_arg_case = internal_folder
            use_clause = ""

            if expected_info not in existing_info_files:
                alternative_infos = [
                    f for f in existing_info_files
                    if f.startswith(f'vehicles--{lower_folder}_')
                ]
                if alternative_infos:
                    alternative_info_file = alternative_infos[0]
                    use_clause = f' (USE {alternative_info_file})'
                    canonical_case = canonical_casing_map.get(lower_folder, internal_folder)
                    final_display_case = canonical_case
                    final_spawn_arg_case = canonical_case
                else:
                    # No info, no alternative. Apply badSet logic.
                    if lower_folder in badSet: # <<< USES badSet loaded internally
                       final_display_case = lower_folder
                       final_spawn_arg_case = lower_folder
            else:
                # Expected info exists. Apply badSet logic.
                if lower_folder in badSet: # <<< USES badSet loaded internally
                    final_display_case = lower_folder
                    final_spawn_arg_case = lower_folder

            # Reconstruct entry (logic remains the same)
            new_entry = []
            for i, e_line in enumerate(entry):
                if i == descriptive_line_index and config_picture_line: # Ensure we have the line
                    # Reconstruct descriptive line
                    parts = config_picture_line.split('" (internal folder name) - ')
                    if len(parts) == 2:
                         new_descriptive_line = f'{package_name} (package)  - "{final_display_case}" (internal folder name) - {parts[1]}'
                         new_entry.append(new_descriptive_line)
                    else:
                         new_entry.append(e_line) # Fallback
                elif e_line == current_spawn_line:
                    # Reconstruct spawn line
                    spawn_match = re.match(r'(core_vehicles\.spawnNewVehicle\(")([^"]+)(")(.*)', e_line)
                    if spawn_match:
                        rest_of_spawn = spawn_match.group(4).rstrip()
                        # Config path uses original folder name from file generation step (implicit)
                        new_spawn_line = f'core_vehicles.spawnNewVehicle("{final_spawn_arg_case}"{rest_of_spawn}{use_clause}\n'
                        new_entry.append(new_spawn_line)
                    else:
                        new_entry.append(e_line) # Fallback
                else:
                    new_entry.append(e_line)

            modified_lines.extend(new_entry)
            entry = []

    # Handle leftovers and write files (logic remains the same)
    if entry:
        modified_lines.extend(entry)

    original_output = os.path.join(script_dir, 'data/outputGOOD (Original).txt')
    if os.path.exists(original_output):
        try:
            os.remove(original_output)
        except OSError as e:
            print(f"Warning: Could not remove existing original file: {e}")
            original_output = os.path.join(script_dir, f'data/outputGOOD (Original-{int(time.time())}).txt') # Avoid collision

    try:
        os.rename(output_path, original_output)
    except OSError as e:
         print(f"Error renaming {output_path} to {original_output}: {e}. Cannot write modified output.")
         return

    try:
        with open(output_path, 'w', encoding='utf-8', errors='replace') as f:
            f.writelines(modified_lines)
    except Exception as e:
        print(f"Error writing modified content to {output_path}: {e}")
        try:
            os.rename(original_output, output_path) # Attempt restore
            print("Attempted to restore original file name.")
        except OSError as restore_e:
            print(f"Failed to restore original file name: {restore_e}")
        return

    print(
        f"Modification complete. Original file moved to "
        f"'{os.path.basename(original_output)}', and updated file is '{os.path.basename(output_path)}'."
    )



def main():
    # --------------------------------------------------------------------------
    # 0) Script directory
    # --------------------------------------------------------------------------
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Modified to go one level up
    pic_info_extract_dir = os.path.join(script_dir, "data", "PicInfoExtractForNewMods")

    # --------------------------------------------------------------------------
    # 1) Run zippy.py if it exists (hidden window on Windows)
    # --------------------------------------------------------------------------
    zippy_module_name = "zippy"  # Name of zippy module file (without .py)
    zippy_module_path = os.path.join(script_dir, "modules/" f"{zippy_module_name}.py") # Path within 'modules'

    print(f"DEBUG (mod_command_line_config_gen.py): zippy_path (before check): {zippy_module_path}")
    if os.path.exists(zippy_module_path):
        print(f"DEBUG (mod_command_line_config_gen.py): zippy.py FOUND, attempting to run DIRECTLY...") # Debug - Direct Call Attempt

        # Dynamically load zippy.py as a module
        spec = importlib.util.spec_from_file_location(zippy_module_name, zippy_module_path)
        zippy_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(zippy_module)

        try:
            zippy_module.main()  # Call zippy.py's main() function DIRECTLY
            print(f"DEBUG (mod_command_line_config_gen.py): zippy.py's main() function executed DIRECTLY.") # Debug - Direct Call Success
        except Exception as e_zippy:
            print(f"Warning: Error running zippy.py directly: {e_zippy}") # Warning - Direct Call Error

    else:
        print(f"Warning: '{zippy_module_path}' not found. zippy.py was not run.")

    # --------------------------------------------------------------------------
    # 2) Define paths
    # --------------------------------------------------------------------------
    inputFile    = os.path.join(script_dir, "data/zip_structure.txt")
    goodFile     = os.path.join(script_dir, "data/outputGOOD.txt")
    badFile      = os.path.join(script_dir, "data/outputBAD.txt")
    subGoodFile  = os.path.join(script_dir, "data/PicInfoExtractForNewMods", "outputGOOD.txt")
    newModsFile  = os.path.join(script_dir, "data/NewMods.txt")

    print("--- mod_command_line_config_gen.py path debug---") # Print "mod_command_line_config_gen.py"
    print("Script Directory (script_dir):", script_dir)
    print("Input File Path (inputFile):", inputFile)
    print("Good File Path (goodFile):", goodFile)
    print("Bad File Path (badFile):", badFile)
    print("Sub Good File Path (subGoodFile):", subGoodFile)
    print("New Mods File Path (newModsFile):", newModsFile)


    # --------------------------------------------------------------------------
    # 2.1) Check if 'zip_structure.txt' is in use
    # --------------------------------------------------------------------------
    if is_file_in_use(inputFile):
        print(f"'{inputFile}' is currently in use. Waiting for 2 seconds...")
        time.sleep(10)
        if is_file_in_use(inputFile):
            print(f"'{inputFile}' is still in use.")
        else:
            print(f"'{inputFile}' is no longer in use. Proceeding.")

    # --------------------------------------------------------------------------
    # 3) Read the input file
    # --------------------------------------------------------------------------
    if not os.path.exists(inputFile):
        print(f"Error: Cannot find {inputFile}")
        sys.exit(1)

    try:
        with open(inputFile, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        print(f"Error: Failed to read file: {inputFile}\n{e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # 4) Read NewMods.txt if it exists
    # --------------------------------------------------------------------------
    
    '''
    newModsSet = set()
    if os.path.exists(newModsFile):
        try:
            with open(newModsFile, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        newModsSet.add(line.lower()) # Convert to lowercase here
        except:
            pass
    else:    
        print(f"something is wrong with newModsSet, forcing reading it anyways")

        try:
            with open(newModsFile, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        newModsSet.add(line.lower()) # Convert to lowercase here
        except:
            print(f"newModsFile not found is still broken")
            pass

    '''       


    print("\n--- Contents of 'data' directory: ---")
    try:
        data_files = os.listdir(script_dir + "/data")
        if data_files:
            for filename in data_files:
                print(f"- {filename}")
        else:
            print("data directory is empty.")
    except FileNotFoundError:
        print(f"Error: 'data' directory not found at path: {script_dir + '/data'}")
    except Exception as e:
        print(f"Error listing files in 'data' directory: {e}")




    print(f"Current working directory: {os.getcwd()}")
    newModsSet = set()

    print(f"Checking if input exists at: {inputFile}") # Added print for file existence check
    if os.path.exists(inputFile):
        print(f"inputFile exists") # Added print for read attempt
    else:
        print(f"inputFile does NOT exist.")

    print(f"Checking if newModsFile exists at: {newModsFile}") # Added print for file existence check
    
    if os.path.exists(newModsFile):
        print(f"newModsFile exists, attempting to read...") # Added print for read attempt
        try:
            with open(newModsFile, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        newModsSet.add(line.lower()) # Convert to lowercase here
            print(f"Successfully read newModsFile.") # Added print for successful read
        except Exception as e:
            print(f"Error reading newModsFile (first attempt): {e}")
            pass
    else:
        print(f"newModsFile does NOT exist.")
        print(f"something is wrong with newModsSet, forcing reading it anyways")

        try:
            with open(newModsFile, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        newModsSet.add(line.lower()) # Convert to lowercase here
            print(f"Successfully read newModsFile (forced read).") # Added print for forced read success
        except Exception as e:
            print(f"newModsFile not found and is still broken: {e}")
            pass

    # --- Print the contents of newModsSet ---
    print("\nContents of newModsSet:")
    if newModsSet:
        for item in newModsSet:
            print(f"- {item}")
    else:
        print("newModsSet content anyways")

        for item in newModsSet:
            print(f"- {item}")

        print("end of newModsSet content anyways")

    # --------------------------------------------------------------------------
    # 5) Hardcode the "bad names"
    # --------------------------------------------------------------------------
    # --- START OF MODIFICATION ---

    badSet = get_bad_names_set(script_dir)



    # --------------------------------------------------------------------------
    # 6) Parse zip_structure.txt content
    # --------------------------------------------------------------------------
    lines = content.splitlines()
    zips = []
    currentZip = ""
    currentVehicleData = {}
    currentZipPathsSet = set()

    def store_current_zip():
        """Helper to push the currently collected zip data into 'zips'."""
        nonlocal currentZip, currentVehicleData, currentZipPathsSet, zips
        if currentZip:
            temp = {
                "zipFile": currentZip,
                "vehicles": {},
                "filesSet": set(currentZipPathsSet)
            }
            for lv, vdat in currentVehicleData.items():
                temp["vehicles"][lv] = {
                    "origName": vdat["origName"],
                    "pcFiles": list(vdat["pcFiles"])
                }
            zips.append(temp)

    for line in lines:
        line = line.strip()
        if "Path = " not in line:
            continue

        if ".zip" in line:
            # Store previous zip before starting a new one
            store_current_zip()

            pathPart = re.sub(r'.*Path\s*=\s*', '', line)
            justZip = re.sub(r'.*[\\/]', '', pathPart)
            currentZip = justZip
            currentVehicleData = {}
            currentZipPathsSet = set()
            continue

        if not currentZip:
            continue

        pathPart2 = re.sub(r'.*Path\s*=\s*', '', line)
        pathPart2 = pathPart2.replace("\\", "/")
        currentZipPathsSet.add(pathPart2)

        if "vehicles/" in pathPart2.lower():
            match = re.search(r'vehicles/(.*)', pathPart2, re.IGNORECASE)
            if match:
                vehiclePath = match.group(1)
                arr = vehiclePath.split('/')
                if len(arr) >= 2:
                    rawVehicleName = arr[0]
                    lowerVehName = rawVehicleName.lower()

                    if lowerVehName not in currentVehicleData:
                        currentVehicleData[lowerVehName] = {
                            "origName": rawVehicleName,
                            "pcFiles": []
                        }

                    if vehiclePath.lower().endswith(".pc"):
                        remainder = arr[-1]
                        currentVehicleData[lowerVehName]["pcFiles"].append(remainder)

    # Store the last zip once done
    store_current_zip()

    # --------------------------------------------------------------------------
    # 7) Build final outputs
    # --------------------------------------------------------------------------
    goodOutput = []
    badOutput = []
    subGoodOutput = []

    badMap = {}
    noConfigList = []
    missingVehicleZips = []

    for zipObj in zips:
        zipFile = zipObj["zipFile"]
        vehDict = zipObj["vehicles"]
        zipPaths = zipObj["filesSet"]

        if len(vehDict) == 0:
            missingVehicleZips.append(zipFile)
            continue

        for lowerVeh, vData in vehDict.items():
            origVehName = vData["origName"]
            pcFiles = vData["pcFiles"]

            # --- START MODIFICATION (Define display/spawn names early) ---
            # Determine the vehicle name to use based on badSet
            spawn_vehicle_arg = origVehName    # Default for spawn command's first arg
            display_vehicle_name = origVehName # Default for descriptive lines
            if lowerVeh in badSet:
                spawn_vehicle_arg = origVehName.lower()
                display_vehicle_name = origVehName.lower() # Lowercase for display too
            # --- END MODIFICATION ---


            if pcFiles:
                for pcFile in pcFiles:
                    config_name = re.sub(r'\.pc$', '', pcFile, flags=re.IGNORECASE)
                    # Use original case for checking file existence in zipPaths and for config path
                    configBase = f"vehicles/{origVehName}/{config_name}"

                    extensions = ["jpg", "jpeg", "png"]
                    picLines = []
                    foundAny = False

                    for ext in extensions:
                        maybePic = f"{configBase}.{ext}"
                        if maybePic in zipPaths:
                            foundAny = True
                            # --- MODIFICATION: Use display_vehicle_name ---
                            picLines.append(
                                f"{zipFile} (package)  - "
                                f"\"{display_vehicle_name}\" (internal folder name) - "
                                f"\"{maybePic}\" (config picture)\r\n"
                            )
                            # --- END MODIFICATION ---

                    # Construct the spawn line using potentially modified spawn_vehicle_arg
                    # and original origVehName for the config path
                    spawnLine = (
                        f"core_vehicles.spawnNewVehicle(\"{spawn_vehicle_arg}\", "
                        f"{{config = 'vehicles/{origVehName}/{pcFile}'}})\r\n\r\n"
                    )


                    if foundAny:
                        for pl in picLines:
                            goodOutput.append(pl)
                        goodOutput.append(spawnLine)

                        # Check lowercase zip filename against lowercase newModsSet entries
                        if zipFile.lower() in newModsSet:
                            for pl in picLines:
                                subGoodOutput.append(pl)
                            subGoodOutput.append(spawnLine)
                    else:
                        # --- MODIFICATION: Use display_vehicle_name ---
                        placeholderLine = (
                            f"{zipFile} (package)  - "
                            f"\"{display_vehicle_name}\" (internal folder name) - "
                            f"\"IMAGE_NOT_FOUND-USEMISSING\" (config picture)\r\n"
                        )
                        # --- END MODIFICATION ---
                        goodOutput.append(placeholderLine)
                        goodOutput.append(spawnLine)

                        # Check lowercase zip filename against lowercase newModsSet entries
                        if zipFile.lower() in newModsSet:
                            subGoodOutput.append(placeholderLine)
                            subGoodOutput.append(spawnLine)

            # Add entries to badMap (conflicting names) or noConfigList
            if lowerVeh in badSet:
                if lowerVeh not in badMap:
                    badMap[lowerVeh] = {
                        "origName": origVehName, # Still store original name if needed elsewhere
                        "zips": set()
                    }
                badMap[lowerVeh]["zips"].add(zipFile)

            # These are NOT bad names, so use original name
            if lowerVeh not in badSet and not pcFiles:
                noConfigList.append({
                    "zipFile": zipFile,
                    "vehicleName": origVehName # Use original name here
                })

    # Process conflicting/vanilla names (these ARE bad names, so use lowercase)
    for lowerVeh, data in badMap.items():
        # Since it's in badMap, we know lowerVeh is in badSet
        # Use the lowercase version for display in badOutput
        display_name_for_bad_output = data["origName"].lower()
        badOutput.append(f"=== {display_name_for_bad_output} ===\r\n") # Header lowercase
        for zFile in data["zips"]:
            badOutput.append(
                f"{zFile} (package)  - "
                f"\"{display_name_for_bad_output}\" (internal folder name)\r\n\r\n" # Name lowercase
            )

    # Process mods with no .pc files (these are NOT bad names, use original case)
    if noConfigList:
        badOutput.append("=== DOES NOT CONTAIN CONFIGURATION FILES (UNDER VEHICLES FOLDER) ===\r\n")
        for item in noConfigList:
            # Use original vehicleName stored earlier
            badOutput.append(
                f"{item['zipFile']} (package)  - "
                f"\"{item['vehicleName']}\" (internal folder name)\r\n\r\n" # Name original case
            )

    # Process mods possibly not vehicles (only zip name shown)
    if missingVehicleZips:
        badOutput.append("=== POSSIBLY NOT VEHICLE MODS ===\r\n")
        for zName in missingVehicleZips:
            badOutput.append(f"{zName} (package)\r\n\r\n")

    # Write good/bad files
    if os.path.exists(goodFile):
        os.remove(goodFile)
    if os.path.exists(badFile):
        os.remove(badFile)

    with open(goodFile, "w", encoding="utf-8", errors="replace") as f:
        f.write("".join(goodOutput))

    with open(badFile, "w", encoding="utf-8", errors="replace") as f:
        f.write("".join(badOutput))

# Write subGoodOutput if we have newMods
    if newModsSet:
        sub_dir = os.path.join(script_dir, "data", "PicInfoExtractForNewMods")
        if not os.path.exists(sub_dir):
            os.makedirs(sub_dir, exist_ok=True)

        if os.path.exists(subGoodFile):
            os.remove(subGoodFile)

        if subGoodOutput:
            with open(subGoodFile, "w", encoding="utf-8", errors="replace") as f:
                f.write("".join(subGoodOutput))

    # Possibly run additional scripts if newModsSet is not empty
    if newModsSet:
        config_info_extractor_module_name = "configinfoextractorNEWMODS"
        config_pics_extractor_module_name = "configpicextractorNEWMODS"

        config_info_extractor_module_path = os.path.join(pic_info_extract_dir, f"{config_info_extractor_module_name}.py")
        config_pics_extractor_module_path = os.path.join(pic_info_extract_dir, f"{config_pics_extractor_module_name}.py")


        print("mod_command_config_gen") # Print "mod_command_config_gen"
        print(f"py1 path: {config_info_extractor_module_path}") # Print py1 path
        print(f"py2 path: {config_pics_extractor_module_path}") # Print py2 path
        print("mod_command_config_gen") # Print "mod_command_config_gen"


        if os.path.exists(config_info_extractor_module_path):
            print(f"DEBUG (mod_command_line_config_gen.py): {config_info_extractor_module_name}.py FOUND, attempting to run as FUNCTION...")
            spec1 = importlib.util.spec_from_file_location(config_info_extractor_module_name, config_info_extractor_module_path)
            config_info_extractor_module = importlib.util.module_from_spec(spec1)
            spec1.loader.exec_module(config_info_extractor_module)
            try:
                asyncio.run(config_info_extractor_module.main()) # Run the async main function using asyncio.run
                print(f"DEBUG (mod_command_line_config_gen.py): {config_info_extractor_module_name}.py's main() function executed as FUNCTION.")
            except Exception as e_info_extractor:
                print(f"Warning: Error running {config_info_extractor_module_name}.py as function: {e_info_extractor}")
        else:
            print(f"Warning: '{config_info_extractor_module_path}' not found, skipping.")

        if os.path.exists(config_pics_extractor_module_path):
            print(f"DEBUG (mod_command_line_config_gen.py): {config_pics_extractor_module_name}.py FOUND, attempting to run as FUNCTION...")
            spec2 = importlib.util.spec_from_file_location(config_pics_extractor_module_name, config_pics_extractor_module_path)
            config_pics_extractor_module = importlib.util.module_from_spec(spec2)
            spec2.loader.exec_module(config_pics_extractor_module)
            try:
                asyncio.run(config_pics_extractor_module.main()) # Run the async main function using asyncio.run
                print(f"DEBUG (mod_command_line_config_gen.py): {config_pics_extractor_module_name}.py's main() function executed as FUNCTION.")
            except Exception as e_pics_extractor:
                print(f"Warning: Error running {config_pics_extractor_module_name}.py as function: {e_pics_extractor}")

        else:
            print(f"Warning: '{config_pics_extractor_module_path}' not found, skipping.")

    else:
        print(f"Warning: 'newModsSet' did not get evaluated.")

    # --------------------------------------------------------------------------
    # 13) Modify outputGOOD.txt to produce "outputGOOD (Original).txt"
    #     and a new "outputGOOD.txt" with the second script's changes
    # --------------------------------------------------------------------------
    modify_output_good(script_dir, output_file='data/outputGOOD.txt', config_info_dir='data/configInfo')

    # Done
    #sys.exit(0)

if __name__ == "__main__":
    main()
