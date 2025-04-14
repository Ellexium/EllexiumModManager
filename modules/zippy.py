import os
import zipfile


def get_zip_tree_optimized(zip_path, output_file, indent_str="    "):
    """
    Extracts and writes the folder structure and files from a ZIP file, optimized for speed
    by reducing write operations.
    """
    output_lines = []  # List to buffer output strings

    try:
        with zipfile.ZipFile(zip_path, 'r') as zfile:
            namelist = zfile.namelist()

            output_lines.append(f"Path = {zip_path}\n")  # Write zip path once

            dir_set = set()
            file_set = set()
            for name in namelist:
                normalized_name = name.replace("/", "\\") # Normalize once per item
                if normalized_name.endswith('\\'):
                    dir_set.add(normalized_name)
                else:
                    file_set.add(normalized_name)

            for dir_path in sorted(dir_set):
                output_lines.append(f"Path = {dir_path}\n") # Keep "Path =" for consistency
            for file_path in sorted(file_set):
                output_lines.append(f"Path = {file_path}\n") # Keep "Path =" for consistency

            output_lines.append("\n")  # Add blank line

            output_file.writelines(output_lines)  # Write all lines at once

    except zipfile.BadZipFile:
        output_file.write(f"Error: Invalid or corrupt ZIP file: {zip_path}\n")
    except Exception as e:
        output_file.write(f"Error processing ZIP file: {zip_path}: {e}\n")


def find_and_display_zip_trees_optimized(folder_path, output_file):
    """
    Searches a folder and its subfolders for ZIP files and writes their contents using the optimized function.
    """
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".zip"):
                zip_path = os.path.join(root, file)
                get_zip_tree_optimized(zip_path, output_file)
    output_file.write("\nDone.\n")


def main():

    script_dir = os.path.dirname(os.path.abspath(__file__))  # Level 1: modules directory
    parent_dir = os.path.dirname(script_dir)              # Level 0: project root directory
    grandparent_dir = os.path.dirname(parent_dir)  

    beamng_vehicles_dir_file = os.path.join(parent_dir, "data/beamng_VANILLA_vehicles_folder.txt")
    try:
        with open(beamng_vehicles_dir_file, "r", encoding="utf-8", errors="replace") as f:
            beamng_vehicles_dir = f.readline().strip()
    except FileNotFoundError:
        print(f"Error: {beamng_vehicles_dir_file} not found.")
        beamng_vehicles_dir = None

    output_file_path = os.path.join(parent_dir, "data/zip_structure.txt") # Changed output file name

    with open(output_file_path, "w", encoding="utf-8", errors="replace") as output_file:
        output_file.write("Searching in parent directory...\n")
        find_and_display_zip_trees_optimized(grandparent_dir, output_file)

        if beamng_vehicles_dir and os.path.exists(beamng_vehicles_dir):
            output_file.write("\nSearching in BeamNG vehicles directory...\n")
            find_and_display_zip_trees_optimized(beamng_vehicles_dir, output_file)
        elif beamng_vehicles_dir:
            print(f"Error: BeamNG vehicles directory '{beamng_vehicles_dir}' does not exist.")

    print(f"Output written to {output_file_path}")


if __name__ == "__main__":
    main()
