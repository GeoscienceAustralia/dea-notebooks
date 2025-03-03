#!/bin/bash

echo "Checking for duplicate .ipynb filenames in the incoming push..."

# Get the list of changed files in the push
while read oldrev newrev refname; do
    # Get all added/modified .ipynb files
    files=$(git diff --name-only --diff-filter=A "$oldrev" "$newrev" | grep '\.ipynb$' || true)

    if [[ -z "$files" ]]; then
        continue  # No new .ipynb files, skip checking
    fi

    # Extract just the filenames (ignore paths)
    filenames=$(basename -a $files)

    # Check for duplicates
    duplicates=$(echo "$filenames" | sort | uniq -d)

    if [[ -n "$duplicates" ]]; then
        echo "Duplicate .ipynb filenames detected in the push:"
        echo "$duplicates"
        echo "Push rejected! Ensure unique .ipynb filenames."
        exit 1  # Reject the push
    fi
done

exit 0  # Allow push if no duplicates

