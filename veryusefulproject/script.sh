#!/bin/bash

excluded_dirs=("contrib" "static" "utils")

# Get the current directory
current_dir=$(pwd)

# Loop through the subdirectories
for dir in "$current_dir"/*/; do
    # Get the base name of the directory
        base_dir=$(basename "$dir")

            # Check if the directory should be excluded
                if [[ " ${excluded_dirs[@]} " =~ " ${base_dir} " ]]; then
                        continue
                            fi

                                # Execute the find commands in the directory
                                    find "$dir" -path "*/migrations/*.py" -not -name "__init__.py" -delete
                                        find "$dir" -path "*/migrations/*.pyc" -delete
                                        done

