import os
import zipfile
import pathlib # Use pathlib for easier path handling
import re

# --- get_zip_tree_optimized remains the same ---
def get_zip_tree_optimized(zip_path, output_file, indent_str="    "):
    """
    Extracts and writes the folder structure and files from a ZIP file, optimized for speed
    by reducing write operations. (No changes needed here)
    """
    output_lines = []
    zip_path_str = str(zip_path)

    try:
        with zipfile.ZipFile(zip_path_str, 'r') as zfile:
            namelist = zfile.namelist()
            output_lines.append(f"Path = {zip_path_str}\n")
            dir_set = set()
            file_set = set()
            for name in namelist:
                normalized_name = name.replace("/", "\\")
                if name.endswith('/'):
                    dir_set.add(normalized_name)
                else:
                    file_set.add(normalized_name)

            for dir_path in sorted(list(dir_set)):
                output_lines.append(f"Path = {dir_path}\n")
            for file_path in sorted(list(file_set)):
                output_lines.append(f"Path = {file_path}\n")

            output_lines.append("\n")
            output_file.writelines(output_lines)

    except zipfile.BadZipFile:
        output_file.writelines([f"Error: Invalid or corrupt ZIP file: {zip_path_str}\n", "\n"])
    except Exception as e:
        output_file.writelines([f"Error processing ZIP file: {zip_path_str}: {e}\n", "\n"])

# --- find_all_zip_files remains the same ---
def find_all_zip_files(folder_path: pathlib.Path) -> list:
    """
    Recursively finds all .zip files within a given folder path.
    """
    zip_paths = []
    print(f"  Scanning for zip files in: {folder_path}")
    if not folder_path.is_dir():
        print(f"    Warning: Provided path is not a directory: {folder_path}")
        return zip_paths
    for item in folder_path.rglob('*.zip'):
        if item.is_file():
            zip_paths.append(item)
    print(f"    Found {len(zip_paths)} zip files.")
    return zip_paths

# --- check_zip_for_prioritization_criteria (MODIFIED NAME & LOGIC) ---
def check_zip_for_prioritization_criteria(zip_path: pathlib.Path) -> bool:
    """
    Checks if a zip file meets prioritization criteria (likely defines a base vehicle):
    1. Contains at least one .jbeam file inside a 'vehicles/[foldername]/' path.
    2. Contains an 'info.json' file inside that *same* 'vehicles/[foldername]/' path.

    Args:
        zip_path (pathlib.Path): Path to the zip file.

    Returns:
        bool: True if criteria are met, False otherwise.
    """
    vehicle_folders_with_jbeam = set()
    vehicle_folders_with_info = set()

    try:
        with zipfile.ZipFile(str(zip_path), 'r') as zf:
            for name in zf.namelist():
                normalized_name = name.replace('\\', '/').lower() # Normalize to forward slash and lowercase

                # Check for paths starting with vehicles/ followed by a folder name
                match = re.match(r"vehicles/([^/]+)/", normalized_name)
                if match:
                    foldername = match.group(1) # Extract folder name (e.g., 'pickup', 'rg_rc')

                    # Check if it's a jbeam within this folder
                    if normalized_name.endswith(".pc"):
                        vehicle_folders_with_jbeam.add(foldername)

                    # Check if it's an info.json within this folder
                    if os.path.basename(normalized_name) == "info.json":
                        vehicle_folders_with_info.add(foldername)

        # Check if there's any folder that has BOTH a jbeam AND an info.json
        common_folders = vehicle_folders_with_jbeam.intersection(vehicle_folders_with_info)

        if common_folders:
            print(f"    PRIORITIZE: {zip_path.name} (Found folder(s) with both .pc and info.json: {common_folders})")
            return True
        else:
            print(f"    DEFER: {zip_path.name} (No folder found containing both .pc and info.json)")
            return False

    except (zipfile.BadZipFile, FileNotFoundError, Exception) as e:
        print(f"    Warning: Could not check zip file {zip_path} for prioritization: {e}")
        return False # Assume does not meet criteria if error

