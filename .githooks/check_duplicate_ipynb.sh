#!/bin/bash

echo "Checking for duplicate .ipynb filenames..."

# Get all existing and staged .ipynb files
all_files=$(git ls-files | grep '\.ipynb$' || true)
staged_files=$(git diff --cached --name-only --diff-filter=A | grep '\.ipynb$' || true)

# Combine them to ensure we check for duplicates globally
combined_files=$(echo -e "$all_files\n$staged_files" | sort -u)

if [[ -z "$combined_files" ]]; then
    exit 0  # No .ipynb files found, allow commit
fi

# Extract only filenames (ignore paths)
filenames=$(basename -a $combined_files)

# Check for duplicates
duplicates=$(echo "$filenames" | sort | uniq -d)

if [[ -n "$duplicates" ]]; then
    echo "Duplicate .ipynb filenames detected in repository and staged changes:"
    echo "$duplicates"
    echo "Commit rejected! Ensure unique .ipynb filenames."
    exit 1  # Prevent commit
fi

exit 0  # Allow commit
