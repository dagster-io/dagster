#!/bin/bash

# Check if all required arguments are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <directory> <search_str> <replace_str>"
    exit 1
fi

directory="$1"
search_str="$2"
replace_str="$3"

# Check if the directory exists
if [ ! -d "$directory" ]; then
    echo "Error: Directory '$directory' does not exist."
    exit 1
fi

# Escape special characters in search_str and replace_str
search_str_escaped=$(printf '%s\n' "$search_str" | sed 's/[[\.*^$/]/\\&/g')
replace_str_escaped=$(printf '%s\n' "$replace_str" | sed 's/[[\.*^$/]/\\&/g')

# Use find to locate all .yml and .yaml files in the directory and its subdirectories
# Then use sed to perform the replacement in-place
find "$directory" \( -name "*.yml" -o -name "*.yaml" \) -type f -print0 | xargs -0 sed -i'' -e "s|$search_str_escaped|$replace_str_escaped|g"

echo "Replacement complete. Check the files in $directory for changes."