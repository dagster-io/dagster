import sys

if __name__ == "__main__":
    if sys.version_info >= (3, 9):
        sys.exit(0)
    sys.exit(1)
