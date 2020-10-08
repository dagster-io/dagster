import shutil


def copy_directory(src, dest):
    try:
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".DS_Store"))
    # Directories are the same
    except shutil.Error as e:
        print("Directory not copied. Error: %s" % e)  # pylint: disable=print-call
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print("Directory not copied. Error: %s" % e)  # pylint: disable=print-call
