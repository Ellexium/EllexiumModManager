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

def modify_output_good(
    script_dir, #this is the parent directory of the script
    output_file='data/outputGOOD.txt',
    config_info_dir='data/configInfo'
):
    """
    This function processes the outputGOOD.txt file, checks for corresponding info.json files
    in the configInfo directory, and modifies spawnNewVehicle lines if necessary.

    - script_dir: base directory path where this script runs.
    - output_file: filename of the outputGOOD to modify.
    - config_info_dir: subdirectory name containing info.json files.
    """
    # Resolve full paths
    parent_dir = script_dir  # Get the directory one level up from script_dir
    output_path = os.path.join(script_dir, output_file)
    config_dir_path = os.path.join(script_dir, config_info_dir)

    if not os.path.isfile(output_path):
        print(f"Error: The file '{output_path}' does not exist.")
        return

    if not os.path.isdir(config_dir_path):
        print(f"Error: The directory '{config_dir_path}' does not exist.")
        return

    # Gather all existing info.json filenames in configInfo
    existing_info_files = set(
        f for f in os.listdir(config_dir_path) if f.endswith('--info.json')
    )

    # Read all lines from the output file
    with open(output_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    modified_lines = []
    entry = []

    for line in lines:
        entry.append(line)

        # Check if the current line is a spawnNewVehicle line
        if 'core_vehicles.spawnNewVehicle' in line:
            # Extract package name and internal folder name from the accumulated entry
            package_name = None
            internal_folder = None

            for e_line in entry:
                match = re.match(
                    r'(\S+)\s+\(package\)\s+-\s+"([^"]+)"\s+\(internal folder name\)',
                    e_line
                )
                if match:
                    package_name = match.group(1)
                    internal_folder = match.group(2)
                    break  # Found what we needed; stop searching

            if not package_name or not internal_folder:
                # print("Warning: Could not find package name or internal folder name in an entry.")
                modified_lines.extend(entry)
                entry = []
                continue

            # Build the expected info.json filename
            expected_info = f'vehicles--{internal_folder}_{package_name}--info.json'

            if expected_info not in existing_info_files:
                # Look for alternative info.json files for the same internal folder
                alternative_infos = [
                    f for f in existing_info_files
                    if f.startswith(f'vehicles--{internal_folder}_') and f != expected_info
                ]

                if alternative_infos:
                    # Grab the first available alternative
                    alternative_info = alternative_infos[0]
                    new_entry = []
                    for e_line in entry:
                        if 'core_vehicles.spawnNewVehicle' in e_line:
                            e_line = e_line.rstrip('\n') + f' (USE {alternative_info})\n'
                        new_entry.append(e_line)
                    modified_lines.extend(new_entry)
                else:
                    # No alternative found; keep the original line
                    # print(f"Warning: No alternative info.json found for '{internal_folder}' in '{package_name}'.")
                    modified_lines.extend(entry)
            else:
                # The expected info.json exists; no modification needed
                modified_lines.extend(entry)

            # Clear the entry for the next batch
            entry = []

    # Handle any leftover lines (those not ending on a spawn line)
    if entry:
        modified_lines.extend(entry)

    # Rename original outputGOOD.txt to outputGOOD (Original).txt
    original_output = os.path.join(script_dir, 'data/outputGOOD (Original).txt')
    if os.path.exists(original_output):
        os.remove(original_output)  # ensure we don't run into a conflict
    os.rename(output_path, original_output)

    # Write the new, modified lines to outputGOOD.txt
    with open(output_path, 'w', encoding='utf-8', errors='replace') as f:
        f.writelines(modified_lines)

    print(
        f"Modification complete. Original file renamed to "
        f"'outputGOOD (Original).txt', and updated file is 'outputGOOD.txt'."
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
    badNamesRaw = []
    vanilla_vehicles_folder_file = os.path.join(script_dir, "data", "beamng_VANILLA_vehicles_folder.txt")
    if os.path.exists(vanilla_vehicles_folder_file):
        try:
            with open(vanilla_vehicles_folder_file, "r", encoding="utf-8", errors="replace") as f:
                vanilla_vehicles_path = f.readline().strip()
                if os.path.isdir(vanilla_vehicles_path):
                    for filename in os.listdir(vanilla_vehicles_path):
                        if filename.lower().endswith(".zip"):
                            badNamesRaw.append(filename[:-4]) # Remove .zip extension
                else:
                    print(f"Warning: Folder path '{vanilla_vehicles_path}' from '{vanilla_vehicles_folder_file}' is not a valid directory.")
        except Exception as e:
            print(f"Warning: Error reading or processing '{vanilla_vehicles_folder_file}': {e}")
    else:
        print(f"Warning: '{vanilla_vehicles_folder_file}' not found. Using default bad names.")
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
        badNamesRaw = [line.strip().lower() for line in badNamesRaw_default.strip().splitlines() if line.strip()]


    badSet = set()
    for ln in badNamesRaw: # Iterate directly over the list
        if ln:
            badSet.add(ln)
    # --- END OF MODIFICATION ---

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

            if pcFiles:
                for pcFile in pcFiles:
                    config_name = re.sub(r'\.pc$', '', pcFile, flags=re.IGNORECASE)
                    configBase = f"vehicles/{origVehName}/{config_name}"

                    extensions = ["jpg", "jpeg", "png"]
                    picLines = []
                    foundAny = False

                    for ext in extensions:
                        maybePic = f"{configBase}.{ext}"
                        if maybePic in zipPaths:
                            foundAny = True
                            picLines.append(
                                f"{zipFile} (package)  - "
                                f"\"{origVehName}\" (internal folder name) - "
                                f"\"{maybePic}\" (config picture)\r\n"
                            )

                    spawnLine = (
                        f"core_vehicles.spawnNewVehicle(\"{origVehName}\", "
                        f"{{config = 'vehicles/{origVehName}/{pcFile}'}})\r\n\r\n"
                    )

                    if foundAny:
                        for pl in picLines:
                            goodOutput.append(pl)
                        goodOutput.append(spawnLine)

                        if zipFile.lower() in newModsSet:
                            for pl in picLines:
                                subGoodOutput.append(pl)
                            subGoodOutput.append(spawnLine)
                    else:
                        placeholderLine = (
                            f"{zipFile} (package)  - "
                            f"\"{origVehName}\" (internal folder name) - "
                            f"\"IMAGE_NOT_FOUND-USEMISSING\" (config picture)\r\n"
                        )
                        goodOutput.append(placeholderLine)
                        goodOutput.append(spawnLine)

                        if zipFile.lower() in newModsSet:
                            subGoodOutput.append(placeholderLine)
                            subGoodOutput.append(spawnLine)

            if lowerVeh in badSet:
                if lowerVeh not in badMap:
                    badMap[lowerVeh] = {
                        "origName": origVehName,
                        "zips": set()
                    }
                badMap[lowerVeh]["zips"].add(zipFile)

            if lowerVeh not in badSet and not pcFiles:
                noConfigList.append({
                    "zipFile": zipFile,
                    "vehicleName": origVehName
                })

    for lowerVeh, data in badMap.items():
        vName = data["origName"]
        badOutput.append(f"=== {vName} ===\r\n")
        for zFile in data["zips"]:
            badOutput.append(
                f"{zFile} (package)  - "
                f"\"{vName}\" (internal folder name)\r\n\r\n"
            )

    if noConfigList:
        badOutput.append("=== DOES NOT CONTAIN CONFIGURATION FILES (UNDER VEHICLES FOLDER) ===\r\n")
        for item in noConfigList:
            badOutput.append(
                f"{item['zipFile']} (package)  - "
                f"\"{item['vehicleName']}\" (internal folder name)\r\n\r\n"
            )

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