# --- main function (MODIFIED to use new check function) ---
def main():
    script_dir = pathlib.Path(__file__).parent # modules directory
    parent_dir = script_dir.parent              # project root directory
    grandparent_dir = parent_dir.parent         # mods directory

    print(f"DEBUG (zippy): script_dir = {script_dir}")
    print(f"DEBUG (zippy): parent_dir = {parent_dir}")
    print(f"DEBUG (zippy): grandparent_dir = {grandparent_dir}")

    # Get BeamNG Vanilla Vehicles Path (logic unchanged)
    beamng_vehicles_dir = None
    # ... (logic to read beamng_VANILLA_vehicles_folder.txt) ...
    beamng_vehicles_dir_file = parent_dir / "data" / "beamng_VANILLA_vehicles_folder.txt"
    try:
        if beamng_vehicles_dir_file.is_file():
            beamng_vehicles_dir_str = beamng_vehicles_dir_file.read_text(encoding="utf-8").strip()
            if beamng_vehicles_dir_str:
                temp_path = pathlib.Path(beamng_vehicles_dir_str)
                if temp_path.is_dir():
                    beamng_vehicles_dir = temp_path
                    print(f"INFO (zippy): Found BeamNG vehicles directory: {beamng_vehicles_dir}")
                else: print(f"WARN (zippy): Path in {beamng_vehicles_dir_file.name} is not a valid directory: '{beamng_vehicles_dir_str}'")
            else: print(f"WARN (zippy): {beamng_vehicles_dir_file.name} is empty.")
        else: print(f"WARN (zippy): {beamng_vehicles_dir_file.name} not found.")
    except Exception as e: print(f"ERROR (zippy): Reading {beamng_vehicles_dir_file.name}: {e}")

    output_file_path = parent_dir / "data" / "zip_structure.txt"

    # Find all zip files
    print("\n--- Finding Zip Files ---")
    all_zip_paths = []
    all_zip_paths.extend(find_all_zip_files(grandparent_dir)) # Scan mods/repo parent
    if beamng_vehicles_dir:
        all_zip_paths.extend(find_all_zip_files(beamng_vehicles_dir))

    # Remove duplicates that might occur if repo is inside mods folder
    all_zip_paths = sorted(list(set(all_zip_paths)))
    print(f"\nTotal unique zip files found: {len(all_zip_paths)}")

    # --- Prioritize Zips based on NEW criteria ---
    print("\n--- Prioritizing Zips (Root info.json AND vehicles/ path) ---")
    prioritized_zips = []
    deferred_zips = []
    for zip_path in all_zip_paths:
        # Use the new checking function
        if check_zip_for_prioritization_criteria(zip_path):
            prioritized_zips.append(zip_path)
        else:
            deferred_zips.append(zip_path)

    # Combine for final processing order
    final_zip_order = prioritized_zips + deferred_zips
    print(f"\n--- Final Zip Processing Order ---")
    print(f"  Prioritized ({len(prioritized_zips)}): {[p.name for p in prioritized_zips]}") # Print names for brevity
    print(f"  Deferred ({len(deferred_zips)}): {[p.name for p in deferred_zips]}")

    # --- Write Output File in Prioritized Order ---
    print(f"\n--- Writing prioritized structure to {output_file_path} ---")
    try:
        with open(output_file_path, "w", encoding="utf-8", errors="replace") as output_file:
            output_file.write("--- Zip Structure (Prioritized: Root info.json AND vehicles/ path) ---\n\n")
            print(f"  Writing {len(final_zip_order)} zip file structures...")
            for zip_path in final_zip_order: # Iterate through the final combined list
                get_zip_tree_optimized(zip_path, output_file)
            output_file.write("\nDone.\n")
        print(f"Output written successfully.")
    except Exception as e:
        print(f"ERROR: Failed to write output file {output_file_path}: {e}")


if __name__ == "__main__":
    main()
