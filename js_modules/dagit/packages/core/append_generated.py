import glob
import os

if __name__ == "__main__":
    paths = glob.glob(r"src/**/types/*.ts", recursive=True)
    at_generated = "@" + "generated"  # construct string to fool phab
    for path in paths:
        # from https://stackoverflow.com/a/27950358
        command = f"""printf '%s\\n%s\\n' "// {at_generated}" "$(cat {path})" > {path}"""
        os.system(command)
