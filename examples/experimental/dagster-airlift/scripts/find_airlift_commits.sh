#!/bin/bash

# Function to decrement version number
decrement_version() {
    echo "$1" | awk -F. '{
        if ($3 > 0) $3--;
        else if ($2 > 0) {$2--; $3=99;}
        else if ($1 > 0) {$1--; $2=99; $3=99;}
        print $1"."$2"."$3
    }'
}

# Get the current version
current_version=$(./scripts/extract_pypi_version.sh)

# Decrement the version
previous_version=$(decrement_version "$current_version")

# Get the upper hash
upper_hash=$(git log --format="%h" --grep="\[dagster-airlift\] $current_version" | head -n 1)

# Get the lower hash
lower_hash=$(git log --format="%h" --grep="\[dagster-airlift\] $previous_version" | head -n 1)

# If either hash is empty, exit with an error
if [ -z "$upper_hash" ] || [ -z "$lower_hash" ]; then
    echo "Error: Could not find one or both version commits."
    exit 1
fi

# Find commits, format them, print to stdout, and copy to clipboard
git log --format="- %s" ${lower_hash}..${upper_hash}^ | 
    grep -E "\[dagster-airlift\]" | 
    sed -E 's/\[(dagster-airlift)\]//g' | 
    sed -E 's/ \(#[0-9]+\)//g' |
    sed -E 's/^- ([a-f0-9]+) /- \1 /' |
    tee >(pbcopy)

# Inform the user that the list has been copied to the clipboard
echo -e "\nCommit list has been copied to the clipboard."