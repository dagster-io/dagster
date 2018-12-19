import os
import zipfile


def zip_folder(folder_path, output_path):
    contents = os.walk(folder_path)
    try:
        zip_file = zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED)
        for root, folders, files in contents:
            # Include all subfolders, including empty ones.
            for path in folders + files:
                absolute_path = os.path.join(root, path)
                zip_file.write(absolute_path)
    finally:
        zip_file.close()
